"""Tests for configuration management."""

from unittest.mock import patch, MagicMock

import pytest

from agentix.config.commands import (
    _is_jira_cloud,
    _setup_bitbucket,
    _setup_confluence,
    _setup_jira,
    _setup_polarion,
)
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


# --- Cloud vs Server detection ---


def test_is_jira_cloud_true():
    assert _is_jira_cloud("https://company.atlassian.net") is True
    assert _is_jira_cloud("https://COMPANY.ATLASSIAN.NET") is True


def test_is_jira_cloud_false():
    assert _is_jira_cloud("https://jira.company.com") is False
    assert _is_jira_cloud("https://jira.selfhosted.example.com") is False


# --- _setup_jira: Cloud flow ---


@patch("agentix.config.commands.requests.get")
@patch("agentix.config.commands.click")
def test_setup_jira_cloud(mock_click, mock_get):
    """Cloud URL prompts for email + API token, validates with v3."""
    mock_click.prompt.side_effect = [
        "https://company.atlassian.net",  # base_url
        "user@company.com",               # email
        "cloud-token",                     # api_token
    ]
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"displayName": "Test User"}
    mock_get.return_value = mock_resp

    result = _setup_jira()

    assert result.base_url == "https://company.atlassian.net"
    assert result.email == "user@company.com"
    assert result.api_token == "cloud-token"
    assert result.auth_type == "basic"

    # Validated against API v3
    call_url = mock_get.call_args[0][0]
    assert "/rest/api/3/myself" in call_url


# --- _setup_jira: Server flow ---


@patch("agentix.config.commands.requests.get")
@patch("agentix.config.commands.click")
def test_setup_jira_server(mock_click, mock_get):
    """Server URL prompts for PAT only, validates with v2 + Bearer."""
    mock_click.prompt.side_effect = [
        "https://jira.company.com",  # base_url
        "my-pat-token",              # PAT
    ]
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"displayName": "Server User"}
    mock_get.return_value = mock_resp

    result = _setup_jira()

    assert result.base_url == "https://jira.company.com"
    assert result.email == ""
    assert result.api_token == "my-pat-token"
    assert result.auth_type == "bearer"

    # Validated against API v2 with Bearer
    call_url = mock_get.call_args[0][0]
    assert "/rest/api/2/myself" in call_url
    call_headers = mock_get.call_args[1].get("headers", {})
    assert call_headers.get("Authorization") == "Bearer my-pat-token"


# --- _setup_confluence ---


@patch("agentix.config.commands.requests.get")
@patch("agentix.config.commands.click")
def test_setup_confluence_dc(mock_click, mock_get):
    """DC/Server Confluence prompts for URL + PAT and validates."""
    mock_click.prompt.side_effect = [
        "https://confluence.company.com",  # base_url
        "confluence-pat",                   # PAT
    ]
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"displayName": "Conf User"}
    mock_get.return_value = mock_resp

    result = _setup_confluence()

    assert result.base_url == "https://confluence.company.com"
    assert result.email == ""
    assert result.api_token == "confluence-pat"
    assert result.auth_type == "bearer"

    # Validated with Bearer auth
    call_url = mock_get.call_args[0][0]
    assert "/rest/api/user/current" in call_url
    call_headers = mock_get.call_args[1].get("headers", {})
    assert call_headers.get("Authorization") == "Bearer confluence-pat"


@patch("agentix.config.commands.requests.get")
@patch("agentix.config.commands.click")
def test_setup_confluence_cloud(mock_click, mock_get):
    """Cloud Confluence prompts for URL + email + token and validates."""
    mock_click.prompt.side_effect = [
        "https://co.atlassian.net/wiki",  # base_url
        "u@co.com",                        # email
        "cloud-tok",                        # API token
    ]
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.json.return_value = {"displayName": "Cloud User"}
    mock_get.return_value = mock_resp

    result = _setup_confluence()

    assert result.base_url == "https://co.atlassian.net/wiki"
    assert result.api_token == "cloud-tok"
    assert result.auth_type == "basic"
    assert result.email == "u@co.com"

    # Validated with Basic auth
    call_url = mock_get.call_args[0][0]
    assert "/rest/api/user/current" in call_url


@patch("agentix.config.commands.requests.get")
@patch("agentix.config.commands.click")
def test_setup_confluence_validation_failure(mock_click, mock_get):
    """Confluence setup continues even when validation fails."""
    mock_click.prompt.side_effect = [
        "https://confluence.company.com",
        "bad-pat",
    ]
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 401
    mock_get.return_value = mock_resp

    result = _setup_confluence()

    assert result.base_url == "https://confluence.company.com"
    assert result.api_token == "bad-pat"


# --- _setup_bitbucket ---


@patch("agentix.config.commands.requests.get")
@patch("agentix.config.commands.click")
def test_setup_bitbucket(mock_click, mock_get):
    """Bitbucket setup prompts for URL + PAT and validates."""
    mock_click.prompt.side_effect = [
        "https://bitbucket.company.com",  # base_url
        "bb-pat-token",                    # PAT
    ]
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_get.return_value = mock_resp

    result = _setup_bitbucket()

    assert result.base_url == "https://bitbucket.company.com"
    assert result.api_token == "bb-pat-token"
    assert result.auth_type == "bearer"

    # Validated with Bearer auth against REST API 1.0
    call_url = mock_get.call_args[0][0]
    assert "/rest/api/1.0/users" in call_url
    call_headers = mock_get.call_args[1].get("headers", {})
    assert call_headers.get("Authorization") == "Bearer bb-pat-token"


@patch("agentix.config.commands.requests.get")
@patch("agentix.config.commands.click")
def test_setup_bitbucket_validation_failure(mock_click, mock_get):
    """Bitbucket setup continues even when validation fails."""
    mock_click.prompt.side_effect = [
        "https://bitbucket.company.com",
        "bad-pat",
    ]
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 401
    mock_get.return_value = mock_resp

    result = _setup_bitbucket()

    assert result.base_url == "https://bitbucket.company.com"
    assert result.api_token == "bad-pat"


@patch("agentix.config.commands.click")
@patch("polarion.v3.client.PolarionClient")
def test_setup_polarion_verify_ssl_enabled_by_default(mock_client_cls, mock_click):
    """Polarion setup should default to SSL verification and persist the choice."""
    mock_click.prompt.side_effect = [
        "https://polarion.company.com/polarion",
        "test-user",
        "test-token",
    ]
    mock_click.confirm.return_value = True

    mock_client = MagicMock()
    mock_client.healthcheck.return_value = {"ok": True}
    mock_client_cls.return_value = mock_client

    result = _setup_polarion()

    assert result.verify_ssl is True
    mock_client_cls.assert_called_once_with(
        url="https://polarion.company.com/polarion",
        username="test-user",
        token="test-token",
        verify_ssl=True,
    )


def test_polarion_verify_ssl_defaults_to_true_in_models():
    cfg = AgentixConfig.from_dict({"profiles": {"p": {"polarion": {}}}})
    assert cfg.profiles["p"].polarion.verify_ssl is True


@patch("agentix.config.commands.requests.get")
@patch("agentix.config.commands.click")
def test_setup_jira_strict_validation_raises_on_http_error(mock_click, mock_get):
    mock_click.prompt.side_effect = [
        "https://company.atlassian.net",
        "user@company.com",
        "bad-token",
    ]
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 401
    mock_get.return_value = mock_resp

    with pytest.raises(ConfigError):
        _setup_jira(strict=True)


@patch("agentix.config.commands.click")
@patch("polarion.v3.client.PolarionClient")
def test_setup_polarion_strict_validation_raises_on_failed_health(mock_client_cls, mock_click):
    mock_click.prompt.side_effect = [
        "https://polarion.company.com/polarion",
        "test-user",
        "test-token",
    ]
    mock_click.confirm.return_value = True

    mock_client = MagicMock()
    mock_client.healthcheck.return_value = {"ok": False, "error": "unauthorized"}
    mock_client_cls.return_value = mock_client

    with pytest.raises(ConfigError):
        _setup_polarion(strict=True)
