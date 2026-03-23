"""CLI commands for Confluence integration."""

import click

from agentix.confluence.client import ConfluenceClient
from agentix.core.auth import resolve_auth

from .attachment import attachment_group
from .comment import comment_group
from .page import page_group
from .search import confluence_search
from .space import space_group


@click.group("confluence")
def confluence_group():
    """Confluence wiki."""
    pass


# Register subcommands in original order
confluence_group.add_command(page_group)
confluence_group.add_command(comment_group)
confluence_group.add_command(attachment_group)
confluence_group.add_command(space_group)
confluence_group.add_command(confluence_search)

__all__ = [
    "confluence_group",
    "resolve_auth",
    "ConfluenceClient",
]
