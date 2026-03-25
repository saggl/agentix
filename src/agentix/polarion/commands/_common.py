"""Shared helpers for Polarion CLI commands."""

import importlib

import click


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
