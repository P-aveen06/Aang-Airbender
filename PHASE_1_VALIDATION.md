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

## 3. Right-point/left-click smoke session

```bash
uv run python -m aang_airbender.app --duration-seconds 300
```

During the five-minute session, do not touch the trackpad after starting:

- [ ] Show a physical-right index-point pose ☝🏻; after about 200 ms, move the pointer with the right
      index fingertip.
- [ ] Break the right index-point pose and confirm pointer output freezes immediately.
- [ ] While right-pointing, show the physical left hand open, then pinch its thumb and index. Confirm
      the cursor freezes when the pinch begins and one click occurs only after a stable pinch is
      released.
- [ ] Open an application from the Dock using the left-hand pinch-and-release click.
- [ ] Hold the left pinch and confirm it neither repeats the click nor begins a drag.
- [ ] Show open palms, a right-hand pinch, two fingers, a fist, and thumbs-down; confirm none moves
      the pointer or emits any click.
- [ ] Confirm cursor travel is sufficient without feeling excessively sensitive.
- [ ] Confirm cursor movement feels responsive without significant jitter or trailing lag.
- [ ] Record timing summary, action counters, failures, and observations in `PROGRESS.md`.

## 4. Required confusion gates

Run these deliberately before calling the vocabulary v1:

- [ ] Move the right hand in ordinary poses; confirm only the strict index-point pose moves the
      cursor.
- [ ] Pinch the physical right thumb and index; confirm it never emits a click.
- [ ] Point with the physical left hand; confirm it never moves the pointer.
- [ ] Bring the left hand into view already pinched; confirm it cannot click until opened and then
      pinched again.
- [ ] Form a left fist slowly and quickly; confirm it cannot become a pinch click while curling.
- [ ] Lose the left role during a pending or armed click; confirm no click occurs.
- [ ] Lose the right role during a pending or armed click; confirm no click occurs and cursor output
      freezes.
- [ ] Cross the hands and vary their entry order; confirm debug roles remain physical R pointer and
      physical L click, or fail closed—never swap actions.
- [ ] In Finder and at least one browser, perform two rapid complete left-pinch cycles and confirm
      two single-click events are produced, with Quartz click state `1` for both.

## 5. Target acquisition

Open `tests/manual/target_acquisition.html` in Safari or Chromium. It presents twenty targets whose
diameter is exactly 44 CSS pixels (normally 44 macOS display-coordinate units at default browser
zoom). Keep browser zoom at 100%, show the right index-point pose, start the run, and acquire every
target with the left-hand pinch click.

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

- [ ] Remove either hand during a pending pinch and confirm no click occurs.
- [ ] Remove the right hand for longer than the configured 200 ms grace and confirm no button
      remains held.
- [ ] Press Control-C and confirm the shutdown state prints `False`.
- [ ] Close/block the camera and confirm the failure path leaves no button held.
- [ ] Run `scripts/verify_safe_release.py`; both objective Quartz assertions pass.

## Acceptance status

`PASS / FAIL / PARTIALLY VERIFIED`

Unresolved or unverified items:

-
