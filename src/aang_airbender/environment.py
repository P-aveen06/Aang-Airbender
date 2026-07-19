from __future__ import annotations

import platform
import sys
from pathlib import Path


def verify_native_environment() -> None:
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError(f"Expected Python 3.11, found {platform.python_version()}")
    if platform.machine() != "arm64":
        raise RuntimeError(
            f"Expected native Apple Silicon arm64, found {platform.machine()}; do not use Rosetta"
        )


def model_path() -> Path:
    return Path(__file__).resolve().parents[2] / "models" / "hand_landmarker.task"
