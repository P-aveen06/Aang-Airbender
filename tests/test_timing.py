import pytest

from aang_airbender.timing import TimingMetrics, percentile, rate_hz


def test_percentile_uses_nearest_rank() -> None:
    assert percentile(list(range(1, 101)), 0.95) == 95
    assert percentile([], 0.95) is None


def test_capture_rate_uses_monotonic_span() -> None:
    assert rate_hz([0, 500_000_000, 1_000_000_000]) == pytest.approx(2.0)


def test_summary_reports_software_latency_and_drops() -> None:
    metrics = TimingMetrics()
    metrics.record_capture(1_000_000)
    metrics.record_capture(501_000_000)
    metrics.record_submission(1_000_000, 3_000_000)
    metrics.record_submission(501_000_000, 506_000_000)
    metrics.record_callback(10_000_000)
    metrics.record_capture_slot_drops(3)
    metrics.record_result_slot_drops(2)
    metrics.record_dispatch(1_000_000, 21_000_000)
    metrics.record_stale()

    summary = metrics.summary()
    assert summary.measurement_duration_seconds == pytest.approx(0.5)
    assert summary.capture_fps == pytest.approx(2.0)
    assert summary.inferred_dropped_results == 1
    assert summary.capture_slot_drops == 3
    assert summary.result_slot_drops == 2
    assert summary.median_latency_ms == 20.0
    assert summary.median_frame_age_ms == 3.5
    assert summary.stale_results == 1
    assert "software pipeline only" in summary.render()


def test_timing_sample_storage_is_bounded() -> None:
    metrics = TimingMetrics(sample_capacity=2)
    for timestamp in (1, 2, 3):
        metrics.record_capture(timestamp)
        metrics.record_submission(0, timestamp)
        metrics.record_callback(timestamp)
        metrics.record_dispatch(0, timestamp)

    summary = metrics.summary()
    assert summary.submitted_frames == 3
    assert summary.callback_results == 3
    assert summary.dispatched_samples == 2
