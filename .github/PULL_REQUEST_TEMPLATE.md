# Aang-Airbender Phase 0

## Scope

- Base branch: `develop`
- Phase implemented: Phase 0 only
- Frozen documents changed: `No` / explain approved exception
- Phase 1 work included: `No`

## What changed

<!-- Concise file-level and behavior summary. -->

## Explicitly not implemented

- [ ] Gesture vocabulary/FSM
- [ ] Click, drag, scroll, clutch, or engagement recognition
- [ ] Filtering, calibration, HUD, or config schema
- [ ] Packaging/menu-bar app
- [ ] Phase 1 abstractions

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

## Permission preflight

```text
# Before-grant result, after-grant result, and terminal restart status
```

## Target-Mac manual validation

- [ ] Palm midpoint controls cursor
- [ ] X mirroring is correct
- [ ] Main-display mapping is correct
- [ ] Normal shutdown releases mouse state
- [ ] Controlled failure releases mouse state

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
- [ ] Full diff reviewed against `PHASE_0_CHECKLIST.md`
- [ ] No unbounded frame/result queue
- [ ] MediaPipe timestamps strictly increase
- [ ] Callback performs no blocking/UI/Quartz work
- [ ] Cleanup and exception paths call idempotent release
- [ ] `PROGRESS.md` updated
- [ ] No secrets, personal paths, or webcam media attached

## Phase 0 author verdict

`PASS / FAIL / PARTIALLY VERIFIED`

Rationale:

## Claude review handoff

- Commit SHA ready for review:
- Target-Mac access available to Claude: `Yes / No`
- Evidence Claude must independently reproduce:
