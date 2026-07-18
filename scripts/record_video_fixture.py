from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2

from aang_airbender.capture import OpenCVLatestFrameCapture
from aang_airbender.environment import verify_native_environment


def main() -> None:
    parser = argparse.ArgumentParser(description="Explicitly record a short local camera fixture")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration-seconds", type=float, default=5.0)
    parser.add_argument(
        "--i-understand-camera-derived-data",
        action="store_true",
        help="required acknowledgement; video contains camera imagery",
    )
    args = parser.parse_args()
    if not args.i_understand_camera_derived_data:
        parser.error("--i-understand-camera-derived-data is required; no recording was made")
    if args.duration_seconds <= 0:
        parser.error("--duration-seconds must be positive")
    if args.output.exists():
        parser.error(f"output already exists; refusing to overwrite: {args.output}")

    verify_native_environment()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    capture = OpenCVLatestFrameCapture()
    frame_version = 0
    frames_written = 0
    writer = None
    started = time.monotonic()
    try:
        with capture:
            while time.monotonic() - started < args.duration_seconds:
                capture.raise_if_failed()
                item = capture.latest.get_after(frame_version)
                if item is None:
                    time.sleep(0.001)
                    continue
                frame_version, frame = item
                if writer is None:
                    height, width = frame.image_bgr.shape[:2]
                    writer = cv2.VideoWriter(
                        str(output),
                        cv2.VideoWriter_fourcc(*"mp4v"),
                        capture.actual_fps or 30.0,
                        (width, height),
                    )
                    if not writer.isOpened():
                        raise RuntimeError(f"Could not create video fixture: {output}")
                writer.write(frame.image_bgr)
                frames_written += 1
    finally:
        capture.stop()
        if writer is not None:
            writer.release()
    elapsed = time.monotonic() - started
    print(f"video_fixture={output} frames={frames_written} duration_s={elapsed:.2f}")


if __name__ == "__main__":
    main()
