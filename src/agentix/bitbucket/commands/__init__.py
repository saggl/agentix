"""CLI commands for Bitbucket integration."""

import click

from agentix.bitbucket.client import BitbucketClient
from agentix.core.auth import resolve_auth

from .branch import branch_group
from .build import build_group
from .commit import commit_group
from .pr import pr_group
from .project import project_group
from .repo import repo_group
from .tag import tag_group
from .user import user_group


@click.group("bitbucket")
def bitbucket_group():
    """Bitbucket repository management."""
    pass


# Register subcommands in original order
bitbucket_group.add_command(project_group)
bitbucket_group.add_command(repo_group)
bitbucket_group.add_command(branch_group)
bitbucket_group.add_command(tag_group)
bitbucket_group.add_command(pr_group)
bitbucket_group.add_command(commit_group)
bitbucket_group.add_command(build_group)
bitbucket_group.add_command(user_group)

__all__ = [
    "bitbucket_group",
    "resolve_auth",
    "BitbucketClient",
]
