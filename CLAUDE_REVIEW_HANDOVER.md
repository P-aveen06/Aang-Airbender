# Aang-Airbender — Claude Validation and PR Review Handover

## Role

Claude is the **independent validator and reviewer**, not the implementation author.

Review Codex's Phase 0 pull request into `develop`. Validate the implementation against the frozen `PLAN.md`, `PHASE_0_CHECKLIST.md`, PR description, and `PROGRESS.md`.

Do not assume Codex's summary is accurate. Inspect the complete diff and reproduce evidence where the available environment permits.

## Inputs required

- Pull-request URL and branch/commit SHA
- `PLAN.md`
- `PHASE_0_CHECKLIST.md`
- `PROGRESS.md`
- `.github/PULL_REQUEST_TEMPLATE.md` completed in the PR
- Repository access
- Target M2 Mac access for hardware validation, when available

If an input is missing, report `INCOMPLETE EVIDENCE` rather than inferring success.

## Review priorities

Review in this order:

1. **Safety:** no stuck logical mouse button, release on exception/shutdown, bounded handoffs.
2. **Scope:** Phase 0 only; no speculative Phase 1 implementation.
3. **Concurrency:** latest-value frame/result slots, minimal callback, no unsafe shared mutation.
4. **Time correctness:** monotonic clocks, strictly increasing MediaPipe millisecond timestamps, stale-result rejection.
5. **Permissions:** clear Accessibility and Camera failure handling, terminal-restart guidance.
6. **Native environment:** Python 3.11, ARM64, reproducible `uv` setup.
7. **Pipeline:** OpenCV AVFoundation → Hand Landmarker LIVE_STREAM → landmarks 5/17 midpoint → main-display Quartz movement.
8. **Measurement:** software latency is correctly labelled and measured; frame age and callback cadence are reported.
9. **Evidence:** commands and outputs are reproducible; observed results are separated from `UNVERIFIED` claims.
10. **Maintainability:** minimal clear code without unnecessary abstractions or drive-by refactors.

## Required validation

### Static review

- Read every changed file.
- Compare the implementation with every Phase 0 checkbox and acceptance condition.
- Inspect cleanup paths, `finally` blocks, signals, exceptions, and normal shutdown.
- Verify no FIFO or unbounded queue is introduced.
- Verify callback code does not dispatch Quartz events or perform blocking work.
- Verify MediaPipe timestamps cannot repeat or go backwards.
- Verify stale/out-of-order result handling.
- Verify the midpoint uses landmarks 5 and 17.
- Verify main-display-only behavior is explicit.
- Verify model provenance/checksum is recorded.

### Automated checks

Run the documented commands when possible, including:

```bash
uv sync --frozen
uv run python -c "import platform; print(platform.python_version(), platform.machine())"
uv run pytest
```

Run lint or type checks only when they are part of the submitted project. Do not add unrelated tooling as a review prerequisite.

### Target-Mac checks

When actual access to the target Mac is available:

- run the permission preflight before granting permissions and confirm useful failure instructions;
- grant permissions, restart the terminal application where required, and rerun preflight;
- run the cursor spike and visually confirm palm-midpoint control and X mirroring;
- inspect the timing report and sample count;
- execute the safe-release test and confirm Quartz reports the left button as released;
- exercise normal shutdown and one controlled failure path;
- note actual hardware, macOS version, terminal app, Python version, and architecture.

When target-Mac access is unavailable, do not approve hardware-specific acceptance items based solely on code inspection. Mark them unverified and choose `INCOMPLETE EVIDENCE` unless the user supplies adequate machine-run evidence.

## Finding format

For every blocking finding, include:

- severity: `BLOCKING` or `NON-BLOCKING`;
- exact file and line or symbol;
- violated checklist item or invariant;
- concrete failure scenario;
- minimum required correction;
- test or evidence needed to close it.

Avoid preferences that do not affect correctness, safety, scope, or maintainability.

## Verdicts

Use exactly one final verdict:

### `APPROVE`

Use only when all acceptance conditions are satisfied or valid target-Mac evidence is present, all required checks pass, and no blocking findings remain.

### `REQUEST CHANGES`

Use when the implementation has one or more correctable blocking defects.

### `INCOMPLETE EVIDENCE`

Use when code may be acceptable but required machine results, logs, checks, or PR evidence are missing. Do not convert missing evidence into a code defect.

## Review output

Return:

1. Verdict
2. Blocking findings
3. Non-blocking findings
4. Checks reproduced and results
5. Target-Mac evidence reproduced or still unverified
6. Acceptance checklist status
7. Residual risks
8. Exact re-review conditions

Do not merge the PR. The user makes the final merge decision.
