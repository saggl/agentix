"""Configuration manager for agentix."""

import os
import stat
import sys
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

import tomli_w

from agentix.core.exceptions import ConfigError

from .models import AgentixConfig, Profile, get_config_path


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
        except (OSError, tomllib.TOMLDecodeError, TypeError, ValueError) as e:
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

    def _split_key(self, key: str) -> list[str]:
        parts = [p.strip() for p in key.split(".") if p.strip()]
        if not parts:
            raise ConfigError("Config key cannot be empty")
        return parts

    def _coerce_value(self, raw_value: str, expected: Any, key: str) -> Any:
        """Coerce CLI string input to the expected target type."""
        if isinstance(expected, bool):
            lowered = raw_value.strip().lower()
            if lowered in {"true", "1", "yes", "on"}:
                return True
            if lowered in {"false", "0", "no", "off"}:
                return False
            raise ConfigError(
                f"Invalid boolean value for '{key}': {raw_value}. "
                "Use true/false, 1/0, yes/no, or on/off."
            )

        if isinstance(expected, int) and not isinstance(expected, bool):
            try:
                return int(raw_value)
            except ValueError as e:
                raise ConfigError(
                    f"Invalid integer value for '{key}': {raw_value}"
                ) from e

        if isinstance(expected, float):
            try:
                return float(raw_value)
            except ValueError as e:
                raise ConfigError(
                    f"Invalid float value for '{key}': {raw_value}"
                ) from e

        # Default string behavior for config fields in this project.
        return raw_value

    def _get_child(self, current: Any, part: str, key: str, *, create_profile: bool = False) -> Any:
        if isinstance(current, dict):
            if part not in current:
                if create_profile and current is self.config.profiles:
                    current[part] = Profile()
                else:
                    raise ConfigError(f"Config key not found: {key}")
            return current[part]

        if hasattr(current, part):
            return getattr(current, part)

        raise ConfigError(f"Config key not found: {key}")

    def get_value(self, key: str) -> Any:
        """Get a config value by dotted key path (e.g., 'profiles.work.jira.base_url')."""
        parts = self._split_key(key)
        current: Any = self.config

        for part in parts:
            current = self._get_child(current, part, key)

        # Return dict view for dataclass-like objects when useful for display.
        if hasattr(current, "to_dict") and callable(current.to_dict):
            return current.to_dict()
        return current

    def set_value(self, key: str, value: str) -> None:
        """Set a config value by dotted key path with type-aware coercion."""
        parts = self._split_key(key)
        current: Any = self.config

        # Navigate to parent node.
        for part in parts[:-1]:
            current = self._get_child(current, part, key, create_profile=True)

        leaf = parts[-1]

        if isinstance(current, dict):
            if leaf not in current:
                raise ConfigError(f"Config key not found: {key}")
            current[leaf] = self._coerce_value(value, current[leaf], key)
        else:
            if not hasattr(current, leaf):
                raise ConfigError(f"Config key not found: {key}")
            expected = getattr(current, leaf)
            setattr(current, leaf, self._coerce_value(value, expected, key))

        self.save(self.config)

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
