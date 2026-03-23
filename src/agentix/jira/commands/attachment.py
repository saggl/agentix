"""Attachment commands for Jira."""

from ._common import _get_client, click, normalize_attachment


@click.group("attachment")
def attachment_group():
    """Manage issue attachments."""
    pass


@attachment_group.command("list")
@click.argument("issue_key")
@click.pass_context
def attachment_list(ctx, issue_key):
    """List attachments on an issue."""
    client = _get_client(ctx)
    attachments = client.get_attachments(issue_key)
    ctx.obj["formatter"].output([normalize_attachment(a) for a in attachments])


@attachment_group.command("add")
@click.argument("issue_key")
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def attachment_add(ctx, issue_key, file_path):
    """Add an attachment to an issue."""
    client = _get_client(ctx)
    result = client.add_attachment(issue_key, file_path)
    ctx.obj["formatter"].success(
        f"Added attachment to {issue_key}",
        data={"attachments": result},
    )


@attachment_group.command("get")
@click.argument("attachment_id")
@click.option("--output", "-o", "output_path", help="Output file path.")
@click.pass_context
def attachment_get(ctx, attachment_id, output_path):
    """Download an attachment."""
    client = _get_client(ctx)
    content = client.get_attachment_content(attachment_id)
    if output_path:
        with open(output_path, "wb") as f:
            f.write(content)
        ctx.obj["formatter"].success(f"Saved attachment to {output_path}")
    else:
        import sys
        sys.stdout.buffer.write(content)
