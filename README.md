# Aang-Airbender

Aang-Airbender Phase 0 is a macOS technical spike proving this exact path:

```text
OpenCV AVFoundation -> MediaPipe Hand Landmarker LIVE_STREAM
-> landmarks 5/17 palm midpoint -> main-display Quartz cursor movement
```

It intentionally has no gesture recognition, clicks, scrolling, filtering, calibration, HUD,
acceleration, or packaging.

## Requirements

- macOS 13 or newer on Apple Silicon
- a terminal application with Camera and Accessibility permission
- [`uv`](https://docs.astral.sh/uv/)

Accessibility changes may not take effect in an already-running terminal. Fully quit the terminal
application (not just its window), reopen it, and rerun the preflight after granting permission.

## Setup

```bash
uv python pin 3.11
uv sync --frozen
uv run python -c "import platform; print(platform.python_version(), platform.machine())"
uv run python scripts/preflight.py
```

The architecture command must report Python `3.11.x` and `arm64`. In **System Settings > Privacy &
Security**, grant Camera and Accessibility access to the terminal application that runs these
commands. The preflight checks both permissions and opens the camera once so macOS can show its
Camera prompt.

## Run

```bash
uv run python -m aang_airbender.app
```

Press Control-C to stop. Shutdown prints a compact software-pipeline timing report. These values
exclude camera exposure/sensor delay before frame capture and display composition/refresh; they are
not motion-to-visible latency.

For a bounded evidence run:

```bash
uv run python -m aang_airbender.app --duration-seconds 30
```

## Validate

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run python scripts/verify_safe_release.py
```

The final command deliberately emits a left-button-down event, simulates a controlled failure, and
then verifies the combined-session Quartz button state after release. Run it only after the
preflight succeeds. Physical mouse and trackpad input remain available as an external recovery path.

## Model provenance

`models/hand_landmarker.task` is MediaPipe's Hand Landmarker `float16`, version `1`, downloaded from
the official Google-hosted MediaPipe model URL recorded in `models/MODEL_INFO.md`. The exact SHA-256
checksum is recorded there and in `PROGRESS.md`.

## Common failures

- `Expected Python 3.11`: rerun `uv python pin 3.11` and `uv sync --frozen`.
- `Expected Apple Silicon arm64`: do not use a Rosetta/x86 terminal or dependency environment.
- Accessibility denied: grant the terminal under Privacy & Security, fully quit it, and reopen it.
- Camera open/read failed: grant Camera access, close other camera users, then rerun the preflight.
- Model load failed: verify `shasum -a 256 models/hand_landmarker.task` against `MODEL_INFO.md`.
