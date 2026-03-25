"""Project commands for Polarion."""

from agentix.polarion.models import normalize_page, normalize_project, normalize_user
from ._common import _call, _get_client, click


@click.group("project")
def project_group():
    """Manage Polarion projects."""
    pass


@project_group.command("list")
@click.option("--query", "-q", default=None, help="Filter projects by name/ID.")
@click.pass_context
def project_list(ctx, query):
    """List all projects."""
    client = _get_client(ctx)
    page = _call("project list", client.projects.list, query=query)
    ctx.obj["formatter"].output(normalize_page(page, normalize_project))


@project_group.command("get")
@click.argument("project_id")
@click.pass_context
def project_get(ctx, project_id):
    """Get project details."""
    client = _get_client(ctx)
    project = _call("project get", client.projects.get, project_id)
    ctx.obj["formatter"].output(normalize_project(project))


@project_group.command("users")
@click.argument("project_id")
@click.option("--limit", "-l", default=200, type=int, help="Max results.")
@click.pass_context
def project_users(ctx, project_id, limit):
    """List project users."""
    client = _get_client(ctx)
    page = _call("project users", client.projects.users, project_id, limit=limit)
    ctx.obj["formatter"].output(normalize_page(page, normalize_user))
