from aang_airbender.perception import (
    BoundedSubmissionLedger,
    StrictlyIncreasingMilliseconds,
    SubmissionMetadata,
    is_strictly_newer,
)


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
