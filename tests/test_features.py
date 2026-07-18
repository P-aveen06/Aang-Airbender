import math
from dataclasses import replace

import pytest

from aang_airbender.config import load_config
from aang_airbender.features import (
    extract_features,
    joint_angle_degrees,
    palm_center,
    palm_relative_points,
)
from aang_airbender.types import HandState, Point2, Point3


def synthetic_open_hand() -> tuple[Point3, ...]:
    points = [Point3(0.5, 0.9, 0.0) for _ in range(21)]
    points[0] = Point3(0.5, 0.9, 0.0)
    chains = {
        1: [(0.32, 0.72), (0.25, 0.60), (0.20, 0.48), (0.15, 0.38)],
        5: [(0.38, 0.66), (0.36, 0.50), (0.34, 0.34), (0.32, 0.18)],
        9: [(0.50, 0.64), (0.50, 0.46), (0.50, 0.28), (0.50, 0.10)],
        13: [(0.62, 0.66), (0.64, 0.50), (0.66, 0.35), (0.68, 0.21)],
        17: [(0.72, 0.71), (0.75, 0.57), (0.78, 0.44), (0.81, 0.33)],
    }
    for start, coordinates in chains.items():
        for offset, (x, y) in enumerate(coordinates):
            points[start + offset] = Point3(x, y, 0.0)
    return tuple(points)


def state(landmarks: tuple[Point3, ...], timestamp_ns: int = 1_000_000_000) -> HandState:
    return HandState(
        image_landmarks=landmarks,
        world_landmarks=(),
        handedness="Left",
        handedness_score=0.99,
        frame_id=1,
        capture_timestamp_ns=timestamp_ns,
        mediapipe_timestamp_ms=timestamp_ns // 1_000_000,
        callback_timestamp_ns=timestamp_ns,
        valid=True,
    )


def test_joint_angle_is_rotation_invariant() -> None:
    assert joint_angle_degrees(Point2(-1, 0), Point2(0, 0), Point2(1, 0)) == pytest.approx(180)
    assert joint_angle_degrees(Point2(0, -1), Point2(0, 0), Point2(0, 1)) == pytest.approx(180)


def test_weighted_palm_centroid_uses_required_five_landmarks() -> None:
    landmarks = list(synthetic_open_hand())
    center = palm_center(landmarks, (1, 1, 2, 1, 1))

    assert center == Point2(
        pytest.approx(
            (
                landmarks[0].x
                + landmarks[5].x
                + 2 * landmarks[9].x
                + landmarks[13].x
                + landmarks[17].x
            )
            / 6
        ),
        pytest.approx(
            (
                landmarks[0].y
                + landmarks[5].y
                + 2 * landmarks[9].y
                + landmarks[13].y
                + landmarks[17].y
            )
            / 6
        ),
    )


def test_palm_relative_transform_aligns_wrist_middle_axis() -> None:
    landmarks = synthetic_open_hand()
    center = palm_center(landmarks, (1, 1, 1, 1, 1))
    local = palm_relative_points(landmarks, center)

    assert local[0].x == pytest.approx(local[9].x)
    assert local[0].y > local[9].y


def test_extract_features_reports_open_fingers_scale_pinch_and_velocity() -> None:
    config = load_config()
    first = extract_features(state(synthetic_open_hand()), config)
    moved = tuple(Point3(point.x + 0.02, point.y, point.z) for point in synthetic_open_hand())
    second = extract_features(state(moved, 1_100_000_000), config, previous=first)

    assert all(first.finger_extension)
    assert first.hand_scale > 0
    assert first.image_hand_scale > 0
    assert math.isfinite(first.pinch_ratio_index)
    assert first.index_middle_separation_ratio > 0
    assert first.palm_facing_score == pytest.approx(1.0)
    assert second.palm_velocity.x == pytest.approx(0.07)
    assert second.palm_velocity.y == pytest.approx(0.0)


def test_palm_facing_score_rejects_back_of_hand_orientation() -> None:
    config = load_config()
    left = extract_features(state(synthetic_open_hand()), config)
    back_facing_state = replace(state(synthetic_open_hand()), handedness="Right")
    back_facing = extract_features(back_facing_state, config)

    assert left.palm_facing_score == pytest.approx(1.0)
    assert back_facing.palm_facing_score == pytest.approx(0.0)
