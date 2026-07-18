from __future__ import annotations

import time

from aang_airbender.safety import MouseSafety, QuartzMouseEventBackend


def wait_for_button_state(safety: MouseSafety, expected: bool, timeout: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if safety.left_button_is_down() is expected:
            return True
        time.sleep(0.01)
    return safety.left_button_is_down() is expected


def exercise_release(label: str, *, simulate_failure: bool) -> None:
    safety = MouseSafety(QuartzMouseEventBackend())
    down_observed = False
    try:
        safety.left_down_for_safety_test()
        down_observed = wait_for_button_state(safety, True)
        if simulate_failure:
            raise RuntimeError("controlled pipeline failure")
    except RuntimeError as error:
        if not simulate_failure:
            raise
        print(f"{label}: simulated={error}")
    finally:
        safety.safe_release_all()
        safety.safe_release_all()
    released = wait_for_button_state(safety, False)
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
