# Aang-Airbender — Progress

## Phase 0 status

**Status:** Not started  
**Author:** Codex  
**Independent reviewer:** Claude  
**Decision:** Pending  
**Target branch:** `develop`  
**Implementation branch:**  
**Pull request:**  
**Commit SHA reviewed:**  
**Target machine:** M2 MacBook Air, macOS 13+  
**Python:** 3.11, ARM64

## Environment

- Date:
- macOS version:
- Hardware:
- Terminal application:
- Python version and architecture:
- `uv` version:
- MediaPipe version:
- OpenCV version:
- PyObjC / Quartz version:
- Hand Landmarker model source/version/checksum:

## Commands run by Codex

```bash
# Record exact commands here.
```

## Permission preflight

- Accessibility check:
- Camera-open check:
- Terminal restarted after grant:
- Notes:

## Capture results

- Requested resolution/FPS:
- Actual resolution:
- Achieved capture FPS:
- Median frame age at submission:
- p95 frame age at submission:
- `CAP_PROP_BUFFERSIZE` observed behavior:

## MediaPipe results

- Submitted frames:
- Callback results:
- Stale/out-of-order results:
- Inferred dropped results:
- Callback/result cadence:

## Software pipeline latency

- Median capture-to-Quartz dispatch:
- p95 capture-to-Quartz dispatch:
- Measurement duration/sample count:

> This is software pipeline latency. It excludes camera exposure/sensor delay before frame acquisition and display composition/refresh.

## Cursor behavior

- Palm midpoint visibly controls cursor:
- X mirroring correct:
- Main-display mapping correct:
- Observed jitter or lag:

## Safety results

- Simulated failure after left-button-down:
- `safe_release_all()` called:
- Quartz button state after release:
- Shutdown release assertion:

## Author tests

```text
Record tests, pass/fail counts, and relevant output.
```

## OpenCV decision

- [ ] Accept OpenCV AVFoundation for Phase 1.
- [ ] Replace with native `AVCaptureSession` in Phase 1.

Reason:

## Acceptance gate — author evidence

- [ ] Permission preflight passes.
- [ ] Python 3.11 ARM64 environment installs cleanly.
- [ ] Cursor follows palm midpoint on target Mac.
- [ ] No unbounded frame/result queue exists.
- [ ] Frame age and software pipeline timing are measured.
- [ ] No held mouse state survives failure or shutdown.

## Codex Phase 0 decision

**PASS / FAIL / PARTIALLY VERIFIED:**

Rationale:

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

- 

Do not begin Phase 1 automatically.
