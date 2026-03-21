"""Schema introspection for agentix CLI commands."""

from typing import Any, Dict, List, Optional

import click


def get_command_schema(
    command: click.Command,
    command_path: str = "agentix",
    include_inherited_options: bool = True,
) -> Dict[str, Any]:
    """Generate JSON schema for a Click command.

    Args:
        command: Click command/group to introspect
        command_path: Full command path (e.g., "agentix jira issue get")
        include_inherited_options: Include global options (--profile, --format, etc.)

    Returns:
        Dictionary containing command schema with arguments, options, and subcommands
    """
    schema: Dict[str, Any] = {
        "command": command_path,
        "description": command.help or command.__doc__ or "",
        "arguments": [],
        "options": [],
        "subcommands": [],
    }

    # Extract arguments
    for param in command.params:
        if isinstance(param, click.Argument):
            schema["arguments"].append(_argument_schema(param))
        elif isinstance(param, click.Option):
            # Skip inherited options if requested
            if not include_inherited_options and _is_inherited_option(param):
                continue
            schema["options"].append(_option_schema(param))

    # Extract subcommands if this is a group
    if isinstance(command, click.Group):
        for subcommand_name in sorted(command.list_commands(click.Context(command))):
            subcommand = command.get_command(click.Context(command), subcommand_name)
            if subcommand:
                sub_path = f"{command_path} {subcommand_name}"
                schema["subcommands"].append({
                    "name": subcommand_name,
                    "description": subcommand.help or "",
                    "path": sub_path,
                })

    return schema


def get_command_tree(
    command: click.Command,
    command_path: str = "agentix",
    max_depth: Optional[int] = None,
    current_depth: int = 0,
) -> Dict[str, Any]:
    """Generate full command tree with nested schemas.

    Args:
        command: Click command/group to introspect
        command_path: Full command path
        max_depth: Maximum recursion depth (None for unlimited)
        current_depth: Current recursion depth

    Returns:
        Dictionary with full nested command tree
    """
    schema = get_command_schema(command, command_path, include_inherited_options=False)

    # Recursively get subcommand schemas if we haven't hit max depth
    if isinstance(command, click.Group) and (max_depth is None or current_depth < max_depth):
        full_subcommands = []
        for subcommand_info in schema["subcommands"]:
            subcommand_name = subcommand_info["name"]
            subcommand = command.get_command(click.Context(command), subcommand_name)
            if subcommand:
                sub_schema = get_command_tree(
                    subcommand,
                    subcommand_info["path"],
                    max_depth,
                    current_depth + 1,
                )
                full_subcommands.append(sub_schema)
        schema["subcommands"] = full_subcommands

    return schema


def find_command_by_path(
    root_command: click.Command,
    path: List[str],
) -> Optional[click.Command]:
    """Find a command by its path components.

    Args:
        root_command: Root CLI command
        path: List of command names (e.g., ["jira", "issue", "get"])

    Returns:
        The found command, or None if not found
    """
    current = root_command

    for component in path:
        if not isinstance(current, click.Group):
            return None

        current = current.get_command(click.Context(current), component)
        if current is None:
            return None

    return current


def _argument_schema(arg: click.Argument) -> Dict[str, Any]:
    """Extract schema for a Click argument."""
    return {
        "name": arg.name,
        "type": _type_name(arg.type),
        "required": arg.required,
        "description": "",  # Click Arguments don't have help text
        "multiple": arg.multiple,
        "nargs": arg.nargs,
    }


def _option_schema(opt: click.Option) -> Dict[str, Any]:
    """Extract schema for a Click option."""
    schema = {
        "name": opt.name,
        "flags": opt.opts,
        "type": _type_name(opt.type),
        "required": opt.required,
        "default": opt.default,
        "description": opt.help or "",
        "multiple": opt.multiple,
        "is_flag": opt.is_flag,
    }

    # Add choices if this is a Choice type
    if isinstance(opt.type, click.Choice):
        schema["choices"] = opt.type.choices

    # Add count info for flags
    if opt.count:
        schema["count"] = True

    return schema


def _type_name(param_type: click.ParamType) -> str:
    """Get human-readable type name."""
    if isinstance(param_type, click.Choice):
        return "choice"
    elif isinstance(param_type, click.types.IntParamType):
        return "integer"
    elif isinstance(param_type, click.types.FloatParamType):
        return "float"
    elif isinstance(param_type, click.types.BoolParamType):
        return "boolean"
    elif isinstance(param_type, click.Path):
        return "path"
    elif isinstance(param_type, click.File):
        return "file"
    else:
        return "string"


def _is_inherited_option(opt: click.Option) -> bool:
    """Check if option is inherited from parent (global options)."""
    # Options like --profile, --format, --verbose are inherited from root
    # We can identify them by common names
    inherited_names = {"profile", "output_format", "verbose", "help", "version"}
    return opt.name in inherited_names
