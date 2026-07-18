import pytest

from aang_airbender.actions import ActionDispatcher
from aang_airbender.types import EventKind, SemanticEvent


class FakeBackend:
    def __init__(self) -> None:
        self.events: list[tuple] = []
        self.left_down = False

    def move_pointer(self, x: float, y: float, *, left_button_held: bool) -> None:
        self.events.append(("drag" if left_button_held else "move", x, y))

    def post_left_down(self) -> None:
        self.left_down = True
        self.events.append(("left_down",))

    def post_left_up(self) -> None:
        self.left_down = False
        self.events.append(("left_up",))

    def post_right_down(self) -> None:
        self.events.append(("right_down",))

    def post_right_up(self) -> None:
        self.events.append(("right_up",))

    def post_pixel_scroll(self, dx: float, dy: float) -> None:
        self.events.append(("scroll", dx, dy))

    def is_left_down(self) -> bool:
        return self.left_down


def test_dispatcher_emits_semantic_events_and_owns_exactly_one_left_release() -> None:
    backend = FakeBackend()
    dispatcher = ActionDispatcher(backend)

    dispatcher.dispatch(SemanticEvent(EventKind.POINTER_MOVE, 1, x=10, y=20))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 2))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 3))
    dispatcher.dispatch(SemanticEvent(EventKind.POINTER_MOVE, 4, x=30, y=40))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_UP, 5))
    dispatcher.dispatch(SemanticEvent(EventKind.RIGHT_CLICK, 6))
    dispatcher.dispatch(SemanticEvent(EventKind.SCROLL, 7, pixel_dx=1, pixel_dy=2))
    dispatcher.safe_release_all()
    dispatcher.safe_release_all()

    assert backend.events == [
        ("move", 10, 20),
        ("left_down",),
        ("drag", 30, 40),
        ("left_up",),
        ("right_down",),
        ("right_up",),
        ("scroll", 1, 2),
    ]
    assert not dispatcher.left_button_is_down()


def test_unowned_physical_left_button_is_not_released() -> None:
    backend = FakeBackend()
    backend.left_down = True
    dispatcher = ActionDispatcher(backend)

    dispatcher.safe_release_all()

    assert backend.left_down
    assert backend.events == []


def test_conflicting_right_click_or_scroll_fails_closed_during_drag() -> None:
    backend = FakeBackend()
    dispatcher = ActionDispatcher(backend)
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 1))

    with pytest.raises(RuntimeError, match="right-click"):
        dispatcher.dispatch(SemanticEvent(EventKind.RIGHT_CLICK, 2))
    with pytest.raises(RuntimeError, match="scroll"):
        dispatcher.dispatch(SemanticEvent(EventKind.SCROLL, 3, pixel_dx=1, pixel_dy=2))

    dispatcher.safe_release_all()
    assert not backend.left_down


def test_failed_right_up_is_retried_by_safe_release() -> None:
    class FailOnceBackend(FakeBackend):
        def __init__(self) -> None:
            super().__init__()
            self.fail_right_up = True

        def post_right_up(self) -> None:
            self.events.append(("right_up",))
            if self.fail_right_up:
                self.fail_right_up = False
                raise RuntimeError("simulated right-up failure")

    backend = FailOnceBackend()
    dispatcher = ActionDispatcher(backend)

    with pytest.raises(RuntimeError, match="right-up"):
        dispatcher.dispatch(SemanticEvent(EventKind.RIGHT_CLICK, 1))
    dispatcher.safe_release_all()

    assert backend.events == [("right_down",), ("right_up",), ("right_up",)]
