from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from enum import Enum, auto

from .config import Phase1Config
from .poses import PoseClassification
from .types import GestureIntent, HandFeatures, IntentKind

LOGGER = logging.getLogger(__name__)


class InteractionState(Enum):
    INACTIVE = auto()
    POINTING = auto()
    CLICK_PENDING = auto()
    CLICK_ARMED = auto()
    FAULT = auto()


@dataclass(frozen=True, slots=True)
class StateTransition:
    machine: str
    previous: str
    current: str
    timestamp_ns: int
    reason: str


class GestureEngine:
    def __init__(self, config: Phase1Config) -> None:
        self.config = config
        self.state = InteractionState.INACTIVE
        self.transitions: deque[StateTransition] = deque(
            maxlen=int(config.section("debug")["state_transition_history_capacity"])
        )
        self._right_candidate_since_ns: int | None = None
        self._right_loss_since_ns: int | None = None
        self._loss_release_sent = False
        self._pinch_since_ns: int | None = None
        self._left_neutral_ready = False

    def _duration_ns(self, key: str) -> int:
        return int(self.config.section("timing")[key]) * 1_000_000

    def _transition(self, state: InteractionState, now_ns: int, reason: str) -> None:
        if state is self.state:
            return
        previous = self.state
        self.state = state
        transition = StateTransition("interaction", previous.name, state.name, now_ns, reason)
        self.transitions.append(transition)
        LOGGER.info(
            "state_transition machine=%s previous=%s current=%s timestamp_ns=%d reason=%s",
            transition.machine,
            transition.previous,
            transition.current,
            transition.timestamp_ns,
            transition.reason,
        )

    @staticmethod
    def _point_intent(features: HandFeatures, now_ns: int) -> GestureIntent:
        return GestureIntent(IntentKind.POINT, now_ns, point=features.index_tip)

    def _cancel_click(self, now_ns: int, reason: str) -> GestureIntent:
        self._pinch_since_ns = None
        self._left_neutral_ready = False
        return GestureIntent(IntentKind.CLICK_CANCEL, now_ns, reason=reason)

    def fault(self, now_ns: int, reason: str) -> list[GestureIntent]:
        intents: list[GestureIntent] = []
        if self.state in (InteractionState.CLICK_PENDING, InteractionState.CLICK_ARMED):
            intents.append(self._cancel_click(now_ns, reason))
        intents.append(GestureIntent(IntentKind.CANCEL, now_ns, reason=reason))
        self._transition(InteractionState.FAULT, now_ns, reason)
        return intents

    def disengage(self, now_ns: int, reason: str) -> list[GestureIntent]:
        intents: list[GestureIntent] = []
        if self.state in (InteractionState.CLICK_PENDING, InteractionState.CLICK_ARMED):
            intents.append(self._cancel_click(now_ns, reason))
        intents.append(GestureIntent(IntentKind.CANCEL, now_ns, reason=reason))
        self._transition(InteractionState.INACTIVE, now_ns, reason)
        self._right_candidate_since_ns = None
        self._right_loss_since_ns = None
        self._loss_release_sent = False
        self._left_neutral_ready = False
        return intents

    def update(
        self,
        right_features: HandFeatures | None,
        right_pose: PoseClassification | None,
        left_features: HandFeatures | None,
        left_pose: PoseClassification | None,
        now_ns: int,
    ) -> list[GestureIntent]:
        if self.state is InteractionState.FAULT:
            return []

        right_present = right_features is not None and right_pose is not None
        right_point = right_present and right_pose.strict_index_point
        if not right_present:
            return self._on_right_loss(now_ns)
        self._right_loss_since_ns = None
        self._loss_release_sent = False

        if not right_point:
            return self._on_right_pose_break(now_ns)
        assert right_features is not None

        if self.state is InteractionState.INACTIVE:
            if self._right_candidate_since_ns is None:
                self._right_candidate_since_ns = now_ns
                return []
            if now_ns - self._right_candidate_since_ns < self._duration_ns(
                "reacquisition_stability_ms"
            ):
                return []
            self._right_candidate_since_ns = None
            self._left_neutral_ready = False
            self._transition(InteractionState.POINTING, now_ns, "right_point_stable")

        if self.state is InteractionState.POINTING:
            return self._update_pointing(right_features, left_pose, now_ns)
        if self.state is InteractionState.CLICK_PENDING:
            return self._update_click_pending(right_features, left_pose, now_ns)
        if self.state is InteractionState.CLICK_ARMED:
            return self._update_click_armed(right_features, left_pose, now_ns)
        return []

    def _on_right_loss(self, now_ns: int) -> list[GestureIntent]:
        intents: list[GestureIntent] = []
        self._right_candidate_since_ns = None
        if self.state in (InteractionState.CLICK_PENDING, InteractionState.CLICK_ARMED):
            intents.append(self._cancel_click(now_ns, "right_role_lost"))
        if self.state is not InteractionState.INACTIVE:
            self._transition(InteractionState.INACTIVE, now_ns, "right_role_lost")
        if self._right_loss_since_ns is None:
            self._right_loss_since_ns = now_ns
            self._loss_release_sent = False
        if not self._loss_release_sent and now_ns - self._right_loss_since_ns >= self._duration_ns(
            "hand_loss_grace_ms"
        ):
            self._loss_release_sent = True
            intents.append(GestureIntent(IntentKind.CANCEL, now_ns, reason="hand_loss_grace"))
        return intents

    def _on_right_pose_break(self, now_ns: int) -> list[GestureIntent]:
        intents: list[GestureIntent] = []
        self._right_candidate_since_ns = None
        if self.state in (InteractionState.CLICK_PENDING, InteractionState.CLICK_ARMED):
            intents.append(self._cancel_click(now_ns, "right_point_broken"))
        if self.state is not InteractionState.INACTIVE:
            self._transition(InteractionState.INACTIVE, now_ns, "right_point_broken")
            intents.append(GestureIntent(IntentKind.CANCEL, now_ns, reason="right_point_broken"))
        self._left_neutral_ready = False
        return intents

    def _update_pointing(
        self,
        right: HandFeatures,
        left_pose: PoseClassification | None,
        now_ns: int,
    ) -> list[GestureIntent]:
        intents = [self._point_intent(right, now_ns)]
        if left_pose is None:
            self._left_neutral_ready = False
            return intents
        if left_pose.index_pinch_open:
            self._left_neutral_ready = True
            return intents
        if left_pose.index_pinch_closed and self._left_neutral_ready:
            self._pinch_since_ns = now_ns
            self._transition(InteractionState.CLICK_PENDING, now_ns, "left_pinch_candidate")
            intents.append(GestureIntent(IntentKind.CLICK_ARM, now_ns))
        return intents

    def _update_click_pending(
        self,
        right: HandFeatures,
        left_pose: PoseClassification | None,
        now_ns: int,
    ) -> list[GestureIntent]:
        if left_pose is None:
            self._transition(InteractionState.POINTING, now_ns, "left_role_lost")
            return [
                self._cancel_click(now_ns, "left_role_lost"),
                self._point_intent(right, now_ns),
            ]
        if left_pose.index_pinch_open:
            self._transition(InteractionState.POINTING, now_ns, "left_pinch_opened_early")
            cancelled = self._cancel_click(now_ns, "left_pinch_opened_early")
            self._left_neutral_ready = True
            return [cancelled, self._point_intent(right, now_ns)]
        if left_pose.index_pinch_closed:
            assert self._pinch_since_ns is not None
            if now_ns - self._pinch_since_ns >= self._duration_ns("pose_stability_ms"):
                self._transition(InteractionState.CLICK_ARMED, now_ns, "left_pinch_stable")
        return [self._point_intent(right, now_ns)]

    def _update_click_armed(
        self,
        right: HandFeatures,
        left_pose: PoseClassification | None,
        now_ns: int,
    ) -> list[GestureIntent]:
        if left_pose is None:
            self._transition(InteractionState.POINTING, now_ns, "left_role_lost")
            return [
                self._cancel_click(now_ns, "left_role_lost"),
                self._point_intent(right, now_ns),
            ]
        if left_pose.index_pinch_open:
            self._pinch_since_ns = None
            self._left_neutral_ready = True
            self._transition(InteractionState.POINTING, now_ns, "left_pinch_released")
            return [
                GestureIntent(IntentKind.CLICK_COMMIT, now_ns),
                self._point_intent(right, now_ns),
            ]
        return [self._point_intent(right, now_ns)]
