from aang_airbender.perception import (
    BoundedSubmissionLedger,
    StrictlyIncreasingMilliseconds,
    SubmissionMetadata,
    assign_hand_roles,
    is_strictly_newer,
)
from aang_airbender.types import HandFrame, HandState, Point3


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


def hand(label: str, score: float = 0.99) -> HandState:
    points = (Point3(0.5, 0.5, 0.0),) * 21
    return HandState(points, (), label, score, 1, 1, 1, 1, True)


def frame(*hands: HandState) -> HandFrame:
    return HandFrame(hands, 1, 1, 1, 1)


def test_role_assignment_uses_physical_labels_not_result_order() -> None:
    right = hand("Right")
    left = hand("Left")

    ordered = assign_hand_roles(frame(right, left), min_confidence=0.6)
    reordered = assign_hand_roles(frame(left, right), min_confidence=0.6)

    assert ordered.right is right and ordered.left is left
    assert reordered.right is right and reordered.left is left


def test_duplicate_or_low_confidence_role_fails_closed() -> None:
    duplicate = assign_hand_roles(frame(hand("Right"), hand("Right")), min_confidence=0.6)
    low = assign_hand_roles(frame(hand("Right", 0.4), hand("Left")), min_confidence=0.6)

    assert duplicate.right is None
    assert duplicate.left is None
    assert low.right is None
    assert low.left is not None
