# Aang-Airbender — Progress

## Phase 0 status

**Status:** Phase 0 accepted and merged into `develop`
**Author:** Codex  
**Independent reviewer:** Claude  
**Decision:** Phase 0 author gate passed; Claude round-2 verdict `APPROVE`
**Target branch:** `develop`  
**Implementation branch:** `codex/phase-0-spike`
**Pull request:** <https://github.com/P-aveen06/Aang-Airbender/pull/1>
**Commit SHA reviewed:** `7ba6504` (Claude round-2 `APPROVE`)
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

- Palm midpoint visibly controls cursor: **PASS** — user confirmed visible palm-following movement
- X mirroring correct: **PASS** — moving the hand right moved the cursor right
- Main-display mapping correct: **PASS** — user controlled the cursor across the main display
- Observed jitter or lag: user reported no significant jitter or lag
- Control-range observation: larger palm travel produced less cursor travel than desired. The user
  does not want excessive sensitivity. Record this for Phase 1 control-box/calibration tuning; do not
  add filtering, calibration, or acceleration to Phase 0.

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
pytest: PASS (14 passed in 4.12s after review fixes, including official-model LIVE_STREAM smoke test)
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
- [x] Cursor follows palm midpoint on target Mac.
- [x] No unbounded frame/result queue exists.
- [x] Frame age and software pipeline timing are measured.
- [x] No held mouse state survives failure or shutdown.

## Codex Phase 0 decision

**PASS / FAIL / PARTIALLY VERIFIED:** PASS

Rationale: Environment, architecture, clean install, bounded handoffs, MediaPipe `LIVE_STREAM`,
camera capture, callback cadence, frame age, software dispatch latency, permission preflight,
objective safe release, visual cursor following, X mirroring, main-display mapping, formatting,
lint, and automated tests are verified. All Phase 0 author acceptance conditions are satisfied.

## Claude independent validation

- Review date: 2026-07-18 (round 2)
- Commit SHA reviewed: `7ba6504`
- Commands reproduced: formatting, lint, tests, and full delta inspection in a Linux container
- Automated checks result: PASS; 14 tests passed in Claude's environment
- Target-Mac checks reproduced: unavailable to Claude; author/user evidence audited and accepted
- Items still unverified: independent target-Mac reproduction only; non-blocking and disclosed
- Blocking findings: none; round-1 B1 resolved
- Non-blocking findings: no unresolved findings; reviewed-SHA documentation nit corrected afterward
- Verdict: `APPROVE`
- Re-review conditions: none

## Review-loop history

| Round | Commit SHA | Claude verdict | Blocking findings | Codex response | Resolved |
|---|---|---|---|---|---|
| 1 | `8d0700a` | `REQUEST CHANGES` | Missing target-Mac evidence | Added complete target evidence; reconciled metrics; addressed both nits | Yes |
| 2 | `7ba6504` | `APPROVE` | None | Phase 0 acceptance gate satisfied | Yes |

## Final user decision

- [x] Merge approved by user.
- [ ] Merge deferred.
- [ ] Phase 0 rejected.

Notes: The project owner reported PR #1 merged into `develop` on 2026-07-18. Codex synchronized
the local `develop` branch with `origin/develop` and created `codex/phase-1-core-five` from the
merged commit before beginning Phase 1.

## Blockers and Phase 1 notes

- Run 1 showed 219.64 ms p95 software latency versus 20.95 ms in run 2; monitor for recurrence.
- Phase 1 control tuning should increase usable cursor travel without making movement excessively
  sensitive; this is explicitly deferred from Phase 0.

## Phase 1 status

**Status:** IN PROGRESS — implementation started with explicit project-owner authorization
**Implementation branch:** `codex/phase-1-core-five`
**Frozen scope and acceptance source:** `PLAN.md`, Phase 1 — Core five and safety
**Validator contract:** `CLAUDE.md`

### Phase 1 startup commands

```bash
git switch develop
git pull --ff-only origin develop
git switch -c codex/phase-1-core-five
```

### Initial Phase 1 decisions and unresolved evidence

- Retain OpenCV AVFoundation based on the Phase 0 decision and evidence.
- Implement the configurable central control box in absolute mode to improve usable cursor travel.
  Do not add Phase 2 acceleration curves or relative mapping.
- Recording scripts will be implemented, but landmark/video capture is explicit opt-in because it
  records camera-derived data. The required target-Mac fixtures remain **UNVERIFIED** until recorded.
- All Phase 1 target-Mac manual acceptance checks remain **UNVERIFIED** until the implementation is
  complete and the exact checks are run and recorded.

### Phase 1 implementation log

```bash
uv add --bounds exact pyyaml jsonschema
.venv/bin/ruff format .
.venv/bin/ruff check .
.venv/bin/pytest
```

Dependency result: added exact direct pins `pyyaml==6.0.3` and `jsonschema==4.26.0`; lockfile
updated. The initial sandboxed `uv add` could not access uv's user cache (`Operation not permitted`);
the approved cache-access retry succeeded.

First headless core slice:

- Added versioned `config.yaml` and strict Draft 2020-12 schema validation. Unknown fields and
  invalid cross-field relationships fail closed.
- Added immutable `HandState`, `HandFeatures`, `GestureIntent`, and `SemanticEvent` domain types.
- Added weighted five-landmark palm centroid, palm-relative joint geometry, normalized pinch
  ratios, palm-facing score, and timestamp-derived velocity.
- Added strict index point, relaxed pointer, two-finger, fist, wake-palm, pinch hysteresis, and
  cross-pinch predicates.
- Formatting: PASS. Lint: PASS.
- Tests: 26 PASS, 1 environment-dependent model smoke test FAIL. The failure is the already-known
  restricted Codex runner limitation: MediaPipe could not create `NSOpenGLPixelFormat` / GPU
  service. The same official model smoke path passed on the unrestricted target Mac in Phase 0.
  This Phase 1 target-Mac rerun remains **UNVERIFIED** until the complete pipeline is ready.

Second core/safety slice:

- Added elapsed-time engagement and gesture FSMs with wake dwell, pose stability, hand-loss grace,
  reacquisition stability, pinch hysteresis, two-finger arbitration and branch locking, one-shot
  right click, scroll, drag, clutch, and terminal fault behavior.
- Added One Euro filtering with initial `min_cutoff=1.0`, `beta=0.007`; configurable central-box
  absolute mapping; natural pixel scrolling without momentum; and fresh filter baselines.
- Centralized camera mirroring and MediaPipe handedness correction in `coordinates.py`; removed the
  obsolete Phase 0 cursor adapter so there is no second mirroring implementation.
- Added the single Phase 1 Quartz action dispatcher with owned-button tracking and idempotent
  `safe_release_all()`; removed the obsolete duplicate Phase 0 safety adapter.
- Added an exception-safe pipeline boundary. Tracking loss, disengagement, simulated fault, config
  reload preparation, display topology change, normal process exit, and exceptional process exit
  are covered with a mocked dispatcher and explicit release assertions.
- Added opt-in landmark/video recording scripts, strict JSONL replay, a synthetic non-camera replay
  fixture, debug rendering off by default, structured state-transition logs, emitted-action counts,
  and reported-false-action counters.
- Updated setup/run/privacy/error documentation. No camera-derived recording was made by Codex.

Validation commands and outputs:

```text
.venv/bin/ruff format .
36 files left unchanged

.venv/bin/ruff check .
All checks passed!

.venv/bin/pytest -q -k 'not official_model_runs_in_live_stream_mode'
50 passed, 1 deselected in 22.66s

# Approved WindowServer-capable target-Mac execution
.venv/bin/pytest
51 passed in 1.63s
```

The full test run includes geometry, pose predicates, FSM sequences, JSONL landmark replay,
configuration failure paths, semantic control, action ownership, pipeline terminal paths, bounded
handoffs, monotonic timestamps, timing metrics, and the official-model `LIVE_STREAM` smoke test.

Current Codex-process permission probe:

```text
.venv/bin/python scripts/preflight.py
Python: 3.11.14
Architecture: arm64
Accessibility trusted: False
AVFoundation camera opened: True
AVFoundation camera frame read: True
PREFLIGHT FAILED — Accessibility permission is missing for the Codex process
```

This does not invalidate the earlier Phase 0 user-terminal permission evidence, but it prevents
Codex from claiming a Phase 1 Quartz end-to-end run. Phase 1 real cursor/click/drag/scroll and
objective release checks are **UNVERIFIED — requires the user's Accessibility-trusted terminal**.

### Phase 1 author self-review fixes

Codex reviewed the complete branch diff against the current `origin/develop`. The optional local
gstack review workflow could not be used safely because its bootstrap requested a destructive reset
of its own installation and unavailable interactive first-run prompts; no repository changes came
from that tool. Codex continued with a direct line-by-line plan, architecture, enum-completeness,
bounded-state, failure-path, and test audit.

Findings fixed before the target-Mac acceptance run:

- Quartz pointer movement now emits `kCGEventLeftMouseDragged` while the dispatcher owns the left
  button; ordinary movement still emits `kCGEventMouseMoved`.
- Right-click is represented as owned right-down/right-up operations. A failed right-up remains
  tracked and is retried by `safe_release_all()`; conflicting right-click/scroll during drag fails
  closed.
- Two-finger arbitration uses configured low-pass velocity smoothing and motion normalized by the
  image-space palm scale, instead of raw distance-dependent motion.
- Camera-facing palm orientation now uses the correct handedness-dependent image-coordinate normal.
  The synthetic fixture had represented a left palm and was relabeled accordingly.
- Fist explicitly excludes both pinch predicates to prevent a curled hand becoming a click/drag.
- Display topology is polled through Quartz. Any online-display ID/bounds change releases inputs and
  stops with a restart instruction.
- FSM transition history changed from an unbounded list to a configured 256-entry ring; logs now use
  explicit parseable fields.
- Intent and semantic-event dispatch are exhaustive and fail closed on an unsupported enum value.
- Added `PHASE_1_VALIDATION.md` and a deterministic 44-unit manual target-acquisition page without
  adding an application HUD or any Phase 2 product behavior.

Review-regression validation:

```text
.venv/bin/ruff format .
PASS
.venv/bin/ruff check .
All checks passed!
.venv/bin/pytest -q -k 'not official_model_runs_in_live_stream_mode'
54 passed, 1 deselected in 22.88s
.venv/bin/python -m compileall -q src scripts tests
PASS

# WindowServer-capable full run
.venv/bin/pytest
55 passed (including official-model LIVE_STREAM smoke)

# Read-only Quartz display probe
DisplayBounds(x=0.0, y=0.0, width=1470.0, height=956.0)
((1, DisplayBounds(x=0.0, y=0.0, width=1470.0, height=956.0)),)
```

Clean lockfile environment:

```text
test ! -e /private/tmp/aang-phase1-review-019f738a && \
  UV_PROJECT_ENVIRONMENT=/private/tmp/aang-phase1-review-019f738a uv sync --frozen
Using CPython 3.11.14
Installed 44 packages

MPLCONFIGDIR=/private/tmp/aang-phase1-matplotlib \
  /private/tmp/aang-phase1-review-019f738a/bin/pytest
55 passed in 60.59s
```

The required user-recorded 30-second landmark fixture, short video, five-minute core-five session,
44-unit target acquisition evidence, 10-minute normal false-click session, 30-minute adversarial
session, and real Quartz safety/loss checks remain **UNVERIFIED**. Exact commands and evidence fields
are in `PHASE_1_VALIDATION.md`.

### Target-Mac debug-preview feedback

- User screenshot showed the initial yellow debug text had insufficient contrast against a light
  wall and was difficult to read.
- Changed the debug overlay to design-system-aligned off-white text with a dark outline so it remains
  legible over both light and dark camera content. This affects only the opt-in Phase 1 debug preview.

### Target-Mac open-palm engagement regression

User-provided 22.36-second screen recording from 2026-07-18 showed stable 21-landmark tracking at
0.94–0.99 confidence while a camera-facing open palm was repeatedly reported as `pose=point` and
the controller remained `engagement=DISENGAGED`. The cursor therefore correctly received no motion
intent, but the wake-palm predicate was unreachable for that real hand.

An offline MediaPipe Tasks `IMAGE`-mode diagnostic on an extracted recording frame reproduced the
failure with all five fingers extended. The raw model result was `Left` at 0.988 confidence, but the
unmirrored AVFoundation path incorrectly exchanged it to `Right`; the handedness-dependent palm
normal then produced `palm_facing_score=0.0`, preventing wake recognition. The physical handedness
label now remains unchanged for unmirrored input and is exchanged only when the camera input itself
is mirrored. Pointer X mapping remains unchanged and continues to mirror exactly once.

Added an anonymous 21-point geometry regression derived from the failing frame. It asserts that the
recorded open palm has five extended digits, passes the configured palm-facing threshold, and is
classified as `wake_palm`.

Validation:

```text
uv run ruff format --check .
37 files already formatted

uv run ruff check .
All checks passed!

uv run pytest -q
56 passed in 3.78s
```

Live camera confirmation after the fix is **UNVERIFIED — requires the user's rerun**. Expected debug
sequence is `wake` → `ARMING` → `ENGAGED` after holding the open palm for about 0.9 seconds; cursor
movement should then be available for the pointer pose.

Follow-up target-Mac screen recording (`Screen Recording 2026-07-18 at 2.11.23 PM.mov`, 47.19 s)
confirms the regression fix on the live AVFoundation path:

- no-hand startup is `pose=none`, `DISENGAGED`, `NEUTRAL`;
- the open palm is consistently recognised as `pose=point,wake` at 0.96–0.99 confidence;
- engagement reaches and remains `ENGAGED`, with gesture state `POINTING`;
- the visible macOS cursor traverses the display in correspondence with palm motion, including both
  horizontal directions; and
- observed callback latency in sampled debug frames is approximately 19.0–25.5 ms.

Result: live open-palm engagement and visible cursor following are **PASS** for this recording. This
evidence does not by itself cover clicking, dragging, right-clicking, scrolling, hand-loss safety,
the five-minute session, or the longer false-action acceptance runs.
