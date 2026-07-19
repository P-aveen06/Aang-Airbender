from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any, TextIO

from .types import HandState, Point3

LANDMARK_FIXTURE_SCHEMA_VERSION = 1


class LandmarkFixtureWriter:
    """Write an explicitly authorized landmark stream without overwriting existing data."""

    def __init__(self, path: Path) -> None:
        self.path = path.resolve()
        self.records = 0
        self._destination: TextIO | None = None

    def __enter__(self) -> LandmarkFixtureWriter:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._destination = self.path.open("x", encoding="utf-8")
        return self

    def write(self, hand: HandState) -> None:
        if self._destination is None:
            raise RuntimeError("Landmark fixture writer is not open")
        self._destination.write(json.dumps(hand_state_to_record(hand), separators=(",", ":")))
        self._destination.write("\n")
        self._destination.flush()
        self.records += 1

    def __exit__(self, _error_type: object, _error: object, _traceback: object) -> None:
        if self._destination is not None:
            self._destination.close()
            self._destination = None


def hand_state_to_record(hand: HandState) -> dict[str, Any]:
    def points(values: tuple[Point3, ...]) -> list[list[float]]:
        return [[point.x, point.y, point.z] for point in values]

    return {
        "schema_version": LANDMARK_FIXTURE_SCHEMA_VERSION,
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
    if record.get("schema_version") != LANDMARK_FIXTURE_SCHEMA_VERSION:
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


def read_landmark_fixture(path: Path) -> Iterator[HandState]:
    with path.open(encoding="utf-8") as fixture:
        for line_number, line in enumerate(fixture, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("record must be an object")
                yield record_to_hand_state(record)
            except (json.JSONDecodeError, KeyError, ValueError) as error:
                raise ValueError(
                    f"Invalid landmark fixture at line {line_number}: {error}"
                ) from error
