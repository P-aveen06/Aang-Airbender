from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from threading import Event, Thread

import cv2
import numpy as np

from .slots import LatestValueSlot

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CapturedFrame:
    frame_id: int
    image_bgr: np.ndarray
    captured_at_ns: int


class CaptureError(RuntimeError):
    pass


class OpenCVLatestFrameCapture:
    def __init__(
        self,
        *,
        camera_index: int = 0,
        width: int = 640,
        height: int = 480,
        fps: float = 30.0,
        on_frame: Callable[[int], None] | None = None,
    ) -> None:
        self.latest = LatestValueSlot[CapturedFrame]()
        self._camera_index = camera_index
        self._width = width
        self._height = height
        self._fps = fps
        self._on_frame = on_frame
        self._stop = Event()
        self._failed = Event()
        self._thread: Thread | None = None
        self._capture: cv2.VideoCapture | None = None
        self.actual_width = 0
        self.actual_height = 0
        self.actual_fps = 0.0
        self.buffer_size_reported: float | None = None

    def start(self) -> None:
        if self._thread is not None:
            raise CaptureError("Capture is already running")

        capture = cv2.VideoCapture(self._camera_index, cv2.CAP_AVFOUNDATION)
        if not capture.isOpened():
            capture.release()
            raise CaptureError(
                "Could not open camera with OpenCV AVFoundation. Run scripts/preflight.py "
                "and verify Camera permission."
            )

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        capture.set(cv2.CAP_PROP_FPS, self._fps)
        # AVFoundation may ignore this. The reported value and measured frame age are evidence.
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.actual_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.actual_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.actual_fps = float(capture.get(cv2.CAP_PROP_FPS))
        self.buffer_size_reported = float(capture.get(cv2.CAP_PROP_BUFFERSIZE))
        self._capture = capture
        self._stop.clear()
        self._failed.clear()
        self._thread = Thread(target=self._run, name="avfoundation-capture", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        assert self._capture is not None
        capture = self._capture
        frame_id = 0
        try:
            while not self._stop.is_set():
                ok, image = capture.read()
                captured_at_ns = time.monotonic_ns()
                if not ok or image is None:
                    LOGGER.error("AVFoundation camera read failed; stopping capture")
                    self._failed.set()
                    self._stop.set()
                    break
                frame_id += 1
                self.latest.publish(CapturedFrame(frame_id, image, captured_at_ns))
                if self._on_frame is not None:
                    self._on_frame(captured_at_ns)
        finally:
            capture.release()

    def raise_if_failed(self) -> None:
        if self._failed.is_set():
            raise CaptureError("AVFoundation camera read failed after capture started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            if self._thread.is_alive() and self._capture is not None:
                LOGGER.warning("Camera read did not stop within 2 seconds; forcing release")
                self._capture.release()
                self._thread.join(timeout=1.0)
        self._thread = None
        self._capture = None

    def __enter__(self) -> OpenCVLatestFrameCapture:
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()
