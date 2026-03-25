"""Document commands for Polarion."""

from agentix.polarion.models import (
    normalize_document,
    normalize_page,
    normalize_workitem_summary,
)
from ._common import _call, _get_client, click


@click.group("document")
def document_group():
    """Manage Polarion documents."""
    pass


@document_group.command("get")
@click.argument("project_id")
@click.option("--uri", default=None, help="Document URI.")
@click.option("--location", default=None, help="Document location path.")
@click.pass_context
def document_get(ctx, project_id, uri, location):
    """Get a document by URI or location."""
    if not uri and not location:
        raise click.UsageError("Either --uri or --location is required.")

    client = _get_client(ctx)
    doc = _call("document get", client.documents.get, project_id, uri=uri, location=location)
    ctx.obj["formatter"].output(normalize_document(doc))


@document_group.command("spaces")
@click.argument("project_id")
@click.pass_context
def document_spaces(ctx, project_id):
    """List document spaces."""
    client = _get_client(ctx)
    spaces = _call("document spaces", client.documents.list_spaces, project_id)
    ctx.obj["formatter"].output(spaces)


@document_group.command("list")
@click.argument("project_id")
@click.argument("space")
@click.option("--limit", "-l", default=100, type=int, help="Max results.")
@click.pass_context
def document_list(ctx, project_id, space, limit):
    """List documents in a space."""
    client = _get_client(ctx)
    page = _call("document list", client.documents.list_in_space, project_id, space, limit=limit)
    ctx.obj["formatter"].output(normalize_page(page, normalize_document))


@document_group.command("workitems")
@click.argument("project_id")
@click.option("--uri", required=True, help="Document URI.")
@click.pass_context
def document_workitems(ctx, project_id, uri):
    """List work items in a document."""
    client = _get_client(ctx)
    page = _call("document workitems", client.documents.workitems, project_id, uri)
    ctx.obj["formatter"].output(normalize_page(page, normalize_workitem_summary))
