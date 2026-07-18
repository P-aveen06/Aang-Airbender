from __future__ import annotations

from threading import Lock
from typing import Protocol


class MouseEventBackend(Protocol):
    def post_left_down(self) -> None: ...

    def post_left_up(self) -> None: ...

    def is_left_down(self) -> bool: ...


class QuartzMouseEventBackend:
    def __init__(self) -> None:
        import Quartz

        self._quartz = Quartz

    def _post(self, event_type: int) -> None:
        current_event = self._quartz.CGEventCreate(None)
        if current_event is None:
            raise RuntimeError("Quartz could not read the current cursor location")
        location = self._quartz.CGEventGetLocation(current_event)
        event = self._quartz.CGEventCreateMouseEvent(
            None, event_type, location, self._quartz.kCGMouseButtonLeft
        )
        if event is None:
            raise RuntimeError("Quartz could not create a left-button event")
        self._quartz.CGEventPost(self._quartz.kCGHIDEventTap, event)

    def post_left_down(self) -> None:
        self._post(self._quartz.kCGEventLeftMouseDown)

    def post_left_up(self) -> None:
        self._post(self._quartz.kCGEventLeftMouseUp)

    def is_left_down(self) -> bool:
        return bool(
            self._quartz.CGEventSourceButtonState(
                self._quartz.kCGEventSourceStateCombinedSessionState,
                self._quartz.kCGMouseButtonLeft,
            )
        )


class MouseSafety:
    def __init__(self, backend: MouseEventBackend) -> None:
        self._backend = backend
        self._lock = Lock()
        self._left_button_held = False

    def left_down_for_safety_test(self) -> None:
        with self._lock:
            if self._left_button_held:
                return
            self._backend.post_left_down()
            self._left_button_held = True

    def safe_release_all(self) -> None:
        with self._lock:
            if not self._left_button_held:
                return
            self._backend.post_left_up()
            self._left_button_held = False

    def left_button_is_down(self) -> bool:
        return self._backend.is_left_down()
