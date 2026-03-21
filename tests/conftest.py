"""Shared test fixtures."""

import pytest
from click.testing import CliRunner

from agentix.config.manager import ConfigManager
from agentix.config.models import (
    AgentixConfig,
    ConfluenceConfig,
    Defaults,
    JenkinsConfig,
    JiraConfig,
    Profile,
)


@pytest.fixture
def cli_runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture
def tmp_config(tmp_path):
    """Create a ConfigManager with a temporary config file."""
    config_path = tmp_path / "config.toml"
    cm = ConfigManager(config_path=config_path)
    config = AgentixConfig(
        default_profile="test",
        defaults=Defaults(format="json"),
        profiles={
            "test": Profile(
                jira=JiraConfig(
                    base_url="https://test.atlassian.net",
                    email="test@example.com",
                    api_token="jira-token-123",
                ),
                confluence=ConfluenceConfig(
                    base_url="https://test.atlassian.net/wiki",
                    email="test@example.com",
                    api_token="confluence-token-123",
                ),
                jenkins=JenkinsConfig(
                    base_url="https://jenkins.test.com",
                    username="testuser",
                    api_token="jenkins-token-123",
                ),
            )
        },
    )
    cm.save(config)
    return cm
