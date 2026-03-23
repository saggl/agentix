"""CLI commands for Jenkins integration."""

import click

from agentix.core.auth import resolve_auth
from agentix.jenkins.client import JenkinsClient

from .build import build_group
from .job import job_group
from .node import node_group
from .pipeline import pipeline_group
from .queue import queue_group
from .test import test_group


@click.group("jenkins")
def jenkins_group():
    """Jenkins CI/CD."""
    pass


# Register subcommands in original order
jenkins_group.add_command(job_group)
jenkins_group.add_command(build_group)
jenkins_group.add_command(test_group)
jenkins_group.add_command(pipeline_group)
jenkins_group.add_command(queue_group)
jenkins_group.add_command(node_group)

__all__ = [
    "jenkins_group",
    "resolve_auth",
    "JenkinsClient",
]
