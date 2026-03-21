"""Configuration manager for agentix."""

import os
import stat
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import tomli_w

from agentix.core.exceptions import ConfigError

from .models import AgentixConfig, get_config_path


class ConfigManager:
    """Load, save, and query agentix configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or get_config_path()
        self._config: Optional[AgentixConfig] = None

    @property
    def config(self) -> AgentixConfig:
        if self._config is None:
            self._config = self.load()
        return self._config

    def exists(self) -> bool:
        return self.config_path.exists()

    def load(self) -> AgentixConfig:
        if not self.config_path.exists():
            return AgentixConfig()
        try:
            data = tomllib.loads(self.config_path.read_text(encoding="utf-8"))
            return AgentixConfig.from_dict(data)
        except Exception as e:
            raise ConfigError(
                f"Failed to load config from {self.config_path}: {e}"
            ) from e

    def save(self, config: Optional[AgentixConfig] = None) -> None:
        cfg = config or self.config
        config_dir = self.config_path.parent
        config_dir.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions on directory
        if sys.platform != "win32":
            os.chmod(config_dir, stat.S_IRWXU)

        self.config_path.write_text(
            tomli_w.dumps(cfg.to_dict()), encoding="utf-8"
        )

        # Set restrictive permissions on file
        if sys.platform != "win32":
            os.chmod(self.config_path, stat.S_IRUSR | stat.S_IWUSR)

        self._config = cfg

    def get_value(self, key: str) -> Any:
        """Get a config value by dotted key path (e.g., 'profiles.work.jira.base_url')."""
        parts = key.split(".")
        data = self.config.to_dict()
        for part in parts:
            if isinstance(data, dict) and part in data:
                data = data[part]
            else:
                raise ConfigError(f"Config key not found: {key}")
        return data

    def set_value(self, key: str, value: str) -> None:
        """Set a config value by dotted key path."""
        parts = key.split(".")
        data = self.config.to_dict()

        # Navigate to parent
        current = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

        self._config = AgentixConfig.from_dict(data)
        self.save()

    def mask_tokens(self) -> dict:
        """Return config dict with tokens/secrets masked."""
        data = self.config.to_dict()
        secret_keys = {"api_token", "token", "password", "secret"}

        def _mask(d: Any) -> Any:
            if isinstance(d, dict):
                return {
                    k: ("***" if k in secret_keys and v else _mask(v))
                    for k, v in d.items()
                }
            if isinstance(d, list):
                return [_mask(i) for i in d]
            return d

        return _mask(data)
