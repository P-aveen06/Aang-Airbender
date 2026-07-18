from __future__ import annotations

import time

from aang_airbender.actions import ActionDispatcher, QuartzActionBackend
from aang_airbender.config import load_config
from aang_airbender.types import EventKind, SemanticEvent


def wait_for_button_state(
    dispatcher: ActionDispatcher, expected: bool, timeout: float = 1.0
) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if dispatcher.left_button_is_down() is expected:
            return True
        time.sleep(0.01)
    return dispatcher.left_button_is_down() is expected


def exercise_release(label: str, *, simulate_failure: bool) -> None:
    config = load_config()
    dispatcher = ActionDispatcher(
        QuartzActionBackend(),
        double_click_interval_ms=int(config.section("timing")["double_click_interval_ms"]),
        double_click_max_distance_pixels=float(
            config.section("control")["double_click_max_distance_pixels"]
        ),
    )
    down_observed = False
    try:
        dispatcher.dispatch(SemanticEvent(EventKind.LEFT_DOWN, time.monotonic_ns()))
        down_observed = wait_for_button_state(dispatcher, True)
        if simulate_failure:
            raise RuntimeError("controlled pipeline failure")
    except RuntimeError as error:
        if not simulate_failure:
            raise
        print(f"{label}: simulated={error}")
    finally:
        dispatcher.safe_release_all()
        dispatcher.safe_release_all()
    released = wait_for_button_state(dispatcher, False)
    print(
        f"{label}: down_observed={down_observed} "
        f"combined_session_left_button_down_after_release={not released}"
    )
    if not released:
        raise AssertionError(f"{label}: left mouse button remained held")
    if not down_observed:
        raise RuntimeError(
            f"{label}: Quartz did not observe the test mouse-down. Run the permission preflight "
            "and grant Accessibility before repeating this test."
        )


def main() -> None:
    exercise_release("controlled_failure", simulate_failure=True)
    exercise_release("normal_shutdown", simulate_failure=False)
    print("SAFE RELEASE ASSERTIONS PASSED")


if __name__ == "__main__":
    main()
