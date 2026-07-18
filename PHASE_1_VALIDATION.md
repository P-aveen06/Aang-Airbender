# Aang-Airbender Phase 1 target-Mac validation

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

- [ ] Landmark output reports approximately 30 seconds and a plausible callback-rate record count.
- [ ] Short video opens locally and corresponds to the landmark-test conditions.
- [ ] The owner has reviewed both files for privacy before adding either to git.

## 3. Core-five smoke session

```bash
uv run python -m aang_airbender.app --duration-seconds 300
```

During the five-minute session, do not touch the trackpad after engagement:

- [ ] Hold a facing open palm for the configured dwell and engage.
- [ ] Browse and open an application using thumb-index pinch clicks.
- [ ] Drag a disposable file or safe test object, then confirm release.
- [ ] Scroll a page using the two-finger command pose.
- [ ] Confirm a stationary two-finger dwell produces exactly one right click.
- [ ] Confirm fist clutches/freezes the pointer and does not disengage.
- [ ] Confirm cursor travel is sufficient without feeling excessively sensitive.
- [ ] Record timing summary, action counters, failures, and observations in `PROGRESS.md`.

## 4. Target acquisition

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

## 5. False-action sessions

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

## 6. Safety and loss paths

- [ ] Begin a drag, remove the hand, and confirm release within the configured 200 ms grace period.
- [ ] Allow full no-hand disengagement and confirm no button remains held.
- [ ] Press Control-C during a drag and confirm the shutdown state prints `False`.
- [ ] Close/block the camera during a drag and confirm the failure path releases the button.
- [ ] Run `scripts/verify_safe_release.py`; both objective Quartz assertions pass.

## Acceptance status

`PASS / FAIL / PARTIALLY VERIFIED`

Unresolved or unverified items:

-
