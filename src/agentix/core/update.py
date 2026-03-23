"""Update support functionality for agentix CLI."""

import json
import logging
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests
from packaging import version

from agentix import __version__
from agentix.config.models import get_config_dir

logger = logging.getLogger(__name__)

# Cache file location
CACHE_FILE = get_config_dir() / ".update_check"

# Cache validity period (24 hours)
CACHE_VALIDITY = timedelta(hours=24)

# PyPI JSON API endpoint
PYPI_API_URL = "https://pypi.org/pypi/agentix-cli/json"

# Request timeout in seconds
REQUEST_TIMEOUT = 5


def _get_cache_path() -> Path:
    """Get the path to the update check cache file."""
    return CACHE_FILE


def _read_cache() -> Optional[dict]:
    """Read the cache file if it exists and is valid JSON."""
    try:
        if not CACHE_FILE.exists():
            return None
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.debug(f"Failed to read cache file: {e}")
        # Delete corrupted cache file
        try:
            CACHE_FILE.unlink()
        except OSError:
            pass
        return None


def _write_cache(latest_version: str) -> None:
    """Write version check results to cache file."""
    try:
        cache_dir = CACHE_FILE.parent
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_data = {
            "last_check": datetime.now(timezone.utc).isoformat(),
            "latest_version": latest_version,
            "current_version": __version__,
        }

        CACHE_FILE.write_text(json.dumps(cache_data, indent=2), encoding="utf-8")
    except OSError as e:
        logger.debug(f"Failed to write cache file: {e}")


def should_check_for_update() -> bool:
    """Check if we should query PyPI based on cache age.

    Returns:
        True if cache is stale or missing, False if cache is fresh.
    """
    cache = _read_cache()
    if not cache:
        return True

    try:
        last_check = datetime.fromisoformat(cache["last_check"])
        # Make sure last_check has timezone info
        if last_check.tzinfo is None:
            last_check = last_check.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age = now - last_check
        return age > CACHE_VALIDITY
    except (KeyError, ValueError) as e:
        logger.debug(f"Invalid cache data: {e}")
        return True


def get_latest_version() -> Optional[str]:
    """Fetch latest version from PyPI.

    Returns:
        Latest version string, or None on error.
    """
    try:
        response = requests.get(PYPI_API_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        latest = data["info"]["version"]
        return latest
    except (requests.RequestException, KeyError, ValueError) as e:
        logger.debug(f"Failed to fetch latest version from PyPI: {e}")
        return None


def is_update_available(current: str, latest: str) -> bool:
    """Compare versions using semantic versioning.

    Args:
        current: Current version string
        latest: Latest version string

    Returns:
        True if latest is newer than current, False otherwise.
    """
    try:
        current_ver = version.parse(current)
        latest_ver = version.parse(latest)
        return latest_ver > current_ver
    except version.InvalidVersion as e:
        logger.debug(f"Invalid version format: {e}")
        return False


def detect_installation_method() -> str:
    """Detect if agentix was installed via uv tool or pip.

    Strategy:
    1. Try to run 'uv tool list'
    2. Check if 'agentix-cli' appears in output
    3. If yes -> installed via uv tool
    4. If no or command fails -> assume pip

    Returns:
        "uv" if installed via uv tool install, "pip" otherwise
    """
    try:
        result = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and "agentix-cli" in result.stdout:
            return "uv"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as e:
        logger.debug(f"Could not detect uv tool installation: {e}")

    return "pip"


def perform_upgrade(method: str = "uv") -> None:
    """Execute upgrade in detached subprocess using appropriate method.

    Args:
        method: Installation method ("uv" or "pip")

    This runs the upgrade in the background without blocking the CLI.
    """
    if method == "uv":
        cmd = ["uv", "tool", "upgrade", "agentix-cli"]
    else:  # pip
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "agentix-cli"]

    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        logger.debug(f"Started background upgrade process using {method}")
    except (OSError, subprocess.SubprocessError) as e:
        logger.debug(f"Failed to start upgrade process with {method}: {e}")


