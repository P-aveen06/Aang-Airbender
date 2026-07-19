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

### 2026-07-19 target-Mac validation §3 — five-minute core session

The owner ran the controller without `--debug` for the required five minutes. The objective terminal
summary was:

```text
measurement_duration_s=300.03 capture_fps=29.94 callback_hz=29.24
submitted=8771 callbacks=8771 capture_slot_drops=3 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=6484 capture_to_quartz_median_ms=22.93 capture_to_quartz_p95_ms=32.84
frame_age_at_submission_median_ms=0.65 frame_age_at_submission_p95_ms=1.22
action_events=LEFT_DOWN:30,LEFT_UP:30,POINTER_MOVE:6484,RIGHT_CLICK:2,SCROLL:88
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
```

The no-debug cadence is close to capture rate, the corrected pipeline remains fresh, all 30 owned
left-button cycles are balanced, no result backlog/drop is inferred, and shutdown leaves no held
left button. Transition-log counts provide additional objective coverage:

```text
wake_dwell_complete=1
pinch_stable=29 pinch_released=29 pinch_cancelled=7
middle_pinch_released=2 right_click_neutral=2
two_finger_motion=8 two_finger_released=8 two_finger_cancelled=41
fist_clutch=10 clutch_released=8
thumbs_down_candidate=1 thumbs_down_dwell_complete=1
tracking_lost=3 hand_reacquired=3
```

The log directly verifies engagement, the configured thumbs-down disengagement path, semantic event
emission, bounded fresh inference, balanced button safety, and the recorded summary. It does not
establish whether applications visibly opened, dragged, right-clicked, or scrolled, whether the
pointer anchor/response felt correct, or whether fist release caused a visible jump. It also shows
that every established drag ended with `pinch_released`; no `DRAGGING -> ... fist` path occurred.
Therefore the required active-drag-to-fist release check was not exercised in this run. Section §3
is **PARTIALLY VERIFIED** pending the owner's visual confirmations and that focused retest.

The owner's visual results for that run were:

```text
palm movement and screen travel: PASS
application opened by thumb-index click: PASS
file/object visibly dragged and released: PASS
right-click menu appeared once per gesture: PASS
page visibly scrolled: FAIL
stationary two fingers caused no action: PASS
fist clutched without disengaging: PASS
fist release caused no cursor jump: FAIL
sensitivity felt acceptable: PASS
```

The owner then ran a focused 45-second no-debug retest. Its objective summary was:

```text
measurement_duration_s=45.01 capture_fps=29.95 callback_hz=28.53
submitted=1284 callbacks=1284 capture_slot_drops=0 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=1072 capture_to_quartz_median_ms=27.85 capture_to_quartz_p95_ms=34.19
frame_age_at_submission_median_ms=0.67 frame_age_at_submission_p95_ms=1.24
action_events=LEFT_DOWN:6,LEFT_UP:6,POINTER_MOVE:1072
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
```

All six established drags again ended with `pinch_released`. The only
`fist_candidate_safe_release` transition began from `POINTING`, not `DRAGGING`, and the run contains
no `fist_release_before_clutch` transition. The focused retest therefore did not exercise the
required drag-to-fist safety path. It is neither a pass nor a failure for that check. The visible
scroll failure and fist-release cursor jump remain explicit §3 failures requiring correction and a
fresh target-Mac retest.

### 2026-07-19 §3 failure investigation and local correction

The two visible failures had separate control-layer causes:

- Scroll recognition produced semantic fractional-pixel deltas, but the Quartz boundary rounded
  each frame independently. A slow deliberate motion could therefore count many `SCROLL` events
  while repeatedly posting zero pixels. The control layer now carries fractional residuals across
  frames, emits only whole nonzero pixel deltas, and clears the residual at scroll boundaries.
- `CLUTCH_OFF` reset the One Euro filter but did not establish a cursor anchor. With absolute palm
  mapping, the first post-fist point therefore moved immediately to the repositioned palm's mapped
  screen coordinate. The control layer now retains the last emitted cursor position, anchors the
  first post-clutch point exactly there, and applies subsequent palm displacement from that fresh
  baseline within the display bounds. Safety cancellation and reacquisition use the same no-jump
  baseline path.

Both regression tests failed against the previous control implementation and pass with the local
correction:

```text
tests/test_control.py::test_clutch_freezes_pointer_and_release_rebaselines_without_jump PASSED
tests/test_control.py::test_safety_cancel_reacquires_from_the_last_cursor_position PASSED
tests/test_control.py::test_fractional_pixel_scroll_accumulates_instead_of_emitting_rounded_zeroes PASSED
```

Local verification after the correction:

```text
.venv/bin/ruff format --check .
38 files already formatted

.venv/bin/ruff check .
All checks passed!

.venv/bin/python -m compileall -q src scripts tests
passed

.venv/bin/pytest -q --ignore=tests/test_model_smoke.py
76 passed in 23.02s

approved landmark replay:
action_events=LEFT_DOWN:1,LEFT_UP:1,POINTER_MOVE:597,RIGHT_CLICK:1
reported_false_actions=none
left_down_after_replay=False
```

The Codex-hosted process cannot create MediaPipe's macOS OpenGL pixel format or observe injected
Quartz mouse-down state, so `test_model_smoke.py` and `verify_safe_release.py` remain target-terminal
checks for this correction. The owner had already passed both classes of check before this diff.
Visible scroll, no-jump fist release, and the still-unexercised drag-to-fist release ordering all
require a fresh target-Mac run before §3 can pass.

### 2026-07-19 §3 correction target-Mac attempts 1–2

The owner ran the corrected controller twice for 90 seconds without `--debug`.

Attempt 1:

```text
measurement_duration_s=90.03 capture_fps=29.97 callback_hz=28.94
submitted=2604 callbacks=2604 capture_slot_drops=2 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=1387 capture_to_quartz_median_ms=23.19 capture_to_quartz_p95_ms=33.94
frame_age_at_submission_median_ms=0.62 frame_age_at_submission_p95_ms=1.23
action_events=LEFT_DOWN:3,LEFT_UP:3,POINTER_MOVE:1387,RIGHT_CLICK:1,SCROLL:394
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
```

Attempt 1 contained 39 `two_finger_motion` scroll episodes, three established drags, and three
normal `pinch_released` drag endings. No fist clutch was attempted.

Attempt 2:

```text
measurement_duration_s=90.03 capture_fps=29.98 callback_hz=29.58
submitted=2663 callbacks=2663 capture_slot_drops=0 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=1148 capture_to_quartz_median_ms=19.99 capture_to_quartz_p95_ms=23.87
frame_age_at_submission_median_ms=0.63 frame_age_at_submission_p95_ms=1.22
action_events=LEFT_DOWN:2,LEFT_UP:2,POINTER_MOVE:1148,SCROLL:413
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
```

Attempt 2 contained 18 `two_finger_motion` episodes, 18 `fist_clutch` transitions, two established
drags, and two normal `pinch_released` drag endings. Four transitions used
`fist_release_before_clutch`, but their previous states were `TWO_FINGER_PENDING` twice,
`PINCH_PENDING` once, and `SCROLLING` once. None began from `DRAGGING`. The required active-button
release-before-clutch path therefore remains unexercised.

Because the corrected control layer emits a semantic `SCROLL` event only when at least one whole,
nonzero pixel is ready, the 394 and 413 counters prove that both target runs dispatched substantial
nonzero Quartz scroll input. Terminal logs cannot establish that the foreground application visibly
scrolled, nor can they show whether the cursor visually stayed fixed when the fist opened. Those two
checks still require the owner's direct PASS/FAIL observation.

The owner supplied the direct visual results after both attempts:

```text
page visibly moved: PASS
cursor stayed still after opening fist: PASS
```

This closes the functional visible-scroll and no-jump clutch-release checks. The owner explicitly
reported that scrolling, although working, was not sufficiently precise or accurate. That remains
an open Phase 1 usability concern and is not being hidden by the functional PASS. The active
drag-to-fist release-before-clutch check remains unverified because neither target run transitioned
from `DRAGGING` into fist handling.

### 2026-07-19 scroll continuity investigation and correction

The owner clarified that scrolling was both jerky and delayed/insensitive to small movements. The
target logs showed that recognition churn, rather than missing output smoothing, was the dominant
cause. Palm velocity was already low-pass filtered with the configured `0.35` alpha, while the two
target runs repeatedly left scroll mode:

```text
attempt 1: 80 pending cancellations / 39 scroll starts
           median scroll episode 266.9 ms; 13/39 ended under 150 ms; 23/39 under 300 ms
           median activation 102.7 ms; p95 activation 167.4 ms
attempt 2: 23 pending cancellations / 18 scroll starts
           median scroll episode 201.1 ms; 7/18 ended under 150 ms; 10/18 under 300 ms
           median activation 132.8 ms; p95 activation 133.2 ms
```

Every one-frame two-finger classification dropout ended the active episode immediately. Returning
to the same physical pose then restarted the configured stability/activation wait, producing the
observed jerk-pause-ignore-restart cycle.

The FSM now tolerates a valid-hand two-finger pose dropout for the existing configured
`pose_stability_ms` interval. If the pose returns inside that interval, it remains locked in
`SCROLLING` and emits a fresh `SCROLL_START` baseline before updates resume; this prevents both an
activation restart and a catch-up velocity burst. A sustained pose break still emits `SCROLL_END`.
Fist and existing engagement/safety cancellation are evaluated before the continuity grace and
remain immediate.

Regression coverage failed against the prior immediate-exit behavior and passes with the
correction:

```text
tests/test_fsm.py::test_two_finger_motion_locks_to_scroll_until_pose_break_is_stable PASSED
tests/test_fsm.py::test_scrolling_recovers_from_short_pose_dropout_with_a_fresh_scroll_baseline PASSED
tests/test_fsm.py::test_fist_cancels_scrolling_immediately_without_pose_dropout_grace PASSED
```

Local verification:

```text
.venv/bin/ruff format --check .
38 files already formatted

.venv/bin/ruff check .
All checks passed!

.venv/bin/python -m compileall -q src scripts tests
passed

.venv/bin/pytest -q --ignore=tests/test_model_smoke.py
78 passed in 23.89s
```

The earlier visible-scroll PASS is reopened only for the changed continuity behavior. A short
target-Mac visual retest must confirm that small vertical movements start promptly and remain
continuous without introducing phantom scroll after the two-finger pose is intentionally released.

### 2026-07-19 scroll-continuity target-Mac PASS and §3 completion

The owner ran two fresh 30-second no-debug sessions with the continuity correction. Their objective
summaries were:

```text
run 1:
measurement_duration_s=30.01 capture_fps=29.96 callback_hz=29.03
submitted=871 callbacks=871 capture_slot_drops=0 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=424 capture_to_quartz_median_ms=21.89 capture_to_quartz_p95_ms=34.05
frame_age_at_submission_median_ms=0.63 frame_age_at_submission_p95_ms=1.22
action_events=LEFT_DOWN:1,LEFT_UP:1,POINTER_MOVE:424,SCROLL:176
reported_false_actions=none
quartz_left_button_down_after_shutdown=False

run 2:
measurement_duration_s=30.02 capture_fps=29.98 callback_hz=29.21
submitted=877 callbacks=877 capture_slot_drops=0 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=203 capture_to_quartz_median_ms=20.10 capture_to_quartz_p95_ms=23.32
frame_age_at_submission_median_ms=0.65 frame_age_at_submission_p95_ms=1.22
action_events=POINTER_MOVE:203,SCROLL:247
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
```

The owner supplied these direct visual results:

```text
small movements respond: PASS
scroll feels continuous: PASS
scroll stops without phantom movement: PASS
```

Run 1 also finally exercised the exact active-drag-to-fist safety sequence:

```text
PINCH_PENDING -> DRAGGING reason=pinch_stable
DRAGGING -> NEUTRAL reason=fist_release_before_clutch
NEUTRAL -> CLUTCHED reason=fist_clutch
```

`fist_release_before_clutch` preceded `fist_clutch` by 100.71 ms, the single owned left-button cycle
was balanced, and shutdown reported no held left button. Combined with the earlier direct
observations that fist clutch did not disengage and fist release caused no cursor jump, this closes
the previously missing drag-release-before-clutch requirement. All §3 core-five smoke-session items
are now **PASS**. The scroll continuity correction did not weaken stationary-two-finger or explicit
release safety criteria.

### 2026-07-19 corrected-tree target automated and Quartz safety checks

The owner reran the complete suite and objective safe-release script from the Accessibility-trusted
target terminal after both control corrections:

```text
uv run pytest -q
79 passed in 4.17s

uv run python scripts/verify_safe_release.py
controlled_failure: simulated=controlled pipeline failure
controlled_failure: down_observed=True combined_session_left_button_down_after_release=False
normal_shutdown: down_observed=True combined_session_left_button_down_after_release=False
SAFE RELEASE ASSERTIONS PASSED
```

This supersedes the earlier 75-test target result for the corrected tree. Both the controlled
failure and normal shutdown paths physically observed an owned mouse-down and verified that the
combined-session left-button state was false after release.

### 2026-07-19 confusion-gate failure and temporal cross-pinch correction

The owner ran the required 120-second no-debug confusion session. Its objective summary was:

```text
measurement_duration_s=120.02 capture_fps=29.97 callback_hz=29.84
submitted=3581 callbacks=3581 capture_slot_drops=0 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=2270 capture_to_quartz_median_ms=19.69 capture_to_quartz_p95_ms=20.45
frame_age_at_submission_median_ms=0.54 frame_age_at_submission_p95_ms=1.20
action_events=LEFT_DOWN:23,LEFT_UP:23,POINTER_MOVE:2270,RIGHT_CLICK:9
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
```

The owner's direct semantic observations override the software-only false-action placeholder:

```text
wrong-button clicks: 7
ambiguous-pinch clicks: 5
clicks while forming fist: 0
fist incorrectly disengaged: NO
thumbs-down incorrectly clutched: NO
```

Therefore the index-versus-middle confusion gate is **FAIL**, not PASS. The fist-formation and
fist-versus-thumbs-down gates pass. The run did not complete either a natural full hand-loss timeout
or a thumbs-down dwell; `thumbs_down_candidate` was interrupted by process exit, so those distinct
checks remain open.

The trace and a deterministic state-machine reproduction exposed a temporal gap in cross-pinch
exclusion. Pose classification rejected a frame where the thumb was near both fingertips, but an
already pending or armed pinch survived that ambiguous frame. On a later clear/open frame, the FSM
could reuse the earlier stability time or commit the armed middle-pinch right click. Static pose
tests did not cover that sequence.

The FSM now cancels a pending index pinch whenever the middle-tip distance is not beyond the
configured cross-pinch-open boundary. It likewise cancels an armed or pending middle pinch whenever
the index-tip distance enters that boundary. Cancellation clears the candidate timestamp and middle
arm, so recognition can restart only from a fresh, unambiguous episode. Active drag priority and
release safety are unchanged.

Regression evidence:

```text
before correction:
tests/test_fsm.py::test_armed_middle_pinch_crossing_ambiguous_zone_emits_no_click FAILED
tests/test_fsm.py::test_ambiguous_cross_pinch_restarts_index_stability_dwell FAILED

after correction:
focused regressions: 2 passed
full suite: 81 passed in 3.33s
ruff format --check: 38 files already formatted
ruff check: All checks passed
```

The required target-Mac index-versus-middle confusion gate remains unchecked until a fresh run with
the correction records zero wrong-button clicks and zero ambiguous-pinch clicks.

### 2026-07-19 right-click non-recognition diagnostic run

The owner reported that thumb-middle right click did not work in a fresh target run. The run was
stopped after 28.93 seconds and emitted only `POINTER_MOVE:408`. It contained zero
`middle_pinch_candidate`, `MIDDLE_PINCH_PENDING`, `middle_pinch_released`, or `RIGHT_CLICK` events.
The temporal ambiguity correction cannot have canceled these attempts because its new guard runs
only after a pinch candidate already exists.

Before full disengagement, the observed command-like transitions were one completed fist clutch and
five additional `fist_candidate_safe_release` transitions. This indicates that at least some hand
shapes were classified as fists rather than thumb-middle pinches. A reliable diagnostic attempt must
keep the non-pinching fingers visibly open, hold thumb-to-middle-tip contact for at least the
configured 100 ms stability dwell, and then release fully; right click is emitted on release.

The same run objectively completed the previously open natural hand-loss gate:

```text
ENGAGED -> SUSPENDED reason=tracking_lost
POINTING -> NEUTRAL reason=tracking_loss_grace_expired
SUSPENDED -> DISENGAGED reason=tracking_loss_timeout
```

No `thumbs_down_candidate` or `thumbs_down_dwell_complete` occurred. After the full timeout, the
remaining roughly ten seconds of gestures were correctly ignored because no new open-palm wake
dwell occurred. The natural hand-loss versus explicit thumbs-down confusion check is therefore
**PASS**. Thumb-middle recognition remains unverified pending a short debug-preview run that shows
the live pose label during the owner's attempted contact and release.

### 2026-07-19 thumb-middle 2/10 debug result

The owner attempted ten thumb-middle right-click gestures in a 30-second debug-preview run and
reported only 2/10 correct. The event and transition counts expose the remaining eight outcomes:

```text
measurement_duration_s=30.03 capture_fps=29.97 callback_hz=29.54
action_events=LEFT_DOWN:4,LEFT_UP:4,POINTER_MOVE:514,RIGHT_CLICK:2
middle_pinch_candidate=2 middle_pinch_released=2
index_pinch_candidate=6 pinch_stable=4 pinch_released=4 pinch_cancelled=2
quartz_left_button_down_after_shutdown=False
```

All two middle-pinch candidates committed correctly on release. Four intended thumb-middle attempts
instead completed balanced index-pinch left-click cycles, and two index-pinch candidates canceled;
the remaining attempts were never classified as either stable pinch. The 2/10 result is therefore a
recognition-layer confusion failure, not an FSM release failure and not a regression caused by the
new pending-state ambiguity cancellation.

A second 30-second debug command in the same attachment never completed open-palm engagement: it
recorded 22 wake starts, 21 wake breaks, zero `wake_dwell_complete`, and `action_events=none`. That
run contains no click evidence and does not change the 2/10 finding.

The working hypothesis is that real thumb-middle contact under the owner's hand orientation and
occlusion often produces inferred landmark geometry in which the thumb-index normalized distance
crosses the index threshold first. Because the current recognizer uses tip-distance thresholds and
gives cross-exclusive index recognition priority, that geometry becomes a wrong left click. A
target landmark capture containing only labeled-by-protocol thumb-middle attempts is required to
measure the actual ratios and finger geometry before changing the recognizer.

### 2026-07-19 targeted thumb-middle landmark replay

The owner created the requested local, camera-derived
`tests/fixtures/landmarks/thumb-middle-10.jsonl` capture. The file remains untracked and is not
approved for git. It contains 822 records over approximately 30 seconds: 758 valid tracked-hand
records and 64 no-hand/invalid records.

Production feature extraction and pose classification found 13 distinct near-pinch episodes in the
performed sequence. Their geometry was cleanly separated:

```text
index-pinch classified frames: 0
middle-pinch classified frames: 58
middle-contact index-ratio range: approximately 0.78-1.07 (clearly open)
middle-contact middle-ratio range: approximately 0.16-0.35 (closed threshold)
```

Replaying the exact timestamps through the production gesture FSM produced:

```text
middle_pinch_candidate=13
middle_pinch_released=10
middle_pinch_cancelled_before_stable=3
RIGHT_CLICK=10
index PINCH_START/PINCH_END=0
```

The three canceled episodes contained only about 60-70 ms of classified contact, below the
configured 100 ms stability dwell. All sufficiently long controlled-posture episodes committed once
on release, and no episode became a wrong left click. This disproves a universal MediaPipe landmark
placement defect and confirms that the controlled posture can separate the two buttons for this
owner. It also shows why reducing thresholds without another confusion run would be unsafe: the
earlier live app posture produced four wrong left-click cycles, while the controlled capture
produced none.

No recognition threshold is changed from this replay alone. The next target app run must use the
same controlled posture as the successful capture, hold each contact clearly beyond 100 ms, and
report correct right clicks, wrong left clicks, and misses separately. The required confusion gate
remains open until all wrong-button and ambiguous clicks are zero.

### 2026-07-19 post-capture live app result and count discrepancy

The owner reported that the controlled posture looked slightly better and supplied these visual
counts:

```text
correct right clicks: 7
wrong left clicks: 3
missed clicks: 3
```

These sum to 13 observed attempts. The attached 30-second no-debug terminal trace objectively
recorded a different button split:

```text
measurement_duration_s=30.03 capture_fps=29.94 callback_hz=29.41
action_events=LEFT_DOWN:6,LEFT_UP:6,POINTER_MOVE:565,RIGHT_CLICK:4
index_pinch_candidate=6 pinch_stable=6 pinch_released=6
middle_pinch_candidate=4 middle_pinch_released=4 right_click_neutral=4
quartz_left_button_down_after_shutdown=False
```

The software therefore emitted four right-click events and six complete left-button cycles. If all
13 attempts were intended to be thumb-middle gestures, the objective result is 4 correct, 6
wrong-button, and 3 unrecognized. If three of the six left cycles were intentional thumb-index
controls, the owner's 7/3/3 categorization may include actions outside the isolated right-click
trial. The intended gesture sequence must be clarified before assigning semantic labels to the ten
emitted button cycles.

Either interpretation still fails the mandatory zero-wrong-button confusion gate. No threshold or
dwell change is made from this run because the controlled landmark fixture produced ten right
clicks and zero left clicks under the same code, while this live trace produced the opposite
classification mix. The next diagnostic must correlate intended gesture labels with the exact
landmark/action timeline rather than relying on aggregate counts.

The owner subsequently clarified that the run mixed intentional thumb-index gestures with
thumb-middle gestures but did not know the count of intentional index attempts. Consequently the
six emitted left-button cycles cannot be divided reliably into correct index actions and wrong
middle-as-index actions. This mixed run is retained as evidence that the gate is not passed, but it
is not used to calculate a confusion rate. Two isolated, fixed-count runs are required next.

### 2026-07-19 isolated index-only and middle-only target runs

The owner supplied two separate 30-second target runs, first using thumb-index only and then
thumb-middle only.

Index-only objective result:

```text
measurement_duration_s=30.00 capture_fps=29.96 callback_hz=29.90
action_events=LEFT_DOWN:10,LEFT_UP:10,POINTER_MOVE:370
pinch_stable=10 pinch_released=10
RIGHT_CLICK=0
quartz_left_button_down_after_shutdown=False
```

An eleventh index candidate began near shutdown but was canceled by `process_exit` before it could
emit a button-down. One earlier candidate entered the ambiguous cross-pinch boundary, canceled, and
then restarted from a fresh stability dwell before committing correctly. This directly exercises
the temporal ambiguity correction without producing a wrong right click.

Middle-only objective result:

```text
measurement_duration_s=30.03 capture_fps=29.94 callback_hz=29.45
action_events=POINTER_MOVE:613,RIGHT_CLICK:16
middle_pinch_candidate=17
middle_pinch_released=16
middle_pinch_cancelled_before_stable=1
LEFT_DOWN=0 LEFT_UP=0
quartz_left_button_down_after_shutdown=False
```

The isolated trials therefore emitted zero wrong-button actions in both directions. The index run
completed ten recognized cycles with no miss among committed attempts. The middle run committed 16
of 17 recognized candidates, with one short-contact cancellation and no false left click. The
observed attempt counts exceeded the requested ten in at least the middle run, so these are recorded
from objective candidate counts rather than assumed manual denominators.

This closes isolated index-versus-middle discrimination but does not yet close the mandatory
alternating confusion gate. One ordered run must alternate the two gestures without repeating a
type, allowing the transition sequence itself to verify whether switching introduces wrong-button
or duplicate actions.

### 2026-07-19 ordered alternating-pinch run

The owner supplied the requested 30-second run after being instructed to alternate thumb-index and
thumb-middle with a full neutral release and no repeated gesture type. The objective button events
were balanced and safely released:

```text
measurement_duration_s=30.03 capture_fps=29.97 callback_hz=29.81
action_events=LEFT_DOWN:5,LEFT_UP:5,POINTER_MOVE:610,RIGHT_CLICK:3,SCROLL:2
index pinch_stable=5 pinch_released=5
middle_pinch_released=3 right_click_neutral=3
quartz_left_button_down_after_shutdown=False
```

However, the same pinch-only run produced command-pose confusion:

```text
fist_clutch=2 clutch_released=2
two_finger_candidate=11 two_finger_cancelled=9
two_finger_motion=2 two_finger_released=2
```

Because neither fist nor scrolling was part of the instructed alternating sequence, both committed
scroll episodes and both fist clutches are unintended actions. The alternating confusion gate
therefore remains **FAIL**, even though this run contains no unbalanced button and the later emitted
button sequence cleanly alternates index/middle.

The transition evidence identifies a gesture-vocabulary boundary collision: intermediate shapes
while forming or releasing a pinch can satisfy the current two-finger or fist recognizer before
thumb contact becomes unambiguous. Tightening scroll timing blindly would regress the already-fixed
small-motion responsiveness, and loosening pinch thresholds would regress wrong-button safety. A
landmark capture of the exact alternating motion is required to determine which thumb/finger
geometry separates intentional scroll and fist from pinch transitions.

### 2026-07-19 controlled alternating landmark replay

The owner created local camera-derived
`tests/fixtures/landmarks/pinch-alternating.jsonl`. It remains untracked and is not approved for
git. The capture contains 835 records, including 811 valid tracked-hand records.

Production classification found clean separation throughout the performed pinch sequence:

```text
index-pinch frames=59
middle-pinch frames=55
two-finger frames=0
fist frames during actual pinch sequence=0
```

One isolated single-frame fist classification occurred at 1.22 seconds during setup, several
seconds before the first index pinch at 6.18 seconds. It neither met the 100 ms clutch dwell nor
emitted an action.

Exact-timestamp production FSM replay emitted:

```text
PINCH_START=5 PINCH_END=5
RIGHT_CLICK=6
SCROLL_START/SCROLL_UPDATE=0
CLUTCH_ON=0
middle_pinch_cancelled_before_stable=0
```

The replay contained no wrong-button, scroll, or clutch action during the alternating sequence.
This disproves an unavoidable vocabulary collision for the controlled hand posture. The earlier
live false scroll/clutch run used materially different intermediate geometry. A fresh target app
run must reproduce the controlled capture posture before the alternating gate can be closed.

### 2026-07-19 controlled-posture live retry and hysteresis correction

The owner repeated the controlled alternating posture in a 30-second live app run. It eliminated
the prior false scroll and clutch actions but exposed a middle-pinch dwell defect:

```text
measurement_duration_s=30.05 capture_fps=23.13 callback_hz=23.07
capture_to_quartz_median_ms=19.88 capture_to_quartz_p95_ms=20.55
action_events=LEFT_DOWN:8,LEFT_UP:8,POINTER_MOVE:518
index pinch_stable=8 pinch_released=8
middle_pinch_candidate=3 middle_pinch_cancelled_before_stable=3
RIGHT_CLICK=0 SCROLL=0 CLUTCH_ON=0
quartz_left_button_down_after_shutdown=False
```

Each canceled middle candidate remained pending longer than the configured 100 ms stability dwell:
approximately 346 ms, 216 ms, and 389 ms. The FSM started the candidate on a fully closed frame but
only armed it if another fully closed frame arrived after 100 ms. If measurement jitter moved into
the configured 0.35-0.50 hysteresis dead zone and remained there until release, the pending state
survived but never armed, producing the contradictory `cancelled_before_stable` result.

Pinch hysteresis now treats the dead zone as continuation of an already-started clear candidate.
Once a clear closed frame starts the episode, closed or dead-zone time counts toward the 100 ms
dwell. Explicit open, opposite-finger cross-pinch ambiguity, fist priority, tracking loss, and all
safety cancellation paths remain unchanged. The same correction is applied consistently to index
and middle pending states.

Regression evidence:

```text
before correction:
test_index_pinch_dead_zone_after_closed_entry_counts_toward_stability FAILED
test_middle_pinch_dead_zone_after_closed_entry_counts_toward_stability FAILED

after correction:
focused regressions: 2 passed
full suite: 83 passed in 5.71s
ruff format --check: 38 files already formatted
ruff check: All checks passed
```

The alternating gate remains open pending a fresh target run of this corrected hysteresis behavior.

### 2026-07-19 corrected-hysteresis alternating target retry

The owner then reran the 30-second live application after the pending-state hysteresis correction,
following the requested `thumb-index -> open -> thumb-middle -> open` repeating sequence. The target
terminal reported:

```text
measurement_duration_s=30.02 capture_fps=23.15 callback_hz=22.82
submitted=685 callbacks=685 capture_slot_drops=0 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=507 capture_to_quartz_median_ms=19.91 capture_to_quartz_p95_ms=33.48
frame_age_at_submission_median_ms=0.65 frame_age_at_submission_p95_ms=1.23
action_events=LEFT_DOWN:8,LEFT_UP:8,POINTER_MOVE:507,RIGHT_CLICK:3
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
```

All three detected middle-pinch candidates now survived the hysteresis dead zone and committed on
release; no `middle_pinch_cancelled_before_stable` transition remained. The run also had no scroll,
fist-clutch, duplicate-button, unbalanced-button, or stuck-button event. This validates the narrow
pending-state hysteresis correction on the target Mac.

It does **not** pass the alternating confusion gate. The objective recognized click order was:

```text
index, index, index, middle, index, index, index, middle, index, middle, index
```

That is eight left-button cycles and three right clicks rather than a clean alternation. Given the
owner's stated strict alternating procedure, some intended thumb-middle pinches were still
recognized as thumb-index pinches. The software-only `reported_false_actions=none` field cannot
detect a mismatch between intended and recognized button semantics and does not override this
result. No further threshold or arbitration change is justified from transition logs alone; the
next diagnostic input must be a landmark capture of the exact failing live sequence so production
features can be replayed frame by frame. The §4 alternating gate remains **FAIL / open**.

### 2026-07-19 count-controlled alternating landmark capture

The owner recorded the requested local camera-derived diagnostic fixture at
`tests/fixtures/landmarks/pinch-alternating-failure-v2.jsonl`. It remains **private, unapproved,
untracked, and excluded from git** unless the owner explicitly approves it. The recording contains
630 records over 27.65 seconds: 489 valid hand results and 141 no-hand results. The intended portion
contains exactly five alternating thumb-index/thumb-middle pairs.

Production feature extraction and pose classification found eleven contact episodes. The first ten
are a clean alternating sequence; the eleventh is a short end-of-run ambiguous/fist-shaped motion
that never becomes a click candidate. Across the five intended thumb-middle contacts, the minimum
middle-pinch ratios were `0.319`, `0.333`, `0.335`, `0.337`, and `0.339` against the configured
`0.350` closed threshold. The opposite index ratios remained clear at `0.722` or greater. Across
the five intended thumb-index contacts, the minimum index ratios were `0.148` to `0.207`, while the
opposite middle ratios remained clear at `1.028` or greater. No intended episode entered the
cross-pinch ambiguity zone.

An exact timestamp replay through the current production feature, pose, and gesture FSM path
produced:

```text
PINCH_START=5
PINCH_END=5
RIGHT_CLICK=5
SCROLL=0
CLUTCH_ON=0
recognized_order=index,middle,index,middle,index,middle,index,middle,index,middle
```

Every middle candidate committed on release after 173-260 ms in the pending state. The capture
therefore validates the corrected hysteresis path and cross-exclusive classification for the
owner's controlled posture. It does not reproduce the earlier live run's 8-left/3-right mismatch,
and it would be unjustified to change pinch thresholds from this evidence. Because the fixture
recorder does not dispatch Quartz events, the §4 live wrong-button gate remains open pending one
count-controlled target-app run of exactly five pairs using this same posture.

### 2026-07-19 45-second live count check

The owner then ran the target application for 45 seconds. The objective summary was:

```text
measurement_duration_s=45.03 capture_fps=23.12 callback_hz=22.68
submitted=1021 callbacks=1021 capture_slot_drops=0 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=819 capture_to_quartz_median_ms=26.11 capture_to_quartz_p95_ms=36.53
frame_age_at_submission_median_ms=0.62 frame_age_at_submission_p95_ms=1.22
action_events=LEFT_DOWN:4,LEFT_UP:4,POINTER_MOVE:819,RIGHT_CLICK:5
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
```

The five detected middle-pinch candidates committed exactly once each. A sixth late middle
candidate was canceled before stable and correctly emitted no click. No scroll or clutch action
was dispatched, left-button events were balanced, and shutdown left no button held. The detected
click order was four index clicks followed by five middle clicks, not five alternating pairs.

The owner's direct observations and procedure were:

```text
sequence performed: five index then five middle on the physical right hand, then the right hand was
lowered and the same sequence was performed with only the physical left hand raised
wrong-button clicks observed: 2
missed clicks observed: 2
ambiguous-contact clicks observed: 5
```

The restored Phase 1 v1.1 perception path is explicitly configured with MediaPipe `num_hands=1`,
and frozen `PLAN.md` starts Phase 1 with the physical right hand only. The owner clarified that the
hands were shown sequentially, never simultaneously, so single-slot competition between two visible
hands did not cause this result. However, the terminal summary and manual error counts aggregate a
right-hand trial with a separate left-hand trial and do not identify which physical hand produced
each wrong, missed, or ambiguous action. They therefore cannot establish the required physical
right-hand confusion rate or justify tuning its thresholds. This combined-hand run is **INVALID for
§4 acceptance**, not a pass. The required retry must use only the physical right hand and strict
`index -> open -> middle -> open` alternation.

### 2026-07-19 physical-right-hand-only alternating retry

The owner reran the controller for 45 seconds with the physical left hand excluded and the physical
right hand performing the requested strict alternating sequence. The objective target summary was:

```text
measurement_duration_s=45.02 capture_fps=23.10 callback_hz=22.26
submitted=1002 callbacks=1002 capture_slot_drops=0 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=339 capture_to_quartz_median_ms=21.76 capture_to_quartz_p95_ms=34.65
frame_age_at_submission_median_ms=0.65 frame_age_at_submission_p95_ms=1.23
action_events=LEFT_DOWN:5,LEFT_UP:5,POINTER_MOVE:339,RIGHT_CLICK:2
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
```

All five index candidates reached stable drag/click state and released cleanly. Only two middle
pinch candidates were detected, and both committed one right click on release. The objective click
order was `index,index,middle,index,index,index,middle`, so three intended middle pinches produced
no button action. No middle attempt was converted into an extra left click: the five balanced left
cycles exactly match the five intended index attempts. Near the end, a fist-shaped frame invoked
safe release, tracking was lost, and the controller cleanly reached full hand-loss disengagement.
No scroll, clutch, duplicate button, unbalanced button, or stuck button was emitted.

This run is **FAIL / open** for the §4 alternating gate because only two of five intended right
clicks were recognized. It also narrows the defect: the current live failure is missed recognition,
not wrong-button arbitration or the already-corrected pending-state dwell. The standalone landmark
capture replayed 5/5, while the live app produced 2/5, so a separate recorder run cannot expose the
failing geometry. The next investigation step is explicit, privacy-gated landmark recording inside
the live application run so the exact missed attempts and emitted events share one timeline. No
threshold change is justified before that evidence exists.

### 2026-07-19 live-run landmark diagnostic instrumentation

To capture the geometry that actually drives a failing Quartz run, the live application now has an
optional `--record-landmarks PATH` diagnostic. It is disabled by default, requires the same explicit
`--i-understand-camera-derived-data` acknowledgement as the standalone recorder, refuses to
overwrite an existing path both before native initialization and atomically when opening the file,
flushes each accepted result, and prints the final path and record count. Normal controller behavior
and every gesture threshold remain unchanged.

Regression coverage verifies that an unacknowledged request is rejected and that an acknowledged
writer round-trips the exact `HandState` JSONL representation while refusing to overwrite an
existing fixture. Local verification:

```text
focused app/replay tests: 4 passed in 26.73s
ruff format --check: 39 files already formatted
ruff check: All checks passed
compileall: passed
host-compatible suite: 84 passed in 38.93s
full suite: 84 passed, 1 environment failure
environment failure: test_model_smoke could not create NSOpenGLPixelFormat in the Codex host
```

The MediaPipe OpenGL smoke limitation is specific to the Codex-hosted process and is unchanged from
earlier validation. The owner's trusted terminal has already run the model successfully and must
rerun the now-85-test full suite with this diagnostic diff. The next target capture remains private
and untracked unless the owner explicitly approves it for git.

### 2026-07-19 exact live-miss replay and threshold correction

The owner ran the physical-right-hand-only live application with the new explicit recorder. The
private, unapproved `tests/fixtures/landmarks/live-middle-misses-v1.jsonl` contains 928 accepted
results and remains untracked. The target summary was:

```text
measurement_duration_s=45.02 capture_fps=22.97 callback_hz=20.63
submitted=929 callbacks=929 capture_slot_drops=1 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=266 capture_to_quartz_median_ms=30.18 capture_to_quartz_p95_ms=79.35
frame_age_at_submission_median_ms=0.64 frame_age_at_submission_p95_ms=1.25
action_events=LEFT_DOWN:5,LEFT_UP:5,POINTER_MOVE:266,RIGHT_CLICK:3
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
landmark_fixture=.../live-middle-misses-v1.jsonl records=928
```

Exact production replay matches the live transitions and identifies two distinct missed-right-click
causes:

- One intended middle pinch repeatedly moved the index tip inside the configured cross-pinch clear
  boundary. Its index ratio reached `0.469-0.498`, below the required `0.500`, while the middle ratio
  was closed. The FSM canceled three restarted middle candidates with
  `middle_pinch_cancelled_ambiguous_cross_pinch` and emitted no button action. This is the required
  fail-closed behavior and must not be weakened.
- One cross-exclusive middle pinch kept the index ratio at `0.533` or greater but reached a minimum
  middle ratio of only `0.3518`, narrowly outside the configured `0.3500` closed onset. It therefore
  produced no candidate despite the correct `11011` extension posture.

A `0.360` closed onset recovers the second clean episode in exact replay, improving this capture
from 3/5 to 4/5 right clicks while preserving all three ambiguous cancellations and all five index
clicks. Replaying every available landmark capture shows no change to the approved mixed fixture,
the two controlled alternating fixtures, index-click counts, or ambiguity cancellations. It also
detects one previously borderline clear middle-only episode in `thumb-middle-10.jsonl` one frame
earlier, allowing that episode to satisfy the unchanged 100 ms stability dwell. The open threshold
remains `0.500`, the cross-pinch clear threshold remains `0.500`, and all dwell/safety behavior is
unchanged.

The configured closed ratio is now `0.360`. Regression coverage first failed at the observed clean
`middle=0.3518/index=0.621` frame and passes after the correction. A separate regression freezes the
observed ambiguous `middle=0.182/index=0.469` frame as neither index nor middle pinch. Local
verification after the correction:

```text
ruff format --check: 39 files already formatted
ruff check: All checks passed
compileall: passed
host-compatible suite: 86 passed in 38.68s
```

Fresh target verification remains required. The complete target suite now contains 87 tests,
including the MediaPipe model smoke check that cannot run in the Codex-hosted process.

### 2026-07-19 release-order root cause and correction

The owner repeated the physical-right-hand-only alternating sequence with live landmark recording
after the `0.360` contact-onset correction. The target run produced five balanced index clicks and
three right clicks:

```text
measurement_duration_s=45.03 capture_fps=23.03 callback_hz=20.30
submitted=914 callbacks=914 capture_slot_drops=20 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=278 capture_to_quartz_median_ms=32.87 capture_to_quartz_p95_ms=46.15
frame_age_at_submission_median_ms=0.66 frame_age_at_submission_p95_ms=1.22
action_events=LEFT_DOWN:5,LEFT_UP:5,POINTER_MOVE:278,RIGHT_CLICK:3
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
landmark_fixture=.../live-middle-misses-v1.jsonl records=913
```

Unlike the prior capture, all five intended middle pinches entered `MIDDLE_PINCH_PENDING` and stayed
there beyond the 100 ms stability dwell. The two missing clicks were canceled only on release. In
both cases the middle fingertip was fully open (`0.753` and `0.766`), but the index ratio briefly
passed through the cross-pinch dead zone (`0.496` and `0.440`). There were zero captured frames in
those episodes where both fingertips were inside the cross-pinch boundary during the closed
contact.

The root cause was an ordering/meaning defect across pose classification and the middle-pinch FSM:

- `middle_pinch_open` required both the middle tip to be open and the index tip already to be beyond
  the cross-pinch boundary, hiding a valid release while the index was merely in its dead zone.
- `MIDDLE_PINCH_PENDING` evaluated cross ambiguity before evaluating release, so an already-armed,
  cross-exclusive middle pinch could be discarded during its opening trajectory.

The correction defines middle release from the middle fingertip opening itself. The FSM still gives
a fully closed index pinch first priority and cancels it as a gesture switch; it then commits or
cancels middle release according to whether the clear middle candidate armed; only an ongoing
non-open contact is subject to cross-pinch ambiguity cancellation. Genuine both-tip ambiguity
during contact therefore remains fail-closed.

Both new regressions failed before the correction and pass afterward:

```text
test_middle_pinch_release_depends_on_middle_tip_opening
test_armed_middle_pinch_commits_when_release_passes_through_cross_dead_zone
```

Existing regressions proving that a middle-to-index transition emits no wrong button and that an
armed middle pinch entering genuine contact-time ambiguity emits nothing also pass. Exact replay of
the new target capture now produces:

```text
LEFT/PINCH_START=5
RIGHT_CLICK=5
order=LEFT,RIGHT,LEFT,RIGHT,LEFT,RIGHT,LEFT,RIGHT,LEFT,RIGHT
```

Local verification after the correction:

```text
ruff format --check: 39 files already formatted
ruff check: All checks passed
compileall: passed
host-compatible suite: 88 passed in 22.99s
```

Fresh target verification remains required. The complete target suite now contains 89 tests. The
new live recording remains private, unapproved, and untracked.

### 2026-07-19 seven-cycle target retry after release correction

The owner performed seven cycles in a 45-second right-hand target run after the release-order
correction. The objective summary was:

```text
measurement_duration_s=45.01 capture_fps=23.13 callback_hz=23.02
submitted=1036 callbacks=1036 capture_slot_drops=0 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=316 capture_to_quartz_median_ms=20.23 capture_to_quartz_p95_ms=24.03
frame_age_at_submission_median_ms=0.68 frame_age_at_submission_p95_ms=1.22
action_events=LEFT_DOWN:7,LEFT_UP:7,POINTER_MOVE:316,RIGHT_CLICK:4
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
```

The release-order defect is absent: there are zero
`middle_pinch_cancelled_ambiguous_cross_pinch` transitions, and every middle candidate that armed
committed exactly one right click. Three additional middle candidates ended with
`middle_pinch_cancelled_before_stable`; their pending durations were approximately 87 ms, 43 ms,
and 89 ms, all below the unchanged 100 ms stability requirement. Two of those short candidates
occurred immediately after successful right-click cycles and may be release/recontact bounce rather
than separate intended cycles. Other expected middle attempts produced no candidate in the
transition log, but this no-recording run does not contain the geometry needed to distinguish a
near-threshold contact from an unrecognized posture.

The run safely emitted balanced left-button events, no scroll or clutch action, fresh latency, and
no held button after shutdown. It remains **FAIL / open** for the §4 alternating gate because the
objective result is 7 left clicks and only 4 right clicks. No dwell or safety threshold is changed
from this evidence.

The owner's direct observations for the same run were:

```text
sequence performed: seven alternating thumb-index/thumb-middle pairs
wrong-button clicks observed: 0
missed right clicks observed: 1
ambiguous-contact clicks observed: 0
```

The zero wrong-button and zero ambiguous-click observations are clean. However, one visually missed
right click implies six successful right clicks, while the controller objectively emitted only four
`RIGHT_CLICK` events. That discrepancy cannot be resolved from transition logs alone and prevents a
pass. The next diagnostic run must record the exact live landmark stream so all seven intended
middle attempts can be aligned with candidate onset, dwell, release, and Quartz emission.

### 2026-07-19 recorded seven-pair diagnostic

The owner repeated exactly seven alternating right-hand pairs with integrated landmark recording.
The private, unapproved `live-seven-misses-v2.jsonl` contains 1,038 records and remains untracked.
The target summary was:

```text
measurement_duration_s=45.01 capture_fps=23.13 callback_hz=23.06
submitted=1038 callbacks=1038 capture_slot_drops=0 result_slot_drops=0
stale_or_out_of_order=0 inferred_dropped=0
dispatch_samples=502 capture_to_quartz_median_ms=20.14 capture_to_quartz_p95_ms=21.46
frame_age_at_submission_median_ms=0.62 frame_age_at_submission_p95_ms=1.22
action_events=LEFT_DOWN:2,LEFT_UP:2,POINTER_MOVE:502,RIGHT_CLICK:6
reported_false_actions=none
quartz_left_button_down_after_shutdown=False
landmark_fixture=.../live-seven-misses-v2.jsonl records=1038
```

MediaPipe reported the physical right hand for 747 of 748 valid results, with the single outlier not
forming an action. Hand identity is therefore not the cause. Exact feature analysis shows that most
intended index approaches did not reach the configured `0.360` contact onset: observed minima were
commonly `0.378-0.435`, and only two sustained episodes classified and emitted left clicks. Six
middle episodes emitted right clicks. Several additional short or noisy contact fragments safely
canceled before their 100 ms dwell; one two-finger candidate also canceled without action.

The 2D image-landmark alternative does not recover the contacts. In this recording, the current 3D
world-landmark measurement produced 12 index-closed frames and 27 middle-closed frames, whereas the
2D image measurement at the same normalized threshold produced only two index-closed frames and
zero middle-closed frames.

Threshold sensitivity replay also rules out another safe scalar adjustment:

```text
closed=0.360 -> this capture LEFT=2 RIGHT=6
closed=0.420 -> this capture LEFT=2 RIGHT=7
closed=0.450 -> this capture LEFT=3 RIGHT=8
```

Raising the threshold as far as `0.450` still fails to recover four of seven intended index clicks
and introduces additional right-click emissions in this and the `thumb-middle-10` capture. It would
trade misses for phantom/duplicate action risk and is therefore rejected. The configured threshold
remains `0.360`; no code or acceptance criterion is weakened from this run.

The §4 gate remains **FAIL / open**. The remaining unknown is visual: whether the physical
thumb-index contacts were fully visible to the camera in a front-facing plane even though
MediaPipe's landmarks kept the tips separated. Resolving that requires synchronized visual evidence
from the same gesture run, not another unlabeled landmark capture or threshold guess.

### 2026-07-19 three-pair visual-correlation attempt

The owner created the requested private `live-visual-three-v3.jsonl` diagnostic and later supplied
the synchronized private Desktop screen recording. Neither artifact is approved for git. The
landmark stream contains 646 records over 29.96 seconds, with 511 valid physical-right-hand results
and 135 no-hand results. Exact replay through the current corrected FSM produces:

```text
PINCH_START/LEFT=6
PINCH_END=6
RIGHT_CLICK=3
order=LEFT,RIGHT,LEFT,RIGHT,LEFT,LEFT,LEFT,RIGHT,LEFT
middle candidates=3; released/committed=3
```

Frame-ID correlation between the debug overlay and the landmark fixture establishes a video offset
of approximately 6.83 seconds. The recording visibly contains six thumb-index cycles and five
thumb-middle approaches, not the requested three alternating pairs. All six index cycles reach
clear fingertip contact and commit. Three middle approaches also show the thumb-tip and middle-tip
landmarks overlapping, reach minima `0.319-0.352`, and commit one right click each. The other two
middle approaches stop at minima `0.380` and `0.404`, above the configured `0.360` contact onset.
At full resolution, their tracked thumb tips land below or alongside the middle fingertip rather
than overlapping it. MediaPipe follows the visible tips consistently in those frames; this is not a
hand-identity, scheduler, release-order, or landmark-placement defect.

This attempt is **INVALID / not an acceptance result** because the performed count and sequence do
not match the instructed three pairs. It nevertheless resolves the visual unknown from the prior
recorded run: the remaining non-recognition is caused by incomplete fingertip-to-fingertip contact.
The prior threshold sweep showed that loosening the scalar threshold introduces extra right-click
emissions without reliably recovering the intended index sequence, so the configured `0.360`
threshold and all safety/dwell rules remain unchanged. The next gate attempt must keep the palm
front-facing, touch the center of the thumb tip directly to the center of the selected fingertip,
hold for longer than 100 ms, and return to a visibly open hand between gestures. Both raw artifacts
remain private, unapproved, and untracked.

### 2026-07-19 Phase 1 validation stopped; MVP demo preparation started

The project owner explicitly stopped the remaining Phase 1 validation and moved the work to MVP
demo preparation. Phase 1 is not marked PASS: the unfinished confusion, application double-click,
target-acquisition, false-action, and remaining safety/loss checks stay recorded as unverified in
`PHASE_1_VALIDATION.md`. No raw private diagnostic capture received git approval as part of this
decision.

For the demo, the camera is now visible during every normal controller run rather than only behind
`--debug`. The renderer uses a native macOS borderless window that is:

- 280×200 points and inset 20 points from the main display's bottom-left;
- mirrored for natural self-view, rounded, shadowed, always on top, and available across Spaces;
- click-through, so it cannot intercept the pointer interactions being demonstrated; and
- free of diagnostic text in normal mode, while `--debug` adds landmarks/FSM details to the same
  compact overlay.

The dimensions and presentation values are schema-validated under `preview` in `config.yaml`.
Local formatting, lint, compilation, and the host-compatible suite pass with 89 tests and one
official-model smoke test deselected. A bounded native five-second launch opened the camera,
processed 96 latest-only results, exited with no actions, and reported
`quartz_left_button_down_after_shutdown=False`.

The requested thumbs-up shortcut is intentionally not active yet because the owner is still
selecting the exact Whisper Flow key combination. Emitting a guessed shortcut would be unsafe. The
gesture and Quartz keyboard integration will be implemented once that exact key plus modifiers is
provided.
