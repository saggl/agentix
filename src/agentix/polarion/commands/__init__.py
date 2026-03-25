"""CLI commands for Polarion integration."""

import click

from agentix.core.auth import resolve_auth
from agentix.polarion.client import create_polarion_client

from .document import document_group
from .health import health_group
from .plan import plan_group
from .project import project_group
from .testrun import testrun_group
from .workitem import workitem_group


@click.group("polarion")
def polarion_group():
    """Polarion ALM management."""
    pass


polarion_group.add_command(project_group)
polarion_group.add_command(workitem_group)
polarion_group.add_command(document_group)
polarion_group.add_command(plan_group)
polarion_group.add_command(testrun_group)
polarion_group.add_command(health_group)

__all__ = [
    "polarion_group",
    "resolve_auth",
    "create_polarion_client",
]
