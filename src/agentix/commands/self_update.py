"""Commands for explicit self-update operations."""

import os

import click

from agentix import __version__
from agentix.core.auto_update import (
    _read_cache,
    _write_cache,
    detect_installation_method,
    get_latest_version,
    is_update_available,
    perform_upgrade,
)
from agentix.core.exceptions import AgentixError


@click.group("self-update")
def self_update_group():
    """Check and apply agentix updates explicitly."""
    pass


@self_update_group.command("status")
@click.pass_context
def self_update_status(ctx):
    """Show update status using cached and local version info."""
    cache = _read_cache() or {}
    env_auto_update = os.environ.get("AGENTIX_AUTO_UPDATE", "")

    latest_cached = cache.get("latest_version")
    update_available = (
        is_update_available(__version__, latest_cached)
        if isinstance(latest_cached, str)
        else False
    )

    ctx.obj["formatter"].output(
        {
            "current_version": __version__,
            "latest_cached_version": latest_cached,
            "last_check": cache.get("last_check"),
            "update_available": update_available,
            "config_auto_update": ctx.obj["config_manager"].config.defaults.auto_update,
            "env_auto_update": env_auto_update or None,
        }
    )


@self_update_group.command("check")
@click.option(
    "--use-cache",
    is_flag=True,
    help="Use cached result if available instead of forcing a live check.",
)
@click.pass_context
def self_update_check(ctx, use_cache):
    """Check PyPI for latest available version."""
    cache = _read_cache() if use_cache else None

    latest = cache.get("latest_version") if cache else None
    from_cache = latest is not None

    if not latest:
        latest = get_latest_version()
        if not latest:
            raise AgentixError("Failed to fetch latest version from PyPI.")
        _write_cache(latest)

    update_available = is_update_available(__version__, latest)
    payload = {
        "current_version": __version__,
        "latest_version": latest,
        "update_available": update_available,
        "source": "cache" if from_cache else "pypi",
    }

    if update_available:
        ctx.obj["formatter"].success(
            f"Update available: {__version__} -> {latest}",
            data=payload,
        )
    else:
        ctx.obj["formatter"].success(
            f"Already up to date ({__version__})",
            data=payload,
        )


@self_update_group.command("apply")
@click.option(
    "--method",
    type=click.Choice(["auto", "uv", "pip"]),
    default="auto",
    show_default=True,
    help="Installation method used for upgrade.",
)
@click.pass_context
def self_update_apply(ctx, method):
    """Start a background upgrade process."""
    selected_method = detect_installation_method() if method == "auto" else method
    perform_upgrade(selected_method)
    ctx.obj["formatter"].success(
        f"Started background upgrade using {selected_method}.",
        data={"method": selected_method},
    )


@click.command("update")
@click.option(
    "--method",
    type=click.Choice(["auto", "uv", "pip"]),
    default="auto",
    show_default=True,
    help="Installation method used for upgrade.",
)
@click.pass_context
def update_command(ctx, method):
    """Update agentix immediately."""
    selected_method = detect_installation_method() if method == "auto" else method
    perform_upgrade(selected_method)
    ctx.obj["formatter"].success(
        f"Started background upgrade using {selected_method}.",
        data={"method": selected_method},
    )
