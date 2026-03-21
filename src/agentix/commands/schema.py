"""Schema command for introspecting agentix CLI structure."""

import click

from agentix.core.exceptions import ValidationError
from agentix.core.schema import find_command_by_path, get_command_schema, get_command_tree


@click.command("schema")
@click.argument("command_path", nargs=-1)
@click.option(
    "--full",
    is_flag=True,
    help="Include full nested command tree (not just immediate subcommands).",
)
@click.pass_context
def schema_command(ctx, command_path, full):
    """Get JSON schema for agentix commands.

    Examples:
        agentix schema                    # All commands
        agentix schema jira              # Jira subcommands
        agentix schema jira issue get    # Specific command
    """
    # Get the root CLI command from the parent context
    root_cli = ctx.parent.command

    # If no path specified, show root schema
    if not command_path:
        if full:
            schema = get_command_tree(root_cli, "agentix")
        else:
            schema = get_command_schema(root_cli, "agentix", include_inherited_options=True)
        ctx.obj["formatter"].output(schema)
        return

    # Find the requested command
    target_command = find_command_by_path(root_cli, list(command_path))

    if target_command is None:
        raise ValidationError(f"Command not found: {' '.join(command_path)}")

    # Generate schema for the target command
    path_str = f"agentix {' '.join(command_path)}"
    if full:
        schema = get_command_tree(target_command, path_str)
    else:
        schema = get_command_schema(target_command, path_str, include_inherited_options=True)

    ctx.obj["formatter"].output(schema)
