from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock

import cv2
import mediapipe as mp
import numpy as np

from .capture import CapturedFrame
from .config import Phase1Config
from .coordinates import CAMERA_INPUT_IS_MIRRORED, corrected_handedness
from .slots import LatestValueSlot
from .types import HandFrame, HandRoles, HandState, Point3


@dataclass(frozen=True, slots=True)
class SubmissionMetadata:
    frame_id: int
    captured_at_ns: int
    submitted_at_ns: int
    mediapipe_timestamp_ms: int


class StrictlyIncreasingMilliseconds:
    def __init__(self) -> None:
        self._last = -1

    def from_monotonic_ns(self, timestamp_ns: int) -> int:
        candidate = timestamp_ns // 1_000_000
        value = max(candidate, self._last + 1)
        self._last = value
        return value


def is_strictly_newer(timestamp_ms: int, last_consumed_timestamp_ms: int) -> bool:
    return timestamp_ms > last_consumed_timestamp_ms


class BoundedSubmissionLedger:
    """Fixed-size timestamp metadata, not a frame/result work queue."""

    def __init__(self, capacity: int = 64) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self._capacity = capacity
        self._items: dict[int, SubmissionMetadata] = {}
        self._lock = Lock()

    def record(self, metadata: SubmissionMetadata) -> None:
        with self._lock:
            if len(self._items) >= self._capacity:
                del self._items[min(self._items)]
            self._items[metadata.mediapipe_timestamp_ms] = metadata

    def pop(self, timestamp_ms: int) -> SubmissionMetadata | None:
        with self._lock:
            return self._items.pop(timestamp_ms, None)

    def discard(self, timestamp_ms: int) -> None:
        with self._lock:
            self._items.pop(timestamp_ms, None)

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)


class LiveHandLandmarker:
    def __init__(
        self,
        model_path: str,
        *,
        config: Phase1Config,
        metrics: object | None = None,
    ) -> None:
        self.latest = LatestValueSlot[HandFrame]()
        self._timestamps = StrictlyIncreasingMilliseconds()
        self._ledger = BoundedSubmissionLedger()
        self._metrics = metrics
        perception = config.section("perception")
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=model_path,
                delegate=mp.tasks.BaseOptions.Delegate.CPU,
            ),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            num_hands=int(perception["num_hands"]),
            min_hand_detection_confidence=float(perception["min_hand_detection_confidence"]),
            min_hand_presence_confidence=float(perception["min_hand_presence_confidence"]),
            min_tracking_confidence=float(perception["min_tracking_confidence"]),
            result_callback=self._callback,
        )
        self._landmarker = mp.tasks.vision.HandLandmarker.create_from_options(options)

    def submit(self, frame: CapturedFrame) -> None:
        timestamp_ms = self._timestamps.from_monotonic_ns(frame.captured_at_ns)
        submitted_at_ns = time.monotonic_ns()
        metadata = SubmissionMetadata(
            frame.frame_id,
            frame.captured_at_ns,
            submitted_at_ns,
            timestamp_ms,
        )
        self._ledger.record(metadata)
        rgb = cv2.cvtColor(frame.image_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
        if self._metrics is not None:
            self._metrics.record_submission(frame.captured_at_ns, submitted_at_ns)
        try:
            self._landmarker.detect_async(image, timestamp_ms)
        except Exception:
            self._ledger.discard(timestamp_ms)
            raise

    def _callback(
        self,
        result: mp.tasks.vision.HandLandmarkerResult,
        _output_image: mp.Image,
        timestamp_ms: int,
    ) -> None:
        callback_at_ns = time.monotonic_ns()
        metadata = self._ledger.pop(timestamp_ms)
        if self._metrics is not None:
            self._metrics.record_callback(callback_at_ns)
        if metadata is None:
            return
        hands: list[HandState] = []
        for index, raw_image_landmarks in enumerate(result.hand_landmarks):
            image_landmarks = tuple(
                Point3(float(item.x), float(item.y), float(item.z)) for item in raw_image_landmarks
            )
            world_landmarks: tuple[Point3, ...] = ()
            if index < len(result.hand_world_landmarks):
                world_landmarks = tuple(
                    Point3(float(item.x), float(item.y), float(item.z))
                    for item in result.hand_world_landmarks[index]
                )
            handedness: str | None = None
            handedness_score = 0.0
            if index < len(result.handedness) and result.handedness[index]:
                category = result.handedness[index][0]
                handedness = corrected_handedness(
                    category.category_name,
                    camera_input_is_mirrored=CAMERA_INPUT_IS_MIRRORED,
                )
                handedness_score = float(category.score)
            hands.append(
                HandState(
                    image_landmarks=image_landmarks,
                    world_landmarks=world_landmarks,
                    handedness=handedness,
                    handedness_score=handedness_score,
                    frame_id=metadata.frame_id,
                    capture_timestamp_ns=metadata.captured_at_ns,
                    mediapipe_timestamp_ms=metadata.mediapipe_timestamp_ms,
                    callback_timestamp_ns=callback_at_ns,
                    valid=len(image_landmarks) == 21,
                )
            )
        self.latest.publish(
            HandFrame(
                hands=tuple(hands),
                frame_id=metadata.frame_id,
                capture_timestamp_ns=metadata.captured_at_ns,
                mediapipe_timestamp_ms=metadata.mediapipe_timestamp_ms,
                callback_timestamp_ns=callback_at_ns,
            )
        )

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self) -> LiveHandLandmarker:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def assign_hand_roles(frame: HandFrame, *, min_confidence: float) -> HandRoles:
    """Assign physical roles without relying on MediaPipe result ordering.

    A duplicate label is ambiguous and therefore invalidates that role. This is
    intentionally stricter than choosing the highest score: a transient role
    swap must never become a click.
    """

    candidates: dict[str, list[HandState]] = {"Right": [], "Left": []}
    for hand in frame.hands:
        if hand.valid and hand.handedness in candidates and hand.handedness_score >= min_confidence:
            candidates[hand.handedness].append(hand)
    return HandRoles(
        right=candidates["Right"][0] if len(candidates["Right"]) == 1 else None,
        left=candidates["Left"][0] if len(candidates["Left"]) == 1 else None,
    )
