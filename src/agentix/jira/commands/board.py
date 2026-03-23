"""Board commands for Jira."""

from ._common import _get_client, click, normalize_board


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
    ctx.obj["formatter"].output([normalize_board(b) for b in boards])


@board_group.command("get")
@click.argument("board_id", type=int)
@click.pass_context
def board_get(ctx, board_id):
    """Get board details."""
    client = _get_client(ctx)
    board = client.get_board(board_id)
    ctx.obj["formatter"].output(normalize_board(board))
