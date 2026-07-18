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
- Terminal application: user-run terminal shell (application name not reported); Codex task runner
  used for author-side automation
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

# User-run target-Mac validation
uv run python scripts/preflight.py
uv run python -m aang_airbender.app --duration-seconds 30
uv run python -m aang_airbender.app --duration-seconds 30
uv run python scripts/verify_safe_release.py
uv run python scripts/verify_safe_release.py
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

- Accessibility check: **PASS** — user-run preflight called
  `ApplicationServices.AXIsProcessTrusted()` and observed `True`.
- Camera-open check: **PASS** — AVFoundation opened and returned a frame after warm-up retry.
- Terminal restarted after grant: permission is active in the user-run shell; whether a full
  application restart was required was not separately reported.
- Notes: Target-Mac preflight output ended with `PREFLIGHT PASSED`.

## Capture results

- Requested resolution/FPS: 640x480 at 30 fps
- Actual resolution: 640x480
- Achieved capture FPS: 29.80 and 29.94 in two bounded 30.03-second user runs
- Median frame age at submission: 0.66 ms (run 1); 0.54 ms (run 2)
- p95 frame age at submission: 1.22 ms (run 1); 1.20 ms (run 2)
- `CAP_PROP_BUFFERSIZE` observed behavior: set to 1; backend reported 0.0. This is not treated as
  proof of buffering behavior; frame age is the evidence.

## MediaPipe results

- Submitted frames: 894 (run 1); 899 (run 2)
- Callback results: 894 (run 1); 899 (run 2)
- Capture-slot drops: 1 (run 1); 0 (run 2)
- Result-slot drops: 0 in both runs
- Stale/out-of-order results: 0 in both runs
- Inferred dropped results: 0 in both runs
- Callback/result cadence: 29.78 Hz (run 1); 29.95 Hz (run 2)

## Software pipeline latency

- Median capture-to-Quartz dispatch: 20.09 ms (run 1); 19.62 ms (run 2)
- p95 capture-to-Quartz dispatch: 219.64 ms (run 1); 20.95 ms (run 2)
- Measurement duration/sample count: 30.03 seconds / 733 dispatches (run 1); 30.03 seconds /
  811 dispatches (run 2)
- Tail-latency note: run 1 contained a material p95 outlier that did not reproduce in run 2.
  Preserve this evidence and investigate recurrence during Phase 1 performance work.

> This is software pipeline latency. It excludes camera exposure/sensor delay before frame acquisition and display composition/refresh.

## Cursor behavior

- Palm midpoint visibly controls cursor: **UNVERIFIED** — user has not yet reported the visual result
- X mirroring correct: **UNVERIFIED** manually; mapping unit test passed
- Main-display mapping correct: **UNVERIFIED** manually; mapping unit test passed
- Observed jitter or lag: **UNVERIFIED**

## Safety results

- Simulated failure after left-button-down: **PASS** twice; Quartz observed the test down and the
  combined-session state was `False` after release
- `safe_release_all()` called: yes, in the safety script's `finally` path and app shutdown path
- Quartz button state after release: `False` after controlled failure and normal shutdown, twice
- Shutdown release assertion: **PASS**; both app runs and both safety-script runs reported release

Observed safety-script output:

```text
controlled_failure: simulated=controlled pipeline failure
controlled_failure: down_observed=True combined_session_left_button_down_after_release=False
normal_shutdown: down_observed=True combined_session_left_button_down_after_release=False
SAFE RELEASE ASSERTIONS PASSED
```

The complete safe-release command passed twice.

## Author tests

```text
ruff format --check: PASS (16 files formatted)
ruff check: PASS (All checks passed)
pytest: PASS (14 passed in 5.21s, including official-model LIVE_STREAM smoke test)
fresh-environment pytest: PASS (14 passed in 1.40s)
```

## OpenCV decision

- [x] Accept OpenCV AVFoundation for Phase 1.
- [ ] Replace with native `AVCaptureSession` in Phase 1.

Reason:

Both target runs sustained approximately 30 fps with p95 frame age at or below 1.22 ms, one or zero
capture-slot drops, and no inferred MediaPipe drops. Retain OpenCV for the Phase 1 starting point.
The run-1 software-latency tail outlier remains a performance investigation item and is not attributed
to capture buffering without evidence.

## Acceptance gate — author evidence

- [x] Permission preflight passes.
- [x] Python 3.11 ARM64 environment installs cleanly.
- [ ] Cursor follows palm midpoint on target Mac.
- [x] No unbounded frame/result queue exists.
- [x] Frame age and software pipeline timing are measured.
- [x] No held mouse state survives failure or shutdown.

## Codex Phase 0 decision

**PASS / FAIL / PARTIALLY VERIFIED:** PARTIALLY VERIFIED

Rationale: Environment, architecture, clean install, bounded handoffs, MediaPipe `LIVE_STREAM`,
camera capture, callback cadence, frame age, software dispatch latency, permission preflight,
objective safe release, formatting, lint, and automated tests are verified. The user's visual cursor,
mirroring, and main-display observations remain unreported, so Phase 0 has not passed yet.

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

- Run 1 showed 219.64 ms p95 software latency versus 20.95 ms in run 2; monitor for recurrence.
- Visual cursor following, X mirroring, and main-display mapping remain `UNVERIFIED` until the user
  reports what was observed during the target-Mac run.

Do not begin Phase 1 automatically.
