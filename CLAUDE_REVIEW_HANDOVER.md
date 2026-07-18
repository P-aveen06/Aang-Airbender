# Aang-Airbender — Claude Phase 1 v1.2 review handover

## Role

Claude is an independent validator and reviewer, not the implementation author. Review the Phase 1
pull request into `develop` against `PLAN.md`, `PHASE_1_VALIDATION.md`, the completed PR body, and
`PROGRESS.md`. Do not merge the PR or substitute review for the project owner's final decision.

`PLAN.md` contains an owner-approved frozen-plan exception dated 2026-07-18. The v1.2 active
vocabulary is intentionally limited to:

- physical right-hand strict index-point ☝🏻 -> cursor from landmark 8;
- physical left-hand thumb-index pinch -> one anchored single click on stable release.

All former Phase 1 gesture meanings are disabled. Treat any reachable drag, right-click, scroll,
open-palm engagement, palm pointer, fist clutch, thumbs-down, or explicit double-click behavior as a
scope defect.

## Review priorities

1. **Role safety:** two simultaneous hands, corrected MediaPipe handedness, no result-order roles,
   duplicate/low-confidence roles fail closed.
2. **Click safety and precision:** left hand must be observed open before arming; pinch hysteresis and
   monotonic stability; pointer freezes at pinch start; release posts one click-state-1 down/up pair
   at that exact anchor; either-role loss cancels.
3. **Pointer behavior:** only a strict physical-right index-point pose moves; landmark 8 is the
   anchor; ordinary poses are inactive; filter response is low-latency and configuration-backed.
4. **Removed behavior:** old gestures are unreachable in the active FSM/control path and absent from
   runtime configuration.
5. **Terminal safety:** `safe_release_all()` remains idempotent and every terminal/error path invokes
   it; objective Quartz button-state verification remains available.
6. **Concurrency and time:** latest-frame/result slots remain bounded; callback remains minimal;
   MediaPipe timestamps are strictly monotonic; all stability/grace timing uses monotonic time.
7. **Evidence discipline:** headless results are distinguished from target-Mac live checks. Missing
   target evidence is `INCOMPLETE EVIDENCE`, not an inferred pass.

## Required checks

```bash
uv sync --frozen
uv run python scripts/preflight.py
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run python scripts/verify_safe_release.py
```

On the target Mac, follow `PHASE_1_VALIDATION.md`. In particular, verify physical role labels in the
debug preview, Dock/application click precision, removed-pose inactivity, either-role loss during a
pending click, false-click sessions, target acquisition, latency/feel, and the objective release
script. Do not mark any check passed unless it was actually run.

## Finding format

For each finding include severity (`BLOCKING` or `NON-BLOCKING`), file and symbol/line, violated
criterion, concrete failure scenario, minimum correction, and evidence needed to close it.

Use exactly one verdict: `APPROVE`, `REQUEST CHANGES`, or `INCOMPLETE EVIDENCE`.

Return the verdict, findings, reproduced checks, target-Mac evidence, acceptance status, residual
risks, and exact re-review conditions. Do not approve or merge on the author's behalf.
