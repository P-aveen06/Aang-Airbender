from __future__ import annotations

import argparse
import logging
import platform
import signal
import sys
import time
from pathlib import Path
from threading import Event

from .capture import CaptureError, OpenCVLatestFrameCapture
from .cursor import QuartzCursor, map_to_screen, palm_midpoint
from .perception import LiveHandLandmarker, is_strictly_newer
from .safety import MouseSafety, QuartzMouseEventBackend
from .timing import TimingMetrics

LOGGER = logging.getLogger(__name__)


def verify_native_environment() -> None:
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError(f"Expected Python 3.11, found {platform.python_version()}")
    if platform.machine() != "arm64":
        raise RuntimeError(
            f"Expected native Apple Silicon arm64, found {platform.machine()}; do not use Rosetta"
        )


def model_path() -> Path:
    return Path(__file__).resolve().parents[2] / "models" / "hand_landmarker.task"


def run(*, duration_seconds: float | None = None) -> int:
    verify_native_environment()
    asset = model_path()
    if not asset.is_file():
        raise RuntimeError(f"Hand Landmarker model is missing: {asset}")

    stop = Event()
    for signal_number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signal_number, lambda *_args: stop.set())

    metrics = TimingMetrics()
    capture = OpenCVLatestFrameCapture(on_frame=metrics.record_capture)
    cursor = QuartzCursor()
    safety = MouseSafety(QuartzMouseEventBackend())
    frame_version = 0
    result_version = 0
    last_result_timestamp_ms = -1

    try:
        with capture, LiveHandLandmarker(str(asset), metrics=metrics) as landmarker:
            LOGGER.info(
                "Camera active: actual=%dx%d reported_fps=%.2f reported_buffer_size=%s",
                capture.actual_width,
                capture.actual_height,
                capture.actual_fps,
                capture.buffer_size_reported,
            )
            deadline = None if duration_seconds is None else time.monotonic() + duration_seconds
            while not stop.is_set():
                if deadline is not None and time.monotonic() >= deadline:
                    stop.set()
                    continue
                capture.raise_if_failed()
                next_frame = capture.latest.get_after(frame_version)
                if next_frame is not None:
                    next_frame_version, frame = next_frame
                    metrics.record_capture_slot_drops(next_frame_version - frame_version - 1)
                    frame_version = next_frame_version
                    landmarker.submit(frame)

                next_result = landmarker.latest.get_after(result_version)
                if next_result is not None:
                    next_result_version, result = next_result
                    metrics.record_result_slot_drops(next_result_version - result_version - 1)
                    result_version = next_result_version
                    consumed_at_ns = time.monotonic_ns()
                    if not is_strictly_newer(
                        result.mediapipe_timestamp_ms, last_result_timestamp_ms
                    ):
                        metrics.record_stale()
                    else:
                        last_result_timestamp_ms = result.mediapipe_timestamp_ms
                        if result.landmarks:
                            anchor_x, anchor_y = palm_midpoint(result.landmarks)
                            screen_x, screen_y = map_to_screen(anchor_x, anchor_y, cursor.bounds)
                            cursor.move(screen_x, screen_y)
                            dispatched_at_ns = time.monotonic_ns()
                            metrics.record_dispatch(result.captured_at_ns, dispatched_at_ns)
                            LOGGER.debug(
                                "frame=%d capture=%d submit=%d callback=%d consume=%d dispatch=%d",
                                result.frame_id,
                                result.captured_at_ns,
                                result.submitted_at_ns,
                                result.callback_at_ns,
                                consumed_at_ns,
                                dispatched_at_ns,
                            )
                        else:
                            safety.safe_release_all()
                time.sleep(0.001)
    except CaptureError:
        raise
    finally:
        capture.stop()
        safety.safe_release_all()
        print(metrics.summary().render())
        print(f"quartz_left_button_down_after_shutdown={safety.left_button_is_down()}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Aang-Airbender Phase 0 cursor spike")
    parser.add_argument("--verbose", action="store_true", help="print per-result timing trace")
    parser.add_argument(
        "--duration-seconds",
        type=float,
        help="stop normally after a bounded validation run",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        raise SystemExit(run(duration_seconds=args.duration_seconds))
    except Exception as error:
        LOGGER.error("Phase 0 pipeline failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
