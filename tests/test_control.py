import pytest

from aang_airbender.config import load_config
from aang_airbender.control import ControlEngine, OneEuroAxis
from aang_airbender.coordinates import DisplayBounds
from aang_airbender.types import EventKind, GestureIntent, IntentKind, Point2


def test_one_euro_filter_tracks_constant_and_resets_to_fresh_baseline() -> None:
    axis = OneEuroAxis(1.0, 0.007, 1.0)

    assert axis.apply(0.2, 1_000_000_000) == pytest.approx(0.2)
    assert 0.2 < axis.apply(0.8, 1_033_000_000) < 0.8
    axis.reset()
    assert axis.apply(0.8, 2_000_000_000) == pytest.approx(0.8)


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


def test_clutch_freezes_pointer_and_release_rebaselines_without_jump() -> None:
    control = ControlEngine(load_config(), DisplayBounds(0, 0, 1000, 500))
    before = control.consume(GestureIntent(IntentKind.POINT, 1, point=Point2(0.5, 0.5)))[0]
    control.consume(GestureIntent(IntentKind.CLUTCH_ON, 1))

    assert not control.consume(GestureIntent(IntentKind.POINT, 2, point=Point2(0.7, 0.7)))

    control.consume(GestureIntent(IntentKind.CLUTCH_OFF, 3))
    rebaselined = control.consume(GestureIntent(IntentKind.POINT, 4, point=Point2(0.7, 0.7)))[0]

    assert (rebaselined.x, rebaselined.y) == pytest.approx((before.x, before.y))

    moved = control.consume(GestureIntent(IntentKind.POINT, 5, point=Point2(0.65, 0.65)))[0]
    assert moved.x > rebaselined.x
    assert moved.y < rebaselined.y


def test_safety_cancel_reacquires_from_the_last_cursor_position() -> None:
    control = ControlEngine(load_config(), DisplayBounds(0, 0, 1000, 500))
    before = control.consume(GestureIntent(IntentKind.POINT, 1, point=Point2(0.5, 0.5)))[0]

    control.consume(GestureIntent(IntentKind.CANCEL, 2, reason="tracking_loss"))
    reacquired = control.consume(GestureIntent(IntentKind.POINT, 3, point=Point2(0.7, 0.7)))[0]

    assert (reacquired.x, reacquired.y) == pytest.approx((before.x, before.y))


def test_pixel_scroll_has_configured_natural_direction_and_no_momentum() -> None:
    control = ControlEngine(load_config(), DisplayBounds(0, 0, 1000, 500))
    control.consume(GestureIntent(IntentKind.SCROLL_START, 1_000_000_000))
    events = control.consume(
        GestureIntent(
            IntentKind.SCROLL_UPDATE,
            1_100_000_000,
            velocity=Point2(0.1, 0.2),
        )
    )

    assert len(events) == 1
    assert events[0].kind is EventKind.SCROLL
    assert events[0].pixel_dx == pytest.approx(9.0)
    assert events[0].pixel_dy == pytest.approx(18.0)
    control.consume(GestureIntent(IntentKind.SCROLL_END, 1_200_000_000))
    assert not control.consume(
        GestureIntent(
            IntentKind.SCROLL_UPDATE,
            1_300_000_000,
            velocity=Point2(0.1, 0.2),
        )
    )


def test_fractional_pixel_scroll_accumulates_instead_of_emitting_rounded_zeroes() -> None:
    config = load_config()
    control = ControlEngine(config, DisplayBounds(0, 0, 1000, 500))
    control.consume(GestureIntent(IntentKind.SCROLL_START, 1_000_000_000))
    velocity_for_point_two_pixels = 0.2 / (float(config.section("control")["scroll_gain"]) * 0.1)

    events = []
    for step in range(1, 7):
        events.extend(
            control.consume(
                GestureIntent(
                    IntentKind.SCROLL_UPDATE,
                    1_000_000_000 + step * 100_000_000,
                    velocity=Point2(0.0, velocity_for_point_two_pixels),
                )
            )
        )

    assert [event.pixel_dy for event in events] == [1.0]
