from dataclasses import dataclass

import pytest

from aang_airbender.cursor import ScreenBounds, map_to_screen, palm_midpoint


@dataclass(frozen=True)
class Landmark:
    x: float
    y: float


def test_palm_midpoint_uses_only_landmarks_5_and_17() -> None:
    landmarks = [Landmark(99.0, 99.0) for _ in range(21)]
    landmarks[5] = Landmark(0.2, 0.4)
    landmarks[17] = Landmark(0.6, 0.8)

    assert palm_midpoint(landmarks) == pytest.approx((0.4, 0.6))


def test_map_to_main_screen_mirrors_x_and_clamps_coordinates() -> None:
    bounds = ScreenBounds(10.0, 20.0, 1000.0, 500.0)

    assert map_to_screen(0.25, 0.5, bounds) == pytest.approx((760.0, 270.0))
    assert map_to_screen(-1.0, 2.0, bounds) == pytest.approx((1010.0, 520.0))
