"""Board commands for Jira."""

from agentix.jira.models import normalize_board
from ._common import _get_client, click, output


@click.group("board")
def board_group():
    """Manage boards."""
    pass


@board_group.command("list")
@click.option("--project", "-p", help="Project key.")
@click.pass_context
def board_list(ctx, project):
    """List boards."""
    client = _get_client(ctx)
    boards = client.get_boards(project)
    output(ctx, [normalize_board(b) for b in boards])


@board_group.command("get")
@click.argument("board_id", type=int)
@click.pass_context
def board_get(ctx, board_id):
    """Get board details."""
    client = _get_client(ctx)
    board = client.get_board(board_id)
    output(ctx, normalize_board(board))
