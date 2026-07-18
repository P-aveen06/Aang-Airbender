from __future__ import annotations

from dataclasses import dataclass

from .config import Phase1Config
from .types import Finger, HandFeatures


@dataclass(frozen=True, slots=True)
class PoseClassification:
    strict_index_point: bool
    relaxed_pointer: bool
    two_finger: bool
    fist: bool
    wake_palm: bool
    index_pinch_closed: bool
    index_pinch_open: bool
    middle_pinch_closed: bool

    @property
    def pointer_family(self) -> bool:
        return self.strict_index_point or self.relaxed_pointer


def classify_pose(features: HandFeatures, config: Phase1Config) -> PoseClassification:
    feature_settings = config.section("features")
    pinch = config.section("pinch")
    poses = config.section("poses")
    extended = features.finger_extension
    confidence_valid = features.confidence >= float(feature_settings["min_valid_confidence"])
    index_closed = features.pinch_ratio_index < float(pinch["closed_ratio"])
    index_open = features.pinch_ratio_index > float(pinch["open_ratio"])
    middle_closed = features.pinch_ratio_middle < float(pinch["closed_ratio"])
    middle_cross_open = features.pinch_ratio_middle > float(pinch["cross_pinch_open_ratio"])
    index_cross_open = features.pinch_ratio_index > float(pinch["cross_pinch_open_ratio"])
    non_pinching = index_open and not middle_closed

    index = extended[Finger.INDEX.value]
    middle = extended[Finger.MIDDLE.value]
    ring = extended[Finger.RING.value]
    pinky = extended[Finger.PINKY.value]
    thumb = extended[Finger.THUMB.value]
    curled_threshold = float(feature_settings["max_curled_joint_angle_degrees"])
    curled = tuple(
        any(angle <= curled_threshold for angle in angles)
        for angles in features.finger_joint_angles_degrees
    )
    strict_point = (
        confidence_valid
        and index
        and all(curled[finger.value] for finger in (Finger.MIDDLE, Finger.RING, Finger.PINKY))
    )
    relaxed = confidence_valid and index and middle and ring and non_pinching
    separation_valid = features.index_middle_separation_ratio >= float(
        poses["min_two_finger_separation_ratio"]
    )
    two_finger = (
        confidence_valid
        and index
        and middle
        and curled[Finger.RING.value]
        and curled[Finger.PINKY.value]
        and separation_valid
        and non_pinching
    )
    fist = confidence_valid and all(
        curled[finger.value] for finger in (Finger.INDEX, Finger.MIDDLE, Finger.RING, Finger.PINKY)
    )
    wake = (
        confidence_valid
        and thumb
        and index
        and middle
        and ring
        and pinky
        and features.palm_facing_score >= float(feature_settings["min_palm_facing_score"])
        and non_pinching
    )
    return PoseClassification(
        strict_index_point=strict_point and not two_finger and non_pinching,
        relaxed_pointer=relaxed,
        two_finger=two_finger,
        fist=fist,
        wake_palm=wake,
        index_pinch_closed=confidence_valid and index_closed and middle_cross_open,
        index_pinch_open=confidence_valid and index_open,
        middle_pinch_closed=confidence_valid and middle_closed and index_cross_open,
    )
