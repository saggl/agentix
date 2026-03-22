"""Tests for auto-update functionality."""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from agentix import __version__
from agentix.config.models import AgentixConfig, Defaults
from agentix.core.auto_update import (
    _get_cache_path,
    _read_cache,
    _write_cache,
    auto_update_if_needed,
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
    monkeypatch.setattr("agentix.core.auto_update.CACHE_FILE", cache_file)
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
    """Test version comparison logic."""

    def test_is_update_available_newer_version(self):
        """Test that newer version is detected."""
        assert is_update_available("0.1.0", "0.2.0") is True

    def test_is_update_available_same_version(self):
        """Test that same version returns False."""
        assert is_update_available("0.2.0", "0.2.0") is False

    def test_is_update_available_older_version(self):
        """Test that older version returns False."""
        assert is_update_available("0.2.0", "0.1.0") is False

    def test_is_update_available_patch_version(self):
        """Test patch version comparison."""
        assert is_update_available("0.2.0", "0.2.1") is True
        assert is_update_available("0.2.1", "0.2.0") is False

    def test_is_update_available_invalid_version(self):
        """Test handling of invalid version strings."""
        assert is_update_available("invalid", "0.2.0") is False
        assert is_update_available("0.2.0", "invalid") is False


class TestInstallationDetection:
    """Test installation method detection."""

    @patch("agentix.core.auto_update.subprocess.run")
    def test_detect_uv_installation(self, mock_run):
        """Test detecting uv tool installation."""
        mock_run.return_value = Mock(
            returncode=0, stdout="agentix-cli v0.2.0\nother-tool v1.0.0"
        )
        assert detect_installation_method() == "uv"

    @patch("agentix.core.auto_update.subprocess.run")
    def test_detect_pip_installation_not_in_list(self, mock_run):
        """Test detecting pip when tool not in uv list."""
        mock_run.return_value = Mock(returncode=0, stdout="other-tool v1.0.0")
        assert detect_installation_method() == "pip"

    @patch("agentix.core.auto_update.subprocess.run")
    def test_detect_pip_installation_uv_not_found(self, mock_run):
        """Test detecting pip when uv command not found."""
        mock_run.side_effect = FileNotFoundError()
        assert detect_installation_method() == "pip"

    @patch("agentix.core.auto_update.subprocess.run")
    def test_detect_pip_installation_uv_fails(self, mock_run):
        """Test detecting pip when uv command fails."""
        mock_run.return_value = Mock(returncode=1)
        assert detect_installation_method() == "pip"

    @patch("agentix.core.auto_update.subprocess.run")
    def test_detect_pip_installation_timeout(self, mock_run):
        """Test detecting pip when uv command times out."""
        mock_run.side_effect = subprocess.TimeoutExpired("uv", 5)
        assert detect_installation_method() == "pip"


class TestCacheManagement:
    """Test cache file management."""

    def test_should_check_for_update_no_cache(self, mock_cache_file):
        """Test that check is needed when cache doesn't exist."""
        assert should_check_for_update() is True

    def test_should_check_for_update_fresh_cache(self, fresh_cache):
        """Test that check is skipped when cache is fresh."""
        assert should_check_for_update() is False

    def test_should_check_for_update_stale_cache(self, stale_cache):
        """Test that check is needed when cache is stale."""
        assert should_check_for_update() is True

    def test_should_check_for_update_malformed_cache(self, malformed_cache):
        """Test that check is needed when cache is malformed."""
        assert should_check_for_update() is True
        # Verify malformed cache was deleted
        assert not malformed_cache.exists()

    def test_read_cache_missing_file(self, mock_cache_file):
        """Test reading non-existent cache file."""
        result = _read_cache()
        assert result is None

    def test_read_cache_valid_file(self, fresh_cache):
        """Test reading valid cache file."""
        result = _read_cache()
        assert result is not None
        assert "last_check" in result
        assert "latest_version" in result
        assert "current_version" in result

    def test_read_cache_malformed_file(self, malformed_cache):
        """Test reading malformed cache file."""
        result = _read_cache()
        assert result is None
        # Verify malformed cache was deleted
        assert not malformed_cache.exists()

    def test_write_cache(self, mock_cache_file):
        """Test writing cache file."""
        _write_cache("0.3.0")
        assert mock_cache_file.exists()

        data = json.loads(mock_cache_file.read_text(encoding="utf-8"))
        assert data["latest_version"] == "0.3.0"
        assert data["current_version"] == __version__
        assert "last_check" in data

    def test_write_cache_creates_directory(self, tmp_path, monkeypatch):
        """Test that cache directory is created if it doesn't exist."""
        cache_dir = tmp_path / "new_dir"
        cache_file = cache_dir / ".update_check"
        monkeypatch.setattr("agentix.core.auto_update.CACHE_FILE", cache_file)

        _write_cache("0.3.0")
        assert cache_file.exists()


class TestPyPIAPI:
    """Test PyPI API interaction."""

    @patch("agentix.core.auto_update.requests.get")
    def test_get_latest_version_success(self, mock_get):
        """Test successful PyPI API response."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "info": {"version": "0.3.0"}
        }
        mock_get.return_value = mock_response

        result = get_latest_version()
        assert result == "0.3.0"
        mock_get.assert_called_once()

    @patch("agentix.core.auto_update.requests.get")
    def test_get_latest_version_network_error(self, mock_get):
        """Test handling of network errors."""
        mock_get.side_effect = requests.RequestException("Network error")

        result = get_latest_version()
        assert result is None

    @patch("agentix.core.auto_update.requests.get")
    def test_get_latest_version_timeout(self, mock_get):
        """Test handling of request timeout."""
        mock_get.side_effect = requests.Timeout("Request timeout")

        result = get_latest_version()
        assert result is None

    @patch("agentix.core.auto_update.requests.get")
    def test_get_latest_version_invalid_response(self, mock_get):
        """Test handling of invalid JSON response."""
        mock_response = Mock()
        mock_response.json.return_value = {}  # Missing 'info' key
        mock_get.return_value = mock_response

        result = get_latest_version()
        assert result is None


class TestSubprocessExecution:
    """Test subprocess execution for upgrades."""

    @patch("agentix.core.auto_update.subprocess.Popen")
    def test_perform_upgrade_uv(self, mock_popen):
        """Test that upgrade uses correct uv command."""
        perform_upgrade("uv")

        mock_popen.assert_called_once_with(
            ["uv", "tool", "upgrade", "agentix-cli"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    @patch("agentix.core.auto_update.subprocess.Popen")
    def test_perform_upgrade_pip(self, mock_popen):
        """Test that upgrade uses correct pip command."""
        perform_upgrade("pip")

        mock_popen.assert_called_once_with(
            [sys.executable, "-m", "pip", "install", "--upgrade", "agentix-cli"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    @patch("agentix.core.auto_update.subprocess.Popen")
    def test_perform_upgrade_defaults_to_uv(self, mock_popen):
        """Test that upgrade defaults to uv when no method specified."""
        perform_upgrade()

        mock_popen.assert_called_once_with(
            ["uv", "tool", "upgrade", "agentix-cli"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    @patch("agentix.core.auto_update.subprocess.Popen")
    def test_perform_upgrade_handles_error(self, mock_popen):
        """Test that upgrade handles subprocess errors gracefully."""
        mock_popen.side_effect = OSError("Command not found")

        # Should not raise exception
        perform_upgrade("uv")


class TestConfiguration:
    """Test configuration-based control of auto-update."""

    @patch("agentix.core.auto_update.should_check_for_update")
    @patch("agentix.core.auto_update.get_latest_version")
    @patch("agentix.core.auto_update.perform_upgrade")
    def test_auto_update_disabled_via_config(
        self, mock_upgrade, mock_get_version, mock_should_check
    ):
        """Test that auto-update respects config setting."""
        config = AgentixConfig()
        config.defaults.auto_update = False

        auto_update_if_needed(config)

        # Should not check for updates or perform upgrade
        mock_should_check.assert_not_called()
        mock_get_version.assert_not_called()
        mock_upgrade.assert_not_called()

    @patch("agentix.core.auto_update.should_check_for_update")
    @patch("agentix.core.auto_update.get_latest_version")
    @patch("agentix.core.auto_update.perform_upgrade")
    def test_auto_update_enabled_via_config(
        self, mock_upgrade, mock_get_version, mock_should_check
    ):
        """Test that auto-update works when enabled in config."""
        config = AgentixConfig()
        config.defaults.auto_update = True

        mock_should_check.return_value = True
        mock_get_version.return_value = "0.3.0"

        auto_update_if_needed(config)

        # Should check for updates
        mock_should_check.assert_called_once()
        mock_get_version.assert_called_once()

    @patch.dict(os.environ, {"AGENTIX_AUTO_UPDATE": "false"})
    @patch("agentix.core.auto_update.should_check_for_update")
    @patch("agentix.core.auto_update.get_latest_version")
    @patch("agentix.core.auto_update.perform_upgrade")
    def test_auto_update_disabled_via_env_var(
        self, mock_upgrade, mock_get_version, mock_should_check
    ):
        """Test that env var disables auto-update."""
        config = AgentixConfig()
        config.defaults.auto_update = True  # Config says enabled

        auto_update_if_needed(config)

        # Should not check (env var takes precedence)
        mock_should_check.assert_not_called()
        mock_get_version.assert_not_called()
        mock_upgrade.assert_not_called()

    @patch.dict(os.environ, {"AGENTIX_AUTO_UPDATE": "true"})
    @patch("agentix.core.auto_update.should_check_for_update")
    @patch("agentix.core.auto_update.get_latest_version")
    @patch("agentix.core.auto_update.perform_upgrade")
    def test_auto_update_enabled_via_env_var(
        self, mock_upgrade, mock_get_version, mock_should_check
    ):
        """Test that env var enables auto-update."""
        config = AgentixConfig()
        config.defaults.auto_update = True

        mock_should_check.return_value = True
        mock_get_version.return_value = "0.3.0"

        auto_update_if_needed(config)

        # Should check for updates
        mock_should_check.assert_called_once()
        mock_get_version.assert_called_once()

    @patch.dict(os.environ, {"AGENTIX_AUTO_UPDATE": "0"})
    @patch("agentix.core.auto_update.should_check_for_update")
    def test_auto_update_env_var_variations(self, mock_should_check):
        """Test various env var values for disabling."""
        config = AgentixConfig()
        config.defaults.auto_update = True

        for value in ["false", "0", "no", "off"]:
            with patch.dict(os.environ, {"AGENTIX_AUTO_UPDATE": value}):
                auto_update_if_needed(config)
                mock_should_check.assert_not_called()


class TestIntegration:
    """Test end-to-end auto-update workflow."""

    @patch("agentix.core.auto_update.detect_installation_method")
    @patch("agentix.core.auto_update.should_check_for_update")
    @patch("agentix.core.auto_update.get_latest_version")
    @patch("agentix.core.auto_update.perform_upgrade")
    @patch("agentix.core.auto_update._write_cache")
    def test_auto_update_if_needed_update_available(
        self,
        mock_write_cache,
        mock_upgrade,
        mock_get_version,
        mock_should_check,
        mock_detect,
    ):
        """Test full workflow when update is available."""
        config = AgentixConfig()
        config.defaults.auto_update = True

        mock_should_check.return_value = True
        mock_get_version.return_value = "0.3.0"
        mock_detect.return_value = "uv"

        with patch("agentix.core.auto_update.__version__", "0.2.0"):
            auto_update_if_needed(config)

        # Should check, fetch version, write cache, detect method, and upgrade
        mock_should_check.assert_called_once()
        mock_get_version.assert_called_once()
        mock_write_cache.assert_called_once_with("0.3.0")
        mock_detect.assert_called_once()
        mock_upgrade.assert_called_once_with("uv")

    @patch("agentix.core.auto_update.should_check_for_update")
    @patch("agentix.core.auto_update.get_latest_version")
    @patch("agentix.core.auto_update.perform_upgrade")
    @patch("agentix.core.auto_update._write_cache")
    def test_auto_update_if_needed_no_update_available(
        self, mock_write_cache, mock_upgrade, mock_get_version, mock_should_check
    ):
        """Test workflow when no update is available."""
        config = AgentixConfig()
        config.defaults.auto_update = True

        mock_should_check.return_value = True
        mock_get_version.return_value = __version__  # Same as current

        auto_update_if_needed(config)

        # Should check, fetch version, write cache, but not upgrade
        mock_should_check.assert_called_once()
        mock_get_version.assert_called_once()
        mock_write_cache.assert_called_once_with(__version__)
        mock_upgrade.assert_not_called()

    @patch("agentix.core.auto_update.should_check_for_update")
    @patch("agentix.core.auto_update.get_latest_version")
    @patch("agentix.core.auto_update.perform_upgrade")
    def test_auto_update_if_needed_cache_fresh(
        self, mock_upgrade, mock_get_version, mock_should_check
    ):
        """Test that fresh cache skips PyPI check."""
        config = AgentixConfig()
        config.defaults.auto_update = True

        mock_should_check.return_value = False  # Cache is fresh

        auto_update_if_needed(config)

        # Should check cache but not fetch or upgrade
        mock_should_check.assert_called_once()
        mock_get_version.assert_not_called()
        mock_upgrade.assert_not_called()

    @patch("agentix.core.auto_update.should_check_for_update")
    @patch("agentix.core.auto_update.get_latest_version")
    @patch("agentix.core.auto_update.perform_upgrade")
    def test_auto_update_if_needed_pypi_failure(
        self, mock_upgrade, mock_get_version, mock_should_check
    ):
        """Test graceful handling of PyPI API failure."""
        config = AgentixConfig()
        config.defaults.auto_update = True

        mock_should_check.return_value = True
        mock_get_version.return_value = None  # Simulate API failure

        auto_update_if_needed(config)

        # Should check but not upgrade on failure
        mock_should_check.assert_called_once()
        mock_get_version.assert_called_once()
        mock_upgrade.assert_not_called()

    @patch("agentix.core.auto_update.detect_installation_method")
    @patch("agentix.core.auto_update.should_check_for_update")
    @patch("agentix.core.auto_update.get_latest_version")
    @patch("agentix.core.auto_update.perform_upgrade")
    @patch("agentix.core.auto_update._write_cache")
    def test_auto_update_with_pip_installation(
        self,
        mock_write_cache,
        mock_upgrade,
        mock_get_version,
        mock_should_check,
        mock_detect,
    ):
        """Test auto-update detects pip and uses pip upgrade."""
        config = AgentixConfig()
        config.defaults.auto_update = True

        mock_should_check.return_value = True
        mock_get_version.return_value = "0.3.0"
        mock_detect.return_value = "pip"

        with patch("agentix.core.auto_update.__version__", "0.2.0"):
            auto_update_if_needed(config)

        # Should detect method and pass to upgrade
        mock_detect.assert_called_once()
        mock_upgrade.assert_called_once_with("pip")
