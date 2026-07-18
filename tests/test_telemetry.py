from aang_airbender.telemetry import ActionMetrics
from aang_airbender.types import EventKind, SemanticEvent


def test_action_and_reported_false_action_counters_are_structured() -> None:
    metrics = ActionMetrics()
    metrics.record_event(SemanticEvent(EventKind.LEFT_CLICK, 1, x=10, y=20))
    metrics.record_false_action(EventKind.LEFT_CLICK)

    assert metrics.render() == ("action_events=LEFT_CLICK:1\nreported_false_actions=LEFT_CLICK:1")
