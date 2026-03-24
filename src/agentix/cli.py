"""Root CLI for agentix."""

import logging
import sys

import click

from agentix import __version__
from agentix.commands.schema import schema_command
from agentix.commands.update import update_command
from agentix.config.commands import config_group
from agentix.config.manager import ConfigManager
from agentix.core.exceptions import AgentixError
from agentix.core.output import OutputFormatter
from agentix.bitbucket.commands import bitbucket_group
from agentix.confluence.commands import confluence_group
from agentix.jenkins.commands import jenkins_group
from agentix.jira.commands import jira_group
from agentix.polarion.commands import polarion_group

# Handle different Click versions - NoArgsIsHelpError was added in Click 8.2.0
NoArgsIsHelpError = getattr(click.exceptions, "NoArgsIsHelpError", None)


@click.group()
@click.option(
    "--profile",
    default=None,
    envvar="AGENTIX_DEFAULT_PROFILE",
    help="Config profile to use.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "table"]),
    default=None,
    help="Output format (default: json).",
)
@click.option("--verbose", is_flag=True, help="Enable verbose logging.")
@click.version_option(version=__version__, prog_name="agentix")
@click.pass_context
def cli(ctx, profile, output_format, verbose):
    """agentix — Unified CLI for Jira, Confluence, Jenkins, Bitbucket, and Polarion."""
    ctx.ensure_object(dict)

    if verbose:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

    config_manager = ConfigManager()
    resolved_format = (
        output_format
        or config_manager.config.defaults.format
        or "json"
    )

    ctx.obj["profile"] = profile
    ctx.obj["config_manager"] = config_manager
    ctx.obj["formatter"] = OutputFormatter(resolved_format)


# Register subgroups
cli.add_command(config_group)
cli.add_command(jira_group)
cli.add_command(confluence_group)
cli.add_command(jenkins_group)
cli.add_command(bitbucket_group)
cli.add_command(polarion_group)
cli.add_command(schema_command)
cli.add_command(update_command)


def _notify_update_available() -> None:
    """Check for updates (throttled by cache) and print a hint when available."""
    from agentix.core.update import (
        _write_cache,
        get_latest_version,
        is_update_available,
        should_check_for_update,
    )

    if not should_check_for_update():
        return

    latest = get_latest_version()
    if not latest:
        return

    _write_cache(latest)

    if is_update_available(__version__, latest):
        click.echo(
            f"New agentix version available: {__version__} -> {latest}. Run: agentix update",
            err=True,
        )


def main():
    """Entry point for the agentix CLI."""
    # Non-blocking by design: update helper handles its own failures.
    _notify_update_available()

    try:
        cli(standalone_mode=False)
    except Exception as e:
        # Handle NoArgsIsHelpError if available (Click >= 8.2.0)
        if NoArgsIsHelpError is not None and isinstance(e, NoArgsIsHelpError):
            # When invoked without arguments, show help gracefully
            cli(["--help"])
        elif isinstance(e, AgentixError):
            formatter = OutputFormatter("json")
            formatter.error(e)
            sys.exit(e.exit_code)
        elif isinstance(e, click.exceptions.Abort):
            sys.exit(130)
        elif isinstance(e, click.ClickException):
            e.show()
            sys.exit(e.exit_code)
        elif isinstance(e, click.exceptions.Exit):
            sys.exit(e.exit_code)
        else:
            # Re-raise unexpected exceptions
            raise


if __name__ == "__main__":
    main()
