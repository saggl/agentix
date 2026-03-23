"""Shared helpers for Jira CLI commands."""

import importlib

import click


def _get_client(ctx: click.Context):
    """Build Jira client from resolved auth.

    Uses symbols from package root (agentix.jira.commands) so tests patching
    that module path continue to work unchanged.
    """
    commands_pkg = importlib.import_module("agentix.jira.commands")
    auth = commands_pkg.resolve_auth(
        "jira",
        ctx.obj["config_manager"],
        profile_name=ctx.obj["profile"],
    )
    return commands_pkg.JiraClient(auth.base_url, auth.user, auth.token, auth.auth_type)
