"""CLI commands for Polarion integration."""

import json

import click

from agentix.core.auth import resolve_auth
from agentix.core.exceptions import AgentixError
from agentix.polarion.client import PolarionClient
from agentix.polarion.models import (
    normalize_action,
    normalize_document,
    normalize_plan,
    normalize_project,
    normalize_testrun,
    normalize_user,
    normalize_workitem,
    normalize_workitem_brief,
)


def _get_client(ctx: click.Context) -> PolarionClient:
    auth = resolve_auth(
        "polarion",
        ctx.obj["config_manager"],
        profile_name=ctx.obj["profile"],
    )
    return PolarionClient(auth.base_url, auth.user, auth.token, auth.auth_type)


@click.group("polarion")
def polarion_group():
    """Polarion ALM."""
    pass


# -- Project commands --


@polarion_group.group("project")
def project_group():
    """Manage Polarion projects."""
    pass


@project_group.command("get")
@click.argument("project_id")
@click.pass_context
def project_get(ctx, project_id):
    """Get project details."""
    client = _get_client(ctx)
    project = client.get_project(project_id)
    ctx.obj["formatter"].output(normalize_project(project))


@project_group.command("users")
@click.argument("project_id")
@click.pass_context
def project_users(ctx, project_id):
    """List users in a project."""
    client = _get_client(ctx)
    users = client.get_project_users(project_id)
    ctx.obj["formatter"].output([normalize_user(u) for u in users])


# -- Work item commands --


@polarion_group.group("workitem")
def workitem_group():
    """Manage work items."""
    pass


@workitem_group.command("get")
@click.argument("project_id")
@click.argument("workitem_id")
@click.pass_context
def workitem_get(ctx, project_id, workitem_id):
    """Get work item details."""
    client = _get_client(ctx)
    wi = client.get_workitem(project_id, workitem_id)
    ctx.obj["formatter"].output(normalize_workitem(wi))


@workitem_group.command("list")
@click.argument("project_id")
@click.option("--query", "-q", default="", help="Polarion query string.")
@click.option("--order", default="Created", help="Sort field (default: Created).")
@click.option("--limit", default=100, type=int, help="Max results (default: 100).")
@click.pass_context
def workitem_list(ctx, project_id, query, order, limit):
    """Search work items."""
    client = _get_client(ctx)
    workitems = client.search_workitems(project_id, query, order, limit)
    ctx.obj["formatter"].output([normalize_workitem_brief(wi) for wi in workitems])


@workitem_group.command("create")
@click.argument("project_id")
@click.option("--type", "workitem_type", required=True, help="Work item type (e.g., requirement, task).")
@click.option("--title", help="Work item title.")
@click.option("--fields", "fields_json", help="Additional fields as JSON string.")
@click.pass_context
def workitem_create(ctx, project_id, workitem_type, title, fields_json):
    """Create a work item."""
    fields = {}
    if title:
        fields["title"] = title
    if fields_json:
        try:
            fields.update(json.loads(fields_json))
        except json.JSONDecodeError as e:
            ctx.obj["formatter"].error(AgentixError(f"Invalid JSON for --fields: {e}"))
            ctx.exit(3)
            return

    client = _get_client(ctx)
    wi = client.create_workitem(project_id, workitem_type, fields or None)
    ctx.obj["formatter"].success(
        f"Created work item {wi.get('id', '')}",
        data=normalize_workitem(wi),
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
    client.delete_workitem(project_id, workitem_id)
    ctx.obj["formatter"].success(f"Deleted work item {workitem_id}")


@workitem_group.command("actions")
@click.argument("project_id")
@click.argument("workitem_id")
@click.pass_context
def workitem_actions(ctx, project_id, workitem_id):
    """List available workflow actions for a work item."""
    client = _get_client(ctx)
    actions = client.get_workitem_actions(project_id, workitem_id)
    ctx.obj["formatter"].output([normalize_action(a) for a in actions])


@workitem_group.command("action")
@click.argument("project_id")
@click.argument("workitem_id")
@click.argument("action_name")
@click.pass_context
def workitem_action(ctx, project_id, workitem_id, action_name):
    """Perform a workflow action on a work item."""
    client = _get_client(ctx)
    client.perform_workitem_action(project_id, workitem_id, action_name)
    ctx.obj["formatter"].success(
        f"Performed action '{action_name}' on {workitem_id}"
    )


# -- Document commands --


@polarion_group.group("document")
def document_group():
    """Manage documents."""
    pass


@document_group.command("get")
@click.argument("project_id")
@click.argument("location")
@click.pass_context
def document_get(ctx, project_id, location):
    """Get a document by location."""
    client = _get_client(ctx)
    doc = client.get_document(project_id, location)
    ctx.obj["formatter"].output(normalize_document(doc))


@document_group.command("spaces")
@click.argument("project_id")
@click.pass_context
def document_spaces(ctx, project_id):
    """List document spaces."""
    client = _get_client(ctx)
    spaces = client.get_document_spaces(project_id)
    ctx.obj["formatter"].output(spaces)


@document_group.command("list")
@click.argument("project_id")
@click.option("--space", "-s", required=True, help="Document space name.")
@click.pass_context
def document_list(ctx, project_id, space):
    """List documents in a space."""
    client = _get_client(ctx)
    docs = client.get_documents_in_space(project_id, space)
    ctx.obj["formatter"].output([normalize_document(d) for d in docs])


# -- Test run commands --


@polarion_group.group("testrun")
def testrun_group():
    """Manage test runs."""
    pass


@testrun_group.command("get")
@click.argument("project_id")
@click.argument("testrun_id")
@click.pass_context
def testrun_get(ctx, project_id, testrun_id):
    """Get a test run."""
    client = _get_client(ctx)
    tr = client.get_testrun(project_id, testrun_id)
    ctx.obj["formatter"].output(normalize_testrun(tr))


@testrun_group.command("list")
@click.argument("project_id")
@click.option("--query", "-q", default="", help="Polarion query string.")
@click.option("--order", default="Created", help="Sort field (default: Created).")
@click.option("--limit", default=100, type=int, help="Max results (default: 100).")
@click.pass_context
def testrun_list(ctx, project_id, query, order, limit):
    """Search test runs."""
    client = _get_client(ctx)
    testruns = client.search_testruns(project_id, query, order, limit)
    ctx.obj["formatter"].output([normalize_testrun(tr) for tr in testruns])


# -- Plan commands --


@polarion_group.group("plan")
def plan_group():
    """Manage plans."""
    pass


@plan_group.command("get")
@click.argument("project_id")
@click.argument("plan_id")
@click.pass_context
def plan_get(ctx, project_id, plan_id):
    """Get a plan."""
    client = _get_client(ctx)
    plan = client.get_plan(project_id, plan_id)
    ctx.obj["formatter"].output(normalize_plan(plan))


@plan_group.command("list")
@click.argument("project_id")
@click.option("--query", "-q", default="", help="Polarion query string.")
@click.option("--order", default="Created", help="Sort field (default: Created).")
@click.option("--limit", default=100, type=int, help="Max results (default: 100).")
@click.pass_context
def plan_list(ctx, project_id, query, order, limit):
    """Search plans."""
    client = _get_client(ctx)
    plans = client.search_plans(project_id, query, order, limit)
    ctx.obj["formatter"].output([normalize_plan(p) for p in plans])


# -- Enum commands --


@polarion_group.command("enum")
@click.argument("project_id")
@click.argument("enum_name")
@click.pass_context
def enum_get(ctx, project_id, enum_name):
    """Get enum options (e.g., requirement-status)."""
    client = _get_client(ctx)
    options = client.get_enum(project_id, enum_name)
    ctx.obj["formatter"].output(options)
