"""Comment commands for Confluence."""

from agentix.confluence.models import normalize_comment
from ._common import _get_client, click


@click.group("comment")
def comment_group():
    """Manage page comments."""
    pass


@comment_group.command("list")
@click.argument("page_id")
@click.pass_context
def comment_list(ctx, page_id):
    """List comments on a page."""
    client = _get_client(ctx)
    comments = client.get_page_comments(page_id)
    ctx.obj["formatter"].output([normalize_comment(c) for c in comments])


@comment_group.command("add")
@click.argument("page_id")
@click.option("--body", "-b", required=True, help="Comment body.")
@click.pass_context
def comment_add(ctx, page_id, body):
    """Add a comment to a page."""
    client = _get_client(ctx)
    result = client.add_page_comment(page_id, body)
    ctx.obj["formatter"].success(
        f"Added comment to page {page_id}",
        data={"id": result.get("id")},
    )


@comment_group.command("get")
@click.argument("comment_id")
@click.pass_context
def comment_get(ctx, comment_id):
    """Get a specific comment."""
    client = _get_client(ctx)
    comment = client.get_comment(comment_id)
    ctx.obj["formatter"].output(normalize_comment(comment))
