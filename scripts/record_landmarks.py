from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from aang_airbender.environment import model_path, verify_native_environment


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Explicitly record a local MediaPipe landmark JSONL fixture"
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration-seconds", type=float, default=30.0)
    parser.add_argument(
        "--i-understand-camera-derived-data",
        action="store_true",
        help="required acknowledgement; recordings may reveal biometric motion",
    )
    args = parser.parse_args()
    if not args.i_understand_camera_derived_data:
        parser.error("--i-understand-camera-derived-data is required; no recording was made")
    if args.duration_seconds <= 0:
        parser.error("--duration-seconds must be positive")
    if args.output.exists():
        parser.error(f"output already exists; refusing to overwrite: {args.output}")

    verify_native_environment()
    from aang_airbender.capture import OpenCVLatestFrameCapture
    from aang_airbender.config import load_config
    from aang_airbender.perception import LiveHandLandmarker
    from aang_airbender.replay import hand_state_to_record

    config = load_config()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    frame_version = 0
    result_version = 0
    records = 0
    started = time.monotonic()
    capture = OpenCVLatestFrameCapture()
    try:
        with (
            output.open("x", encoding="utf-8") as destination,
            capture,
            LiveHandLandmarker(str(model_path()), config=config) as landmarker,
        ):
            while time.monotonic() - started < args.duration_seconds:
                capture.raise_if_failed()
                frame_item = capture.latest.get_after(frame_version)
                if frame_item is not None:
                    frame_version, frame = frame_item
                    landmarker.submit(frame)
                result_item = landmarker.latest.get_after(result_version)
                if result_item is not None:
                    result_version, hand = result_item
                    destination.write(json.dumps(hand_state_to_record(hand), separators=(",", ":")))
                    destination.write("\n")
                    records += 1
                time.sleep(0.001)
    finally:
        capture.stop()
    elapsed = time.monotonic() - started
    print(f"landmark_fixture={output} records={records} duration_s={elapsed:.2f}")


if __name__ == "__main__":
    main()
