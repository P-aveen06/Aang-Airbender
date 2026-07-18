from __future__ import annotations

import time
from dataclasses import dataclass

from .actions import ActionDispatcher
from .config import Phase1Config
from .control import ControlEngine
from .coordinates import DisplayBounds
from .features import extract_features
from .fsm import GestureEngine
from .perception import assign_hand_roles
from .poses import PoseClassification, classify_pose
from .telemetry import ActionMetrics
from .types import GestureIntent, HandFeatures, HandFrame, HandState, IntentKind, SemanticEvent


@dataclass(frozen=True, slots=True)
class PipelineResult:
    right_features: HandFeatures | None
    left_features: HandFeatures | None
    right_pose: PoseClassification | None
    left_pose: PoseClassification | None
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
        self._previous_right_features: HandFeatures | None = None
        self._previous_left_features: HandFeatures | None = None

    def process_frame(self, frame: HandFrame) -> PipelineResult:
        confidence = float(self.config.section("features")["min_valid_confidence"])
        roles = assign_hand_roles(frame, min_confidence=confidence)
        right_features, right_pose = self._extract_role(roles.right, role="right")
        left_features, left_pose = self._extract_role(roles.left, role="left")
        intents = self.gestures.update(
            right_features,
            right_pose,
            left_features,
            left_pose,
            frame.capture_timestamp_ns,
        )
        events = self._dispatch_intents(intents)
        return PipelineResult(right_features, left_features, right_pose, left_pose, events)

    def process_hand(self, hand: HandState) -> PipelineResult:
        """Compatibility helper for v1 fixture readers; live code uses process_frame."""

        return self.process_frame(
            HandFrame(
                hands=(hand,) if hand.valid else (),
                frame_id=hand.frame_id,
                capture_timestamp_ns=hand.capture_timestamp_ns,
                mediapipe_timestamp_ms=hand.mediapipe_timestamp_ms,
                callback_timestamp_ns=hand.callback_timestamp_ns,
            )
        )

    def _extract_role(
        self, hand: HandState | None, *, role: str
    ) -> tuple[HandFeatures | None, PoseClassification | None]:
        previous = (
            self._previous_right_features if role == "right" else self._previous_left_features
        )
        if hand is None:
            if role == "right":
                self._previous_right_features = None
            else:
                self._previous_left_features = None
            return None, None
        try:
            features = extract_features(hand, self.config, previous=previous)
        except ValueError:
            if role == "right":
                self._previous_right_features = None
            else:
                self._previous_left_features = None
            return None, None
        if role == "right":
            self._previous_right_features = features
        else:
            self._previous_left_features = features
        return features, classify_pose(features, self.config)

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
