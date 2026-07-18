from __future__ import annotations

from typing import Any

from .fsm import GestureEngine
from .poses import PoseClassification
from .types import HandFeatures, HandFrame

# OpenCV uses BGR. Small black text with a light outline stays legible without
# covering the user's target area.
DEBUG_TEXT_BGR = (20, 20, 20)
DEBUG_TEXT_OUTLINE_BGR = (248, 250, 251)
DEBUG_FONT_SCALE = 0.34
DEBUG_LINE_HEIGHT_PX = 15
DEBUG_MARGIN_PX = 8


def debug_text_origins(height: int, line_count: int) -> tuple[tuple[int, int], ...]:
    return tuple(
        (
            DEBUG_MARGIN_PX,
            height - DEBUG_MARGIN_PX - DEBUG_LINE_HEIGHT_PX * (line_count - line_number - 1),
        )
        for line_number in range(line_count)
    )


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
        frame: HandFrame,
        right_features: HandFeatures | None,
        left_features: HandFeatures | None,
        right_pose: PoseClassification | None,
        left_pose: PoseClassification | None,
        engine: GestureEngine,
    ) -> None:
        if frame.frame_id % self._every_n_frames:
            return
        image = image_bgr.copy()
        height, width = image.shape[:2]
        for hand in frame.hands:
            color = (40, 180, 40) if hand.handedness == "Right" else (220, 120, 20)
            for landmark in hand.image_landmarks:
                self._cv2.circle(
                    image,
                    (int(landmark.x * width), int(landmark.y * height)),
                    2,
                    color,
                    -1,
                )
        right_status = (
            "missing"
            if right_pose is None
            else "POINT"
            if right_pose.strict_index_point
            else "inactive"
        )
        if left_pose is None:
            left_status = "missing"
        elif left_pose.index_pinch_closed:
            left_status = "pinched"
        elif left_pose.index_pinch_open:
            left_status = "open"
        else:
            left_status = "ambiguous"
        right_confidence = 0.0 if right_features is None else right_features.confidence
        left_confidence = 0.0 if left_features is None else left_features.confidence
        callback_latency_ms = (frame.callback_timestamp_ns - frame.capture_timestamp_ns) / 1_000_000
        lines = (
            f"R pointer={right_status} {right_confidence:.2f} | "
            f"L click={left_status} {left_confidence:.2f}",
            f"state={engine.state.name} frame={frame.frame_id} "
            f"callback={callback_latency_ms:.1f}ms",
        )
        for line, origin in zip(lines, debug_text_origins(height, len(lines)), strict=True):
            self._cv2.putText(
                image,
                line,
                origin,
                self._cv2.FONT_HERSHEY_SIMPLEX,
                DEBUG_FONT_SCALE,
                DEBUG_TEXT_OUTLINE_BGR,
                2,
                self._cv2.LINE_AA,
            )
            self._cv2.putText(
                image,
                line,
                origin,
                self._cv2.FONT_HERSHEY_SIMPLEX,
                DEBUG_FONT_SCALE,
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
