"""Test run commands for Polarion."""

from agentix.polarion.models import (
    normalize_page,
    normalize_test_record,
    normalize_testrun,
)
from ._common import _call, _get_client, click


@click.group("testrun")
def testrun_group():
    """Manage Polarion test runs."""
    pass


@testrun_group.command("get")
@click.argument("project_id")
@click.argument("testrun_id")
@click.pass_context
def testrun_get(ctx, project_id, testrun_id):
    """Get test run details."""
    client = _get_client(ctx)
    tr = _call("testrun get", client.testruns.get, project_id, testrun_id)
    ctx.obj["formatter"].output(normalize_testrun(tr))


@testrun_group.command("search")
@click.argument("project_id")
@click.option("--query", "-q", default=None, help="Polarion query.")
@click.option("--limit", "-l", default=100, type=int, help="Max results.")
@click.pass_context
def testrun_search(ctx, project_id, query, limit):
    """Search test runs."""
    client = _get_client(ctx)
    page = _call("testrun search", client.testruns.search, project_id, query=query, limit=limit)
    ctx.obj["formatter"].output(normalize_page(page, normalize_testrun))


@testrun_group.command("records")
@click.argument("project_id")
@click.argument("testrun_id")
@click.option("--limit", "-l", default=500, type=int, help="Max results.")
@click.pass_context
def testrun_records(ctx, project_id, testrun_id, limit):
    """List test run records."""
    client = _get_client(ctx)
    tr = _call("testrun get", client.testruns.get, project_id, testrun_id)
    page = _call("testrun records", client.testruns.records, tr.uri, limit=limit)
    ctx.obj["formatter"].output(normalize_page(page, normalize_test_record))
