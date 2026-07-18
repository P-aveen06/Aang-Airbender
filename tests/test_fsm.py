from aang_airbender.config import load_config
from aang_airbender.fsm import GestureEngine, InteractionState
from aang_airbender.poses import PoseClassification
from aang_airbender.types import HandFeatures, IntentKind, Point2

MS = 1_000_000


def features(timestamp_ns: int = 0, *, tip: Point2 | None = None) -> HandFeatures:
    tip = tip or Point2(0.5, 0.5)
    return HandFeatures(
        index_tip=tip,
        palm_center=Point2(0.5, 0.5),
        palm_orientation_radians=0.0,
        palm_facing_score=1.0,
        hand_scale=0.2,
        image_hand_scale=0.2,
        finger_extension=(False, True, False, False, False),
        finger_joint_angles_degrees=((90.0, 90.0),) * 5,
        pinch_ratio_index=0.8,
        pinch_ratio_middle=0.8,
        index_middle_separation_ratio=0.8,
        thumb_direction_down_ratio=0.0,
        palm_velocity=Point2(0.0, 0.0),
        anchor_velocity=Point2(0.0, 0.0),
        confidence=0.99,
        timestamp_ns=timestamp_ns,
    )


def pose(*, point: bool = False, closed: bool = False, opened: bool = False):
    return PoseClassification(point, closed, opened, True)


def activate(engine: GestureEngine, now_ns: int = 0) -> int:
    engine.update(features(now_ns), pose(point=True, opened=True), None, None, now_ns)
    active_at = now_ns + 200 * MS
    intents = engine.update(
        features(active_at), pose(point=True, opened=True), None, None, active_at
    )
    assert engine.state is InteractionState.POINTING
    assert [intent.kind for intent in intents] == [IntentKind.POINT]
    return active_at


def make_left_neutral(engine: GestureEngine, now_ns: int) -> None:
    engine.update(
        features(now_ns),
        pose(point=True, opened=True),
        features(now_ns),
        pose(opened=True),
        now_ns,
    )


def test_right_index_point_requires_configured_reacquisition_stability() -> None:
    engine = GestureEngine(load_config())

    assert not engine.update(features(0), pose(point=True, opened=True), None, None, 0)
    assert not engine.update(
        features(199 * MS), pose(point=True, opened=True), None, None, 199 * MS
    )
    intents = engine.update(features(200 * MS), pose(point=True, opened=True), None, None, 200 * MS)

    assert engine.state is InteractionState.POINTING
    assert [intent.kind for intent in intents] == [IntentKind.POINT]


def test_non_pointing_right_pose_immediately_freezes_output() -> None:
    engine = GestureEngine(load_config())
    active_at = activate(engine)

    intents = engine.update(features(active_at + MS), pose(opened=True), None, None, active_at + MS)

    assert engine.state is InteractionState.INACTIVE
    assert [intent.kind for intent in intents] == [IntentKind.CANCEL]


def test_left_hand_must_be_seen_open_before_a_pinch_can_arm() -> None:
    engine = GestureEngine(load_config())
    active_at = activate(engine)

    preclosed = engine.update(
        features(active_at + MS),
        pose(point=True, opened=True),
        features(active_at + MS),
        pose(closed=True),
        active_at + MS,
    )
    make_left_neutral(engine, active_at + 2 * MS)
    armed = engine.update(
        features(active_at + 3 * MS),
        pose(point=True, opened=True),
        features(active_at + 3 * MS),
        pose(closed=True),
        active_at + 3 * MS,
    )

    assert [intent.kind for intent in preclosed] == [IntentKind.POINT]
    assert [intent.kind for intent in armed] == [IntentKind.POINT, IntentKind.CLICK_ARM]
    assert engine.state is InteractionState.CLICK_PENDING


def test_stable_left_pinch_commits_once_on_release() -> None:
    engine = GestureEngine(load_config())
    active_at = activate(engine)
    make_left_neutral(engine, active_at + MS)
    close_at = active_at + 2 * MS
    engine.update(
        features(close_at),
        pose(point=True, opened=True),
        features(close_at),
        pose(closed=True),
        close_at,
    )

    held = engine.update(
        features(close_at + 100 * MS),
        pose(point=True, opened=True),
        features(close_at + 100 * MS),
        pose(closed=True),
        close_at + 100 * MS,
    )
    released = engine.update(
        features(close_at + 101 * MS),
        pose(point=True, opened=True),
        features(close_at + 101 * MS),
        pose(opened=True),
        close_at + 101 * MS,
    )

    assert engine.state is InteractionState.POINTING
    assert [intent.kind for intent in held] == [IntentKind.POINT]
    assert [intent.kind for intent in released] == [IntentKind.CLICK_COMMIT, IntentKind.POINT]


def test_early_release_and_left_role_loss_cancel_without_click() -> None:
    for release_pose in (pose(opened=True), None):
        engine = GestureEngine(load_config())
        active_at = activate(engine)
        make_left_neutral(engine, active_at + MS)
        close_at = active_at + 2 * MS
        engine.update(
            features(close_at),
            pose(point=True, opened=True),
            features(close_at),
            pose(closed=True),
            close_at,
        )

        intents = engine.update(
            features(close_at + 50 * MS),
            pose(point=True, opened=True),
            features(close_at + 50 * MS) if release_pose is not None else None,
            release_pose,
            close_at + 50 * MS,
        )

        assert IntentKind.CLICK_CANCEL in [intent.kind for intent in intents]
        assert IntentKind.CLICK_COMMIT not in [intent.kind for intent in intents]


def test_right_role_loss_cancels_click_immediately_and_releases_at_grace() -> None:
    engine = GestureEngine(load_config())
    active_at = activate(engine)
    make_left_neutral(engine, active_at + MS)
    close_at = active_at + 2 * MS
    engine.update(
        features(close_at),
        pose(point=True, opened=True),
        features(close_at),
        pose(closed=True),
        close_at,
    )

    lost = engine.update(None, None, features(close_at + MS), pose(closed=True), close_at + MS)
    before_grace = engine.update(None, None, None, None, close_at + 199 * MS)
    at_grace = engine.update(None, None, None, None, close_at + 201 * MS)

    assert [intent.kind for intent in lost] == [IntentKind.CLICK_CANCEL]
    assert before_grace == []
    assert [intent.kind for intent in at_grace] == [IntentKind.CANCEL]
    assert engine.state is InteractionState.INACTIVE


def test_fault_and_shutdown_always_emit_terminal_cancel() -> None:
    engine = GestureEngine(load_config())

    assert engine.disengage(1, "shutdown")[-1].kind is IntentKind.CANCEL
    assert engine.fault(2, "failure")[-1].kind is IntentKind.CANCEL
    assert engine.state is InteractionState.FAULT
