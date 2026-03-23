"""Tests for update core functionality."""

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import pytest
import requests

from agentix import __version__
from agentix.core.update import (
    _read_cache,
    _write_cache,
    detect_installation_method,
    get_latest_version,
    is_update_available,
    perform_upgrade,
    should_check_for_update,
)


@pytest.fixture
def mock_cache_file(tmp_path, monkeypatch):
    """Mock the cache file location to use a temporary directory."""
    cache_file = tmp_path / ".update_check"
    monkeypatch.setattr("agentix.core.update.CACHE_FILE", cache_file)
    return cache_file


@pytest.fixture
def fresh_cache(mock_cache_file):
    """Create a fresh cache file (less than 24 hours old)."""
    cache_data = {
        "last_check": datetime.now(timezone.utc).isoformat(),
        "latest_version": "0.2.0",
        "current_version": "0.2.0",
    }
    mock_cache_file.write_text(json.dumps(cache_data), encoding="utf-8")
    return mock_cache_file


@pytest.fixture
def stale_cache(mock_cache_file):
    """Create a stale cache file (more than 24 hours old)."""
    old_time = datetime.now(timezone.utc) - timedelta(hours=25)
    cache_data = {
        "last_check": old_time.isoformat(),
        "latest_version": "0.1.0",
        "current_version": "0.1.0",
    }
    mock_cache_file.write_text(json.dumps(cache_data), encoding="utf-8")
    return mock_cache_file


@pytest.fixture
def malformed_cache(mock_cache_file):
    """Create a malformed cache file."""
    mock_cache_file.write_text("not valid json", encoding="utf-8")
    return mock_cache_file


class TestVersionComparison:
    def test_is_update_available_newer_version(self):
        assert is_update_available("0.1.0", "0.2.0") is True

    def test_is_update_available_same_version(self):
        assert is_update_available("0.2.0", "0.2.0") is False

    def test_is_update_available_older_version(self):
        assert is_update_available("0.2.0", "0.1.0") is False

    def test_is_update_available_patch_version(self):
        assert is_update_available("0.2.0", "0.2.1") is True
        assert is_update_available("0.2.1", "0.2.0") is False

    def test_is_update_available_invalid_version(self):
        assert is_update_available("invalid", "0.2.0") is False
        assert is_update_available("0.2.0", "invalid") is False


class TestInstallationDetection:
    @patch("agentix.core.update.subprocess.run")
    def test_detect_uv_installation(self, mock_run):
        mock_run.return_value = Mock(
            returncode=0, stdout="agentix-cli v0.2.0\nother-tool v1.0.0"
        )
        assert detect_installation_method() == "uv"

    @patch("agentix.core.update.subprocess.run")
    def test_detect_pip_installation_not_in_list(self, mock_run):
        mock_run.return_value = Mock(returncode=0, stdout="other-tool v1.0.0")
        assert detect_installation_method() == "pip"

    @patch("agentix.core.update.subprocess.run")
    def test_detect_pip_installation_uv_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        assert detect_installation_method() == "pip"

    @patch("agentix.core.update.subprocess.run")
    def test_detect_pip_installation_uv_fails(self, mock_run):
        mock_run.return_value = Mock(returncode=1)
        assert detect_installation_method() == "pip"

    @patch("agentix.core.update.subprocess.run")
    def test_detect_pip_installation_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired("uv", 5)
        assert detect_installation_method() == "pip"


class TestCacheManagement:
    def test_should_check_for_update_no_cache(self, mock_cache_file):
        assert should_check_for_update() is True

    def test_should_check_for_update_fresh_cache(self, fresh_cache):
        assert should_check_for_update() is False

    def test_should_check_for_update_stale_cache(self, stale_cache):
        assert should_check_for_update() is True

    def test_should_check_for_update_malformed_cache(self, malformed_cache):
        assert should_check_for_update() is True
        assert not malformed_cache.exists()

    def test_read_cache_missing_file(self, mock_cache_file):
        result = _read_cache()
        assert result is None

    def test_read_cache_valid_file(self, fresh_cache):
        result = _read_cache()
        assert result is not None
        assert "last_check" in result
        assert "latest_version" in result
        assert "current_version" in result

    def test_read_cache_malformed_file(self, malformed_cache):
        result = _read_cache()
        assert result is None
        assert not malformed_cache.exists()

    def test_write_cache(self, mock_cache_file):
        _write_cache("0.3.0")
        assert mock_cache_file.exists()

        data = json.loads(mock_cache_file.read_text(encoding="utf-8"))
        assert data["latest_version"] == "0.3.0"
        assert data["current_version"] == __version__
        assert "last_check" in data

    def test_write_cache_creates_directory(self, tmp_path, monkeypatch):
        cache_dir = tmp_path / "new_dir"
        cache_file = cache_dir / ".update_check"
        monkeypatch.setattr("agentix.core.update.CACHE_FILE", cache_file)

        _write_cache("0.3.0")
        assert cache_file.exists()


class TestPyPIAPI:
    @patch("agentix.core.update.requests.get")
    def test_get_latest_version_success(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "info": {"version": "0.3.0"}
        }
        mock_get.return_value = mock_response

        result = get_latest_version()
        assert result == "0.3.0"
        mock_get.assert_called_once()

    @patch("agentix.core.update.requests.get")
    def test_get_latest_version_network_error(self, mock_get):
        mock_get.side_effect = requests.RequestException("Network error")

        result = get_latest_version()
        assert result is None

    @patch("agentix.core.update.requests.get")
    def test_get_latest_version_timeout(self, mock_get):
        mock_get.side_effect = requests.Timeout("Request timeout")

        result = get_latest_version()
        assert result is None

    @patch("agentix.core.update.requests.get")
    def test_get_latest_version_invalid_response(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        result = get_latest_version()
        assert result is None


class TestSubprocessExecution:
    @patch("agentix.core.update.subprocess.Popen")
    def test_perform_upgrade_uv(self, mock_popen):
        perform_upgrade("uv")

        mock_popen.assert_called_once_with(
            ["uv", "tool", "upgrade", "agentix-cli"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    @patch("agentix.core.update.subprocess.Popen")
    def test_perform_upgrade_pip(self, mock_popen):
        perform_upgrade("pip")

        mock_popen.assert_called_once_with(
            [sys.executable, "-m", "pip", "install", "--upgrade", "agentix-cli"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    @patch("agentix.core.update.subprocess.Popen")
    def test_perform_upgrade_defaults_to_uv(self, mock_popen):
        perform_upgrade()

        mock_popen.assert_called_once_with(
            ["uv", "tool", "upgrade", "agentix-cli"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    @patch("agentix.core.update.subprocess.Popen")
    def test_perform_upgrade_handles_error(self, mock_popen):
        mock_popen.side_effect = OSError("Command not found")

        perform_upgrade("uv")
