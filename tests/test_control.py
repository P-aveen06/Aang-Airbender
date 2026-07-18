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
    control = ControlEngine(load_config(), DisplayBounds(0, 0, 1000, 500))

    events = control.consume(
        GestureIntent(IntentKind.POINT, 1_000_000_000, point=Point2(0.2, 0.18))
    )

    assert len(events) == 1
    assert events[0].kind is EventKind.POINTER_MOVE
    assert events[0].x == pytest.approx(1000.0)
    assert events[0].y == pytest.approx(0.0)


def test_clutch_freezes_pointer_and_release_resets_filter() -> None:
    control = ControlEngine(load_config(), DisplayBounds(0, 0, 1000, 500))
    control.consume(GestureIntent(IntentKind.CLUTCH_ON, 1))

    assert not control.consume(GestureIntent(IntentKind.POINT, 2, point=Point2(0.5, 0.5)))

    control.consume(GestureIntent(IntentKind.CLUTCH_OFF, 3))
    assert control.consume(GestureIntent(IntentKind.POINT, 4, point=Point2(0.5, 0.5)))


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
