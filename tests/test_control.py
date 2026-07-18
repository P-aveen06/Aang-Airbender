import pytest

from aang_airbender.config import load_config
from aang_airbender.control import ControlEngine, OneEuroAxis
from aang_airbender.coordinates import DisplayBounds
from aang_airbender.types import EventKind, GestureIntent, IntentKind, Point2


def test_one_euro_filter_tracks_constant_and_resets_to_fresh_baseline() -> None:
    axis = OneEuroAxis(1.0, 4.0, 1.0)

    assert axis.apply(0.2, 1_000_000_000) == pytest.approx(0.2)
    assert 0.2 < axis.apply(0.8, 1_033_000_000) < 0.8
    axis.reset()
    assert axis.apply(0.8, 2_000_000_000) == pytest.approx(0.8)


def test_configured_filter_has_low_lag_during_deliberate_sweep() -> None:
    settings = load_config().section("control")
    axis = OneEuroAxis(
        float(settings["one_euro_min_cutoff"]),
        float(settings["one_euro_beta"]),
        float(settings["one_euro_derivative_cutoff"]),
    )
    timestamp_ns = 0
    output = 0.0
    for step in range(16):
        timestamp_ns += 33_333_333
        value = step / 15
        output = axis.apply(value, timestamp_ns)

    # Less than 10% of the camera width behind after a 500 ms full-width sweep.
    assert 1.0 - output < 0.10


def test_configured_filter_attenuates_stationary_index_tip_jitter() -> None:
    settings = load_config().section("control")
    axis = OneEuroAxis(
        float(settings["one_euro_min_cutoff"]),
        float(settings["one_euro_beta"]),
        float(settings["one_euro_derivative_cutoff"]),
    )
    output = [
        axis.apply(0.5 + (0.01 if step % 2 else -0.01), (step + 1) * 33_333_333)
        for step in range(120)
    ]

    # The raw synthetic jitter is 0.02 peak-to-peak; keep settled output below 0.005.
    assert max(output[-60:]) - min(output[-60:]) < 0.005


def test_point_is_filtered_mirrored_and_expanded_by_control_box() -> None:
    config = load_config()
    control = ControlEngine(config, DisplayBounds(0, 0, 1000, 500))

    events = control.consume(
        GestureIntent(
            IntentKind.POINT,
            1_000_000_000,
            point=Point2(1.0 - config.control_box.right, config.control_box.top),
        )
    )

    assert len(events) == 1
    assert events[0].kind is EventKind.POINTER_MOVE
    assert events[0].x == pytest.approx(1000.0)
    assert events[0].y == pytest.approx(0.0)


def test_click_freezes_pointer_and_commits_at_the_arm_anchor() -> None:
    control = ControlEngine(load_config(), DisplayBounds(0, 0, 1000, 500))
    first = control.consume(GestureIntent(IntentKind.POINT, 1_000_000_000, point=Point2(0.5, 0.5)))[
        0
    ]
    control.consume(GestureIntent(IntentKind.CLICK_ARM, 1_001_000_000))

    assert not control.consume(
        GestureIntent(IntentKind.POINT, 1_033_000_000, point=Point2(0.3, 0.3))
    )
    click = control.consume(GestureIntent(IntentKind.CLICK_COMMIT, 1_100_000_000))

    assert len(click) == 1
    assert click[0].kind is EventKind.LEFT_CLICK
    assert click[0].x == first.x
    assert click[0].y == first.y
    assert (
        control.consume(GestureIntent(IntentKind.POINT, 1_133_000_000, point=Point2(0.3, 0.3)))[
            0
        ].kind
        is EventKind.POINTER_MOVE
    )


def test_cancelled_click_emits_no_action_and_pointer_resumes() -> None:
    control = ControlEngine(load_config(), DisplayBounds(0, 0, 1000, 500))
    control.consume(GestureIntent(IntentKind.POINT, 1, point=Point2(0.5, 0.5)))
    control.consume(GestureIntent(IntentKind.CLICK_ARM, 2))

    assert not control.consume(GestureIntent(IntentKind.CLICK_CANCEL, 3))
    assert not control.consume(GestureIntent(IntentKind.CLICK_COMMIT, 4))
    assert control.consume(GestureIntent(IntentKind.POINT, 5, point=Point2(0.6, 0.5)))


def test_terminal_cancel_discards_anchor_and_resets_filter() -> None:
    control = ControlEngine(load_config(), DisplayBounds(0, 0, 1000, 500))
    control.consume(GestureIntent(IntentKind.POINT, 1, point=Point2(0.5, 0.5)))
    control.consume(GestureIntent(IntentKind.CLICK_ARM, 2))

    control.consume(GestureIntent(IntentKind.CANCEL, 3))

    assert not control.consume(GestureIntent(IntentKind.CLICK_COMMIT, 4))
    fresh = control.consume(GestureIntent(IntentKind.POINT, 5, point=Point2(0.3, 0.5)))
    assert fresh[0].kind is EventKind.POINTER_MOVE
