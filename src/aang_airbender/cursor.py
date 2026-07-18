from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


class NormalizedLandmark(Protocol):
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class ScreenBounds:
    x: float
    y: float
    width: float
    height: float


def palm_midpoint(landmarks: Sequence[NormalizedLandmark]) -> tuple[float, float]:
    if len(landmarks) <= 17:
        raise ValueError("At least 18 landmarks are required")
    return (
        (landmarks[5].x + landmarks[17].x) / 2.0,
        (landmarks[5].y + landmarks[17].y) / 2.0,
    )


def map_to_screen(x: float, y: float, bounds: ScreenBounds) -> tuple[float, float]:
    mirrored_x = 1.0 - min(max(x, 0.0), 1.0)
    clamped_y = min(max(y, 0.0), 1.0)
    return (
        bounds.x + mirrored_x * bounds.width,
        bounds.y + clamped_y * bounds.height,
    )


class QuartzCursor:
    def __init__(self) -> None:
        import Quartz

        self._quartz = Quartz
        display_id = Quartz.CGMainDisplayID()
        rect = Quartz.CGDisplayBounds(display_id)
        self.bounds = ScreenBounds(
            float(rect.origin.x),
            float(rect.origin.y),
            float(rect.size.width),
            float(rect.size.height),
        )

    def move(self, x: float, y: float) -> None:
        event = self._quartz.CGEventCreateMouseEvent(
            None,
            self._quartz.kCGEventMouseMoved,
            (x, y),
            self._quartz.kCGMouseButtonLeft,
        )
        if event is None:
            raise RuntimeError("Quartz could not create a mouse-move event")
        self._quartz.CGEventPost(self._quartz.kCGHIDEventTap, event)
