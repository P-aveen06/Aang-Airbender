from dataclasses import replace

from aang_airbender.config import load_config
from aang_airbender.fsm import EngagementState, GestureEngine, GestureState
from aang_airbender.poses import PoseClassification
from aang_airbender.types import HandFeatures, IntentKind, Point2

MS = 1_000_000


def feature(
    now_ns: int, *, x: float = 0.5, y: float = 0.5, vx: float = 0, vy: float = 0
) -> HandFeatures:
    return HandFeatures(
        palm_center=Point2(x, y),
        palm_orientation_radians=0,
        palm_facing_score=1,
        hand_scale=0.2,
        image_hand_scale=0.2,
        finger_extension=(True, True, True, True, True),
        finger_joint_angles_degrees=((170, 170),) * 5,
        pinch_ratio_index=0.8,
        pinch_ratio_middle=0.8,
        index_middle_separation_ratio=0.8,
        palm_velocity=Point2(vx, vy),
        anchor_velocity=Point2(vx, vy),
        confidence=0.99,
        timestamp_ns=now_ns,
    )


def pose(**changes: bool) -> PoseClassification:
    base = PoseClassification(
        strict_index_point=False,
        relaxed_pointer=False,
        two_finger=False,
        fist=False,
        wake_palm=False,
        index_pinch_closed=False,
        index_pinch_open=True,
        middle_pinch_closed=False,
    )
    return replace(base, **changes)


def engaged_engine() -> tuple[GestureEngine, int]:
    engine = GestureEngine(load_config())
    engine.update(feature(0), pose(wake_palm=True, relaxed_pointer=True), 0)
    intents = engine.update(
        feature(900 * MS),
        pose(wake_palm=True, relaxed_pointer=True),
        900 * MS,
    )
    assert engine.engagement is EngagementState.ENGAGED
    assert any(intent.kind is IntentKind.ENGAGE_REQUEST for intent in intents)
    return engine, 900 * MS


def test_wake_uses_elapsed_time_not_frame_count() -> None:
    engine = GestureEngine(load_config())
    wake = pose(wake_palm=True)

    for now in (0, 100 * MS, 899 * MS):
        engine.update(feature(now), wake, now)
    assert engine.engagement is EngagementState.ARMING

    engine.update(feature(900 * MS), wake, 900 * MS)
    assert engine.engagement is EngagementState.ENGAGED


def test_stable_index_pinch_emits_down_then_hysteretic_release_emits_up() -> None:
    engine, now = engaged_engine()
    closed = pose(index_pinch_closed=True, index_pinch_open=False)

    assert not engine.update(feature(now + MS), closed, now + MS)
    start = engine.update(feature(now + 101 * MS), closed, now + 101 * MS)
    assert [item.kind for item in start] == [IntentKind.PINCH_START]
    assert engine.gesture is GestureState.DRAGGING

    dead_zone = pose(index_pinch_closed=False, index_pinch_open=False)
    assert [
        item.kind for item in engine.update(feature(now + 150 * MS), dead_zone, now + 150 * MS)
    ] == [IntentKind.POINT]
    end = engine.update(feature(now + 160 * MS), pose(index_pinch_open=True), now + 160 * MS)
    assert [item.kind for item in end] == [IntentKind.PINCH_END]


def test_tracking_loss_during_drag_releases_at_grace_and_disengages_later() -> None:
    engine, now = engaged_engine()
    closed = pose(index_pinch_closed=True, index_pinch_open=False)
    engine.update(feature(now + MS), closed, now + MS)
    engine.update(feature(now + 101 * MS), closed, now + 101 * MS)

    assert not engine.update(None, None, now + 110 * MS)
    assert not engine.update(None, None, now + 309 * MS)
    release = engine.update(None, None, now + 310 * MS)
    assert [item.kind for item in release] == [IntentKind.PINCH_END, IntentKind.CANCEL]
    assert engine.engagement is EngagementState.SUSPENDED
    assert not engine.update(None, None, now + 400 * MS)

    engine.update(None, None, now + 2610 * MS)
    assert engine.engagement is EngagementState.DISENGAGED


def test_two_finger_motion_locks_to_scroll_until_pose_breaks() -> None:
    engine, now = engaged_engine()
    two = pose(two_finger=True)
    engine.update(feature(now + MS), two, now + MS)
    assert not engine.update(feature(now + 20 * MS, y=0.51, vy=0.5), two, now + 20 * MS)
    start = engine.update(feature(now + 101 * MS, y=0.51, vy=0.5), two, now + 101 * MS)

    assert [item.kind for item in start] == [IntentKind.SCROLL_START, IntentKind.SCROLL_UPDATE]
    assert engine.gesture is GestureState.SCROLLING
    update = engine.update(feature(now + 800 * MS, y=0.52, vy=0), two, now + 800 * MS)
    assert [item.kind for item in update] == [IntentKind.SCROLL_UPDATE]
    end = engine.update(feature(now + 810 * MS), pose(), now + 810 * MS)
    assert [item.kind for item in end] == [IntentKind.SCROLL_END]


def test_stationary_two_finger_right_clicks_once_and_requires_neutral() -> None:
    engine, now = engaged_engine()
    two = pose(two_finger=True)
    engine.update(feature(now + MS), two, now + MS)

    click = engine.update(feature(now + 651 * MS), two, now + 651 * MS)
    assert [item.kind for item in click] == [IntentKind.RIGHT_CLICK]
    assert not engine.update(feature(now + 900 * MS), two, now + 900 * MS)
    assert engine.gesture is GestureState.RIGHT_CLICK_COMMITTED

    engine.update(feature(now + 901 * MS), pose(), now + 901 * MS)
    assert engine.gesture is GestureState.NEUTRAL


def test_fist_clutches_without_disengaging_and_release_sets_fresh_state() -> None:
    engine, now = engaged_engine()
    fist = pose(fist=True)
    engine.update(feature(now + MS), fist, now + MS)
    on = engine.update(feature(now + 101 * MS), fist, now + 101 * MS)

    assert [item.kind for item in on] == [IntentKind.CLUTCH_ON]
    assert engine.engagement is EngagementState.ENGAGED
    off = engine.update(feature(now + 102 * MS), pose(), now + 102 * MS)
    assert [item.kind for item in off] == [IntentKind.CLUTCH_OFF]


def test_fault_cancels_drag_and_is_terminal() -> None:
    engine, now = engaged_engine()
    closed = pose(index_pinch_closed=True, index_pinch_open=False)
    engine.update(feature(now + MS), closed, now + MS)
    engine.update(feature(now + 101 * MS), closed, now + 101 * MS)

    intents = engine.fault(now + 102 * MS, "simulated_exception")

    assert [item.kind for item in intents] == [IntentKind.PINCH_END, IntentKind.CANCEL]
    assert engine.engagement is EngagementState.FAULT


def test_low_confidence_cancels_pending_click_immediately() -> None:
    engine, now = engaged_engine()
    closed = pose(index_pinch_closed=True, index_pinch_open=False)
    engine.update(feature(now + MS), closed, now + MS)
    assert engine.gesture is GestureState.PINCH_PENDING

    low_confidence = replace(feature(now + 2 * MS), confidence=0.1)
    assert not engine.update(low_confidence, closed, now + 2 * MS)

    assert engine.gesture is GestureState.NEUTRAL
    assert engine.engagement is EngagementState.SUSPENDED


def test_reacquisition_cancels_active_state_and_establishes_fresh_baseline() -> None:
    engine, now = engaged_engine()
    closed = pose(index_pinch_closed=True, index_pinch_open=False)
    engine.update(feature(now + MS), closed, now + MS)
    engine.update(feature(now + 101 * MS), closed, now + 101 * MS)
    assert engine.gesture is GestureState.DRAGGING

    engine.update(None, None, now + 110 * MS)
    engine.update(feature(now + 120 * MS), closed, now + 120 * MS)
    intents = engine.update(feature(now + 320 * MS), closed, now + 320 * MS)

    assert intents[0].kind is IntentKind.PINCH_END
    assert intents[1].kind is IntentKind.CANCEL
    assert engine.engagement is EngagementState.ENGAGED


def test_transition_history_is_fixed_size() -> None:
    config = load_config()
    config.section("debug")["state_transition_history_capacity"] = 2
    engine = GestureEngine(config)

    engine._transition_engagement(EngagementState.ARMING, 1, "one")
    engine._transition_engagement(EngagementState.ENGAGED, 2, "two")
    engine._transition_engagement(EngagementState.DISENGAGED, 3, "three")

    assert [item.reason for item in engine.transitions] == ["two", "three"]
