from __future__ import annotations

import argparse
import logging
import signal
import time
from threading import Event

from .actions import ActionDispatcher, QuartzActionBackend
from .capture import OpenCVLatestFrameCapture
from .config import load_config
from .debug import DebugRenderer
from .environment import model_path, verify_native_environment
from .perception import LiveHandLandmarker, is_strictly_newer
from .pipeline import Phase1Pipeline
from .timing import TimingMetrics
from .types import EventKind

LOGGER = logging.getLogger(__name__)


def run(*, duration_seconds: float | None = None, debug: bool = False) -> int:
    verify_native_environment()
    config = load_config()
    asset = model_path()
    if not asset.is_file():
        raise RuntimeError(f"Hand Landmarker model is missing: {asset}")

    stop = Event()
    for signal_number in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signal_number, lambda *_args: stop.set())

    metrics = TimingMetrics()
    capture = OpenCVLatestFrameCapture(on_frame=metrics.record_capture)
    backend = QuartzActionBackend()
    dispatcher = ActionDispatcher(
        backend,
        double_click_interval_ms=int(config.section("timing")["double_click_interval_ms"]),
        double_click_max_distance_pixels=float(
            config.section("control")["double_click_max_distance_pixels"]
        ),
    )
    display_bounds = backend.main_display_bounds()
    display_topology = backend.display_topology_signature()
    pipeline = Phase1Pipeline(config, display_bounds, dispatcher)
    renderer = (
        DebugRenderer(int(config.section("debug")["render_every_n_frames"])) if debug else None
    )
    frame_version = 0
    result_version = 0
    last_result_timestamp_ms = -1
    display_check_interval_ns = (
        int(config.section("timing")["display_topology_check_ms"]) * 1_000_000
    )
    next_display_check_ns = time.monotonic_ns() + display_check_interval_ns

    try:
        with (
            pipeline,
            capture,
            LiveHandLandmarker(str(asset), config=config, metrics=metrics) as landmarker,
        ):
            LOGGER.info(
                "Camera active: actual=%dx%d reported_fps=%.2f reported_buffer_size=%s",
                capture.actual_width,
                capture.actual_height,
                capture.actual_fps,
                capture.buffer_size_reported,
            )
            deadline = None if duration_seconds is None else time.monotonic() + duration_seconds
            while not stop.is_set():
                now_ns = time.monotonic_ns()
                if now_ns >= next_display_check_ns:
                    if backend.display_topology_signature() != display_topology:
                        pipeline.display_topology_changed(now_ns)
                        raise RuntimeError(
                            "Display topology changed; held inputs were released. Restart "
                            "Aang-Airbender to use the new display layout."
                        )
                    next_display_check_ns = now_ns + display_check_interval_ns
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
                        pipeline_result = pipeline.process_hand(result)
                        for event in pipeline_result.events:
                            if event.kind is EventKind.POINTER_MOVE:
                                dispatched_at_ns = time.monotonic_ns()
                                metrics.record_dispatch(
                                    result.capture_timestamp_ns, dispatched_at_ns
                                )
                        if renderer is not None:
                            debug_frame = capture.latest.get_after(0)
                            if debug_frame is not None:
                                renderer.render(
                                    debug_frame[1].image_bgr,
                                    result,
                                    pipeline_result.features,
                                    pipeline_result.pose,
                                    pipeline.gestures,
                                )
                        LOGGER.debug(
                            "frame=%d capture=%d callback=%d consume=%d engagement=%s gesture=%s",
                            result.frame_id,
                            result.capture_timestamp_ns,
                            result.callback_timestamp_ns,
                            consumed_at_ns,
                            pipeline.gestures.engagement.name,
                            pipeline.gestures.gesture.name,
                        )
                time.sleep(0.001)
    finally:
        capture.stop()
        pipeline.safe_release_all()
        if renderer is not None:
            renderer.close()
        print(metrics.summary().render())
        print(pipeline.action_metrics.render())
        print(f"quartz_left_button_down_after_shutdown={dispatcher.left_button_is_down()}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Aang-Airbender Phase 1 core-five controller")
    parser.add_argument("--verbose", action="store_true", help="print per-result timing trace")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="show the configured every-Nth-frame landmark/FSM debug preview",
    )
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
        raise SystemExit(run(duration_seconds=args.duration_seconds, debug=args.debug))
    except Exception as error:
        LOGGER.error("Phase 1 pipeline failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
