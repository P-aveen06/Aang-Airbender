from __future__ import annotations

from threading import Lock
from typing import Protocol

from .coordinates import DisplayBounds
from .types import EventKind, SemanticEvent


class ActionBackend(Protocol):
    def move_pointer(self, x: float, y: float) -> None: ...

    def post_left_down(self) -> None: ...

    def post_left_up(self) -> None: ...

    def post_right_click(self) -> None: ...

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

    def move_pointer(self, x: float, y: float) -> None:
        self._post_mouse(
            self._quartz.kCGEventMouseMoved,
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

    def post_right_click(self) -> None:
        location = self._cursor_location()
        self._post_mouse(
            self._quartz.kCGEventRightMouseDown,
            self._quartz.kCGMouseButtonRight,
            location,
        )
        self._post_mouse(
            self._quartz.kCGEventRightMouseUp,
            self._quartz.kCGMouseButtonRight,
            location,
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

    def dispatch(self, event: SemanticEvent) -> None:
        with self._lock:
            if event.kind is EventKind.POINTER_MOVE:
                if event.x is None or event.y is None:
                    raise ValueError("POINTER_MOVE requires x and y")
                self._backend.move_pointer(event.x, event.y)
            elif event.kind is EventKind.LEFT_DOWN:
                if not self._left_button_held:
                    self._backend.post_left_down()
                    self._left_button_held = True
            elif event.kind is EventKind.LEFT_UP:
                if self._left_button_held:
                    self._backend.post_left_up()
                    self._left_button_held = False
            elif event.kind is EventKind.RIGHT_CLICK:
                self._backend.post_right_click()
            elif event.kind is EventKind.SCROLL:
                if event.pixel_dx is None or event.pixel_dy is None:
                    raise ValueError("SCROLL requires pixel_dx and pixel_dy")
                self._backend.post_pixel_scroll(event.pixel_dx, event.pixel_dy)

    def safe_release_all(self) -> None:
        with self._lock:
            if self._left_button_held:
                self._backend.post_left_up()
                self._left_button_held = False

    def left_button_is_down(self) -> bool:
        return self._backend.is_left_down()
