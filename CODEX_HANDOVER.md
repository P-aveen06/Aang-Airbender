# Aang-Airbender — Codex Implementation Handover

## Mission

Codex is the **implementation author** for Aang-Airbender. Implement **Phase 0 only** and raise a pull request from a dedicated feature branch into `develop`.

Claude is the **independent validator and reviewer** after the pull request is marked ready for review. Codex must provide enough reproducible evidence for Claude to validate the implementation without reconstructing the development process.

The user remains the final authority for scope changes, acceptance exceptions, and merge approval.

## Read first

Read these files completely before changing code:

1. `PLAN.md` — frozen product and architecture source of truth.
2. `PHASE_0_CHECKLIST.md` — immediate implementation scope and acceptance gate.
3. `PROGRESS.md` — record commands, measurements, decisions, failures, and blockers.
4. `.github/PULL_REQUEST_TEMPLATE.md` — required pull-request evidence.

For Phase 0, the checklist defines the implementation boundary. The plan defines architectural intent and future constraints.

Do not modify acceptance criteria because implementation is difficult. Any proposed deviation must be documented and approved by the user before being treated as accepted.

## Collaboration model

### Codex responsibilities

Codex must:

- implement the smallest coherent Phase 0 change set;
- work on a dedicated branch, recommended: `codex/phase-0-spike`;
- preserve unrelated repository changes;
- run every check available in its environment;
- update `PROGRESS.md` with exact commands, outputs, measurements, and `UNVERIFIED` hardware items;
- self-review the final diff against `PLAN.md` and `PHASE_0_CHECKLIST.md`;
- raise a **draft PR** into `develop` while work or evidence is incomplete;
- mark the PR ready only when the author checklist and evidence package are complete;
- address Claude's blocking findings on the same branch and explicitly map each finding to its fix or rationale;
- stop at the Phase 0 acceptance gate.

Codex must not:

- approve its own implementation;
- merge the PR;
- silently relax tests, acceptance criteria, or safety invariants;
- mark target-Mac behavior as passed unless it was actually exercised and recorded;
- begin Phase 1 automatically;
- use Claude as a substitute for missing author-side tests.

### Claude responsibilities

Claude should receive `CLAUDE_REVIEW_HANDOVER.md`, `CLAUDE_REVIEW_PROMPT.txt`, the PR URL, and access to the repository and relevant test environment.

Claude independently:

- reads the frozen plan, Phase 0 checklist, PR description, and `PROGRESS.md`;
- reviews the complete diff rather than only Codex's summary;
- verifies scope containment and architectural invariants;
- runs or reproduces available automated tests;
- validates target-Mac steps when it has actual access to the machine;
- distinguishes observed results from author-provided claims;
- reports blocking defects, non-blocking improvements, and unverified items;
- issues one verdict: `APPROVE`, `REQUEST CHANGES`, or `INCOMPLETE EVIDENCE`.

Claude must not rewrite the plan, expand Phase 0, or waive acceptance criteria. Only the user may approve a deviation.

### Merge rule

The PR is mergeable only when:

1. Codex's author checklist is complete.
2. Required automated checks pass.
3. Hardware-dependent results are either independently reproduced or clearly recorded with evidence on the target Mac.
4. Claude's latest verdict is `APPROVE` with no unresolved blocking findings.
5. The user performs or authorizes the final merge.

AI approval is advisory evidence, not a replacement for the user's final merge decision.

## Target environment

- macOS 13 or newer
- Apple Silicon, initially an M2 MacBook Air
- Python pinned exactly to **3.11** using `uv python pin 3.11`
- MediaPipe Tasks Hand Landmarker in `LIVE_STREAM` mode
- OpenCV with the AVFoundation backend for initial capture
- PyObjC / Quartz for cursor events and Accessibility state checks
- One hand, 640×480, requested 30 fps

Do not silently switch Python versions, use Rosetta/x86 dependencies, or replace the selected APIs without documenting a measured blocker.

## Immediate implementation objective

Build the smallest runnable spike that does all of the following:

1. Pins Python 3.11 and installs native ARM64 dependencies reproducibly.
2. Provides a preflight script that:
   - checks Accessibility with `AXIsProcessTrusted()`;
   - attempts one camera open so macOS can request Camera permission;
   - exits with clear corrective instructions;
   - warns that the terminal application normally needs a full restart after Accessibility permission is granted.
3. Captures webcam frames through OpenCV AVFoundation with a **single-slot latest-frame handoff**. Never create an unbounded queue.
4. Submits frames to MediaPipe `HandLandmarker.detect_async()` with strictly monotonically increasing integer-millisecond timestamps.
5. Keeps the MediaPipe callback minimal. It must create an immutable result and overwrite a single latest-result slot; no UI work, blocking work, Quartz dispatch, or direct mutable FSM/pipeline state in the callback.
6. Consumes the latest result on the pipeline thread and discards stale or out-of-order results.
7. Uses the midpoint of landmarks 5 and 17 as the sole Phase 0 cursor anchor.
8. Mirrors X, maps normalized coordinates to the main display, and posts raw Quartz mouse-move events.
9. Records timing for capture, MediaPipe submission, callback, pipeline consumption, and Quartz dispatch.
10. Implements idempotent `safe_release_all()` and an objective test using `CGEventSourceButtonState(kCGEventSourceStateCombinedSessionState, kCGMouseButtonLeft)`.

## Required repository output

Keep the repository minimal. Create only what Phase 0 needs, typically:

```text
aang-airbender/
├── .github/
│   └── PULL_REQUEST_TEMPLATE.md
├── .python-version
├── PLAN.md
├── PHASE_0_CHECKLIST.md
├── PROGRESS.md
├── README.md
├── pyproject.toml
├── uv.lock
├── models/
│   └── hand_landmarker.task
├── scripts/
│   └── preflight.py
├── src/aang_airbender/
│   ├── __init__.py
│   ├── app.py
│   ├── capture.py
│   ├── perception.py
│   ├── cursor.py
│   ├── safety.py
│   └── timing.py
└── tests/
    └── test_safety.py
```

This layout is illustrative, not permission to build future modules. Prefer fewer clear files over speculative abstractions.

## Technical invariants

- Use monotonic clocks for all internal timing.
- MediaPipe input timestamps must be strictly increasing even when two frames arrive within the same millisecond.
- Preserve the high-resolution capture timestamp separately from MediaPipe's millisecond timestamp.
- Frames and results are latest-value slots, not FIFO work queues.
- The callback must tolerate MediaPipe dropping submitted frames in live-stream mode.
- No mouse button may remain logically held after simulated tracking loss, controlled failure, exception handling, or normal shutdown.
- Attempting `CAP_PROP_BUFFERSIZE=1` is allowed, but never treat success as proof that AVFoundation honored it. Measure frame age.
- Phase 0 reports **software pipeline latency**, not motion-to-visible latency. Do not compare it directly with the later 80 ms product target.
- Keep ordinary mouse and trackpad recovery available.

## Suggested execution order

1. Inspect the existing repository and preserve unrelated user changes.
2. Create a dedicated Phase 0 branch from current `develop`.
3. Pin Python 3.11 and create the minimal `uv` project.
4. Add dependencies and verify `platform.machine() == "arm64"`.
5. Add the official Hand Landmarker model asset and record its source/version/checksum in `PROGRESS.md` or `README.md`.
6. Implement and run the permission preflight before debugging the main pipeline.
7. Implement capture plus frame timestamps and latest-frame exchange.
8. Implement MediaPipe live-stream submission, callback handoff, and stale-result rejection.
9. Implement main-display mapping and raw Quartz cursor movement using the palm midpoint.
10. Implement timing counters and a compact end-of-run summary.
11. Implement `safe_release_all()` and the objective button-state test.
12. Run the acceptance checklist and record results in `PROGRESS.md`.
13. Self-review the full diff and complete the PR template.
14. Push the branch and raise a PR into `develop`.
15. Stop and hand the PR to Claude. Do not continue into Phase 1.

## Commands to make available

Document the exact commands in `README.md`. Aim for a workflow similar to:

```bash
uv python pin 3.11
uv sync
uv run python -c "import platform; print(platform.python_version(), platform.machine())"
uv run python scripts/preflight.py
uv run python -m aang_airbender.app
uv run pytest
```

The final command names may differ if there is a concrete reason, but they must be simple and documented.

## Minimum timing report

At shutdown, print or save:

- achieved capture FPS;
- submitted frame count;
- callback/result count;
- stale/out-of-order result count;
- inferred dropped-result count where measurable;
- median and p95 accepted-frame-capture-to-Quartz-dispatch software latency;
- median and p95 frame age at inference submission.

Also record whether OpenCV capture is acceptable or whether native AVFoundation should be the Phase 1 fallback.

## PR evidence package

The PR must contain or link to:

- exact scope implemented and explicit out-of-scope confirmation;
- file-level change summary;
- exact commands run;
- automated test output;
- permission-preflight output;
- Python and machine architecture output;
- target-Mac cursor test result;
- timing summary and sample count;
- safe-release assertion result;
- model source, version, and checksum;
- every `UNVERIFIED` acceptance item;
- known limitations and blockers;
- Phase 0 verdict: `PASS`, `FAIL`, or `PARTIALLY VERIFIED`.

Logs should be concise and scrubbed of secrets or personal filesystem data. Do not attach webcam images or video unless the user explicitly approves it.

## Acceptance gate

Phase 0 passes only if:

- the preflight clearly detects missing permissions and passes after permissions are correctly granted and the terminal is restarted where required;
- dependencies install natively under pinned Python 3.11 on ARM64;
- the cursor visibly follows the landmarks 5/17 palm midpoint on the target Mac;
- no frame or result path can grow without bound;
- frame age, callback cadence, and software pipeline latency are measured;
- the safe-release assertion passes after a simulated failure and normal shutdown.

If hardware or macOS permissions cannot be exercised in the current Codex environment, implement the code and tests that can be verified there, then provide exact target-Mac commands and mark each hardware-dependent acceptance item as **UNVERIFIED**, not passed.

## Explicitly out of scope

Do not implement or scaffold beyond immediate necessity:

- gesture vocabulary or FSM;
- clicks, drag, scroll, clutch, right-click recognition, engagement logic;
- fixture recording;
- filtering, acceleration, calibration, or HUD;
- YAML config/schema or migrations;
- menu-bar app or `.app` packaging;
- Phase 1 abstractions, plugins, profiles, or system gestures;
- style rewrites of the frozen plan.

## Working rules

- Make the smallest coherent change set.
- Do not rewrite `PLAN.md` or `PHASE_0_CHECKLIST.md` unless a demonstrated implementation blocker requires a clearly documented correction approved by the user.
- Do not claim target-Mac behavior that was not run on the target Mac.
- Surface permission or native-wheel failures directly; do not hide them behind generic exceptions.
- Add comments only where concurrency, timestamp conversion, or macOS event behavior is non-obvious.
- Keep mouse-down testing isolated and ensure release in `finally` blocks and process cleanup paths.
- Keep the PR focused; no drive-by refactors or formatting-only churn.
- Finish with a concise implementation summary, files changed, commands run, test results, measured numbers, unresolved blockers, and the Phase 0 pass/fail decision.

## First Codex instruction

Read all handover files and inspect the repository. Implement Phase 0 on a dedicated branch, collect the required evidence, raise a PR into `develop`, and stop for Claude's independent review. Do not begin Phase 1 or merge the PR.
