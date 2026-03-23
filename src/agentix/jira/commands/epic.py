"""Epic commands for Jira."""

from agentix.jira.models import normalize_issue, normalize_issue_brief
from ._common import _get_client, click, output


@click.group("epic")
def epic_group():
    """Manage epics."""
    pass


@epic_group.command("list")
@click.option("--project", "-p", help="Project key.")
@click.pass_context
def epic_list(ctx, project):
    """List epics."""
    client = _get_client(ctx)
    epics = client.get_epics(project)
    output(ctx, [normalize_issue_brief(e) for e in epics])


@epic_group.command("get")
@click.argument("epic_key")
@click.pass_context
def epic_get(ctx, epic_key):
    """Get epic details."""
    client = _get_client(ctx)
    epic = client.get_issue(epic_key)
    output(ctx, normalize_issue(epic))


@epic_group.command("issues")
@click.argument("epic_key")
@click.option("--max-results", default=50, type=int, help="Max results.")
@click.pass_context
def epic_issues(ctx, epic_key, max_results):
    """List issues in an epic."""
    client = _get_client(ctx)
    issues = client.get_epic_issues(epic_key, max_results=max_results)
    output(ctx, [normalize_issue_brief(i) for i in issues])
