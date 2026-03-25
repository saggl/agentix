"""Plan commands for Polarion."""

from agentix.polarion.models import (
    normalize_page,
    normalize_plan,
    normalize_workitem_summary,
)
from ._common import _call, _get_client, click


@click.group("plan")
def plan_group():
    """Manage Polarion plans."""
    pass


@plan_group.command("get")
@click.argument("project_id")
@click.argument("plan_id")
@click.pass_context
def plan_get(ctx, project_id, plan_id):
    """Get plan details."""
    client = _get_client(ctx)
    plan = _call("plan get", client.plans.get, project_id, plan_id)
    ctx.obj["formatter"].output(normalize_plan(plan))


@plan_group.command("search")
@click.argument("project_id")
@click.option("--query", "-q", default=None, help="Polarion query.")
@click.option("--limit", "-l", default=100, type=int, help="Max results.")
@click.pass_context
def plan_search(ctx, project_id, query, limit):
    """Search plans."""
    client = _get_client(ctx)
    page = _call("plan search", client.plans.search, project_id, query=query, limit=limit)
    ctx.obj["formatter"].output(normalize_page(page, normalize_plan))


@plan_group.command("workitems")
@click.argument("project_id")
@click.argument("plan_id")
@click.option("--limit", "-l", default=200, type=int, help="Max results.")
@click.pass_context
def plan_workitems(ctx, project_id, plan_id, limit):
    """List work items in a plan."""
    client = _get_client(ctx)
    page = _call("plan workitems", client.plans.workitems, project_id, plan_id, limit=limit)
    ctx.obj["formatter"].output(normalize_page(page, normalize_workitem_summary))
