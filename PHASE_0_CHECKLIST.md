# Aang-Airbender — Phase 0 Implementation Checklist

**Timebox:** 1 day  
**Goal:** prove the webcam → MediaPipe → Quartz cursor pipeline on the target M2 MacBook Air.

## 1. Environment

- [ ] Pin the project interpreter with `uv python pin 3.11`; commit the generated `.python-version`.
- [ ] Create the clean `uv` project under that pinned interpreter and verify `python -c "import platform; print(platform.python_version(), platform.machine())"` reports Python 3.11 and `arm64`.
- [ ] Pin `mediapipe`, `opencv-python`, `pyobjc-framework-Quartz`, and required support packages.
- [ ] Add the exact `hand_landmarker.task` model asset under `models/`.
- [ ] Verify all dependencies install natively on Apple Silicon from a clean environment.

## 2. Permissions

- [ ] Add `scripts/preflight.py` that calls `AXIsProcessTrusted()` and exits with a clear error when Accessibility permission is missing.
- [ ] In the same preflight, attempt to open the webcam once so macOS can present the Camera permission prompt and report failure clearly.
- [ ] Document how to grant Camera and Accessibility permissions to the terminal application running the spike.
- [ ] Fully quit and restart the terminal application after granting Accessibility permission, then rerun the preflight.
- [ ] Do not debug capture, MediaPipe, or Quartz until the preflight passes.

## 3. Capture

- [ ] Open the webcam through OpenCV using the AVFoundation backend.
- [ ] Request 640×480 at 30 fps.
- [ ] Use a single-slot latest-frame handoff; never queue stale frames.
- [ ] Record `frame_id` and a monotonic capture timestamp for every accepted frame.
- [ ] Measure achieved capture rate and frame age.

## 4. Hand Landmarker

- [ ] Configure MediaPipe `HandLandmarker` in `LIVE_STREAM` mode for one hand.
- [ ] Supply strictly increasing millisecond timestamps to `detect_async()`.
- [ ] Keep the MediaPipe callback minimal: build an immutable result and overwrite a latest-result slot.
- [ ] Consume results on the pipeline thread, not inside the callback.
- [ ] Discard stale or out-of-order results.

## 5. Cursor output

- [ ] Use the palm midpoint `(landmark 5 + landmark 17) / 2` as the single cursor anchor.
- [ ] Mirror X so movement feels natural in the webcam view.
- [ ] Map the normalized coordinate to the main display.
- [ ] Move the cursor using a raw Quartz mouse-move event.
- [ ] Do not add filtering, acceleration, gestures, calibration, or HUD behavior.

## 6. Timing trace

For each processed frame, capture:

- [ ] Capture timestamp.
- [ ] MediaPipe submission timestamp.
- [ ] Callback timestamp.
- [ ] Pipeline-consume timestamp.
- [ ] Quartz dispatch timestamp.
- [ ] Frame age at inference submission.

Print or save a compact timing summary containing:

- [ ] Achieved capture FPS.
- [ ] Callback/result cadence.
- [ ] Median and p95 **software pipeline latency** from accepted-frame capture timestamp to Quartz dispatch.
- [ ] Number of submitted frames, returned results, and dropped/stale frames.

The software pipeline latency deliberately excludes camera exposure, sensor/driver delay before the capture timestamp, display composition, and display refresh. Do not compare this Phase 0 measurement directly with the Phase 2 `< 80 ms` motion-to-visible target.

## 7. Safe-release test

- [ ] Emit a test left-button-down event.
- [ ] Simulate tracking loss or a controlled pipeline failure.
- [ ] Call `safe_release_all()`.
- [ ] Assert `CGEventSourceButtonState(kCGEventSourceStateCombinedSessionState, kCGMouseButtonLeft)` is `False` after release.
- [ ] Repeat the assertion during normal process shutdown.

## Acceptance gate

Phase 0 passes only when all are true:

- [ ] The permission preflight passes after any required terminal restart.
- [ ] Cursor visibly follows the palm midpoint on the target Mac.
- [ ] Native ARM64 dependencies install from a clean environment using the pinned Python version.
- [ ] No unbounded frame or result queue exists.
- [ ] Frame age, result cadence, and dispatch timing are measured.
- [ ] No held mouse state survives tracking loss or shutdown.

## Explicitly out of scope

Do **not** add during Phase 0:

- Gesture vocabulary or gesture FSM
- Click, drag, scroll, clutch, or right-click recognition
- One Euro filtering or acceleration curves
- Calibration
- HUD or menu-bar UI
- Configuration schema or migration logic
- Fixture recording
- Packaging as a macOS `.app`
- Production abstractions not required by the spike

## End-of-day output

- [ ] Runnable spike command documented in `README.md` or `PROGRESS.md`.
- [ ] Timing summary recorded in `PROGRESS.md`.
- [ ] Pass/fail decision recorded for OpenCV capture latency.
- [ ] Known failures and Phase 1 blockers listed.
- [ ] Stop after the acceptance decision; do not continue into Phase 1 automatically.
