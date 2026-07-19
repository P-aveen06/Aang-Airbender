from aang_airbender.coordinates import DisplayBounds
from aang_airbender.debug import (
    DEBUG_FONT_SCALE,
    DEBUG_TEXT_BGR,
    debug_text_origins,
    overlay_origin,
)


def test_compact_black_debug_text_is_anchored_at_bottom_left() -> None:
    assert DEBUG_TEXT_BGR == (27, 24, 24)
    assert DEBUG_FONT_SCALE < 0.5
    assert debug_text_origins(480, 3) == ((8, 438), (8, 455), (8, 472))


def test_camera_overlay_is_inset_from_main_display_bottom_left() -> None:
    bounds = DisplayBounds(x=0.0, y=0.0, width=1470.0, height=956.0)

    assert overlay_origin(bounds, width=280, height=200, margin=20) == (20.0, 20.0)
