import pytest

from aang_airbender.actions import ActionDispatcher, QuartzActionBackend
from aang_airbender.types import EventKind, SemanticEvent


class FakeBackend:
    def __init__(self) -> None:
        self.events: list[tuple] = []
        self.left_down = False

    def move_pointer(self, x: float, y: float, *, left_button_held: bool) -> None:
        self.events.append(("drag" if left_button_held else "move", x, y))

    def post_left_down(self, click_count: int) -> None:
        self.left_down = True
        self.events.append(("left_down", click_count))

    def post_left_up(self, click_count: int) -> None:
        self.left_down = False
        self.events.append(("left_up", click_count))

    def post_right_down(self) -> None:
        self.events.append(("right_down",))

    def post_right_up(self) -> None:
        self.events.append(("right_up",))

    def post_pixel_scroll(self, dx: float, dy: float) -> None:
        self.events.append(("scroll", dx, dy))

    def is_left_down(self) -> bool:
        return self.left_down


def test_quartz_mouse_event_receives_explicit_double_click_state() -> None:
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

    backend._post_mouse(1, 0, (10.0, 20.0), click_count=2)

    assert len(quartz.fields) == 1
    assert quartz.fields[0][1:] == (quartz.kCGMouseEventClickState, 2)


def test_dispatcher_emits_semantic_events_and_owns_exactly_one_left_release() -> None:
    backend = FakeBackend()
    dispatcher = ActionDispatcher(
        backend, double_click_interval_ms=500, double_click_max_distance_pixels=12
    )

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
        ("left_down", 1),
        ("drag", 30, 40),
        ("left_up", 1),
        ("right_down",),
        ("right_up",),
        ("scroll", 1, 2),
    ]
    assert not dispatcher.left_button_is_down()


def test_unowned_physical_left_button_is_not_released() -> None:
    backend = FakeBackend()
    backend.left_down = True
    dispatcher = ActionDispatcher(
        backend, double_click_interval_ms=500, double_click_max_distance_pixels=12
    )

    dispatcher.safe_release_all()

    assert backend.left_down
    assert backend.events == []


def test_conflicting_right_click_or_scroll_fails_closed_during_drag() -> None:
    backend = FakeBackend()
    dispatcher = ActionDispatcher(
        backend, double_click_interval_ms=500, double_click_max_distance_pixels=12
    )
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
    dispatcher = ActionDispatcher(
        backend, double_click_interval_ms=500, double_click_max_distance_pixels=12
    )

    with pytest.raises(RuntimeError, match="right-up"):
        dispatcher.dispatch(SemanticEvent(EventKind.RIGHT_CLICK, 1))
    dispatcher.safe_release_all()

    assert backend.events == [("right_down",), ("right_up",), ("right_up",)]


def test_second_click_cycle_within_configured_interval_has_double_click_state() -> None:
    backend = FakeBackend()
    dispatcher = ActionDispatcher(
        backend, double_click_interval_ms=500, double_click_max_distance_pixels=12
    )

    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 1_000_000_000))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_UP, 1_050_000_000))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 1_300_000_000))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_UP, 1_350_000_000))

    assert backend.events == [
        ("left_down", 1),
        ("left_up", 1),
        ("left_down", 2),
        ("left_up", 2),
    ]


def test_click_after_configured_interval_restarts_at_single_click_state() -> None:
    backend = FakeBackend()
    dispatcher = ActionDispatcher(
        backend, double_click_interval_ms=200, double_click_max_distance_pixels=12
    )

    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 1_000_000_000))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_UP, 1_050_000_000))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 1_251_000_000))

    assert backend.events[-1] == ("left_down", 1)


def test_click_after_pointer_moves_beyond_configured_distance_is_single() -> None:
    backend = FakeBackend()
    dispatcher = ActionDispatcher(
        backend, double_click_interval_ms=500, double_click_max_distance_pixels=12
    )
    dispatcher.dispatch(SemanticEvent(EventKind.POINTER_MOVE, 1, x=10, y=20))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 2))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_UP, 3))
    dispatcher.dispatch(SemanticEvent(EventKind.POINTER_MOVE, 4, x=100, y=100))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 5))

    assert backend.events[-1] == ("left_down", 1)


def test_drag_cycle_does_not_arm_a_following_double_click() -> None:
    backend = FakeBackend()
    dispatcher = ActionDispatcher(
        backend, double_click_interval_ms=500, double_click_max_distance_pixels=12
    )
    dispatcher.dispatch(SemanticEvent(EventKind.POINTER_MOVE, 1, x=10, y=20))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 2))
    dispatcher.dispatch(SemanticEvent(EventKind.POINTER_MOVE, 3, x=11, y=20))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_UP, 4))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 5))

    assert backend.events[-1] == ("left_down", 1)


def test_safe_release_clears_an_unfinished_double_click_sequence() -> None:
    backend = FakeBackend()
    dispatcher = ActionDispatcher(
        backend, double_click_interval_ms=500, double_click_max_distance_pixels=12
    )
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 1))
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_UP, 2))
    dispatcher.safe_release_all()
    dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 3))

    assert backend.events[-1] == ("left_down", 1)
