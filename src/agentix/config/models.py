"""Configuration data models for agentix."""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class JiraConfig:
    base_url: str = ""
    email: str = ""
    api_token: str = ""
    auth_type: str = "basic"  # "basic" or "bearer"


@dataclass
class ConfluenceConfig:
    base_url: str = ""
    email: str = ""
    api_token: str = ""
    auth_type: str = "basic"  # "basic" or "bearer"


@dataclass
class JenkinsConfig:
    base_url: str = ""
    username: str = ""
    api_token: str = ""
    auth_type: str = "basic"  # "basic" or "bearer"


@dataclass
class BitbucketConfig:
    base_url: str = ""
    username: str = ""
    api_token: str = ""
    auth_type: str = "bearer"  # "basic" or "bearer"


@dataclass
class Profile:
    jira: JiraConfig = field(default_factory=JiraConfig)
    confluence: ConfluenceConfig = field(default_factory=ConfluenceConfig)
    jenkins: JenkinsConfig = field(default_factory=JenkinsConfig)
    bitbucket: BitbucketConfig = field(default_factory=BitbucketConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        return cls(
            jira=JiraConfig(**data.get("jira", {})),
            confluence=ConfluenceConfig(**data.get("confluence", {})),
            jenkins=JenkinsConfig(**data.get("jenkins", {})),
            bitbucket=BitbucketConfig(**data.get("bitbucket", {})),
        )

    def to_dict(self) -> Dict[str, Any]:
        result = {}
        for service_name in ("jira", "confluence", "jenkins", "bitbucket"):
            cfg = getattr(self, service_name)
            d = {k: v for k, v in cfg.__dict__.items() if v}
            if d:
                result[service_name] = d
        return result


@dataclass
class Defaults:
    format: str = "json"
    auto_update: bool = True


@dataclass
class AgentixConfig:
    default_profile: str = "default"
    defaults: Defaults = field(default_factory=Defaults)
    profiles: Dict[str, Profile] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentixConfig":
        profiles = {}
        for name, pdata in data.get("profiles", {}).items():
            profiles[name] = Profile.from_dict(pdata)
        return cls(
            default_profile=data.get("default_profile", "default"),
            defaults=Defaults(**data.get("defaults", {})),
            profiles=profiles,
        )

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"default_profile": self.default_profile}
        defaults_dict = {k: v for k, v in self.defaults.__dict__.items() if v}
        if defaults_dict:
            result["defaults"] = defaults_dict
        if self.profiles:
            result["profiles"] = {
                name: p.to_dict() for name, p in self.profiles.items()
            }
        return result

    def get_profile(self, name: Optional[str] = None) -> Profile:
        profile_name = name or self.default_profile
        if profile_name not in self.profiles:
            self.profiles[profile_name] = Profile()
        return self.profiles[profile_name]


def get_config_dir() -> Path:
    """Return the platform-appropriate config directory."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "agentix"


def get_config_path() -> Path:
    return get_config_dir() / "config.toml"
