from aang_airbender.actions import ActionDispatcher
from aang_airbender.types import EventKind, SemanticEvent


class FakeBackend:
    def __init__(self) -> None:
        self.events: list[tuple] = []
        self.left_down = False

    def move_pointer(self, x: float, y: float) -> None:
        self.events.append(("move", x, y))

    def post_left_down(self) -> None:
        self.left_down = True
        self.events.append(("left_down",))

    def post_left_up(self) -> None:
        self.left_down = False
        self.events.append(("left_up",))

    def post_right_click(self) -> None:
        self.events.append(("right_click",))

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
    dispatcher.dispatch(SemanticEvent(EventKind.RIGHT_CLICK, 4))
    dispatcher.dispatch(SemanticEvent(EventKind.SCROLL, 5, pixel_dx=1, pixel_dy=2))
    dispatcher.safe_release_all()
    dispatcher.safe_release_all()

    assert backend.events == [
        ("move", 10, 20),
        ("left_down",),
        ("right_click",),
        ("scroll", 1, 2),
        ("left_up",),
    ]
    assert not dispatcher.left_button_is_down()


def test_unowned_physical_left_button_is_not_released() -> None:
    backend = FakeBackend()
    backend.left_down = True
    dispatcher = ActionDispatcher(backend)

    dispatcher.safe_release_all()

    assert backend.left_down
    assert backend.events == []
