"""Tests for update command."""

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from agentix.cli import cli


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


def test_update_command_alias(runner):
    with patch("agentix.commands.update.detect_installation_method") as mock_detect, patch(
        "agentix.commands.update.perform_upgrade"
    ) as mock_upgrade:
        mock_detect.return_value = "pip"

        result = runner.invoke(cli, ["update"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["method"] == "pip"
    mock_upgrade.assert_called_once_with("pip")
