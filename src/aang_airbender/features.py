from __future__ import annotations

import math
from collections.abc import Sequence
from typing import cast

from .config import Phase1Config
from .types import HandFeatures, HandState, Point2, Point3

PALM_INDICES = (0, 5, 9, 13, 17)
FINGER_CHAINS = (
    (1, 2, 3, 4),
    (5, 6, 7, 8),
    (9, 10, 11, 12),
    (13, 14, 15, 16),
    (17, 18, 19, 20),
)


def distance(a: Point3, b: Point3) -> float:
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)


def joint_angle_degrees(a: Point2, vertex: Point2, c: Point2) -> float:
    first = (a.x - vertex.x, a.y - vertex.y)
    second = (c.x - vertex.x, c.y - vertex.y)
    denominator = math.hypot(*first) * math.hypot(*second)
    if denominator == 0.0:
        return 0.0
    cosine = max(
        -1.0,
        min(1.0, (first[0] * second[0] + first[1] * second[1]) / denominator),
    )
    return math.degrees(math.acos(cosine))


def palm_center(landmarks: Sequence[Point3], weights: Sequence[float]) -> Point2:
    if len(landmarks) != 21:
        raise ValueError("Exactly 21 landmarks are required")
    if len(weights) != len(PALM_INDICES) or sum(weights) <= 0.0:
        raise ValueError("A positive weight is required for each palm landmark")
    total = sum(weights)
    return Point2(
        sum(
            landmarks[index].x * weight for index, weight in zip(PALM_INDICES, weights, strict=True)
        )
        / total,
        sum(
            landmarks[index].y * weight for index, weight in zip(PALM_INDICES, weights, strict=True)
        )
        / total,
    )


def palm_relative_points(landmarks: Sequence[Point3], center: Point2) -> tuple[Point2, ...]:
    wrist = landmarks[0]
    middle_mcp = landmarks[9]
    axis_y = (wrist.x - middle_mcp.x, wrist.y - middle_mcp.y)
    length = math.hypot(*axis_y)
    if length == 0.0:
        raise ValueError("Palm orientation is undefined")
    unit_y = (axis_y[0] / length, axis_y[1] / length)
    unit_x = (unit_y[1], -unit_y[0])
    return tuple(
        Point2(
            (item.x - center.x) * unit_x[0] + (item.y - center.y) * unit_x[1],
            (item.x - center.x) * unit_y[0] + (item.y - center.y) * unit_y[1],
        )
        for item in landmarks
    )


def finger_joint_angles(local: Sequence[Point2]) -> tuple[tuple[float, ...], ...]:
    return tuple(
        tuple(
            joint_angle_degrees(
                local[chain[offset]], local[chain[offset + 1]], local[chain[offset + 2]]
            )
            for offset in range(len(chain) - 2)
        )
        for chain in FINGER_CHAINS
    )


def palm_facing_score(landmarks: Sequence[Point3]) -> float:
    wrist = landmarks[0]
    index = landmarks[5]
    pinky = landmarks[17]
    first = (index.x - wrist.x, index.y - wrist.y, index.z - wrist.z)
    second = (pinky.x - wrist.x, pinky.y - wrist.y, pinky.z - wrist.z)
    normal = (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )
    magnitude = math.sqrt(sum(component * component for component in normal))
    return abs(normal[2]) / magnitude if magnitude > 0.0 else 0.0


def extract_features(
    hand: HandState,
    config: Phase1Config,
    *,
    previous: HandFeatures | None = None,
) -> HandFeatures:
    if not hand.valid or len(hand.image_landmarks) != 21:
        raise ValueError("Cannot extract features from an invalid hand state")
    settings = config.section("features")
    weights = tuple(float(value) for value in settings["palm_center_weights"])
    center = palm_center(hand.image_landmarks, weights)
    local = palm_relative_points(hand.image_landmarks, center)
    angles = finger_joint_angles(local)
    extension_threshold = float(settings["min_joint_angle_degrees"])
    extended = cast(
        tuple[bool, bool, bool, bool, bool],
        tuple(all(angle >= extension_threshold for angle in finger) for finger in angles),
    )
    scale_landmarks = (
        hand.world_landmarks if len(hand.world_landmarks) == 21 else hand.image_landmarks
    )
    scale = distance(scale_landmarks[5], scale_landmarks[17])
    if scale <= 0.0:
        raise ValueError("Hand scale is zero")
    thumb_tip = scale_landmarks[4]
    index_tip = scale_landmarks[8]
    middle_tip = scale_landmarks[12]
    elapsed_seconds = (
        (hand.capture_timestamp_ns - previous.timestamp_ns) / 1_000_000_000
        if previous is not None
        else 0.0
    )
    velocity = Point2(0.0, 0.0)
    if previous is not None and elapsed_seconds > 0.0:
        velocity = Point2(
            (center.x - previous.palm_center.x) / elapsed_seconds,
            (center.y - previous.palm_center.y) / elapsed_seconds,
        )
    wrist = hand.image_landmarks[0]
    middle = hand.image_landmarks[9]
    return HandFeatures(
        palm_center=center,
        palm_orientation_radians=math.atan2(wrist.y - middle.y, wrist.x - middle.x),
        palm_facing_score=palm_facing_score(hand.image_landmarks),
        hand_scale=scale,
        finger_extension=extended,
        finger_joint_angles_degrees=angles,
        pinch_ratio_index=distance(thumb_tip, index_tip) / scale,
        pinch_ratio_middle=distance(thumb_tip, middle_tip) / scale,
        palm_velocity=velocity,
        anchor_velocity=velocity,
        confidence=hand.handedness_score,
        timestamp_ns=hand.capture_timestamp_ns,
    )
