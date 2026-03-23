"""Shared helpers for Jenkins CLI commands."""

import importlib

import click


def _get_client(ctx: click.Context):
    """Build Jenkins client from resolved auth.

    Uses symbols from package root (agentix.jenkins.commands) so tests patching
    that module path continue to work unchanged.
    """
    commands_pkg = importlib.import_module("agentix.jenkins.commands")
    auth = commands_pkg.resolve_auth(
        "jenkins",
        ctx.obj["config_manager"],
        profile_name=ctx.obj["profile"],
    )
    return commands_pkg.JenkinsClient(auth.base_url, auth.user, auth.token, auth.auth_type)
