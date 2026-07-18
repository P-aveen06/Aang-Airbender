from __future__ import annotations

from dataclasses import dataclass

from .config import Phase1Config
from .types import Finger, HandFeatures


@dataclass(frozen=True, slots=True)
class PoseClassification:
    strict_index_point: bool
    index_pinch_closed: bool
    index_pinch_open: bool
    confidence_valid: bool

    @property
    def pointer_family(self) -> bool:
        return self.strict_index_point


def classify_pose(features: HandFeatures, config: Phase1Config) -> PoseClassification:
    feature_settings = config.section("features")
    pinch = config.section("pinch")
    confidence_valid = features.confidence >= float(feature_settings["min_valid_confidence"])
    extended = features.finger_extension
    curled_threshold = float(feature_settings["max_curled_joint_angle_degrees"])
    curled = tuple(
        any(angle <= curled_threshold for angle in angles)
        for angles in features.finger_joint_angles_degrees
    )
    four_fingers_curled = all(
        curled[finger.value] for finger in (Finger.INDEX, Finger.MIDDLE, Finger.RING, Finger.PINKY)
    )
    index_closed = (
        confidence_valid
        and features.pinch_ratio_index < float(pinch["closed_ratio"])
        and not four_fingers_curled
    )
    index_open = confidence_valid and features.pinch_ratio_index > float(pinch["open_ratio"])
    strict_point = (
        confidence_valid
        and index_open
        and extended[Finger.INDEX.value]
        and all(curled[finger.value] for finger in (Finger.MIDDLE, Finger.RING, Finger.PINKY))
    )
    return PoseClassification(
        strict_index_point=strict_point,
        index_pinch_closed=index_closed,
        index_pinch_open=index_open,
        confidence_valid=confidence_valid,
    )
