"""Tests for auth resolution."""


import pytest

from agentix.core.auth import resolve_auth
from agentix.core.exceptions import AuthenticationError


def test_resolve_from_config(tmp_config):
    auth = resolve_auth("jira", tmp_config, profile_name="test")
    assert auth.base_url == "https://test.atlassian.net"
    assert auth.user == "test@example.com"
    assert auth.token == "jira-token-123"


def test_resolve_jenkins_from_config(tmp_config):
    auth = resolve_auth("jenkins", tmp_config, profile_name="test")
    assert auth.base_url == "https://jenkins.test.com"
    assert auth.user == "testuser"
    assert auth.token == "jenkins-token-123"


def test_resolve_missing_credentials(tmp_config):
    # Create a profile with no jira config
    tmp_config.config.profiles["empty"] = __import__(
        "agentix.config.models", fromlist=["Profile"]
    ).Profile()
    with pytest.raises(AuthenticationError, match="Missing jira credentials"):
        resolve_auth("jira", tmp_config, profile_name="empty")


def test_env_var_override(tmp_config, monkeypatch):
    monkeypatch.setenv("AGENTIX_JIRA_BASE_URL", "https://env.atlassian.net")
    auth = resolve_auth("jira", tmp_config, profile_name="test")
    assert auth.base_url == "https://env.atlassian.net"
    # Other fields still from config
    assert auth.user == "test@example.com"


def test_cli_flag_override(tmp_config):
    auth = resolve_auth(
        "jira",
        tmp_config,
        profile_name="test",
        base_url="https://flag.atlassian.net",
        user="flag@user.com",
        token="flag-token",
    )
    assert auth.base_url == "https://flag.atlassian.net"
    assert auth.user == "flag@user.com"
    assert auth.token == "flag-token"


def test_unknown_service(tmp_config):
    with pytest.raises(AuthenticationError, match="Unknown service"):
        resolve_auth("unknown", tmp_config)
