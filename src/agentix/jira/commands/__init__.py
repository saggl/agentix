"""CLI commands for Jira integration."""

import click

from agentix.core.auth import resolve_auth
from agentix.jira.client import JiraClient

from .attachment import attachment_group
from .board import board_group
from .comment import comment_group
from .component import component_group
from .epic import epic_group
from .issue import issue_group
from .metadata import metadata_group
from .project import project_group
from .search import jira_search
from .sprint import sprint_group
from .version import version_group


@click.group("jira")
def jira_group():
    """Jira issue tracking."""
    pass


# Register subcommands in original order
jira_group.add_command(issue_group)
jira_group.add_command(comment_group)
jira_group.add_command(attachment_group)
jira_group.add_command(sprint_group)
jira_group.add_command(epic_group)
jira_group.add_command(board_group)
jira_group.add_command(project_group)
jira_group.add_command(component_group)
jira_group.add_command(version_group)
jira_group.add_command(metadata_group)
jira_group.add_command(jira_search)

__all__ = [
    "jira_group",
    "resolve_auth",
    "JiraClient",
]
