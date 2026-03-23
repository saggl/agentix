"""Sprint commands for Jira."""

from agentix.jira.models import normalize_issue_brief, normalize_sprint
from ._common import _get_client, click, output


@click.group("sprint")
def sprint_group():
    """Manage sprints."""
    pass


@sprint_group.command("list")
@click.option("--board", "-b", required=True, type=int, help="Board ID.")
@click.option("--state", type=click.Choice(["active", "closed", "future"]), help="Sprint state filter.")
@click.pass_context
def sprint_list(ctx, board, state):
    """List sprints for a board."""
    client = _get_client(ctx)
    sprints = client.get_sprints(board, state=state)
    output(ctx, [normalize_sprint(s) for s in sprints])


@sprint_group.command("get")
@click.argument("sprint_id", type=int)
@click.pass_context
def sprint_get(ctx, sprint_id):
    """Get sprint details."""
    client = _get_client(ctx)
    sprint = client.get_sprint(sprint_id)
    output(ctx, normalize_sprint(sprint))


@sprint_group.command("issues")
@click.argument("sprint_id", type=int)
@click.option("--max-results", default=50, type=click.IntRange(1), help="Max results.")
@click.pass_context
def sprint_issues(ctx, sprint_id, max_results):
    """List issues in a sprint."""
    client = _get_client(ctx)
    issues = client.get_sprint_issues(sprint_id, max_results=max_results)
    output(ctx, [normalize_issue_brief(i) for i in issues])


@sprint_group.command("active")
@click.option("--board", "-b", required=True, type=int, help="Board ID.")
@click.pass_context
def sprint_active(ctx, board):
    """Get the active sprint for a board."""
    client = _get_client(ctx)
    sprint = client.get_active_sprint(board)
    if sprint:
        output(ctx, normalize_sprint(sprint))
    else:
        output(ctx, {"message": "No active sprint found."})
