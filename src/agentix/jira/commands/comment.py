"""Comment commands for Jira."""

from ._common import _get_client, click, normalize_comment


@click.group("comment")
def comment_group():
    """Manage issue comments."""
    pass


@comment_group.command("list")
@click.argument("issue_key")
@click.pass_context
def comment_list(ctx, issue_key):
    """List comments on an issue."""
    client = _get_client(ctx)
    comments = client.get_comments(issue_key)
    ctx.obj["formatter"].output([normalize_comment(c) for c in comments])


@comment_group.command("add")
@click.argument("issue_key")
@click.option("--body", "-b", required=True, help="Comment text.")
@click.pass_context
def comment_add(ctx, issue_key, body):
    """Add a comment to an issue."""
    client = _get_client(ctx)
    result = client.add_comment(issue_key, body)
    ctx.obj["formatter"].success(
        f"Added comment to {issue_key}",
        data={"id": result.get("id")},
    )


@comment_group.command("get")
@click.argument("issue_key")
@click.argument("comment_id")
@click.pass_context
def comment_get(ctx, issue_key, comment_id):
    """Get a specific comment."""
    client = _get_client(ctx)
    comment = client.get_comment(issue_key, comment_id)
    ctx.obj["formatter"].output(normalize_comment(comment))
