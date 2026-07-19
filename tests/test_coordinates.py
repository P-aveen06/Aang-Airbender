import pytest

from aang_airbender.config import ControlBoxConfig
from aang_airbender.coordinates import (
    DisplayBounds,
    camera_to_display_orientation,
    corrected_handedness,
    map_control_box_to_display,
)
from aang_airbender.types import Point2


def test_unmirrored_camera_is_mirrored_exactly_once_for_display_control() -> None:
    assert camera_to_display_orientation(
        Point2(0.25, 0.4), camera_input_is_mirrored=False
    ) == Point2(0.75, 0.4)
    assert camera_to_display_orientation(
        Point2(0.25, 0.4), camera_input_is_mirrored=True
    ) == Point2(0.25, 0.4)


def test_mediapipe_handedness_is_corrected_in_same_convention_module() -> None:
    assert corrected_handedness("Left", camera_input_is_mirrored=False) == "Left"
    assert corrected_handedness("Right", camera_input_is_mirrored=False) == "Right"
    assert corrected_handedness("Right", camera_input_is_mirrored=True) == "Left"


def test_central_control_box_expands_and_clamps_to_display() -> None:
    box = ControlBoxConfig(0.2, 0.2, 0.8, 0.8)
    bounds = DisplayBounds(10.0, 20.0, 1200.0, 800.0)

    assert map_control_box_to_display(Point2(0.2, 0.2), box, bounds) == Point2(10.0, 20.0)
    assert map_control_box_to_display(Point2(0.8, 0.8), box, bounds) == Point2(1210.0, 820.0)
    mapped = map_control_box_to_display(Point2(0.5, 0.5), box, bounds)
    assert mapped.x == pytest.approx(610.0)
    assert mapped.y == pytest.approx(420.0)
    assert map_control_box_to_display(Point2(-1.0, 2.0), box, bounds) == Point2(10.0, 820.0)
