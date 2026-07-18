import pytest

from aang_airbender.actions import ActionDispatcher, QuartzActionBackend
from aang_airbender.types import EventKind, SemanticEvent


class FakeBackend:
    def __init__(self) -> None:
        self.events: list[tuple] = []
        self.left_down = False

    def move_pointer(self, x: float, y: float, *, left_button_held: bool) -> None:
        self.events.append(("drag" if left_button_held else "move", x, y))

    def post_left_down(
        self, click_count: int, *, location: tuple[float, float] | None = None
    ) -> None:
        self.left_down = True
        self.events.append(("left_down", click_count, location))

    def post_left_up(
        self, click_count: int, *, location: tuple[float, float] | None = None
    ) -> None:
        self.left_down = False
        self.events.append(("left_up", click_count, location))

    def is_left_down(self) -> bool:
        return self.left_down


def test_quartz_mouse_event_receives_explicit_single_click_state() -> None:
    class FakeQuartz:
        kCGMouseEventClickState = 42
        kCGHIDEventTap = 7

        def __init__(self) -> None:
            self.fields: list[tuple[object, int, int]] = []

        def CGEventCreateMouseEvent(
            self, _source: object, _event_type: int, _location: tuple[float, float], _button: int
        ) -> object:
            return object()

        def CGEventSetIntegerValueField(self, event: object, field: int, value: int) -> None:
            self.fields.append((event, field, value))

        def CGEventPost(self, _tap: int, _event: object) -> None:
            pass

    quartz = FakeQuartz()
    backend = QuartzActionBackend.__new__(QuartzActionBackend)
    backend._quartz = quartz

    backend._post_mouse(1, 0, (10.0, 20.0), click_count=1)

    assert len(quartz.fields) == 1
    assert quartz.fields[0][1:] == (quartz.kCGMouseEventClickState, 1)


def test_atomic_click_moves_to_anchor_and_posts_one_owned_down_up_pair() -> None:
    backend = FakeBackend()
    dispatcher = ActionDispatcher(backend)

    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_CLICK, 1, x=10, y=20))
    dispatcher.safe_release_all()
    dispatcher.safe_release_all()

    assert backend.events == [
        ("move", 10, 20),
        ("left_down", 1, (10, 20)),
        ("left_up", 1, (10, 20)),
    ]
    assert not dispatcher.left_button_is_down()


def test_two_rapid_click_events_remain_two_single_clicks() -> None:
    backend = FakeBackend()
    dispatcher = ActionDispatcher(backend)

    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_CLICK, 1, x=10, y=20))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_CLICK, 2, x=10, y=20))

    assert backend.events == [
        ("move", 10, 20),
        ("left_down", 1, (10, 20)),
        ("left_up", 1, (10, 20)),
        ("move", 10, 20),
        ("left_down", 1, (10, 20)),
        ("left_up", 1, (10, 20)),
    ]


def test_failed_atomic_click_up_is_retried_by_safe_release() -> None:
    class FailOnceBackend(FakeBackend):
        def __init__(self) -> None:
            super().__init__()
            self.fail_up = True

        def post_left_up(
            self, click_count: int, *, location: tuple[float, float] | None = None
        ) -> None:
            self.events.append(("left_up", click_count, location))
            if self.fail_up:
                self.fail_up = False
                raise RuntimeError("simulated left-up failure")
            self.left_down = False

    backend = FailOnceBackend()
    dispatcher = ActionDispatcher(backend)

    with pytest.raises(RuntimeError, match="left-up"):
        dispatcher.dispatch(SemanticEvent(EventKind.LEFT_CLICK, 1, x=10, y=20))
    dispatcher.safe_release_all()

    assert backend.events == [
        ("move", 10, 20),
        ("left_down", 1, (10, 20)),
        ("left_up", 1, (10, 20)),
        ("left_up", 1, (10, 20)),
    ]
    assert not backend.left_down


def test_failed_atomic_click_down_is_conservatively_released() -> None:
    class FailDownBackend(FakeBackend):
        def post_left_down(
            self, click_count: int, *, location: tuple[float, float] | None = None
        ) -> None:
            super().post_left_down(click_count, location=location)
            raise RuntimeError("simulated left-down failure")

    backend = FailDownBackend()
    dispatcher = ActionDispatcher(backend)

    with pytest.raises(RuntimeError, match="left-down"):
        dispatcher.dispatch(SemanticEvent(EventKind.LEFT_CLICK, 1, x=10, y=20))
    dispatcher.safe_release_all()

    assert backend.events == [
        ("move", 10, 20),
        ("left_down", 1, (10, 20)),
        ("left_up", 1, (10, 20)),
    ]
    assert not backend.left_down


def test_unowned_physical_left_button_is_not_released() -> None:
    backend = FakeBackend()
    backend.left_down = True
    dispatcher = ActionDispatcher(backend)

    dispatcher.safe_release_all()

    assert backend.left_down
    assert backend.events == []


def test_controlled_legacy_down_is_released_once_and_idempotently() -> None:
    backend = FakeBackend()
    dispatcher = ActionDispatcher(backend)
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 1))

    dispatcher.safe_release_all()
    dispatcher.safe_release_all()

    assert backend.events == [("left_down", 1, None), ("left_up", 1, None)]
