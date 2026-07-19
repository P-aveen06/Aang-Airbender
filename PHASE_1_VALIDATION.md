# Aang-Airbender Phase 1 target-Mac validation

> **Stopped by project owner on 2026-07-19.** This checklist is retained as historical evidence but
> was not completed and does not approve Phase 1. Subsequent MVP-demo work, including the always-on
> camera overlay and planned thumbs-up shortcut, is outside this unfinished validation result.

This worksheet preserves the frozen Phase 1 acceptance criteria from `PLAN.md`. Do not mark an item
verified unless the exact check was run in an Accessibility-trusted terminal on the target Mac.

## 1. Environment and automated checks

```bash
uv sync --frozen
uv run python scripts/preflight.py
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run python scripts/verify_safe_release.py
```

Record the complete outputs in `PROGRESS.md`.

Target-Mac progress recorded 2026-07-19:

- [x] `uv sync --frozen`
- [x] permission and camera preflight
- [x] `ruff format --check .`
- [x] `ruff check .`
- [x] complete `pytest` suite
- [x] objective safe-release assertions

## 2. Explicit fixture capture

These commands create camera-derived files. Review them before committing or sharing.

```bash
uv run python scripts/record_landmarks.py \
  --output tests/fixtures/landmarks/phase1-recorded.jsonl \
  --duration-seconds 30 \
  --i-understand-camera-derived-data

uv run python scripts/record_video_fixture.py \
  --output tests/fixtures/videos/phase1-short.mp4 \
  --duration-seconds 5 \
  --i-understand-camera-derived-data
```

- [x] Landmark output reports approximately 30 seconds and a plausible callback-rate record count.
- [x] Short video opens locally and corresponds to the landmark-test conditions.
- [x] The owner has reviewed both files for privacy before adding either to git.

## 3. Core-five smoke session

```bash
uv run python -m aang_airbender.app --duration-seconds 300
```

During the five-minute session, do not touch the trackpad after engagement:

- [x] Hold a facing open palm for the configured dwell and engage.
- [x] Move the pointer using palm motion; confirm the anchor feels independent of fingertip motion.
- [x] Browse and open an application using thumb-index pinch-and-release clicks.
- [x] Hold a thumb-index pinch to drag a disposable file or safe test object, then confirm release.
- [x] Emit exactly one right click by closing and releasing a thumb-middle pinch, then returning to
      neutral.
- [x] Scroll a page using two fingers plus vertical motion; after the continuity correction, small
      movements respond continuously and intentional release causes no phantom movement.
- [x] Hold two fingers still and confirm no pointer, click, or scroll event occurs.
- [x] Confirm fist releases any active drag before clutching/freezing the pointer, and does not
      disengage even when held longer than one second.
- [x] Confirm fist release re-baselines the pointer without a jump.
- [x] Hold thumbs-down for the configured one-second dwell and confirm disengagement.
- [x] Confirm cursor travel is sufficient without feeling excessively sensitive.
- [x] Record timing summary, action counters, failures, and observations in `PROGRESS.md`.

## 4. Required confusion gates

Run these deliberately before calling the vocabulary v1:

- [ ] Alternate thumb-index and thumb-middle pinches; record any wrong-button click. The ambiguous
      cross-pinch zone must emit nothing.
- [x] Form a fist slowly and quickly; confirm no left or right click occurs while fingers curl.
- [x] Alternate fist and thumbs-down; confirm fist never disengages and thumbs-down never clutches.
- [x] Drop the hand naturally out of frame; confirm this follows hand-loss grace/full-timeout paths,
      never the explicit thumbs-down path.
- [ ] In Finder and at least one browser, perform two complete thumb-index pinch cycles at normal
      double-click cadence and confirm the target application interprets them as a double-click.

Application-level double-click behavior is a target-Mac acceptance check. The automated tests prove
two complete `LEFT_DOWN`/`LEFT_UP` cycles are emitted and the second Quartz pair receives click state
`2` inside configured time/distance allowances, but do not substitute for this real-app check.

## 5. Target acquisition

Open `tests/manual/target_acquisition.html` in Safari or Chromium. It presents twenty targets whose
diameter is exactly 44 CSS pixels (normally 44 macOS display-coordinate units at default browser
zoom). Keep browser zoom at 100%, engage Aang-Airbender, start the run, and acquire every target.

- Browser/version:
- Browser zoom:
- Display resolution/scaling:
- Hits:
- Misses:
- Median acquisition time:
- p95 acquisition time:
- [ ] All 20 targets acquired; misses and timing support “reliably” in the owner's judgment.

## 6. False-action sessions

Run without `--debug`; debug preview is not part of normal pointing behavior.

```bash
uv run python -m aang_airbender.app --duration-seconds 600
uv run python -m aang_airbender.app --duration-seconds 1800
```

- Normal pointing, 10 minutes: false clicks observed =
- Adversarial conversational hand motion, 30 minutes: false clicks observed =
- [ ] Normal pointing produced exactly zero false clicks.
- [ ] Adversarial motion produced fewer than one false click (therefore zero observed false clicks).

Do not average the two sessions or reinterpret the thresholds.

## 7. Safety and loss paths

- [ ] Begin a drag, remove the hand, and confirm release within the configured 200 ms grace period.
- [ ] Allow full no-hand disengagement and confirm no button remains held.
- [ ] Begin a drag, form a fist, and confirm left-button release occurs before clutch activation.
- [ ] Begin a drag, hold thumbs-down through its dwell, and confirm release before disengagement.
- [ ] Press Control-C during a drag and confirm the shutdown state prints `False`.
- [ ] Close/block the camera during a drag and confirm the failure path releases the button.
- [ ] Run `scripts/verify_safe_release.py`; both objective Quartz assertions pass.

## Acceptance status

`STOPPED / INCOMPLETE — owner moved to MVP demo preparation before the remaining gates`

Unresolved or unverified items:

- Alternating thumb-index/thumb-middle confusion gate
- Finder and browser application-level double-click checks
- Twenty-target acquisition test
- Ten-minute and thirty-minute false-action sessions
- Remaining manual safety/loss-path matrix
