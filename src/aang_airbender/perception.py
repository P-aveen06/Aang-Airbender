from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock

import cv2
import mediapipe as mp
import numpy as np

from .capture import CapturedFrame
from .slots import LatestValueSlot


@dataclass(frozen=True, slots=True)
class Landmark2D:
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class SubmissionMetadata:
    frame_id: int
    captured_at_ns: int
    submitted_at_ns: int
    mediapipe_timestamp_ms: int


@dataclass(frozen=True, slots=True)
class LandmarkResult:
    frame_id: int
    landmarks: tuple[Landmark2D, ...]
    captured_at_ns: int
    submitted_at_ns: int
    mediapipe_timestamp_ms: int
    callback_at_ns: int


class StrictlyIncreasingMilliseconds:
    def __init__(self) -> None:
        self._last = -1

    def from_monotonic_ns(self, timestamp_ns: int) -> int:
        candidate = timestamp_ns // 1_000_000
        value = max(candidate, self._last + 1)
        self._last = value
        return value


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
    def __init__(self, model_path: str, *, metrics: object | None = None) -> None:
        self.latest = LatestValueSlot[LandmarkResult]()
        self._timestamps = StrictlyIncreasingMilliseconds()
        self._ledger = BoundedSubmissionLedger()
        self._metrics = metrics
        options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(
                model_asset_path=model_path,
                delegate=mp.tasks.BaseOptions.Delegate.CPU,
            ),
            running_mode=mp.tasks.vision.RunningMode.LIVE_STREAM,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.6,
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
        landmarks: tuple[Landmark2D, ...] = ()
        if result.hand_landmarks:
            landmarks = tuple(
                Landmark2D(float(item.x), float(item.y)) for item in result.hand_landmarks[0]
            )
        self.latest.publish(
            LandmarkResult(
                metadata.frame_id,
                landmarks,
                metadata.captured_at_ns,
                metadata.submitted_at_ns,
                metadata.mediapipe_timestamp_ms,
                callback_at_ns,
            )
        )

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self) -> LiveHandLandmarker:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
