import time
from pathlib import Path

import numpy as np

from aang_airbender.capture import CapturedFrame
from aang_airbender.config import load_config
from aang_airbender.perception import LiveHandLandmarker


def test_official_model_runs_in_live_stream_mode() -> None:
    model = Path(__file__).resolve().parents[1] / "models" / "hand_landmarker.task"
    frame = CapturedFrame(1, np.zeros((480, 640, 3), dtype=np.uint8), time.monotonic_ns())

    with LiveHandLandmarker(str(model), config=load_config()) as landmarker:
        landmarker.submit(frame)
        deadline = time.monotonic() + 5.0
        result = None
        while result is None and time.monotonic() < deadline:
            result = landmarker.latest.get_after(0)
            time.sleep(0.01)

    assert result is not None
    _version, value = result
    assert value.frame_id == 1
    assert not value.valid
    assert value.image_landmarks == ()
