"""Attachment commands for Confluence."""

from agentix.confluence.models import normalize_attachment
from ._common import _get_client, click


@click.group("attachment")
def attachment_group():
    """Manage page attachments."""
    pass


@attachment_group.command("list")
@click.argument("page_id")
@click.pass_context
def attachment_list(ctx, page_id):
    """List attachments on a page."""
    client = _get_client(ctx)
    attachments = client.get_page_attachments(page_id)
    ctx.obj["formatter"].output([normalize_attachment(a) for a in attachments])


@attachment_group.command("add")
@click.argument("page_id")
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def attachment_add(ctx, page_id, file_path):
    """Add an attachment to a page."""
    client = _get_client(ctx)
    client.add_page_attachment(page_id, file_path)
    ctx.obj["formatter"].success(f"Added attachment to page {page_id}")


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
