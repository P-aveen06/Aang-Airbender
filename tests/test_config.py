import json

import pytest
import yaml

from aang_airbender.config import ConfigurationError, load_config, repository_root


def test_repository_configuration_is_valid() -> None:
    config = load_config()

    assert config.raw["config_version"] == 1
    assert config.control_box.left < config.control_box.right


def test_unknown_configuration_field_fails_closed(tmp_path) -> None:
    raw = yaml.safe_load((repository_root() / "config.yaml").read_text())
    raw["unexpected"] = True
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(raw))

    with pytest.raises(ConfigurationError, match="Additional properties"):
        load_config(config_path)


def test_invalid_cross_field_configuration_fails_closed(tmp_path) -> None:
    raw = yaml.safe_load((repository_root() / "config.yaml").read_text())
    raw["pinch"]["closed_ratio"] = raw["pinch"]["open_ratio"]
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(raw))

    with pytest.raises(ConfigurationError, match="closed_ratio must be less"):
        load_config(config_path)


def test_disabled_two_finger_right_click_fallback_cannot_be_selected(tmp_path) -> None:
    raw = yaml.safe_load((repository_root() / "config.yaml").read_text())
    raw["gestures"]["right_click_candidate"] = "two_finger_dwell"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(raw))

    with pytest.raises(ConfigurationError, match="selected but disabled"):
        load_config(config_path)


def test_schema_is_valid_draft_2020_12_json() -> None:
    schema = json.loads((repository_root() / "config.schema.json").read_text())

    assert schema["$schema"].endswith("2020-12/schema")
