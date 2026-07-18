from dataclasses import replace
from pathlib import Path

import pytest

from aang_airbender.config import load_config
from aang_airbender.features import extract_features
from aang_airbender.poses import classify_pose
from aang_airbender.replay import (
    hand_frame_to_record,
    read_landmark_fixture,
    record_to_hand_frame,
)

FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "landmarks" / "synthetic_open_then_loss.jsonl"
)


def test_jsonl_landmark_replay_drives_geometry_and_pose_classification() -> None:
    frames = list(read_landmark_fixture(FIXTURE))

    assert len(frames) == 2
    assert len(frames[0].hands) == 1
    pose = classify_pose(extract_features(frames[0].hands[0], load_config()), load_config())
    assert not pose.strict_index_point
    assert not frames[1].hands


def test_landmark_replay_rejects_malformed_records(tmp_path) -> None:
    fixture = tmp_path / "bad.jsonl"
    fixture.write_text('{"schema_version":99}\n')

    with pytest.raises(ValueError, match="line 1"):
        list(read_landmark_fixture(fixture))

    fixture.write_text('{"schema_version":2,"hands":[1]}\n')
    with pytest.raises(ValueError, match="line 1"):
        list(read_landmark_fixture(fixture))


def test_two_hand_frame_record_round_trip_preserves_roles_and_metadata() -> None:
    original = list(read_landmark_fixture(FIXTURE))[0]
    right = replace(original.hands[0], handedness="Right")
    left = replace(original.hands[0], handedness="Left")
    two_hand = replace(original, hands=(right, left))

    restored = record_to_hand_frame(hand_frame_to_record(two_hand))

    assert restored == two_hand
