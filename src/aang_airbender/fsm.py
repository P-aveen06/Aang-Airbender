from __future__ import annotations

import logging
import math
from collections import deque
from dataclasses import dataclass
from enum import Enum, auto

from .config import Phase1Config
from .poses import PoseClassification
from .types import GestureIntent, HandFeatures, IntentKind, Point2

LOGGER = logging.getLogger(__name__)


class EngagementState(Enum):
    DISENGAGED = auto()
    ARMING = auto()
    ENGAGED = auto()
    SUSPENDED = auto()
    FAULT = auto()


class GestureState(Enum):
    NEUTRAL = auto()
    POINTING = auto()
    PINCH_PENDING = auto()
    MIDDLE_PINCH_PENDING = auto()
    TWO_FINGER_PENDING = auto()
    DRAGGING = auto()
    SCROLLING = auto()
    RIGHT_CLICK_COMMITTED = auto()
    CLUTCHED = auto()
    UNKNOWN = auto()


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
        self.engagement = EngagementState.DISENGAGED
        self.gesture = GestureState.NEUTRAL
        self.transitions: deque[StateTransition] = deque(
            maxlen=int(config.section("debug")["state_transition_history_capacity"])
        )
        self._engagement_since_ns: int | None = None
        self._loss_since_ns: int | None = None
        self._loss_cancelled = False
        self._reacquired_since_ns: int | None = None
        self._disengage_since_ns: int | None = None
        self._candidate_since_ns: int | None = None
        self._middle_pinch_armed = False
        self._two_finger_origin: Point2 | None = None

    def _duration_ns(self, section: str, key: str) -> int:
        return int(self.config.section(section)[key]) * 1_000_000

    def _transition_engagement(self, state: EngagementState, now_ns: int, reason: str) -> None:
        if state is self.engagement:
            return
        previous = self.engagement
        self.engagement = state
        transition = StateTransition("engagement", previous.name, state.name, now_ns, reason)
        self.transitions.append(transition)
        LOGGER.info(
            "state_transition machine=%s previous=%s current=%s timestamp_ns=%d reason=%s",
            transition.machine,
            transition.previous,
            transition.current,
            transition.timestamp_ns,
            transition.reason,
        )

    def _transition_gesture(self, state: GestureState, now_ns: int, reason: str) -> None:
        if state is self.gesture:
            return
        previous = self.gesture
        self.gesture = state
        transition = StateTransition("gesture", previous.name, state.name, now_ns, reason)
        self.transitions.append(transition)
        LOGGER.info(
            "state_transition machine=%s previous=%s current=%s timestamp_ns=%d reason=%s",
            transition.machine,
            transition.previous,
            transition.current,
            transition.timestamp_ns,
            transition.reason,
        )

    def _cancel_active(self, now_ns: int, reason: str) -> list[GestureIntent]:
        intents: list[GestureIntent] = []
        if self.gesture is GestureState.DRAGGING:
            intents.append(
                GestureIntent(IntentKind.PINCH_END, now_ns, pinch_kind="index", reason=reason)
            )
        elif self.gesture is GestureState.SCROLLING:
            intents.append(GestureIntent(IntentKind.SCROLL_END, now_ns, reason=reason))
        if self.gesture is GestureState.CLUTCHED:
            intents.append(GestureIntent(IntentKind.CLUTCH_OFF, now_ns, reason=reason))
        intents.append(GestureIntent(IntentKind.CANCEL, now_ns, reason=reason))
        self._transition_gesture(GestureState.NEUTRAL, now_ns, reason)
        self._candidate_since_ns = None
        self._middle_pinch_armed = False
        self._two_finger_origin = None
        return intents

    def fault(self, now_ns: int, reason: str) -> list[GestureIntent]:
        intents = self._cancel_active(now_ns, reason)
        self._transition_engagement(EngagementState.FAULT, now_ns, reason)
        return intents

    def disengage(self, now_ns: int, reason: str) -> list[GestureIntent]:
        intents = self._cancel_active(now_ns, reason)
        self._transition_engagement(EngagementState.DISENGAGED, now_ns, reason)
        self._engagement_since_ns = None
        self._disengage_since_ns = None
        return intents

    def update(
        self,
        features: HandFeatures | None,
        pose: PoseClassification | None,
        now_ns: int,
    ) -> list[GestureIntent]:
        if self.engagement is EngagementState.FAULT:
            return []
        confidence_threshold = float(self.config.section("features")["min_valid_confidence"])
        if features is None or pose is None or features.confidence < confidence_threshold:
            if self.gesture in (
                GestureState.PINCH_PENDING,
                GestureState.MIDDLE_PINCH_PENDING,
                GestureState.TWO_FINGER_PENDING,
            ):
                self._transition_gesture(
                    GestureState.NEUTRAL, now_ns, "pending_cancelled_low_confidence"
                )
                self._candidate_since_ns = None
                self._two_finger_origin = None
            return self._on_tracking_loss(now_ns)
        engagement_intents = self._on_valid_hand(pose, now_ns)
        if self.engagement is not EngagementState.ENGAGED:
            return engagement_intents
        if pose.thumbs_down:
            return engagement_intents
        return engagement_intents + self._update_gesture(features, pose, now_ns)

    def _on_tracking_loss(self, now_ns: int) -> list[GestureIntent]:
        self._reacquired_since_ns = None
        self._disengage_since_ns = None
        if self.engagement not in (EngagementState.ENGAGED, EngagementState.SUSPENDED):
            if self.engagement is EngagementState.ARMING:
                self._transition_engagement(EngagementState.DISENGAGED, now_ns, "arming_hand_lost")
                self._engagement_since_ns = None
            return []
        if self._loss_since_ns is None:
            self._loss_since_ns = now_ns
            self._loss_cancelled = False
            self._transition_engagement(EngagementState.SUSPENDED, now_ns, "tracking_lost")
        elapsed = now_ns - self._loss_since_ns
        if elapsed >= self._duration_ns("timing", "disengage_timeout_ms"):
            return self.disengage(now_ns, "tracking_loss_timeout")
        if (
            elapsed >= self._duration_ns("timing", "hand_loss_grace_ms")
            and not self._loss_cancelled
        ):
            self._loss_cancelled = True
            return self._cancel_active(now_ns, "tracking_loss_grace_expired")
        return []

    def _on_valid_hand(self, pose: PoseClassification, now_ns: int) -> list[GestureIntent]:
        if self.engagement is EngagementState.DISENGAGED:
            if pose.wake_palm:
                self._engagement_since_ns = now_ns
                self._transition_engagement(EngagementState.ARMING, now_ns, "wake_pose_started")
            return []
        if self.engagement is EngagementState.ARMING:
            if not pose.wake_palm:
                self._engagement_since_ns = None
                self._transition_engagement(EngagementState.DISENGAGED, now_ns, "wake_pose_broken")
                return []
            assert self._engagement_since_ns is not None
            if now_ns - self._engagement_since_ns >= self._duration_ns("timing", "wake_dwell_ms"):
                self._transition_engagement(EngagementState.ENGAGED, now_ns, "wake_dwell_complete")
                self._transition_gesture(GestureState.NEUTRAL, now_ns, "engaged")
                return [GestureIntent(IntentKind.ENGAGE_REQUEST, now_ns)]
            return []
        if self.engagement is EngagementState.SUSPENDED:
            self._loss_since_ns = None
            if self._reacquired_since_ns is None:
                self._reacquired_since_ns = now_ns
                return []
            if now_ns - self._reacquired_since_ns >= self._duration_ns(
                "timing", "reacquisition_stability_ms"
            ):
                intents = self._cancel_active(now_ns, "reacquisition_fresh_baseline")
                self._transition_engagement(EngagementState.ENGAGED, now_ns, "hand_reacquired")
                self._reacquired_since_ns = None
                return intents
            return []
        self._loss_since_ns = None
        self._loss_cancelled = False
        if pose.thumbs_down:
            if self._disengage_since_ns is None:
                intents = self._cancel_active(now_ns, "thumbs_down_candidate")
                self._disengage_since_ns = now_ns
                return intents
            if now_ns - self._disengage_since_ns >= self._duration_ns(
                "timing", "thumbs_down_dwell_ms"
            ):
                return self.disengage(now_ns, "thumbs_down_dwell_complete")
            return []
        self._disengage_since_ns = None
        return []

    def _stable_for(self, now_ns: int, duration_key: str = "pose_stability_ms") -> bool:
        if self._candidate_since_ns is None:
            self._candidate_since_ns = now_ns
            return False
        return now_ns - self._candidate_since_ns >= self._duration_ns("timing", duration_key)

    def _update_gesture(
        self,
        features: HandFeatures,
        pose: PoseClassification,
        now_ns: int,
    ) -> list[GestureIntent]:
        if pose.fist and self.gesture is not GestureState.CLUTCHED:
            if self.gesture in (
                GestureState.PINCH_PENDING,
                GestureState.MIDDLE_PINCH_PENDING,
                GestureState.TWO_FINGER_PENDING,
                GestureState.DRAGGING,
                GestureState.SCROLLING,
                GestureState.RIGHT_CLICK_COMMITTED,
            ):
                intents = self._cancel_active(now_ns, "fist_release_before_clutch")
                self._candidate_since_ns = now_ns
                return intents
            if self._candidate_since_ns is None:
                intents = self._cancel_active(now_ns, "fist_candidate_safe_release")
                self._candidate_since_ns = now_ns
                return intents
            if self._stable_for(now_ns):
                self._transition_gesture(GestureState.CLUTCHED, now_ns, "fist_clutch")
                self._candidate_since_ns = None
                return [GestureIntent(IntentKind.CLUTCH_ON, now_ns)]
            return []

        if self.gesture is GestureState.DRAGGING:
            if pose.index_pinch_open:
                self._transition_gesture(GestureState.NEUTRAL, now_ns, "pinch_released")
                return [GestureIntent(IntentKind.PINCH_END, now_ns, pinch_kind="index")]
            return [GestureIntent(IntentKind.POINT, now_ns, point=features.palm_center)]

        if self.gesture is GestureState.SCROLLING:
            if not pose.two_finger:
                self._transition_gesture(GestureState.NEUTRAL, now_ns, "two_finger_released")
                self._two_finger_origin = None
                return [GestureIntent(IntentKind.SCROLL_END, now_ns)]
            return [
                GestureIntent(
                    IntentKind.SCROLL_UPDATE,
                    now_ns,
                    point=features.palm_center,
                    velocity=features.palm_velocity,
                )
            ]

        if self.gesture is GestureState.RIGHT_CLICK_COMMITTED:
            if pose.pointer_active:
                self._transition_gesture(GestureState.NEUTRAL, now_ns, "right_click_neutral")
            return []

        if self.gesture is GestureState.CLUTCHED:
            if not pose.fist:
                self._transition_gesture(GestureState.NEUTRAL, now_ns, "clutch_released")
                return [GestureIntent(IntentKind.CLUTCH_OFF, now_ns)]
            return []

        if self.gesture is GestureState.PINCH_PENDING:
            if pose.index_pinch_open:
                self._transition_gesture(GestureState.NEUTRAL, now_ns, "pinch_cancelled")
                self._candidate_since_ns = None
                return []
            if pose.index_pinch_closed and self._stable_for(now_ns):
                self._transition_gesture(GestureState.DRAGGING, now_ns, "pinch_stable")
                self._candidate_since_ns = None
                return [GestureIntent(IntentKind.PINCH_START, now_ns, pinch_kind="index")]
            return []

        if self.gesture is GestureState.MIDDLE_PINCH_PENDING:
            if pose.index_pinch_closed:
                self._transition_gesture(
                    GestureState.NEUTRAL, now_ns, "middle_pinch_cancelled_by_index_pinch"
                )
                self._candidate_since_ns = None
                self._middle_pinch_armed = False
                return []
            if pose.middle_pinch_closed:
                if self._stable_for(now_ns):
                    self._middle_pinch_armed = True
                return []
            if pose.middle_pinch_open:
                armed = self._middle_pinch_armed
                self._candidate_since_ns = None
                self._middle_pinch_armed = False
                if armed:
                    self._transition_gesture(
                        GestureState.RIGHT_CLICK_COMMITTED,
                        now_ns,
                        "middle_pinch_released",
                    )
                    return [GestureIntent(IntentKind.RIGHT_CLICK, now_ns)]
                self._transition_gesture(
                    GestureState.NEUTRAL, now_ns, "middle_pinch_cancelled_before_stable"
                )
            return []

        if self.gesture is GestureState.TWO_FINGER_PENDING:
            return self._update_two_finger(features, pose, now_ns)

        if pose.index_pinch_closed:
            self._candidate_since_ns = now_ns
            self._transition_gesture(GestureState.PINCH_PENDING, now_ns, "index_pinch_candidate")
            return []

        gesture_settings = self.config.section("gestures")
        if gesture_settings["right_click_candidate"] == "middle_pinch" and pose.middle_pinch_closed:
            self._candidate_since_ns = now_ns
            self._middle_pinch_armed = False
            self._transition_gesture(
                GestureState.MIDDLE_PINCH_PENDING, now_ns, "middle_pinch_candidate"
            )
            return []

        if pose.two_finger:
            self._candidate_since_ns = now_ns
            self._two_finger_origin = features.palm_center
            self._transition_gesture(
                GestureState.TWO_FINGER_PENDING, now_ns, "two_finger_candidate"
            )
            return []

        self._candidate_since_ns = None
        if pose.pointer_family:
            self._transition_gesture(GestureState.POINTING, now_ns, "pointer_pose")
            return [GestureIntent(IntentKind.POINT, now_ns, point=features.palm_center)]
        self._transition_gesture(GestureState.UNKNOWN, now_ns, "unknown_pose")
        return []

    def _update_two_finger(
        self,
        features: HandFeatures,
        pose: PoseClassification,
        now_ns: int,
    ) -> list[GestureIntent]:
        if not pose.two_finger:
            self._transition_gesture(GestureState.NEUTRAL, now_ns, "two_finger_cancelled")
            self._candidate_since_ns = None
            self._two_finger_origin = None
            return []
        assert self._candidate_since_ns is not None
        assert self._two_finger_origin is not None
        if now_ns - self._candidate_since_ns < self._duration_ns("timing", "pose_stability_ms"):
            return []
        control = self.config.section("control")
        displacement = (
            math.hypot(
                features.palm_center.x - self._two_finger_origin.x,
                features.palm_center.y - self._two_finger_origin.y,
            )
            / features.image_hand_scale
        )
        velocity = (
            math.hypot(features.palm_velocity.x, features.palm_velocity.y)
            / features.image_hand_scale
        )
        if displacement >= float(
            control["two_finger_scroll_displacement_ratio"]
        ) or velocity >= float(control["two_finger_scroll_velocity_ratio_per_second"]):
            self._transition_gesture(GestureState.SCROLLING, now_ns, "two_finger_motion")
            return [
                GestureIntent(IntentKind.SCROLL_START, now_ns, point=features.palm_center),
                GestureIntent(
                    IntentKind.SCROLL_UPDATE,
                    now_ns,
                    point=features.palm_center,
                    velocity=features.palm_velocity,
                ),
            ]
        still = displacement <= float(control["two_finger_stillness_radius_ratio"])
        candidate = self.config.section("gestures")["right_click_candidate"]
        fallback_enabled = self.config.section("gestures")[
            "enable_two_finger_dwell_right_click_fallback"
        ]
        if (
            candidate == "two_finger_dwell"
            and fallback_enabled
            and still
            and now_ns - self._candidate_since_ns
            >= self._duration_ns("timing", "right_click_dwell_ms")
        ):
            self._transition_gesture(
                GestureState.RIGHT_CLICK_COMMITTED, now_ns, "two_finger_right_click"
            )
            return [GestureIntent(IntentKind.RIGHT_CLICK, now_ns)]
        return []
