"""Workitem commands for Polarion."""

from agentix.polarion.models import (
    _link,
    normalize_page,
    normalize_workitem_detail,
    normalize_workitem_summary,
)
from ._common import _get_client, click


@click.group("workitem")
def workitem_group():
    """Manage Polarion work items."""
    pass


@workitem_group.command("get")
@click.argument("project_id")
@click.argument("workitem_id")
@click.pass_context
def workitem_get(ctx, project_id, workitem_id):
    """Get work item details."""
    client = _get_client(ctx)
    wi = client.workitems.get(project_id, workitem_id)
    ctx.obj["formatter"].output(normalize_workitem_detail(wi))


@workitem_group.command("search")
@click.argument("project_id")
@click.option("--query", "-q", default=None, help="Polarion query (Lucene syntax).")
@click.option("--sort", "-s", default="Created", help="Sort field.")
@click.option("--limit", "-l", default=100, type=int, help="Max results.")
@click.pass_context
def workitem_search(ctx, project_id, query, sort, limit):
    """Search work items."""
    client = _get_client(ctx)
    page = client.workitems.search(project_id, query=query, sort=sort, limit=limit)
    ctx.obj["formatter"].output(normalize_page(page, normalize_workitem_summary))


@workitem_group.command("create")
@click.argument("project_id")
@click.option("--type", "-t", "type_id", required=True, help="Work item type ID.")
@click.option("--title", required=True, help="Work item title.")
@click.option("--description", "-d", default=None, help="Description (HTML).")
@click.pass_context
def workitem_create(ctx, project_id, type_id, title, description):
    """Create a new work item."""
    from polarion.v3.types.workitem import WorkitemCreate

    payload = WorkitemCreate(type_id=type_id, title=title, description_html=description)
    client = _get_client(ctx)
    wi = client.workitems.create(project_id, payload)
    ctx.obj["formatter"].success(
        f"Created work item {wi.id}",
        data=normalize_workitem_detail(wi),
    )


@workitem_group.command("update")
@click.argument("project_id")
@click.argument("workitem_id")
@click.option("--title", default=None, help="New title.")
@click.option("--status", "status_id", default=None, help="New status ID.")
@click.option("--priority", "priority_id", default=None, help="New priority ID.")
@click.option("--description", "-d", default=None, help="New description (HTML).")
@click.pass_context
def workitem_update(ctx, project_id, workitem_id, title, status_id, priority_id, description):
    """Update a work item."""
    from polarion.v3.types.workitem import WorkitemUpdate

    payload = WorkitemUpdate(
        title=title,
        status_id=status_id,
        priority_id=priority_id,
        description_html=description,
    )
    client = _get_client(ctx)
    wi = client.workitems.update(project_id, workitem_id, payload)
    ctx.obj["formatter"].success(
        f"Updated work item {wi.id}",
        data=normalize_workitem_detail(wi),
    )


@workitem_group.command("delete")
@click.argument("project_id")
@click.argument("workitem_id")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.pass_context
def workitem_delete(ctx, project_id, workitem_id, yes):
    """Delete a work item."""
    if not yes:
        click.confirm(f"Delete work item {workitem_id}?", abort=True)

    client = _get_client(ctx)
    client.workitems.delete(project_id, workitem_id)
    ctx.obj["formatter"].success(f"Deleted work item {workitem_id}")


@workitem_group.command("actions")
@click.argument("project_id")
@click.argument("workitem_id")
@click.pass_context
def workitem_actions(ctx, project_id, workitem_id):
    """List available workflow actions."""
    client = _get_client(ctx)
    actions = client.workitems.available_actions(project_id, workitem_id)
    ctx.obj["formatter"].output(actions)


@workitem_group.command("links")
@click.argument("project_id")
@click.argument("workitem_id")
@click.pass_context
def workitem_links(ctx, project_id, workitem_id):
    """List work item links."""
    client = _get_client(ctx)
    links = client.workitems.links(project_id, workitem_id)
    ctx.obj["formatter"].output([_link(lnk) for lnk in links])
