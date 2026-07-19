from pathlib import Path

import pytest

from aang_airbender.app import _validate_landmark_recording_request
from aang_airbender.replay import LandmarkFixtureWriter, read_landmark_fixture
from aang_airbender.types import HandState


def hand_state() -> HandState:
    return HandState(
        image_landmarks=(),
        world_landmarks=(),
        handedness=None,
        handedness_score=0.0,
        frame_id=7,
        capture_timestamp_ns=1_000_000_000,
        mediapipe_timestamp_ms=1_000,
        callback_timestamp_ns=1_020_000_000,
        valid=False,
    )


def test_live_landmark_recording_requires_explicit_camera_data_acknowledgement(
    tmp_path: Path,
) -> None:
    output = tmp_path / "live.jsonl"

    with pytest.raises(ValueError, match="camera-derived-data is required"):
        _validate_landmark_recording_request(output, camera_data_acknowledged=False)

    _validate_landmark_recording_request(output, camera_data_acknowledged=True)


def test_landmark_fixture_writer_round_trips_and_refuses_to_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "live.jsonl"
    expected = hand_state()

    with LandmarkFixtureWriter(output) as writer:
        writer.write(expected)

    assert writer.records == 1
    assert list(read_landmark_fixture(output)) == [expected]
    with pytest.raises(FileExistsError), LandmarkFixtureWriter(output):
        pass
