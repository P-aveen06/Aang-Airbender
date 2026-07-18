from aang_airbender.debug import (
    DEBUG_FONT_SCALE,
    DEBUG_TEXT_BGR,
    debug_text_origins,
)


def test_compact_black_debug_text_is_anchored_at_bottom_left() -> None:
    assert DEBUG_TEXT_BGR == (27, 24, 24)
    assert DEBUG_FONT_SCALE < 0.5
    assert debug_text_origins(480, 3) == ((8, 438), (8, 455), (8, 472))
