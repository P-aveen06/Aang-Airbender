from threading import Lock
from types import SimpleNamespace

import numpy as np

from aang_airbender.capture import CapturedFrame
from aang_airbender.perception import (
    BoundedSubmissionLedger,
    LiveHandLandmarker,
    StrictlyIncreasingMilliseconds,
    SubmissionMetadata,
    is_strictly_newer,
)
from aang_airbender.slots import LatestValueSlot


def metadata(timestamp_ms: int) -> SubmissionMetadata:
    return SubmissionMetadata(timestamp_ms, 1, 2, timestamp_ms)


def test_mediapipe_timestamps_strictly_increase_within_same_millisecond() -> None:
    timestamps = StrictlyIncreasingMilliseconds()

    assert [
        timestamps.from_monotonic_ns(value) for value in (1_000_000, 1_000_000, 500_000, 2_000_000)
    ] == [1, 2, 3, 4]


def test_only_strictly_newer_results_are_accepted() -> None:
    assert is_strictly_newer(11, 10)
    assert not is_strictly_newer(10, 10)
    assert not is_strictly_newer(9, 10)


def test_submission_ledger_has_fixed_capacity_and_evicts_oldest() -> None:
    ledger = BoundedSubmissionLedger(capacity=2)
    ledger.record(metadata(10))
    ledger.record(metadata(11))
    ledger.record(metadata(12))

    assert len(ledger) == 2
    assert ledger.pop(10) is None
    assert ledger.pop(11) == metadata(11)


class FakeAsyncLandmarker:
    def __init__(self) -> None:
        self.calls: list[int] = []

    def detect_async(self, _image: object, timestamp_ms: int) -> None:
        self.calls.append(timestamp_ms)


def test_live_landmarker_allows_only_one_submission_until_callback() -> None:
    landmarker = object.__new__(LiveHandLandmarker)
    landmarker.latest = LatestValueSlot()
    landmarker._timestamps = StrictlyIncreasingMilliseconds()
    landmarker._ledger = BoundedSubmissionLedger()
    landmarker._submission_lock = Lock()
    landmarker._submission_in_flight = False
    landmarker._metrics = None
    landmarker._landmarker = FakeAsyncLandmarker()
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    first = CapturedFrame(1, image, 1_000_000)
    skipped = CapturedFrame(2, image, 2_000_000)
    resumed = CapturedFrame(3, image, 3_000_000)

    assert landmarker.submit(first)
    assert not landmarker.submit(skipped)
    assert landmarker._landmarker.calls == [1]

    empty_result = SimpleNamespace(hand_landmarks=[], hand_world_landmarks=[], handedness=[])
    landmarker._callback(empty_result, None, 1)

    assert landmarker.submit(resumed)
    assert landmarker._landmarker.calls == [1, 3]
