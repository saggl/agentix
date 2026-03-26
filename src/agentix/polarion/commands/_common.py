"""Shared helpers for Polarion CLI commands."""

import importlib
from typing import Any, Callable, TypeVar

import click
import requests

from agentix.core.exceptions import (
    AgentixError,
    AuthenticationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

T = TypeVar("T")


def _get_client(ctx: click.Context):
    """Build Polarion client from resolved auth."""
    commands_pkg = importlib.import_module("agentix.polarion.commands")
    config_manager = ctx.obj["config_manager"]
    auth = commands_pkg.resolve_auth(
        "polarion",
        config_manager,
        profile_name=ctx.obj["profile"],
    )
    profile = config_manager.config.get_profile(ctx.obj["profile"])
    return commands_pkg.create_polarion_client(auth, verify_ssl=profile.polarion.verify_ssl)


def _map_polarion_error(error: Exception, operation: str) -> AgentixError:
    """Convert backend/transport exceptions into typed Agentix errors."""
    if isinstance(error, AgentixError):
        return error

    message = str(error).strip() or type(error).__name__
    lower = message.lower()

    if isinstance(error, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return NetworkError(f"Polarion network error during {operation}: {message}")

    if isinstance(error, requests.exceptions.SSLError):
        return NetworkError(
            f"Polarion SSL error during {operation}: {message}. "
            "Check certificates or set polarion.verify_ssl=false "
            "if you intentionally use self-signed certs."
        )

    if "401" in lower or "403" in lower or "unauthorized" in lower or "forbidden" in lower:
        return AuthenticationError(f"Polarion authentication failed during {operation}: {message}")

    if "404" in lower or "not found" in lower:
        return NotFoundError(f"Polarion resource not found during {operation}: {message}")

    if "429" in lower or "rate limit" in lower or "too many requests" in lower:
        return RateLimitError(f"Polarion rate limit exceeded during {operation}: {message}")

    if "500" in lower or "502" in lower or "503" in lower or "504" in lower:
        return ServerError(f"Polarion server error during {operation}: {message}")

    if "400" in lower or "invalid" in lower or "validation" in lower:
        return ValidationError(f"Polarion rejected request during {operation}: {message}")

    return AgentixError(f"Polarion API error during {operation}: {message}")


def _call(operation: str, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a Polarion SDK call and normalize errors for CLI output/exit codes."""
    try:
        return func(*args, **kwargs)
    except Exception as error:  # noqa: BLE001
        raise _map_polarion_error(error, operation) from error
