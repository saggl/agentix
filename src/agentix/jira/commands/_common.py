"""Shared helpers for Jira CLI commands."""

import importlib

import click


def output(ctx: click.Context, data):
    """Render command output using configured formatter."""
    ctx.obj["formatter"].output(data)


def success(ctx: click.Context, message: str, data=None):
    """Render a success response using configured formatter."""
    ctx.obj["formatter"].success(message, data=data)


def error_exit(ctx: click.Context, exc, exit_code: int = 3):
    """Render an error response and exit with a non-zero code."""
    ctx.obj["formatter"].error(exc)
    ctx.exit(exit_code)


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
