# Aang-Airbender — Progress

## Phase 0 status

**Status:** In progress
**Author:** Codex  
**Independent reviewer:** Claude  
**Decision:** Pending  
**Target branch:** `develop`  
**Implementation branch:** `codex/phase-0-spike`
**Pull request:** <https://github.com/P-aveen06/Aang-Airbender/pull/1>
**Commit SHA reviewed:** `3d16fbb` (author self-review; later PR-link-only commit excluded)
**Target machine:** M2 MacBook Air, macOS 13+  
**Python:** 3.11, ARM64

## Environment

- Date: 2026-07-18
- macOS version: 26.5.1 (build 25F80)
- Hardware: MacBook Air (Mac14,2), Apple M2, 16 GB
- Terminal application: Codex desktop task runner; target Terminal permission/restart flow `UNVERIFIED`
- Python version and architecture: CPython 3.11.14, `arm64` (observed)
- `uv` version: 0.9.13
- MediaPipe version: 0.10.21
- OpenCV version: 4.11.0 (distribution `opencv-python==4.11.0.86`)
- PyObjC / Quartz version: 12.2.1
- Hand Landmarker model source/version/checksum: MediaPipe Hand Landmarker `float16/1`;
  official Google-hosted URL in `models/MODEL_INFO.md`; SHA-256
  `fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1`

## Commands run by Codex

```bash
git switch -c codex/phase-0-spike
uv python pin 3.11
uv add --bounds exact mediapipe opencv-python pyobjc-framework-Quartz
uv add --bounds exact pyobjc-framework-ApplicationServices
uv add --dev --bounds exact pytest ruff
uv add mediapipe==0.10.21 opencv-python==4.11.0.86
curl --fail --location --output models/hand_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
shasum -a 256 models/hand_landmarker.task
.venv/bin/python -c "import platform; print(platform.python_version(), platform.machine())"
.venv/bin/ruff format .
.venv/bin/ruff format --check .
.venv/bin/ruff check .
.venv/bin/pytest
.venv/bin/python scripts/preflight.py
test ! -e /private/tmp/aang-phase0-clean-env-019f738a && \
  UV_PROJECT_ENVIRONMENT=/private/tmp/aang-phase0-clean-env-019f738a uv sync --frozen
/private/tmp/aang-phase0-clean-env-019f738a/bin/python -c \
  "import platform; print(platform.python_version(), platform.machine())"
MPLCONFIGDIR=/private/tmp/aang-matplotlib \
  /private/tmp/aang-phase0-clean-env-019f738a/bin/pytest
MPLCONFIGDIR=/private/tmp/aang-matplotlib \
  .venv/bin/python -u -m aang_airbender.app --duration-seconds 10
.venv/bin/python -u scripts/verify_safe_release.py
```

Observed setup output:

```text
Pinned `.python-version` to `3.11`
Python 3.11.14 arm64
mediapipe 0.10.21
opencv 4.11.0
pytest 9.1.1
ruff 0.15.22
```

Initial `uv run` before `README.md` existed failed in Hatchling with
`OSError: Readme file does not exist: README.md`; adding the required README resolved it.

The initially resolved `mediapipe==0.10.35` hard-aborted during native task creation in the
restricted runner. The implementation was changed to exact pins `mediapipe==0.10.21` and
`opencv-python==4.11.0.86`. With explicit CPU inference, the restricted runner reports its missing
WindowServer GPU service as a Python exception; outside that restriction the official-model
`LIVE_STREAM` smoke test passes.

Fresh-environment evidence:

```text
Using CPython 3.11.14
Creating virtual environment at: /private/tmp/aang-phase0-clean-env-019f738a
Installed 38 packages
3.11.14 arm64
mediapipe 0.10.21; opencv-python 4.11.0.86; pyobjc-framework-Quartz 12.2.1
14 tests passed
```

## Permission preflight

- Accessibility check: **FAILED** — corrected preflight called
  `ApplicationServices.AXIsProcessTrusted()` and observed `False`, with terminal-restart guidance.
- Camera-open check: **PASS** — AVFoundation opened and returned a frame after warm-up retry.
- Terminal restarted after grant: **UNVERIFIED**
- Notes: Camera capture now works. Accessibility must be granted and the runner fully restarted
  before visible cursor and objective mouse-down safety validation.

## Capture results

- Requested resolution/FPS: 640x480 at 30 fps
- Actual resolution: 640x480
- Achieved capture FPS: 24.04 during a bounded 10.03-second run
- Median frame age at submission: 0.62 ms
- p95 frame age at submission: 1.23 ms
- `CAP_PROP_BUFFERSIZE` observed behavior: set to 1; backend reported 0.0. This is not treated as
  proof of buffering behavior; frame age is the evidence.

## MediaPipe results

- Submitted frames: 241
- Callback results: 241
- Capture-slot drops: 0
- Result-slot drops: 0
- Stale/out-of-order results: 0
- Inferred dropped results: 0
- Callback/result cadence: 24.03 Hz

## Software pipeline latency

- Median capture-to-Quartz dispatch: **UNVERIFIED** — no hand landmarks during bounded run
- p95 capture-to-Quartz dispatch: **UNVERIFIED** — no hand landmarks during bounded run
- Measurement duration/sample count: 10.03 seconds / 0 Quartz dispatch samples

> This is software pipeline latency. It excludes camera exposure/sensor delay before frame acquisition and display composition/refresh.

## Cursor behavior

- Palm midpoint visibly controls cursor: **UNVERIFIED** — Accessibility denied
- X mirroring correct: **UNVERIFIED** manually; mapping unit test passed
- Main-display mapping correct: **UNVERIFIED** manually; mapping unit test passed
- Observed jitter or lag: **UNVERIFIED**

## Safety results

- Simulated failure after left-button-down: attempted; test down was not observable because
  Accessibility is denied
- `safe_release_all()` called: yes, in the safety script's `finally` path and app shutdown path
- Quartz button state after release: `False`, but full down-then-release assertion is `UNVERIFIED`
- Shutdown release assertion: app reported `quartz_left_button_down_after_shutdown=False`

Observed safety-script output:

```text
controlled_failure: simulated=controlled pipeline failure
controlled_failure: down_observed=False combined_session_left_button_down_after_release=False
RuntimeError: Quartz did not observe the test mouse-down. Run the permission preflight and grant
Accessibility before repeating this test.
```

## Author tests

```text
ruff format --check: PASS (16 files formatted)
ruff check: PASS (All checks passed)
pytest: PASS (14 passed in 5.21s, including official-model LIVE_STREAM smoke test)
fresh-environment pytest: PASS (14 passed in 1.40s)
```

## OpenCV decision

- [ ] Accept OpenCV AVFoundation for Phase 1.
- [ ] Replace with native `AVCaptureSession` in Phase 1.

Reason:

Pending a target run with hand landmarks and Accessibility permission. The observed frame age is
low, but the 10-second/no-hand sample is insufficient for the Phase 1 backend decision.

## Acceptance gate — author evidence

- [ ] Permission preflight passes.
- [x] Python 3.11 ARM64 environment installs cleanly.
- [ ] Cursor follows palm midpoint on target Mac.
- [x] No unbounded frame/result queue exists.
- [ ] Frame age and software pipeline timing are measured.
- [ ] No held mouse state survives failure or shutdown.

## Codex Phase 0 decision

**PASS / FAIL / PARTIALLY VERIFIED:** PARTIALLY VERIFIED

Rationale: Environment, architecture, clean install, bounded handoffs, MediaPipe `LIVE_STREAM`,
camera capture, callback cadence, frame age, shutdown cleanup, formatting, lint, and automated tests
are verified. Accessibility preflight, visible cursor behavior, dispatch latency with a detected hand,
and objective down-then-release Quartz state remain unverified, so Phase 0 has not passed.

## Claude independent validation

- Review date:
- Commit SHA reviewed:
- Commands reproduced:
- Automated checks result:
- Target-Mac checks reproduced:
- Items still unverified:
- Blocking findings:
- Non-blocking findings:
- Verdict: `APPROVE / REQUEST CHANGES / INCOMPLETE EVIDENCE`
- Re-review conditions:

## Review-loop history

| Round | Commit SHA | Claude verdict | Blocking findings | Codex response | Resolved |
|---|---|---|---|---|---|
| 1 |  |  |  |  |  |

## Final user decision

- [ ] Merge approved by user.
- [ ] Merge deferred.
- [ ] Phase 0 rejected.

Notes:

## Blockers and Phase 1 notes

- Accessibility permission is not granted to the current runner.
- Cursor behavior, timing measurements, and objective Quartz safe-release assertions remain
  `UNVERIFIED` until the permission preflight passes on the target Mac.

Do not begin Phase 1 automatically.
