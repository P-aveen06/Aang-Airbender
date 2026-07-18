# Aang-Airbender Phase 1 v1.2

## Scope

- Base branch: `develop`
- Phase implemented: Phase 1 v1.2 right-point/left-click only
- Frozen documents changed: `PLAN.md`, owner-approved exception dated 2026-07-18
- Later-phase work included: `No`

## What changed

<!-- Concise file-level and behavior summary. -->

## Explicitly disabled

- [ ] Open-palm engagement and palm pointer
- [ ] Right-hand click
- [ ] Drag
- [ ] Right-click
- [ ] Scroll
- [ ] Fist clutch/pause
- [ ] Thumbs-down disengagement
- [ ] Gesture double-click
- [ ] Calibration, acceleration, HUD, and packaging

## Environment

```text
macOS:
Hardware:
Terminal:
Python:
Architecture:
uv:
MediaPipe:
OpenCV:
PyObjC:
Model source/version/checksum:
```

## Commands run

```bash
# Exact reproducible commands
```

## Automated tests

```text
# Pass/fail counts and meaningful output
```

## Target-Mac manual validation

- [ ] Physical right-hand ☝🏻 alone moves the cursor from index landmark 8
- [ ] Ordinary right-hand poses do not move the cursor
- [ ] Physical left thumb-index pinch commits one click on release
- [ ] Cursor remains at the frozen pinch-start anchor for the click
- [ ] Either-role loss cancels a pending click
- [ ] Removed gestures emit no action
- [ ] Main-display mapping and mirroring are correct
- [ ] Normal shutdown and controlled failure leave left-button state false

Evidence/notes:

## Measurements

```text
Achieved capture FPS:
Submitted frames:
Callback results:
Stale/out-of-order results:
Inferred dropped results:
Median software latency:
p95 software latency:
Sample count/duration:
Median frame age:
p95 frame age:
```

> These are software-pipeline measurements, not motion-to-visible latency.

## Safety assertion

```text
Quartz left-button state after simulated failure:
Quartz left-button state after normal shutdown:
```

## Unverified items

<!-- List every acceptance item not actually exercised. Write `None` only when true. -->

-

## Known limitations and blockers

-

## Author self-review

- [ ] Full diff reviewed against `PLAN.md`
- [ ] Owner-approved frozen-plan exception recorded in the PR body
- [ ] Physical roles come from corrected handedness, never result ordering
- [ ] Duplicate/invalid roles fail closed
- [ ] No unbounded frame/result queue
- [ ] Callback performs no blocking/UI/Quartz work
- [ ] No OS mouse button is held across perception frames
- [ ] Cleanup and exception paths call idempotent release
- [ ] `PROGRESS.md` updated
- [ ] No secrets, personal paths, or webcam media attached

## Phase 1 author verdict

`PASS / FAIL / PARTIALLY VERIFIED`

Rationale:

## Reviewer handoff

- Commit SHA ready for review:
- Target-Mac access available to reviewer: `Yes / No`
- Evidence the reviewer must independently reproduce:
