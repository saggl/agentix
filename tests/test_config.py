"""Tests for configuration management."""


import pytest

from agentix.config.manager import ConfigManager
from agentix.config.models import (
    AgentixConfig,
    ConfluenceConfig,
    Defaults,
    JiraConfig,
    Profile,
)
from agentix.core.exceptions import ConfigError


def test_empty_config_when_no_file(tmp_path):
    cm = ConfigManager(config_path=tmp_path / "nonexistent.toml")
    cfg = cm.config
    assert cfg.default_profile == "default"
    assert cfg.defaults.format == "json"
    assert cfg.profiles == {}


def test_save_and_load(tmp_path):
    config_path = tmp_path / "config.toml"
    cm = ConfigManager(config_path=config_path)
    config = AgentixConfig(
        default_profile="work",
        defaults=Defaults(format="table"),
        profiles={
            "work": Profile(
                jira=JiraConfig(
                    base_url="https://work.atlassian.net",
                    email="me@work.com",
                    api_token="tok123",
                )
            )
        },
    )
    cm.save(config)

    # Reload
    cm2 = ConfigManager(config_path=config_path)
    loaded = cm2.config
    assert loaded.default_profile == "work"
    assert loaded.defaults.format == "table"
    assert loaded.profiles["work"].jira.base_url == "https://work.atlassian.net"
    assert loaded.profiles["work"].jira.api_token == "tok123"


def test_get_value(tmp_config):
    assert tmp_config.get_value("default_profile") == "test"
    assert tmp_config.get_value("profiles.test.jira.base_url") == "https://test.atlassian.net"


def test_get_value_missing(tmp_config):
    with pytest.raises(ConfigError):
        tmp_config.get_value("profiles.nonexistent.jira.url")


def test_set_value(tmp_config):
    tmp_config.set_value("profiles.test.jira.base_url", "https://new.atlassian.net")
    assert tmp_config.get_value("profiles.test.jira.base_url") == "https://new.atlassian.net"


def test_set_value_missing_key_raises(tmp_config):
    with pytest.raises(ConfigError):
        tmp_config.set_value("profiles.test.jira.does_not_exist", "x")


def test_defaults_from_legacy_data_ignores_auto_update_field():
    cfg = AgentixConfig.from_dict({"defaults": {"format": "table", "auto_update": False}})
    assert cfg.defaults.format == "table"


def test_mask_tokens(tmp_config):
    masked = tmp_config.mask_tokens()
    jira = masked["profiles"]["test"]["jira"]
    assert jira["api_token"] == "***"
    assert jira["base_url"] == "https://test.atlassian.net"
    assert jira["email"] == "test@example.com"


def test_get_profile_creates_if_missing(tmp_config):
    cfg = tmp_config.config
    profile = cfg.get_profile("new_profile")
    assert profile.jira.base_url == ""
    assert "new_profile" in cfg.profiles


def test_set_value_creates_profile_if_missing(tmp_config):
    tmp_config.set_value("profiles.work.jira.base_url", "https://work.atlassian.net")
    assert tmp_config.get_value("profiles.work.jira.base_url") == "https://work.atlassian.net"


def test_config_roundtrip(tmp_path):
    """Test that config survives serialization/deserialization."""
    config = AgentixConfig(
        default_profile="prod",
        profiles={
            "prod": Profile(
                jira=JiraConfig(base_url="https://prod.atlassian.net", email="a@b.com", api_token="t"),
                confluence=ConfluenceConfig(base_url="https://prod.atlassian.net/wiki", email="a@b.com", api_token="t"),
            )
        },
    )
    d = config.to_dict()
    restored = AgentixConfig.from_dict(d)
    assert restored.default_profile == "prod"
    assert restored.profiles["prod"].jira.base_url == "https://prod.atlassian.net"
    assert restored.profiles["prod"].confluence.email == "a@b.com"
