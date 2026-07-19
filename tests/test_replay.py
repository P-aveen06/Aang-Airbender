from pathlib import Path

import pytest

from aang_airbender.config import load_config
from aang_airbender.features import extract_features
from aang_airbender.poses import classify_pose
from aang_airbender.replay import read_landmark_fixture

FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "landmarks" / "synthetic_open_then_loss.jsonl"
)


def test_jsonl_landmark_replay_drives_geometry_and_pose_classification() -> None:
    states = list(read_landmark_fixture(FIXTURE))

    assert len(states) == 2
    assert states[0].valid
    pose = classify_pose(extract_features(states[0], load_config()), load_config())
    assert pose.wake_palm
    assert pose.relaxed_pointer
    assert not states[1].valid


def test_landmark_replay_rejects_malformed_records(tmp_path) -> None:
    fixture = tmp_path / "bad.jsonl"
    fixture.write_text('{"schema_version":99}\n')

    with pytest.raises(ValueError, match="line 1"):
        list(read_landmark_fixture(fixture))
