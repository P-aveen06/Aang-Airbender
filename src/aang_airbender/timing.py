from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass
from statistics import median
from threading import Lock


def percentile(values: list[float], percentile_value: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(percentile_value * len(ordered)) - 1)
    return ordered[index]


def rate_hz(timestamps_ns: list[int]) -> float | None:
    if len(timestamps_ns) < 2:
        return None
    elapsed_seconds = (timestamps_ns[-1] - timestamps_ns[0]) / 1_000_000_000
    return (len(timestamps_ns) - 1) / elapsed_seconds if elapsed_seconds > 0 else None


@dataclass(frozen=True, slots=True)
class TimingSummary:
    measurement_duration_seconds: float | None
    capture_fps: float | None
    callback_hz: float | None
    submitted_frames: int
    callback_results: int
    capture_slot_drops: int
    result_slot_drops: int
    stale_results: int
    inferred_dropped_results: int
    dispatched_samples: int
    median_latency_ms: float | None
    p95_latency_ms: float | None
    median_frame_age_ms: float | None
    p95_frame_age_ms: float | None

    def render(self) -> str:
        def number(value: float | None) -> str:
            return "n/a" if value is None else f"{value:.2f}"

        return "\n".join(
            (
                "Aang-Airbender software timing summary",
                f"measurement_duration_s={number(self.measurement_duration_seconds)} "
                f"capture_fps={number(self.capture_fps)} callback_hz={number(self.callback_hz)}",
                f"submitted={self.submitted_frames} callbacks={self.callback_results} "
                f"capture_slot_drops={self.capture_slot_drops} "
                f"result_slot_drops={self.result_slot_drops} "
                f"stale_or_out_of_order={self.stale_results} "
                f"inferred_dropped={self.inferred_dropped_results}",
                f"dispatch_samples={self.dispatched_samples} "
                f"capture_to_quartz_median_ms={number(self.median_latency_ms)} "
                f"capture_to_quartz_p95_ms={number(self.p95_latency_ms)}",
                f"frame_age_at_submission_median_ms={number(self.median_frame_age_ms)} "
                f"frame_age_at_submission_p95_ms={number(self.p95_frame_age_ms)}",
                "software pipeline only; excludes sensor and display latency",
            )
        )


class TimingMetrics:
    """Lifetime counters with percentile/rate samples capped to the latest configured window."""

    def __init__(self, sample_capacity: int = 10_000) -> None:
        if sample_capacity < 2:
            raise ValueError("sample_capacity must be at least 2")
        self._lock = Lock()
        self._capture_timestamps: deque[int] = deque(maxlen=sample_capacity)
        self._callback_timestamps: deque[int] = deque(maxlen=sample_capacity)
        self._frame_ages_ms: deque[float] = deque(maxlen=sample_capacity)
        self._latencies_ms: deque[float] = deque(maxlen=sample_capacity)
        self._submitted = 0
        self._callbacks = 0
        self._capture_slot_drops = 0
        self._result_slot_drops = 0
        self._stale = 0

    def record_capture(self, captured_at_ns: int) -> None:
        with self._lock:
            self._capture_timestamps.append(captured_at_ns)

    def record_submission(self, captured_at_ns: int, submitted_at_ns: int) -> None:
        with self._lock:
            self._submitted += 1
            self._frame_ages_ms.append((submitted_at_ns - captured_at_ns) / 1_000_000)

    def record_callback(self, callback_at_ns: int) -> None:
        with self._lock:
            self._callbacks += 1
            self._callback_timestamps.append(callback_at_ns)

    def record_capture_slot_drops(self, count: int) -> None:
        with self._lock:
            self._capture_slot_drops += count

    def record_result_slot_drops(self, count: int) -> None:
        with self._lock:
            self._result_slot_drops += count

    def record_stale(self) -> None:
        with self._lock:
            self._stale += 1

    def record_dispatch(self, captured_at_ns: int, dispatched_at_ns: int) -> None:
        with self._lock:
            self._latencies_ms.append((dispatched_at_ns - captured_at_ns) / 1_000_000)

    def summary(self) -> TimingSummary:
        with self._lock:
            capture_timestamps = list(self._capture_timestamps)
            callback_timestamps = list(self._callback_timestamps)
            frame_ages = list(self._frame_ages_ms)
            latencies = list(self._latencies_ms)
            submitted = self._submitted
            callbacks = self._callbacks
            capture_slot_drops = self._capture_slot_drops
            result_slot_drops = self._result_slot_drops
            stale = self._stale
        return TimingSummary(
            measurement_duration_seconds=(
                (capture_timestamps[-1] - capture_timestamps[0]) / 1_000_000_000
                if len(capture_timestamps) >= 2
                else None
            ),
            capture_fps=rate_hz(capture_timestamps),
            callback_hz=rate_hz(callback_timestamps),
            submitted_frames=submitted,
            callback_results=callbacks,
            capture_slot_drops=capture_slot_drops,
            result_slot_drops=result_slot_drops,
            stale_results=stale,
            inferred_dropped_results=max(0, submitted - callbacks),
            dispatched_samples=len(latencies),
            median_latency_ms=median(latencies) if latencies else None,
            p95_latency_ms=percentile(latencies, 0.95),
            median_frame_age_ms=median(frame_ages) if frame_ages else None,
            p95_frame_age_ms=percentile(frame_ages, 0.95),
        )
