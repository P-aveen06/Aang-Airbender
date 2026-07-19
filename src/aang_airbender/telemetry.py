from __future__ import annotations

from collections import Counter

from .types import EventKind, SemanticEvent


class ActionMetrics:
    def __init__(self) -> None:
        self._emitted: Counter[str] = Counter()
        self._reported_false: Counter[str] = Counter()

    def record_event(self, event: SemanticEvent) -> None:
        self._emitted[event.kind.name] += 1

    def record_false_action(self, kind: EventKind) -> None:
        self._reported_false[kind.name] += 1

    def render(self) -> str:
        emitted = (
            ",".join(f"{name}:{count}" for name, count in sorted(self._emitted.items())) or "none"
        )
        reported_false = (
            ",".join(f"{name}:{count}" for name, count in sorted(self._reported_false.items()))
            or "none"
        )
        return f"action_events={emitted}\nreported_false_actions={reported_false}"
