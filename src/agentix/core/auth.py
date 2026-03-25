"""Authentication resolution for agentix."""

import os
from dataclasses import dataclass
from typing import Optional, cast

from .exceptions import AuthenticationError

from agentix.config.manager import ConfigManager


@dataclass
class ServiceAuth:
    """Resolved authentication credentials for a service."""

    base_url: str
    user: str
    token: str
    auth_type: str = "basic"  # "basic" or "bearer"


# Maps service name -> (env var prefix, user field name, config attribute names)
_SERVICE_ENV = {
    "jira": ("AGENTIX_JIRA", "email", ("base_url", "email", "api_token")),
    "confluence": ("AGENTIX_CONFLUENCE", "email", ("base_url", "email", "api_token")),
    "jenkins": ("AGENTIX_JENKINS", "username", ("base_url", "username", "api_token")),
    "bitbucket": ("AGENTIX_BITBUCKET", "username", ("base_url", "username", "api_token")),
    "polarion": ("AGENTIX_POLARION", "username", ("base_url", "username", "api_token")),
}


def resolve_auth(
    service: str,
    config_manager: ConfigManager,
    profile_name: Optional[str] = None,
    base_url: Optional[str] = None,
    user: Optional[str] = None,
    token: Optional[str] = None,
) -> ServiceAuth:
    """Resolve auth credentials: CLI flag -> env var -> config file -> error."""
    if service not in _SERVICE_ENV:
        raise AuthenticationError(f"Unknown service: {service}")

    env_prefix, user_field, config_attrs = _SERVICE_ENV[service]
    base_attr, user_attr, token_attr = config_attrs

    # Load config profile values
    profile = config_manager.config.get_profile(profile_name)
    service_config = getattr(profile, service)

    # Resolve each field: CLI flag -> env var -> config
    resolved_url = (
        base_url
        or os.environ.get(f"{env_prefix}_BASE_URL")
        or getattr(service_config, base_attr, "")
    )
    resolved_user = (
        user
        or os.environ.get(f"{env_prefix}_{user_field.upper()}")
        or getattr(service_config, user_attr, "")
    )
    resolved_token = (
        token
        or os.environ.get(f"{env_prefix}_API_TOKEN")
        or getattr(service_config, token_attr, "")
    )
    resolved_auth_type = str(
        os.environ.get(f"{env_prefix}_AUTH_TYPE")
        or getattr(service_config, "auth_type", "basic")
    )

    # Validate
    missing = []
    if not resolved_url:
        missing.append(f"base_url (set via --base-url, {env_prefix}_BASE_URL, or config)")
    if not resolved_user and resolved_auth_type == "basic":
        missing.append(
            f"{user_field} (set via --{user_field}, {env_prefix}_{user_field.upper()}, or config)"
        )
    if not resolved_token:
        missing.append(f"api_token (set via --token, {env_prefix}_API_TOKEN, or config)")

    if missing:
        raise AuthenticationError(
            f"Missing {service} credentials:\n  " + "\n  ".join(missing)
            + "\n\nRun 'agentix config init' to set up credentials."
        )

    return ServiceAuth(
        base_url=cast(str, resolved_url),
        user=cast(str, resolved_user),
        token=cast(str, resolved_token),
        auth_type=resolved_auth_type,
    )
