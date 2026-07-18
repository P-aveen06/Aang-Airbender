# Aang-Airbender

Aang-Airbender is a local macOS hand controller. Phase 1 v1.2 intentionally exposes only pointer
movement and a single left click on the proven Phase 0 path:

```text
OpenCV AVFoundation -> MediaPipe Hand Landmarker LIVE_STREAM (up to two hands)
-> immutable HandFrame -> physical-handedness roles -> timestamp FSM
-> filtered right index tip -> anchored left pinch -> Quartz pointer/single-click events
```

Phase 1 is still under validation. It does not include drag, right-click, scroll, double-click,
pause/clutch, wake/disengage gestures, calibration, relative mapping, acceleration curves, a
HUD/menu-bar app, packaging, or later gesture vocabulary.

## Requirements

- macOS 13 or newer on Apple Silicon
- a terminal application with Camera and Accessibility permission
- [`uv`](https://docs.astral.sh/uv/)

Accessibility changes may not take effect in an already-running terminal. Fully quit the terminal
application—not just its window—reopen it, and rerun the preflight after granting permission.

## Setup

```bash
uv python pin 3.11
uv sync --frozen
uv run python -c "import platform; print(platform.python_version(), platform.machine())"
uv run python scripts/preflight.py
```

The architecture command must report Python `3.11.x` and `arm64`. In **System Settings > Privacy &
Security**, grant Camera and Accessibility access to the terminal application running the commands.

## Run Phase 1

```bash
uv run python -m aang_airbender.app
```

Use exactly these two gestures:

- **Move:** show only the physical right hand in a strict index-point pose ☝🏻. After the configured
  200 ms stability period, landmark 8 (the index fingertip) controls the cursor. Breaking the pose
  freezes cursor output.
- **Left click:** while the right hand is still pointing, first show the physical left hand open,
  then touch/pinch its thumb and index finger. The cursor freezes at the pinch-start location. Keep
  the pinch closed for at least 100 ms and release it to emit exactly one click at that frozen
  location.

Holding the left pinch does nothing beyond keeping the click armed: it does not drag. If either hand
is lost or becomes invalid before release, the click is cancelled. A left pinch that enters the
camera already closed must open once before it can arm, preventing surprise clicks during hand
entry. Open palms, right-hand pinches, two fingers, fists, thumbs-down, and every other pose emit no
action. Two quick left pinches remain two single-click Quartz events; there is no explicit
double-click behavior.

Press Control-C to stop. Shutdown and error paths release any left button held by Aang-Airbender.
The physical trackpad and mouse remain available as the external recovery path.

The central camera control box in `config.yaml` maps to the complete main display. The default box
spans 50% of camera width and 54% of camera height. The right index tip uses a low-latency One Euro
filter (`min_cutoff=1.0`, `beta=4.0`); this replaces the laggy palm-tuned beta without adding a Phase
2 acceleration curve. Tune only through validated configuration; invalid and unknown values fail
closed.

For a bounded run or opt-in debug preview:

```bash
uv run python -m aang_airbender.app --duration-seconds 30
uv run python -m aang_airbender.app --duration-seconds 30 --debug
```

Debug rendering is off by default. Shutdown prints software pipeline timing, emitted action counts,
reported false-action counts, and the objective combined-session Quartz left-button state. Software
timing excludes camera sensor delay and display composition; it is not motion-to-visible latency.

## Validate without camera access

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest -k 'not official_model_runs_in_live_stream_mode'
```

The full `uv run pytest` includes the official-model `LIVE_STREAM` smoke test and requires a macOS
session capable of creating MediaPipe's graphics context. The geometry, poses, FSM, replay, control,
action safety, and configuration layers run headlessly.

After the permission preflight succeeds, verify real Quartz release behavior:

```bash
uv run python scripts/verify_safe_release.py
```

That script deliberately emits left-button-down events before controlled-failure and normal-shutdown
checks. It verifies `CGEventSourceButtonState` is false after each release.

## Opt-in fixture recording

These commands record camera-derived data locally. Nothing records automatically. Review the output
before committing or sharing it; video and hand motion can contain sensitive information. Existing
files are never overwritten.

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

The repository includes a non-camera synthetic JSONL replay for deterministic tests. Phase 1's
required 30-second target-Mac landmark fixture and short video remain acceptance evidence to collect.

## Model provenance

`models/hand_landmarker.task` is MediaPipe Hand Landmarker `float16`, version `1`, from the official
Google-hosted URL recorded in `models/MODEL_INFO.md`. Its SHA-256 checksum is recorded there and in
`PROGRESS.md`.

## Common failures

- `Expected Python 3.11`: rerun `uv python pin 3.11` and `uv sync --frozen`.
- `Expected Apple Silicon arm64`: do not use a Rosetta/x86 terminal or environment.
- Accessibility denied: grant the terminal access, fully quit it, reopen it, and rerun preflight.
- Camera open/read failed: grant Camera access, close other camera users, and rerun preflight.
- Model load failed: verify `shasum -a 256 models/hand_landmarker.task` against `MODEL_INFO.md`.
- Invalid configuration: read the complete field path in the startup error and compare
  `config.yaml` with `config.schema.json`; the application will not run with unsafe values.
