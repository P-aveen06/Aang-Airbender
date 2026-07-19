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

### Phase 1 review-loop history

| Round | Commit SHA | Claude verdict | Blocking findings | Codex response | Resolved |
|---|---|---|---|---|---|
| 1 | `7466131` | `REQUEST CHANGES` | Phase 1 target-Mac acceptance evidence absent | Kept the PR draft; continued owner-led live validation | No |
| 2 | `cb2b238` | `REQUEST CHANGES` | Acceptance evidence incomplete; PR metadata described reverted v1.2 | Restored v1.1, documented the excursion, aligned the approved checklist, and prepared the measured latency correction | Pending round 3 |

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

### Compact debug-overlay feedback

The user reported that the high-contrast debug block at the top-left remained visually distracting.
Moved the three diagnostic lines to the bottom-left, reduced the font scale from 0.55 to 0.38, and
changed the foreground to the design system's near-black primary text color. A thin off-white edge
preserves readability when the camera background is dark. Added a headless unit test for the color,
compact scale, and bottom-left positioning.

```text
uv run ruff format --check .
38 files already formatted

uv run ruff check .
All checks passed!

uv run pytest -q
57 passed in 4.29s
```

### Core-gesture usability recording

User-provided 117.01-second target-Mac recording (`Screen Recording 2026-07-18 at
2.36.07 PM.mov`) shows that the current vocabulary is technically active but not yet usable enough
for the Phase 1 acceptance gate:

- open-palm pointing remains engaged and moves the cursor;
- the two-finger pose enters `TWO_FINGER_PENDING`, commits `RIGHT_CLICK_COMMITTED`, and visibly
  opens a Dock context menu;
- the same two-finger pose also enters `SCROLLING`, including while the context menu is open, which
  demonstrates that motion-versus-stillness arbitration is difficult for the user to predict;
- the user's intended thumb-index circle/pinch is repeatedly reported as `pose=unknown`, so the
  recording does not demonstrate a reliable left click or drag; and
- removing the hand reaches `SUSPENDED`, but because a drag was not established this recording does
  not verify objective button release during hand loss.

Status: right-click emission is **PASS**, scroll-state entry is **PASS but usability-conflicted**,
left click and drag are **FAIL/UNVERIFIED**, and hand-loss release during drag remains **UNVERIFIED**.
The user requested a deliberate redesign of the core gesture vocabulary. No frozen gesture mapping
or acceptance criterion has been changed pending project-owner approval.

### Owner-approved gesture vocabulary v1.1 implementation

On 2026-07-18 the project owner approved the Phase 1 vocabulary v1.1 exception supplied through
Claude review. Per the owner's instruction, the first commit changed only the authorized `PLAN.md`
sections (§3, §3.1, §3.3, §3.4, §5.3, and open questions 2–3):

```text
3298b45 docs: approve phase 1 gesture vocabulary v1.1
1 file changed, 37 insertions(+), 27 deletions(-)
```

No other frozen acceptance criterion was changed. The implementation now uses:

- the existing weighted centroid of landmarks 0/5/9/13/17 and existing One Euro pointer filter;
- neutral palm movement rather than the index fingertip as the pointer input;
- cross-exclusive thumb-index left-button hold/release and thumb-middle right-click-on-release;
- held left pinch as drag, without a separate drag gesture;
- motion-gated two-finger scrolling, with stationary two-finger right-click disabled by default;
- fist release-before-clutch and fresh-baseline release behavior;
- a configured monotonic thumbs-down dwell, distinct from configured hand-loss grace and timeout;
  configured pinch hysteresis at close `< 0.35` and open `> 0.50`; and
- explicit Quartz click-state `2` on a second complete click cycle inside configured time and
  cursor-distance allowances. Drag cycles, distant clicks, and safety cancellation reset the
  double-click sequence.

Added non-camera regression coverage for the mandatory confusion gates: index versus middle pinch,
fist formation versus pinch, fist versus thumbs-down, natural hand loss versus thumbs-down, and two
complete index-pinch click cycles. Real-application interpretation of those two cycles as a
double-click remains **UNVERIFIED — requires the target-Mac run in `PHASE_1_VALIDATION.md`**.

Final local validation for the current diff:

```text
.venv/bin/ruff format --check .
38 files already formatted

.venv/bin/ruff check .
All checks passed!

.venv/bin/python -m compileall -q src scripts tests
PASS

.venv/bin/pytest -q
73 passed, 1 failed in 23.01s
FAIL: tests/test_model_smoke.py::test_official_model_runs_in_live_stream_mode
RuntimeError: Could not create an NSOpenGLPixelFormat

.venv/bin/pytest -q --ignore=tests/test_model_smoke.py
73 passed in 22.71s
```

The full-suite failure is the existing WindowServer/graphics-context limitation in this Codex
process. It does not establish a target-Mac failure or pass. The official-model `LIVE_STREAM` smoke
test, live gesture confusion gates, real-app double-click, and all remaining target-Mac acceptance
checks are **UNVERIFIED** for this v1.1 change until rerun from the user's permitted terminal.

### Phase 1 pointer-sensitivity tuning

After live use, the project owner requested faster palm-to-cursor response. Narrowed the existing
absolute control box from `0.20..0.80` to `0.25..0.75` horizontally and from `0.18..0.82` to
`0.23..0.77` vertically. The full display now requires 50% of camera width and 54% of camera height,
which is approximately 20% more horizontal response and 18.5% more vertical response than the
initial Phase 1 configuration. This remains Phase 1 absolute control-box tuning; no Phase 2 relative
mapping or acceleration curve was added.

The first targeted formatting command incorrectly included Markdown and YAML inputs. Ruff reported
that Markdown formatting requires preview mode and that YAML is not a Python expression. The Python
files in that command were already formatted; targeted lint and mapping/configuration tests passed:

```text
.venv/bin/ruff check tests/test_control.py src/aang_airbender/control.py src/aang_airbender/coordinates.py
All checks passed!

.venv/bin/pytest -q tests/test_config.py tests/test_coordinates.py tests/test_control.py
12 passed in 0.16s
```

Repository validation after the tuning:

```text
.venv/bin/ruff format --check .
38 files already formatted

.venv/bin/ruff check .
All checks passed!

.venv/bin/python -m compileall -q src scripts tests
PASS

.venv/bin/pytest -q --ignore=tests/test_model_smoke.py
73 passed in 24.14s

.venv/bin/pytest -q
1 failed, 73 passed in 24.07s
FAIL: tests/test_model_smoke.py::test_official_model_runs_in_live_stream_mode
RuntimeError: Could not create an NSOpenGLPixelFormat
```

The full-suite failure is the existing graphics-context restriction in the Codex process, not a
new mapping failure. Live target-Mac feel, cursor travel, jitter, and click-precision impact are
**UNVERIFIED** until the owner reruns the controller. The increase is deliberately moderate because
excessive sensitivity would worsen the currently observed click-target retention problem.

### v1.2 excursion and owner-directed v1.1 restoration

On 2026-07-18 the owner approved an experimental Phase 1 v1.2 vocabulary with a physical-right
index-tip pointer and physical-left atomic pinch click. The branch recorded that decision and
implementation in these commits:

```text
f49e870 docs: approve phase 1 gesture vocabulary v1.2
28e8a52 feat: implement two-hand point and click vocabulary
8ba9f6a docs: add phase 1 v1.2 validation evidence
```

Target-Mac use then showed that the experimental vocabulary was not usable for the owner. The owner
explicitly requested a return to the original palm-controlled pointer state. Commit `cb2b238`
reverted the complete v1.2 tree and restored the exact v1.1 plus sensitivity-tuning tree from
`7521b27`. The v1.2 right-index/two-hand vocabulary is therefore historical branch context only;
it is not the active implementation or acceptance target.

On 2026-07-19 the owner also approved a narrow follow-up correction to the two contradictory Phase
1 checklist bullets in frozen `PLAN.md` §4. The correction makes those bullets match the already
approved v1.1 rules: `TWO_FINGER_PENDING` is motion-gated scrolling with the stationary fallback
disabled by default, and right-click is a cross-exclusive thumb-middle pinch emitted once on
release. No acceptance threshold, phase boundary, or other frozen section changed.

Claude round 2 reviewed pushed head `cb2b238` and confirmed that the active source is the v1.1
implementation plus the sensitivity tune. The review requested this execution-history record and a
v1.1 rewrite of the stale PR title/body before another review round. Camera-derived recordings from
the v1.2 experiment and subsequent latency investigation remain local and were not added to git.

### 2026-07-19 click-accuracy latency investigation

The owner reported that 3 of 5 click attempts worked during the target-Mac recording
`Screen Recording 2026-07-19 at 6.59.11 AM.mov`. The matching debug run did not show a gesture
recognition miss: it emitted exactly five `PINCH_PENDING -> DRAGGING -> NEUTRAL` cycles and ended
with `LEFT_DOWN:5,LEFT_UP:5,POINTER_MOVE:1277`. It also reported no stale results, out-of-order
results, result-slot drops, or inferred callback drops.

The captured pointer positions were nevertheless stale. The debug overlay showed callback latency
growing from approximately 35.9 ms on the first attempt to 67.5 ms, 156.3 ms, 198.3 ms, and then
798.4 ms. The terminal summary reported `capture_to_quartz_median_ms=55.65` and
`capture_to_quartz_p95_ms=2015.87`. This confirms that the click accuracy failure was caused first
by an accumulating MediaPipe `LIVE_STREAM` inference backlog, not by the pinch-distance thresholds.

`LiveHandLandmarker` now permits only one asynchronous inference request at a time. Camera capture
continues independently; frames offered while inference is busy are not added to a stale queue, and
the newest available frame may be submitted as soon as the callback completes. A regression test
verifies that a second frame is rejected while one request is in flight and that submission resumes
with the newest frame after its callback. Palm cursor input, pinch thresholds, held-pinch drag, and
all other Phase 1 v1.1 gesture semantics remain unchanged.

Local verification for the latency fix:

```text
uv run ruff format --check .
38 files already formatted

uv run ruff check .
All checks passed!

uv run python -m compileall -q src scripts tests
PASS

uv run pytest -q
75 passed in 3.36s
```

At that stage, fresh target-Mac validation remained **UNVERIFIED**. The owner needed to rerun five
deliberate clicks and confirm that callback latency no longer grows during the session. If Quartz
again emits all five down/up pairs but the application still registers fewer clicks after latency
is bounded, the next investigation is target retention during the existing held-pinch drag, not
weaker pinch detection.

Fresh target-Mac verification was then completed using
`Screen Recording 2026-07-19 at 7.21.01 AM.mov`, with small changes in palm angle and hand
direction between attempts. The browser click tester visibly advanced from 0 to 5 test clicks. The
controller emitted six complete Quartz cycles, matching one click to start/open the tester plus the
five counted test clicks:

```text
action_events=LEFT_DOWN:6,LEFT_UP:6,POINTER_MOVE:996
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
```

The one-request-in-flight correction eliminated the accumulating latency seen in the previous run:

```text
measurement_duration_s=60.05 capture_fps=29.47 callback_hz=20.00
submitted=1201 callbacks=1201 capture_slot_drops=11 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
capture_to_quartz_median_ms=34.62 capture_to_quartz_p95_ms=51.71
frame_age_at_submission_median_ms=0.80 frame_age_at_submission_p95_ms=17.09
```

The log also showed one additional `PINCH_PENDING -> NEUTRAL pinch_cancelled` candidate. In the
matching video interval, the hand used a more pronounced thumb-index “OK” circle and the overlay
reported `pose=unknown`; the candidate never emitted `LEFT_DOWN`. Mild direction changes completed
normally. This is a bounded false negative for that variation and a correct fail-closed outcome,
with no phantom click or stuck button. The target-Mac evidence verifies the latency correction and
five-click browser registration. Broader Phase 1 precision, Dock/Excalidraw behavior, and the full
gesture-confusion matrix remain separate acceptance checks.

### 2026-07-19 target-Mac validation §1 — environment and automated checks

The owner ran the first validation block from the Accessibility-trusted terminal on the target M2
MacBook Air at head `63d5c3e`. Dependency sync, permission/camera preflight, the complete test
suite, and both objective safe-release scenarios passed:

```text
uv sync --frozen
Uninstalled 1 package in 157ms
Installed 1 package in 22ms
~ mediapipe==0.10.21

uv run python scripts/preflight.py
Uninstalled 1 package in 93ms
Installed 1 package in 41ms
Python: 3.11.14
Architecture: arm64
Accessibility trusted: True
AVFoundation camera opened: True
AVFoundation camera frame read: True
PREFLIGHT PASSED

uv run pytest -q
Uninstalled 1 package in 81ms
Installed 1 package in 17ms
........................................................................... [100%]
75 passed in 3.72s

uv run python scripts/verify_safe_release.py
Uninstalled 1 package in 123ms
Installed 1 package in 19ms
controlled_failure: simulated=controlled pipeline failure
controlled_failure: down_observed=True combined_session_left_button_down_after_release=False
normal_shutdown: down_observed=True combined_session_left_button_down_after_release=False
SAFE RELEASE ASSERTIONS PASSED

uv run ruff format --check .
Uninstalled 1 package in 82ms
Installed 1 package in 18ms
38 files already formatted

uv run ruff check .
Uninstalled 1 package in 83ms
Installed 1 package in 16ms
All checks passed!
```

This establishes the correct Python/architecture, trusted Accessibility permission, working camera,
official-model test coverage, and no surviving left-button state after either controlled failure or
normal shutdown. All six required commands passed; target-Mac validation §1 is **PASS**.

### 2026-07-19 target-Mac validation §2 — fixture capture

The owner ran both explicit opt-in fixture recorders. The landmark fixture is technically valid:

```text
tests/fixtures/landmarks/phase1-recorded.jsonl
size=2.2 MiB records=820 valid=784 invalid=36
captured_landmark_span_s=28.1602 approximate_callback_hz=29.12
schema_versions=[1]
```

An offline replay inspection found valid examples from every requested gesture family:

```text
wake_palm=515 pointer_active=616 index_pinch_closed=20 middle_pinch_closed=9
two_finger=9 fist=103 thumbs_down=2
```

The first requested video decoded without errors at 640×480 and 30 fps, but contained only 94
frames / 3.13 seconds. Representative frames showed the owner's face without a visible hand
gesture, so `phase1-short.mp4` does not satisfy the Phase 1 fixture gate and remains excluded from
git.

The owner recaptured and reviewed `tests/fixtures/videos/phase1-short-v2.mp4`. It decodes without
errors and contains 185 frames / 6.17 seconds at 640×480 and 30 fps. Dense frame inspection confirms
a clearly visible, stable open palm under the same lighting, distance, and camera setup as the
landmark recording. The video shows the owner's face; after watching it, the owner explicitly
approved both `phase1-recorded.jsonl` and `phase1-short-v2.mp4` for git on 2026-07-19. Section §2 is
**PASS**. The original `phase1-short.mp4` is not approved and must remain uncommitted.
