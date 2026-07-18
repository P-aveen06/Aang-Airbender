from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .types import HandFrame, HandState, Point3

LANDMARK_FIXTURE_SCHEMA_VERSION = 2


def hand_state_to_record(hand: HandState) -> dict[str, Any]:
    def points(values: tuple[Point3, ...]) -> list[list[float]]:
        return [[point.x, point.y, point.z] for point in values]

    return {
        "schema_version": 1,
        "image_landmarks": points(hand.image_landmarks),
        "world_landmarks": points(hand.world_landmarks),
        "handedness": hand.handedness,
        "handedness_score": hand.handedness_score,
        "frame_id": hand.frame_id,
        "capture_timestamp_ns": hand.capture_timestamp_ns,
        "mediapipe_timestamp_ms": hand.mediapipe_timestamp_ms,
        "callback_timestamp_ns": hand.callback_timestamp_ns,
        "valid": hand.valid,
    }


def record_to_hand_state(record: dict[str, Any]) -> HandState:
    if record.get("schema_version") != 1:
        raise ValueError("Unsupported landmark fixture schema_version")

    def points(name: str) -> tuple[Point3, ...]:
        values = record.get(name)
        if not isinstance(values, list):
            raise ValueError(f"Fixture field {name} must be a list")
        try:
            return tuple(Point3(float(item[0]), float(item[1]), float(item[2])) for item in values)
        except (IndexError, TypeError, ValueError) as error:
            raise ValueError(f"Fixture field {name} contains an invalid landmark") from error

    image = points("image_landmarks")
    world = points("world_landmarks")
    valid = bool(record.get("valid"))
    if valid and len(image) != 21:
        raise ValueError("A valid fixture record must contain 21 image landmarks")
    return HandState(
        image_landmarks=image,
        world_landmarks=world,
        handedness=record.get("handedness"),
        handedness_score=float(record.get("handedness_score", 0.0)),
        frame_id=int(record["frame_id"]),
        capture_timestamp_ns=int(record["capture_timestamp_ns"]),
        mediapipe_timestamp_ms=int(record["mediapipe_timestamp_ms"]),
        callback_timestamp_ns=int(record["callback_timestamp_ns"]),
        valid=valid,
    )


def hand_frame_to_record(frame: HandFrame) -> dict[str, Any]:
    hands = []
    for hand in frame.hands:
        record = hand_state_to_record(hand)
        hands.append(
            {
                key: value
                for key, value in record.items()
                if key
                not in {
                    "schema_version",
                    "frame_id",
                    "capture_timestamp_ns",
                    "mediapipe_timestamp_ms",
                    "callback_timestamp_ns",
                }
            }
        )
    return {
        "schema_version": LANDMARK_FIXTURE_SCHEMA_VERSION,
        "hands": hands,
        "frame_id": frame.frame_id,
        "capture_timestamp_ns": frame.capture_timestamp_ns,
        "mediapipe_timestamp_ms": frame.mediapipe_timestamp_ms,
        "callback_timestamp_ns": frame.callback_timestamp_ns,
    }


def record_to_hand_frame(record: dict[str, Any]) -> HandFrame:
    if record.get("schema_version") == 1:
        hand = record_to_hand_state(record)
        return HandFrame(
            hands=(hand,) if hand.valid else (),
            frame_id=hand.frame_id,
            capture_timestamp_ns=hand.capture_timestamp_ns,
            mediapipe_timestamp_ms=hand.mediapipe_timestamp_ms,
            callback_timestamp_ns=hand.callback_timestamp_ns,
        )
    if record.get("schema_version") != LANDMARK_FIXTURE_SCHEMA_VERSION:
        raise ValueError("Unsupported landmark fixture schema_version")
    raw_hands = record.get("hands")
    if not isinstance(raw_hands, list):
        raise ValueError("Fixture field hands must be a list")
    if len(raw_hands) > 2 or not all(isinstance(item, dict) for item in raw_hands):
        raise ValueError("Fixture field hands must contain at most two hand objects")
    metadata = {
        "frame_id": int(record["frame_id"]),
        "capture_timestamp_ns": int(record["capture_timestamp_ns"]),
        "mediapipe_timestamp_ms": int(record["mediapipe_timestamp_ms"]),
        "callback_timestamp_ns": int(record["callback_timestamp_ns"]),
    }
    hands = tuple(
        record_to_hand_state({"schema_version": 1, **item, **metadata}) for item in raw_hands
    )
    return HandFrame(hands=hands, **metadata)


def read_landmark_fixture(path: Path) -> Iterator[HandFrame]:
    with path.open(encoding="utf-8") as fixture:
        for line_number, line in enumerate(fixture, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("record must be an object")
                yield record_to_hand_frame(record)
            except (json.JSONDecodeError, KeyError, ValueError) as error:
                raise ValueError(
                    f"Invalid landmark fixture at line {line_number}: {error}"
                ) from error
