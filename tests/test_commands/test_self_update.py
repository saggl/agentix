"""Tests for self-update commands."""

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from agentix.cli import cli


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


def test_self_update_status(runner):
    with patch("agentix.commands.self_update._read_cache") as mock_read:
        mock_read.return_value = {
            "latest_version": "9.9.9",
            "last_check": "2026-01-01T00:00:00+00:00",
        }

        result = runner.invoke(cli, ["self-update", "status"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["current_version"]
    assert data["latest_cached_version"] == "9.9.9"
    assert "update_available" in data


def test_self_update_check_live(runner):
    with patch("agentix.commands.self_update.get_latest_version") as mock_latest, patch(
        "agentix.commands.self_update._write_cache"
    ) as mock_write:
        mock_latest.return_value = "9.9.9"

        result = runner.invoke(cli, ["self-update", "check"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["latest_version"] == "9.9.9"
    assert data["data"]["source"] == "pypi"
    mock_write.assert_called_once_with("9.9.9")


def test_self_update_check_cache(runner):
    with patch("agentix.commands.self_update._read_cache") as mock_read, patch(
        "agentix.commands.self_update.get_latest_version"
    ) as mock_latest:
        mock_read.return_value = {"latest_version": "1.2.3"}

        result = runner.invoke(cli, ["self-update", "check", "--use-cache"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["latest_version"] == "1.2.3"
    assert data["data"]["source"] == "cache"
    mock_latest.assert_not_called()


def test_self_update_apply_auto(runner):
    with patch("agentix.commands.self_update.detect_installation_method") as mock_detect, patch(
        "agentix.commands.self_update.perform_upgrade"
    ) as mock_upgrade:
        mock_detect.return_value = "uv"

        result = runner.invoke(cli, ["self-update", "apply"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["method"] == "uv"
    mock_upgrade.assert_called_once_with("uv")
