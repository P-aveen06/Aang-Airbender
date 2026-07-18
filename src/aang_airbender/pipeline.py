from __future__ import annotations

import time
from dataclasses import dataclass

from .actions import ActionDispatcher
from .config import Phase1Config
from .control import ControlEngine
from .coordinates import DisplayBounds
from .features import extract_features
from .fsm import GestureEngine
from .poses import PoseClassification, classify_pose
from .telemetry import ActionMetrics
from .types import GestureIntent, HandFeatures, HandState, IntentKind, SemanticEvent


@dataclass(frozen=True, slots=True)
class PipelineResult:
    features: HandFeatures | None
    pose: PoseClassification | None
    events: tuple[SemanticEvent, ...]


class Phase1Pipeline:
    def __init__(
        self,
        config: Phase1Config,
        bounds: DisplayBounds,
        dispatcher: ActionDispatcher,
    ) -> None:
        self.config = config
        self.dispatcher = dispatcher
        self.control = ControlEngine(config, bounds)
        self.gestures = GestureEngine(config)
        self.action_metrics = ActionMetrics()
        self._previous_features: HandFeatures | None = None

    def process_hand(self, hand: HandState) -> PipelineResult:
        if hand.valid:
            features = extract_features(hand, self.config, previous=self._previous_features)
            self._previous_features = features
            pose = classify_pose(features, self.config)
            intents = self.gestures.update(features, pose, hand.capture_timestamp_ns)
        else:
            features = None
            pose = None
            self._previous_features = None
            intents = self.gestures.update(None, None, hand.capture_timestamp_ns)
        events = self._dispatch_intents(intents)
        return PipelineResult(features, pose, events)

    def _dispatch_intents(self, intents: list[GestureIntent]) -> tuple[SemanticEvent, ...]:
        events: list[SemanticEvent] = []
        for intent in intents:
            if intent.kind is IntentKind.CANCEL:
                self.dispatcher.safe_release_all()
            for event in self.control.consume(intent):
                self.dispatcher.dispatch(event)
                self.action_metrics.record_event(event)
                events.append(event)
        return tuple(events)

    def safe_release_all(self) -> None:
        self.dispatcher.safe_release_all()

    def fault(self, now_ns: int, reason: str) -> None:
        try:
            self._dispatch_intents(self.gestures.fault(now_ns, reason))
        finally:
            self.dispatcher.safe_release_all()

    def shutdown(self, now_ns: int, reason: str = "shutdown") -> None:
        try:
            self._dispatch_intents(self.gestures.disengage(now_ns, reason))
        finally:
            self.dispatcher.safe_release_all()

    def prepare_config_reload(self, now_ns: int) -> None:
        self.shutdown(now_ns, "config_reload")

    def display_topology_changed(self, now_ns: int) -> None:
        self.shutdown(now_ns, "display_topology_changed")

    def __enter__(self) -> Phase1Pipeline:
        return self

    def __exit__(
        self, error_type: type[BaseException] | None, _error: object, _traceback: object
    ) -> None:
        if error_type is None:
            self.shutdown(time.monotonic_ns(), "process_exit")
        else:
            self.fault(time.monotonic_ns(), f"exception:{error_type.__name__}")
