import pytest

from aang_airbender.safety import MouseSafety


class FakeBackend:
    def __init__(self) -> None:
        self.down = False
        self.down_events = 0
        self.up_events = 0

    def post_left_down(self) -> None:
        self.down = True
        self.down_events += 1

    def post_left_up(self) -> None:
        self.down = False
        self.up_events += 1

    def is_left_down(self) -> bool:
        return self.down


@pytest.mark.parametrize("controlled_failure", [False, True])
def test_safe_release_is_idempotent_on_shutdown_and_failure(controlled_failure: bool) -> None:
    backend = FakeBackend()
    safety = MouseSafety(backend)

    try:
        safety.left_down_for_safety_test()
        if controlled_failure:
            raise RuntimeError("controlled failure")
    except RuntimeError:
        pass
    finally:
        safety.safe_release_all()
        safety.safe_release_all()

    assert backend.down is False
    assert backend.down_events == 1
    assert backend.up_events == 1


def test_safe_release_does_not_release_unowned_physical_button_state() -> None:
    backend = FakeBackend()
    backend.down = True
    safety = MouseSafety(backend)

    safety.safe_release_all()

    assert backend.down is True
    assert backend.up_events == 0
