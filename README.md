# Aang-Airbender

Aang-Airbender is a local macOS hand controller. Phase 1 builds the safe “core five” on the proven
Phase 0 path:

```text
OpenCV AVFoundation -> MediaPipe Hand Landmarker LIVE_STREAM -> immutable HandState
-> palm-relative features -> timestamp FSM -> filtered absolute control
-> semantic events -> Quartz mouse and pixel-scroll events
```

Phase 1 is still under validation. It does not include calibration, relative mapping, acceleration
curves, scroll momentum, a HUD/menu-bar app, packaging, or later gesture vocabulary.

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

The controller starts disengaged. Hold an open palm facing the camera for about 0.9 seconds to
engage. Open palm has that meaning only while disengaged. The v1.1 candidate vocabulary is:

- Palm movement: move the pointer from the filtered weighted palm centroid, not the index fingertip.
- Thumb-index pinch: press the left button; hold the pinch to drag and open it to release.
- Thumb-middle pinch: arm a right click; opening the pinch emits it once, then return to neutral.
- Two fingers, index and middle: vertical motion scrolls. Holding the pose still does nothing.
- Fist: release held input, then clutch/freeze the pointer. Opening the fist resets the pointer
  filter baseline. A fist does not disengage the controller.
- Thumbs-down for about one second: disengage.
- Hand loss: release held input after about 200 ms; disengage after the full timeout.

Index and middle pinches are cross-exclusive: keep the non-pinching finger clearly open. An
ambiguous pinch emits no click. Stationary two-finger right-click remains available only as a
disabled configuration fallback and is not part of the default vocabulary.

Two complete left-pinch cycles inside the configured time and cursor-distance allowances mark the
second Quartz down/up pair with click state `2`. This supports application-level double-clicks while
preventing a drag or distant second click from being promoted to a double-click.

Press Control-C to stop. Shutdown and error paths release any left button held by Aang-Airbender.
The physical trackpad and mouse remain available as the external recovery path.

The central camera control box in `config.yaml` maps to the complete main display. This intentionally
increases useful cursor travel without adding the Phase 2 acceleration curve. Tune only through the
validated configuration; invalid and unknown values fail closed. The default box spans 50% of the
camera width and 54% of its height, giving approximately 20% more horizontal response and 18.5%
more vertical response than the initial Phase 1 values.

The camera preview is always visible while the controller is running. It appears as a mirrored,
borderless, click-through 280×200 overlay at the bottom-left of the main display. Its dimensions,
margin, corner radius, mirroring, and render cadence are configured under `preview` in
`config.yaml`.

For a bounded run or a preview with diagnostic annotations:

```bash
uv run python -m aang_airbender.app --duration-seconds 30
uv run python -m aang_airbender.app --duration-seconds 30 --debug
```

The normal overlay contains only the camera image. `--debug` adds landmarks, recognized poses, FSM
state, and callback latency to that same compact overlay. Shutdown prints software pipeline timing,
emitted action counts, reported false-action counts, and the objective combined-session Quartz
left-button state. Software timing excludes camera sensor delay and display composition; it is not
motion-to-visible latency.

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
