"""Attachment commands for Jira."""

from agentix.jira.models import normalize_attachment
from ._common import _get_client, click, output, success


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
    output(ctx, [normalize_attachment(a) for a in attachments])


@attachment_group.command("add")
@click.argument("issue_key")
@click.argument("file_path", type=click.Path(exists=True))
@click.pass_context
def attachment_add(ctx, issue_key, file_path):
    """Add an attachment to an issue."""
    client = _get_client(ctx)
    result = client.add_attachment(issue_key, file_path)
    success(ctx, 
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
        success(ctx, f"Saved attachment to {output_path}")
    else:
        import sys
        sys.stdout.buffer.write(content)
