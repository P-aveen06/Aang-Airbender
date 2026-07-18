from __future__ import annotations

from threading import Lock
from typing import Protocol

from .coordinates import DisplayBounds
from .types import EventKind, SemanticEvent


class ActionBackend(Protocol):
    def move_pointer(self, x: float, y: float, *, left_button_held: bool) -> None: ...

    def post_left_down(
        self, click_count: int, *, location: tuple[float, float] | None = None
    ) -> None: ...

    def post_left_up(
        self, click_count: int, *, location: tuple[float, float] | None = None
    ) -> None: ...

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

    def post_left_down(
        self, click_count: int, *, location: tuple[float, float] | None = None
    ) -> None:
        self._post_mouse(
            self._quartz.kCGEventLeftMouseDown,
            self._quartz.kCGMouseButtonLeft,
            location or self._cursor_location(),
            click_count=click_count,
        )

    def post_left_up(
        self, click_count: int, *, location: tuple[float, float] | None = None
    ) -> None:
        self._post_mouse(
            self._quartz.kCGEventLeftMouseUp,
            self._quartz.kCGMouseButtonLeft,
            location or self._cursor_location(),
            click_count=click_count,
        )

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
        self._pointer_position: tuple[float, float] | None = None

    def dispatch(self, event: SemanticEvent) -> None:
        with self._lock:
            if event.kind is EventKind.POINTER_MOVE:
                if event.x is None or event.y is None:
                    raise ValueError("POINTER_MOVE requires x and y")
                self._backend.move_pointer(
                    event.x, event.y, left_button_held=self._left_button_held
                )
                self._pointer_position = (event.x, event.y)
            elif event.kind is EventKind.LEFT_CLICK:
                if self._left_button_held:
                    raise RuntimeError("Refusing to click while the left button is held")
                if event.x is None or event.y is None:
                    raise ValueError("LEFT_CLICK requires x and y")
                self._backend.move_pointer(event.x, event.y, left_button_held=False)
                self._pointer_position = (event.x, event.y)
                # Once a down is attempted, conservatively assume ownership so a
                # caller's terminal cleanup will post an up even if the backend raises.
                self._left_button_held = True
                self._backend.post_left_down(1, location=self._pointer_position)
                self._backend.post_left_up(1, location=self._pointer_position)
                self._left_button_held = False
            elif event.kind is EventKind.LEFT_DOWN:
                if not self._left_button_held:
                    self._left_button_held = True
                    self._backend.post_left_down(1)
            elif event.kind is EventKind.LEFT_UP:
                if self._left_button_held:
                    self._backend.post_left_up(1, location=self._pointer_position)
                    self._left_button_held = False
            else:
                raise ValueError(f"Unsupported semantic event: {event.kind!r}")

    def safe_release_all(self) -> None:
        with self._lock:
            first_error: Exception | None = None
            if self._left_button_held:
                try:
                    self._backend.post_left_up(1, location=self._pointer_position)
                except Exception as error:
                    first_error = error
                else:
                    self._left_button_held = False
            if first_error is not None:
                raise first_error

    def left_button_is_down(self) -> bool:
        return self._backend.is_left_down()
