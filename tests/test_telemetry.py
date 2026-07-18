from aang_airbender.telemetry import ActionMetrics
from aang_airbender.types import EventKind, SemanticEvent


def test_action_and_reported_false_action_counters_are_structured() -> None:
    metrics = ActionMetrics()
    metrics.record_event(SemanticEvent(EventKind.LEFT_DOWN, 1))
    metrics.record_event(SemanticEvent(EventKind.LEFT_UP, 2))
    metrics.record_false_action(EventKind.LEFT_DOWN)

    assert metrics.render() == (
        "action_events=LEFT_DOWN:1,LEFT_UP:1\nreported_false_actions=LEFT_DOWN:1"
    )
