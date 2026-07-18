from dataclasses import replace

from aang_airbender.config import load_config
from aang_airbender.poses import classify_pose
from aang_airbender.types import HandFeatures, Point2


def features(
    extension: tuple[bool, bool, bool, bool, bool],
    *,
    index_ratio: float = 0.8,
    confidence: float = 0.99,
) -> HandFeatures:
    angles = tuple((170.0, 170.0) if item else (90.0, 90.0) for item in extension)
    return HandFeatures(
        index_tip=Point2(0.5, 0.5),
        palm_center=Point2(0.5, 0.5),
        palm_orientation_radians=0.0,
        palm_facing_score=1.0,
        hand_scale=0.2,
        image_hand_scale=0.2,
        finger_extension=extension,
        finger_joint_angles_degrees=angles,
        pinch_ratio_index=index_ratio,
        pinch_ratio_middle=0.8,
        index_middle_separation_ratio=0.8,
        thumb_direction_down_ratio=0.0,
        palm_velocity=Point2(0.0, 0.0),
        anchor_velocity=Point2(0.0, 0.0),
        confidence=confidence,
        timestamp_ns=1,
    )


def test_only_index_extended_is_the_pointer_pose() -> None:
    config = load_config()

    point = classify_pose(features((False, True, False, False, False)), config)
    open_palm = classify_pose(features((True, True, True, True, True)), config)
    two_fingers = classify_pose(features((False, True, True, False, False)), config)
    fist = classify_pose(features((False, False, False, False, False)), config)

    assert point.strict_index_point
    assert not open_palm.strict_index_point
    assert not two_fingers.strict_index_point
    assert not fist.strict_index_point


def test_right_thumb_index_pinch_breaks_pointer_pose() -> None:
    pose = classify_pose(
        features((False, True, False, False, False), index_ratio=0.30), load_config()
    )

    assert pose.index_pinch_closed
    assert not pose.strict_index_point


def test_left_pinch_uses_configured_hysteresis_dead_zone() -> None:
    config = load_config()
    base = features((False, True, False, False, False), index_ratio=0.30)

    assert classify_pose(base, config).index_pinch_closed
    dead_zone = classify_pose(replace(base, pinch_ratio_index=0.40), config)
    assert not dead_zone.index_pinch_closed
    assert not dead_zone.index_pinch_open
    assert classify_pose(replace(base, pinch_ratio_index=0.60), config).index_pinch_open


def test_fist_shape_cannot_become_a_click_pinch() -> None:
    pose = classify_pose(
        features((False, False, False, False, False), index_ratio=0.20), load_config()
    )

    assert not pose.index_pinch_closed


def test_low_confidence_hand_emits_no_active_pose() -> None:
    pose = classify_pose(
        features((False, True, False, False, False), index_ratio=0.30, confidence=0.2),
        load_config(),
    )

    assert not pose.confidence_valid
    assert not pose.strict_index_point
    assert not pose.index_pinch_closed
    assert not pose.index_pinch_open
