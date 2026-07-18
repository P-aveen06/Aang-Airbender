from __future__ import annotations

import math

from .config import Phase1Config
from .coordinates import (
    CAMERA_INPUT_IS_MIRRORED,
    DisplayBounds,
    camera_to_display_orientation,
    map_control_box_to_display,
)
from .types import EventKind, GestureIntent, IntentKind, Point2, SemanticEvent


class LowPassFilter:
    def __init__(self) -> None:
        self._value: float | None = None

    def reset(self) -> None:
        self._value = None

    def apply(self, value: float, alpha: float) -> float:
        if self._value is None:
            self._value = value
        else:
            self._value = alpha * value + (1.0 - alpha) * self._value
        return self._value


class OneEuroAxis:
    def __init__(self, min_cutoff: float, beta: float, derivative_cutoff: float) -> None:
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.derivative_cutoff = derivative_cutoff
        self._signal = LowPassFilter()
        self._derivative = LowPassFilter()
        self._last_raw: float | None = None
        self._last_timestamp_ns: int | None = None

    @staticmethod
    def _alpha(cutoff: float, elapsed_seconds: float) -> float:
        time_constant = 1.0 / (2.0 * math.pi * cutoff)
        return 1.0 / (1.0 + time_constant / elapsed_seconds)

    def reset(self) -> None:
        self._signal.reset()
        self._derivative.reset()
        self._last_raw = None
        self._last_timestamp_ns = None

    def apply(self, value: float, timestamp_ns: int) -> float:
        if self._last_timestamp_ns is None or self._last_raw is None:
            self._last_timestamp_ns = timestamp_ns
            self._last_raw = value
            return self._signal.apply(value, 1.0)
        elapsed = (timestamp_ns - self._last_timestamp_ns) / 1_000_000_000
        if elapsed <= 0.0:
            return self._signal.apply(value, 0.0)
        derivative = (value - self._last_raw) / elapsed
        filtered_derivative = self._derivative.apply(
            derivative, self._alpha(self.derivative_cutoff, elapsed)
        )
        cutoff = self.min_cutoff + self.beta * abs(filtered_derivative)
        filtered = self._signal.apply(value, self._alpha(cutoff, elapsed))
        self._last_timestamp_ns = timestamp_ns
        self._last_raw = value
        return filtered


class PointerFilter:
    def __init__(self, config: Phase1Config) -> None:
        settings = config.section("control")
        arguments = (
            float(settings["one_euro_min_cutoff"]),
            float(settings["one_euro_beta"]),
            float(settings["one_euro_derivative_cutoff"]),
        )
        self._x = OneEuroAxis(*arguments)
        self._y = OneEuroAxis(*arguments)

    def reset(self) -> None:
        self._x.reset()
        self._y.reset()

    def apply(self, point: Point2, timestamp_ns: int) -> Point2:
        return Point2(
            self._x.apply(point.x, timestamp_ns),
            self._y.apply(point.y, timestamp_ns),
        )


class ControlEngine:
    def __init__(self, config: Phase1Config, bounds: DisplayBounds) -> None:
        self.config = config
        self.bounds = bounds
        self.pointer_filter = PointerFilter(config)
        self._latest_pointer: Point2 | None = None
        self._click_anchor: Point2 | None = None

    def consume(self, intent: GestureIntent) -> tuple[SemanticEvent, ...]:
        if intent.kind is IntentKind.CANCEL:
            self.pointer_filter.reset()
            self._latest_pointer = None
            self._click_anchor = None
            return ()
        if intent.kind is IntentKind.CLICK_CANCEL:
            self._click_anchor = None
            return ()
        if intent.kind is IntentKind.CLICK_ARM:
            self._click_anchor = self._latest_pointer
            return ()
        if intent.kind is IntentKind.CLICK_COMMIT:
            anchor = self._click_anchor
            self._click_anchor = None
            if anchor is None:
                return ()
            return (
                SemanticEvent(
                    EventKind.LEFT_CLICK,
                    intent.timestamp_ns,
                    x=anchor.x,
                    y=anchor.y,
                ),
            )
        if intent.kind is IntentKind.POINT:
            if intent.point is None:
                raise ValueError("POINT requires a point")
            filtered = self.pointer_filter.apply(intent.point, intent.timestamp_ns)
            oriented = camera_to_display_orientation(
                filtered, camera_input_is_mirrored=CAMERA_INPUT_IS_MIRRORED
            )
            mapped = map_control_box_to_display(oriented, self.config.control_box, self.bounds)
            self._latest_pointer = mapped
            if self._click_anchor is not None:
                return ()
            return (
                SemanticEvent(
                    EventKind.POINTER_MOVE,
                    intent.timestamp_ns,
                    x=mapped.x,
                    y=mapped.y,
                ),
            )
        raise ValueError(f"Unsupported gesture intent: {intent.kind!r}")
