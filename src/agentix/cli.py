"""Root CLI for agentix."""

import logging
import sys

import click

from agentix import __version__
from agentix.commands.schema import schema_command
from agentix.config.commands import config_group
from agentix.config.manager import ConfigManager
from agentix.core.exceptions import AgentixError
from agentix.core.output import OutputFormatter
from agentix.bitbucket.commands import bitbucket_group
from agentix.confluence.commands import confluence_group
from agentix.jenkins.commands import jenkins_group
from agentix.jira.commands import jira_group


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
    """agentix — Unified CLI for Jira, Confluence, Jenkins, and Bitbucket."""
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
cli.add_command(schema_command)


def main():
    """Entry point for the agentix CLI."""
    try:
        cli(standalone_mode=False)
    except AgentixError as e:
        formatter = OutputFormatter("json")
        formatter.error(e)
        sys.exit(e.exit_code)
    except click.exceptions.Abort:
        sys.exit(130)
    except click.exceptions.Exit as e:
        sys.exit(e.exit_code)


if __name__ == "__main__":
    main()
