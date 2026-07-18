import pytest

from aang_airbender.actions import ActionDispatcher
from aang_airbender.config import load_config
from aang_airbender.coordinates import DisplayBounds
from aang_airbender.fsm import EngagementState, GestureState
from aang_airbender.pipeline import Phase1Pipeline
from aang_airbender.types import EventKind, HandState, SemanticEvent

MS = 1_000_000


class FakeBackend:
    def __init__(self) -> None:
        self.down = False
        self.down_events = 0
        self.up_events = 0

    def move_pointer(self, _x: float, _y: float) -> None:
        pass

    def post_left_down(self) -> None:
        self.down = True
        self.down_events += 1

    def post_left_up(self) -> None:
        self.down = False
        self.up_events += 1

    def post_right_click(self) -> None:
        pass

    def post_pixel_scroll(self, _dx: float, _dy: float) -> None:
        pass

    def is_left_down(self) -> bool:
        return self.down


def pipeline() -> tuple[Phase1Pipeline, FakeBackend]:
    backend = FakeBackend()
    runtime = Phase1Pipeline(
        load_config(),
        DisplayBounds(0, 0, 1000, 500),
        ActionDispatcher(backend),
    )
    return runtime, backend


def invalid_hand(timestamp_ns: int) -> HandState:
    return HandState((), (), None, 0, 1, timestamp_ns, timestamp_ns // MS, timestamp_ns, False)


def hold_left(runtime: Phase1Pipeline) -> None:
    runtime.dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, 1))


@pytest.mark.parametrize(
    "terminal_path",
    ["shutdown", "fault", "config_reload", "display_topology_change"],
)
def test_all_explicit_terminal_paths_release_owned_left_button_once(terminal_path: str) -> None:
    runtime, backend = pipeline()
    hold_left(runtime)

    if terminal_path == "shutdown":
        runtime.shutdown(2)
    elif terminal_path == "fault":
        runtime.fault(2, "simulated")
    elif terminal_path == "config_reload":
        runtime.prepare_config_reload(2)
    else:
        runtime.display_topology_changed(2)
    runtime.safe_release_all()

    assert not backend.down
    assert backend.down_events == 1
    assert backend.up_events == 1


def test_context_exception_and_normal_process_exit_both_release() -> None:
    failed, failed_backend = pipeline()
    with pytest.raises(RuntimeError, match="controlled"), failed:
        hold_left(failed)
        raise RuntimeError("controlled")
    assert not failed_backend.down

    normal, normal_backend = pipeline()
    with normal:
        hold_left(normal)
    assert not normal_backend.down


def test_tracking_loss_during_drag_releases_at_configured_grace() -> None:
    runtime, backend = pipeline()
    runtime.gestures.engagement = EngagementState.ENGAGED
    runtime.gestures.gesture = GestureState.DRAGGING
    hold_left(runtime)

    runtime.process_hand(invalid_hand(0))
    assert backend.down
    runtime.process_hand(invalid_hand(199 * MS))
    assert backend.down
    runtime.process_hand(invalid_hand(200 * MS))

    assert not backend.down
    assert backend.up_events == 1
