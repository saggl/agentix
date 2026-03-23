"""Shared helpers for Bitbucket CLI commands."""

import importlib

import click


def _get_client(ctx: click.Context):
    """Build Bitbucket client from resolved auth.

    Uses symbols from package root (agentix.bitbucket.commands) so tests patching
    that module path continue to work unchanged.
    """
    commands_pkg = importlib.import_module("agentix.bitbucket.commands")
    auth = commands_pkg.resolve_auth(
        "bitbucket",
        ctx.obj["config_manager"],
        profile_name=ctx.obj["profile"],
    )
    return commands_pkg.BitbucketClient(auth.base_url, auth.user, auth.token, auth.auth_type)
