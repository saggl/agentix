"""Shared helpers for Confluence CLI commands."""

import importlib

import click


def _get_client(ctx: click.Context):
    """Build Confluence client from resolved auth.

    Uses symbols from package root (agentix.confluence.commands) so tests patching
    that module path continue to work unchanged.
    """
    commands_pkg = importlib.import_module("agentix.confluence.commands")
    auth = commands_pkg.resolve_auth(
        "confluence",
        ctx.obj["config_manager"],
        profile_name=ctx.obj["profile"],
    )
    return commands_pkg.ConfluenceClient(auth.base_url, auth.user, auth.token, auth.auth_type)
