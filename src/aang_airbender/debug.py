from __future__ import annotations

from typing import Any

from .fsm import GestureEngine
from .poses import PoseClassification
from .types import HandFeatures, HandState

# OpenCV uses BGR. These mirror the design system's primary light/dark text contrast.
DEBUG_TEXT_BGR = (249, 250, 250)
DEBUG_TEXT_OUTLINE_BGR = (24, 24, 24)


class DebugRenderer:
    def __init__(self, every_n_frames: int) -> None:
        if every_n_frames < 1:
            raise ValueError("Debug render cadence must be positive")
        import cv2

        self._cv2 = cv2
        self._every_n_frames = every_n_frames
        self._window = "Aang-Airbender Phase 1 Debug"
        self._rendered = False

    def render(
        self,
        image_bgr: Any,
        hand: HandState,
        features: HandFeatures | None,
        pose: PoseClassification | None,
        engine: GestureEngine,
    ) -> None:
        if hand.frame_id % self._every_n_frames:
            return
        image = image_bgr.copy()
        height, width = image.shape[:2]
        for landmark in hand.image_landmarks:
            self._cv2.circle(
                image,
                (int(landmark.x * width), int(landmark.y * height)),
                3,
                (0, 255, 0),
                -1,
            )
        pose_names = "none"
        if pose is not None:
            pose_names = (
                ",".join(
                    name
                    for name, active in (
                        ("point", pose.pointer_family),
                        ("pinch", pose.index_pinch_closed),
                        ("two", pose.two_finger),
                        ("fist", pose.fist),
                        ("wake", pose.wake_palm),
                    )
                    if active
                )
                or "unknown"
            )
        confidence = 0.0 if features is None else features.confidence
        callback_latency_ms = (hand.callback_timestamp_ns - hand.capture_timestamp_ns) / 1_000_000
        lines = (
            f"pose={pose_names} confidence={confidence:.2f}",
            f"engagement={engine.engagement.name} gesture={engine.gesture.name}",
            f"frame={hand.frame_id} callback_ms={callback_latency_ms:.1f}",
        )
        for line_number, line in enumerate(lines, start=1):
            origin = (10, 24 * line_number)
            self._cv2.putText(
                image,
                line,
                origin,
                self._cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                DEBUG_TEXT_OUTLINE_BGR,
                4,
                self._cv2.LINE_AA,
            )
            self._cv2.putText(
                image,
                line,
                origin,
                self._cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                DEBUG_TEXT_BGR,
                1,
                self._cv2.LINE_AA,
            )
        self._cv2.imshow(self._window, image)
        self._cv2.waitKey(1)
        self._rendered = True

    def close(self) -> None:
        if self._rendered:
            self._cv2.destroyWindow(self._window)
