"""Project commands for Jira."""

from agentix.jira.models import normalize_project
from ._common import _get_client, click


@click.group("project")
def project_group():
    """Manage projects."""
    pass


@project_group.command("list")
@click.pass_context
def project_list(ctx):
    """List projects."""
    client = _get_client(ctx)
    projects = client.get_projects()
    ctx.obj["formatter"].output([normalize_project(p) for p in projects])


@project_group.command("get")
@click.argument("project_key")
@click.pass_context
def project_get(ctx, project_key):
    """Get project details."""
    client = _get_client(ctx)
    project = client.get_project(project_key)
    ctx.obj["formatter"].output(normalize_project(project))
