from __future__ import annotations

from threading import Lock
from typing import Protocol

from .coordinates import DisplayBounds
from .types import EventKind, SemanticEvent


class ActionBackend(Protocol):
    def move_pointer(self, x: float, y: float, *, left_button_held: bool) -> None: ...

    def post_left_down(self) -> None: ...

    def post_left_up(self) -> None: ...

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

    def _post_mouse(self, event_type: int, button: int, location: tuple[float, float]) -> None:
        event = self._quartz.CGEventCreateMouseEvent(None, event_type, location, button)
        if event is None:
            raise RuntimeError("Quartz could not create a mouse event")
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

    def post_left_down(self) -> None:
        self._post_mouse(
            self._quartz.kCGEventLeftMouseDown,
            self._quartz.kCGMouseButtonLeft,
            self._cursor_location(),
        )

    def post_left_up(self) -> None:
        self._post_mouse(
            self._quartz.kCGEventLeftMouseUp,
            self._quartz.kCGMouseButtonLeft,
            self._cursor_location(),
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
    def __init__(self, backend: ActionBackend) -> None:
        self._backend = backend
        self._lock = Lock()
        self._left_button_held = False
        self._right_button_held = False

    def dispatch(self, event: SemanticEvent) -> None:
        with self._lock:
            if event.kind is EventKind.POINTER_MOVE:
                if event.x is None or event.y is None:
                    raise ValueError("POINTER_MOVE requires x and y")
                self._backend.move_pointer(
                    event.x, event.y, left_button_held=self._left_button_held
                )
            elif event.kind is EventKind.LEFT_DOWN:
                if not self._left_button_held:
                    self._backend.post_left_down()
                    self._left_button_held = True
            elif event.kind is EventKind.LEFT_UP:
                if self._left_button_held:
                    self._backend.post_left_up()
                    self._left_button_held = False
            elif event.kind is EventKind.RIGHT_CLICK:
                if self._left_button_held:
                    raise RuntimeError("Refusing to right-click while the left button is held")
                self._backend.post_right_down()
                self._right_button_held = True
                self._backend.post_right_up()
                self._right_button_held = False
            elif event.kind is EventKind.SCROLL:
                if self._left_button_held:
                    raise RuntimeError("Refusing to scroll while the left button is held")
                if event.pixel_dx is None or event.pixel_dy is None:
                    raise ValueError("SCROLL requires pixel_dx and pixel_dy")
                self._backend.post_pixel_scroll(event.pixel_dx, event.pixel_dy)
            else:
                raise ValueError(f"Unsupported semantic event: {event.kind!r}")

    def safe_release_all(self) -> None:
        with self._lock:
            first_error: Exception | None = None
            if self._left_button_held:
                try:
                    self._backend.post_left_up()
                except Exception as error:
                    first_error = error
                else:
                    self._left_button_held = False
            if self._right_button_held:
                try:
                    self._backend.post_right_up()
                except Exception as error:
                    if first_error is None:
                        first_error = error
                else:
                    self._right_button_held = False
            if first_error is not None:
                raise first_error

    def left_button_is_down(self) -> bool:
        return self._backend.is_left_down()
