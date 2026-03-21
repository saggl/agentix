"""CLI commands for Confluence integration."""

import click

from agentix.core.auth import resolve_auth
from agentix.confluence.client import ConfluenceClient
from agentix.confluence.models import (
    normalize_attachment,
    normalize_comment,
    normalize_page,
    normalize_page_brief,
    normalize_space,
)


def _get_client(ctx: click.Context) -> ConfluenceClient:
    auth = resolve_auth(
        "confluence",
        ctx.obj["config_manager"],
        profile_name=ctx.obj["profile"],
    )
    return ConfluenceClient(auth.base_url, auth.user, auth.token)


@click.group("confluence")
def confluence_group():
    """Confluence wiki."""
    pass


# -- Page commands --


@confluence_group.group("page")
def page_group():
    """Manage Confluence pages."""
    pass


@page_group.command("get")
@click.argument("page_id")
@click.option(
    "--body-format",
    type=click.Choice(["storage", "atlas_doc_format"]),
    default="storage",
    help="Body format.",
)
@click.pass_context
def page_get(ctx, page_id, body_format):
    """Get a page by ID."""
    client = _get_client(ctx)
    page = client.get_page(page_id, body_format=body_format)
    ctx.obj["formatter"].output(normalize_page(page))


@page_group.command("search")
@click.option("--query", "-q", required=True, help="Search query text.")
@click.option("--space", "-s", help="Space key to search in.")
@click.option("--max-results", default=25, type=int, help="Max results.")
@click.pass_context
def page_search(ctx, query, space, max_results):
    """Search for pages."""
    client = _get_client(ctx)
    pages = client.search_pages(query, space_key=space, max_results=max_results)
    ctx.obj["formatter"].output([normalize_page_brief(p) for p in pages])


@page_group.command("create")
@click.option("--space-id", required=True, help="Space ID.")
@click.option("--title", "-t", required=True, help="Page title.")
@click.option("--body", "-b", required=True, help="Page body (storage format HTML).")
@click.option("--parent-id", help="Parent page ID.")
@click.pass_context
def page_create(ctx, space_id, title, body, parent_id):
    """Create a new page."""
    client = _get_client(ctx)
    result = client.create_page(
        space_id=space_id,
        title=title,
        body=body,
        parent_id=parent_id,
    )
    ctx.obj["formatter"].success(
        f"Created page '{title}'",
        data={"id": result.get("id"), "title": result.get("title")},
    )


@page_group.command("update")
@click.argument("page_id")
@click.option("--title", "-t", required=True, help="Page title.")
@click.option("--body", "-b", required=True, help="Page body (storage format HTML).")
@click.option("--version-message", help="Version comment.")
@click.pass_context
def page_update(ctx, page_id, title, body, version_message):
    """Update a page (auto-increments version)."""
    client = _get_client(ctx)
    result = client.update_page_auto(
        page_id, title, body, version_message=version_message
    )
    ctx.obj["formatter"].success(
        f"Updated page '{title}'",
        data={"id": result.get("id"), "version": result.get("version", {}).get("number")},
    )


@page_group.command("delete")
@click.argument("page_id")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.pass_context
def page_delete(ctx, page_id, yes):
    """Delete a page."""
    if not yes:
        click.confirm(f"Delete page {page_id}?", abort=True)
    client = _get_client(ctx)
    client.delete_page(page_id)
    ctx.obj["formatter"].success(f"Deleted page {page_id}")


@page_group.command("move")
@click.argument("page_id")
@click.option("--target-parent", required=True, help="Target parent page ID.")
@click.pass_context
def page_move(ctx, page_id, target_parent):
    """Move a page under a new parent."""
    client = _get_client(ctx)
    client.move_page(page_id, target_parent)
    ctx.obj["formatter"].success(f"Moved page {page_id} under {target_parent}")


# -- Comment commands --


@confluence_group.group("comment")
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


# -- Attachment commands --


@confluence_group.group("attachment")
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


# -- Space commands --


@confluence_group.group("space")
def space_group():
    """Manage spaces."""
    pass


@space_group.command("list")
@click.pass_context
def space_list(ctx):
    """List spaces."""
    client = _get_client(ctx)
    spaces = client.get_spaces()
    ctx.obj["formatter"].output([normalize_space(s) for s in spaces])


@space_group.command("get")
@click.argument("space_id")
@click.pass_context
def space_get(ctx, space_id):
    """Get space details."""
    client = _get_client(ctx)
    space = client.get_space(space_id)
    ctx.obj["formatter"].output(normalize_space(space))


# -- Search --


@confluence_group.command("search")
@click.argument("cql")
@click.option("--max-results", default=25, type=int, help="Max results.")
@click.pass_context
def confluence_search(ctx, cql, max_results):
    """Search with CQL (Confluence Query Language)."""
    client = _get_client(ctx)
    results = list(client.search_cql(cql, max_results=max_results))
    ctx.obj["formatter"].output([normalize_page_brief(r) for r in results])
