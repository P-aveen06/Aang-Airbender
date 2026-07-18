from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import yaml


class ConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ControlBoxConfig:
    left: float
    top: float
    right: float
    bottom: float


@dataclass(frozen=True, slots=True)
class Phase1Config:
    raw: dict[str, Any]
    control_box: ControlBoxConfig

    def section(self, name: str) -> dict[str, Any]:
        value = self.raw[name]
        assert isinstance(value, dict)
        return value


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(path: Path | None = None, schema_path: Path | None = None) -> Phase1Config:
    config_path = path or repository_root() / "config.yaml"
    validation_path = schema_path or repository_root() / "config.schema.json"
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        schema = jsonschema.validators.Draft202012Validator(
            json.loads(validation_path.read_text(encoding="utf-8"))
        )
    except (OSError, ValueError, yaml.YAMLError) as error:
        raise ConfigurationError(f"Could not read Phase 1 configuration: {error}") from error
    if not isinstance(raw, dict):
        raise ConfigurationError("Phase 1 configuration must be a mapping")
    errors = sorted(schema.iter_errors(raw), key=lambda item: list(item.absolute_path))
    if errors:
        details = "; ".join(
            f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in errors
        )
        raise ConfigurationError(f"Invalid Phase 1 configuration: {details}")

    control = raw["control"]
    box = control["control_box"]
    if box["left"] >= box["right"] or box["top"] >= box["bottom"]:
        raise ConfigurationError("Invalid Phase 1 configuration: control box has no positive area")
    pinch = raw["pinch"]
    if pinch["closed_ratio"] >= pinch["open_ratio"]:
        raise ConfigurationError(
            "Invalid Phase 1 configuration: pinch closed_ratio must be less than open_ratio"
        )
    if pinch["cross_pinch_open_ratio"] < pinch["open_ratio"]:
        raise ConfigurationError(
            "Invalid Phase 1 configuration: cross-pinch open ratio must be at least open_ratio"
        )
    timing = raw["timing"]
    if timing["hand_loss_grace_ms"] >= timing["disengage_timeout_ms"]:
        raise ConfigurationError(
            "Invalid Phase 1 configuration: hand-loss grace must be shorter than disengagement"
        )
    gestures = raw["gestures"]
    if (
        gestures["right_click_candidate"] == "two_finger_dwell"
        and not gestures["enable_two_finger_dwell_right_click_fallback"]
    ):
        raise ConfigurationError(
            "Invalid Phase 1 configuration: two-finger dwell right-click fallback "
            "is selected but disabled"
        )
    return Phase1Config(
        raw=raw,
        control_box=ControlBoxConfig(
            float(box["left"]), float(box["top"]), float(box["right"]), float(box["bottom"])
        ),
    )
