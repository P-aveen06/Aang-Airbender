from dataclasses import replace

from aang_airbender.config import load_config
from aang_airbender.poses import classify_pose
from aang_airbender.types import HandFeatures, Point2


def features(
    extension: tuple[bool, bool, bool, bool, bool],
    *,
    index_ratio: float = 0.8,
    middle_ratio: float = 0.8,
    facing: float = 1.0,
) -> HandFeatures:
    angles = tuple((170.0, 170.0) if item else (90.0, 90.0) for item in extension)
    return HandFeatures(
        palm_center=Point2(0.5, 0.5),
        palm_orientation_radians=0.0,
        palm_facing_score=facing,
        hand_scale=0.2,
        finger_extension=extension,
        finger_joint_angles_degrees=angles,
        pinch_ratio_index=index_ratio,
        pinch_ratio_middle=middle_ratio,
        palm_velocity=Point2(0.0, 0.0),
        anchor_velocity=Point2(0.0, 0.0),
        confidence=0.99,
        timestamp_ns=1,
    )


def test_strict_index_point_and_fist_are_distinct() -> None:
    config = load_config()

    point = classify_pose(features((False, True, False, False, False)), config)
    fist = classify_pose(features((False, False, False, False, False)), config)

    assert point.strict_index_point
    assert point.pointer_family
    assert not point.fist
    assert fist.fist
    assert not fist.pointer_family


def test_open_palm_is_wake_and_is_available_as_relaxed_pointer_by_context() -> None:
    pose = classify_pose(features((True, True, True, True, True)), load_config())

    assert pose.wake_palm
    assert pose.relaxed_pointer


def test_two_finger_pose_requires_ring_and_pinky_curled() -> None:
    config = load_config()

    assert classify_pose(features((False, True, True, False, False)), config).two_finger
    assert not classify_pose(features((False, True, True, True, False)), config).two_finger


def test_index_pinch_uses_hysteresis_and_cross_pinch_exclusion() -> None:
    config = load_config()
    base = features((False, True, False, False, False), index_ratio=0.30, middle_ratio=0.80)

    assert classify_pose(base, config).index_pinch_closed
    assert not classify_pose(replace(base, pinch_ratio_index=0.40), config).index_pinch_closed
    assert not classify_pose(replace(base, pinch_ratio_middle=0.30), config).index_pinch_closed
    assert classify_pose(replace(base, pinch_ratio_index=0.60), config).index_pinch_open


def test_experimental_middle_pinch_requires_index_cross_pinch_open() -> None:
    config = load_config()

    assert classify_pose(
        features((False, True, False, False, False), index_ratio=0.8, middle_ratio=0.3),
        config,
    ).middle_pinch_closed
    assert not classify_pose(
        features((False, True, False, False, False), index_ratio=0.3, middle_ratio=0.3),
        config,
    ).middle_pinch_closed
