from __future__ import annotations

import math
from threading import Lock
from typing import Protocol

from .coordinates import DisplayBounds
from .types import EventKind, SemanticEvent


class ActionBackend(Protocol):
    def move_pointer(self, x: float, y: float, *, left_button_held: bool) -> None: ...

    def post_left_down(self, click_count: int) -> None: ...

    def post_left_up(self, click_count: int) -> None: ...

    def post_right_down(self) -> None: ...

    def post_right_up(self) -> None: ...

    def post_pixel_scroll(self, dx: float, dy: float) -> None: ...

    def is_left_down(self) -> bool: ...


class QuartzActionBackend:
    def __init__(self) -> None:
        import Quartz

        self._quartz = Quartz

    def main_display_bounds(self) -> DisplayBounds:
        rect = self._quartz.CGDisplayBounds(self._quartz.CGMainDisplayID())
        return DisplayBounds(
            float(rect.origin.x),
            float(rect.origin.y),
            float(rect.size.width),
            float(rect.size.height),
        )

    def display_topology_signature(self) -> tuple[tuple[int, DisplayBounds], ...]:
        error, _displays, count = self._quartz.CGGetOnlineDisplayList(0, None, None)
        if error != self._quartz.kCGErrorSuccess:
            raise RuntimeError(f"Quartz could not enumerate online displays: error {error}")
        error, displays, _count = self._quartz.CGGetOnlineDisplayList(count, None, None)
        if error != self._quartz.kCGErrorSuccess:
            raise RuntimeError(f"Quartz could not read online displays: error {error}")
        signature = []
        for display_id in displays:
            rect = self._quartz.CGDisplayBounds(display_id)
            signature.append(
                (
                    int(display_id),
                    DisplayBounds(
                        float(rect.origin.x),
                        float(rect.origin.y),
                        float(rect.size.width),
                        float(rect.size.height),
                    ),
                )
            )
        return tuple(signature)

    def _cursor_location(self) -> tuple[float, float]:
        event = self._quartz.CGEventCreate(None)
        if event is None:
            raise RuntimeError("Quartz could not read the current cursor location")
        location = self._quartz.CGEventGetLocation(event)
        return float(location.x), float(location.y)

    def _post_mouse(
        self,
        event_type: int,
        button: int,
        location: tuple[float, float],
        *,
        click_count: int | None = None,
    ) -> None:
        event = self._quartz.CGEventCreateMouseEvent(None, event_type, location, button)
        if event is None:
            raise RuntimeError("Quartz could not create a mouse event")
        if click_count is not None:
            self._quartz.CGEventSetIntegerValueField(
                event,
                self._quartz.kCGMouseEventClickState,
                click_count,
            )
        self._quartz.CGEventPost(self._quartz.kCGHIDEventTap, event)

    def move_pointer(self, x: float, y: float, *, left_button_held: bool) -> None:
        self._post_mouse(
            (
                self._quartz.kCGEventLeftMouseDragged
                if left_button_held
                else self._quartz.kCGEventMouseMoved
            ),
            self._quartz.kCGMouseButtonLeft,
            (x, y),
        )

    def post_left_down(self, click_count: int) -> None:
        self._post_mouse(
            self._quartz.kCGEventLeftMouseDown,
            self._quartz.kCGMouseButtonLeft,
            self._cursor_location(),
            click_count=click_count,
        )

    def post_left_up(self, click_count: int) -> None:
        self._post_mouse(
            self._quartz.kCGEventLeftMouseUp,
            self._quartz.kCGMouseButtonLeft,
            self._cursor_location(),
            click_count=click_count,
        )

    def post_right_down(self) -> None:
        self._post_mouse(
            self._quartz.kCGEventRightMouseDown,
            self._quartz.kCGMouseButtonRight,
            self._cursor_location(),
        )

    def post_right_up(self) -> None:
        self._post_mouse(
            self._quartz.kCGEventRightMouseUp,
            self._quartz.kCGMouseButtonRight,
            self._cursor_location(),
        )

    def post_pixel_scroll(self, dx: float, dy: float) -> None:
        event = self._quartz.CGEventCreateScrollWheelEvent(
            None,
            self._quartz.kCGScrollEventUnitPixel,
            2,
            int(round(dy)),
            int(round(dx)),
        )
        if event is None:
            raise RuntimeError("Quartz could not create a pixel-scroll event")
        self._quartz.CGEventPost(self._quartz.kCGHIDEventTap, event)

    def is_left_down(self) -> bool:
        return bool(
            self._quartz.CGEventSourceButtonState(
                self._quartz.kCGEventSourceStateCombinedSessionState,
                self._quartz.kCGMouseButtonLeft,
            )
        )


class ActionDispatcher:
    def __init__(
        self,
        backend: ActionBackend,
        *,
        double_click_interval_ms: int,
        double_click_max_distance_pixels: float,
    ) -> None:
        if double_click_interval_ms <= 0:
            raise ValueError("Double-click interval must be positive")
        if double_click_max_distance_pixels <= 0:
            raise ValueError("Double-click distance must be positive")
        self._backend = backend
        self._lock = Lock()
        self._double_click_interval_ns = double_click_interval_ms * 1_000_000
        self._double_click_max_distance_pixels = double_click_max_distance_pixels
        self._left_button_held = False
        self._right_button_held = False
        self._active_left_click_count = 1
        self._left_dragged = False
        self._last_left_up_timestamp_ns: int | None = None
        self._pointer_position: tuple[float, float] | None = None
        self._last_left_up_position: tuple[float, float] | None = None

    def _reset_left_click_sequence(self) -> None:
        self._last_left_up_timestamp_ns = None
        self._last_left_up_position = None
        if not self._left_button_held:
            self._active_left_click_count = 1
            self._left_dragged = False

    def dispatch(self, event: SemanticEvent) -> None:
        with self._lock:
            if event.kind is EventKind.POINTER_MOVE:
                if event.x is None or event.y is None:
                    raise ValueError("POINTER_MOVE requires x and y")
                self._backend.move_pointer(
                    event.x, event.y, left_button_held=self._left_button_held
                )
                self._pointer_position = (event.x, event.y)
                if self._left_button_held:
                    self._left_dragged = True
            elif event.kind is EventKind.LEFT_DOWN:
                if not self._left_button_held:
                    elapsed = (
                        event.timestamp_ns - self._last_left_up_timestamp_ns
                        if self._last_left_up_timestamp_ns is not None
                        else None
                    )
                    distance = (
                        math.dist(self._pointer_position, self._last_left_up_position)
                        if self._pointer_position is not None
                        and self._last_left_up_position is not None
                        else 0.0
                    )
                    self._active_left_click_count = (
                        2
                        if elapsed is not None
                        and 0 <= elapsed <= self._double_click_interval_ns
                        and distance <= self._double_click_max_distance_pixels
                        else 1
                    )
                    self._backend.post_left_down(self._active_left_click_count)
                    self._left_button_held = True
                    self._left_dragged = False
            elif event.kind is EventKind.LEFT_UP:
                if self._left_button_held:
                    self._backend.post_left_up(self._active_left_click_count)
                    self._left_button_held = False
                    if self._left_dragged:
                        self._last_left_up_timestamp_ns = None
                        self._last_left_up_position = None
                    else:
                        self._last_left_up_timestamp_ns = event.timestamp_ns
                        self._last_left_up_position = self._pointer_position
            elif event.kind is EventKind.RIGHT_CLICK:
                if self._left_button_held:
                    raise RuntimeError("Refusing to right-click while the left button is held")
                self._reset_left_click_sequence()
                self._backend.post_right_down()
                self._right_button_held = True
                self._backend.post_right_up()
                self._right_button_held = False
            elif event.kind is EventKind.SCROLL:
                if self._left_button_held:
                    raise RuntimeError("Refusing to scroll while the left button is held")
                self._reset_left_click_sequence()
                if event.pixel_dx is None or event.pixel_dy is None:
                    raise ValueError("SCROLL requires pixel_dx and pixel_dy")
                self._backend.post_pixel_scroll(event.pixel_dx, event.pixel_dy)
            else:
                raise ValueError(f"Unsupported semantic event: {event.kind!r}")

    def safe_release_all(self) -> None:
        with self._lock:
            self._last_left_up_timestamp_ns = None
            self._last_left_up_position = None
            first_error: Exception | None = None
            if self._left_button_held:
                try:
                    self._backend.post_left_up(self._active_left_click_count)
                except Exception as error:
                    first_error = error
                else:
                    self._left_button_held = False
                    self._active_left_click_count = 1
                    self._left_dragged = False
            if self._right_button_held:
                try:
                    self._backend.post_right_up()
                except Exception as error:
                    if first_error is None:
                        first_error = error
                else:
                    self._right_button_held = False
            if not self._left_button_held:
                self._active_left_click_count = 1
                self._left_dragged = False
            if first_error is not None:
                raise first_error

    def left_button_is_down(self) -> bool:
        return self._backend.is_left_down()
