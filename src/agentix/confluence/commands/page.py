"""Page commands for Confluence."""

from agentix.core.exceptions import AgentixError
from agentix.confluence.models import normalize_page, normalize_page_brief
from ._common import _get_client, click


@click.group("page")
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


@page_group.command("children")
@click.argument("page_id")
@click.option("--max-results", type=int, help="Maximum results to return.")
@click.pass_context
def page_children(ctx, page_id, max_results):
    """List child pages of a page."""
    client = _get_client(ctx)
    children = client.get_page_children(page_id, max_results=max_results)
    ctx.obj["formatter"].output([normalize_page_brief(c) for c in children])


@page_group.command("find")
@click.option("--space", "-s", required=True, help="Space key.")
@click.option("--title", "-t", required=True, help="Page title.")
@click.pass_context
def page_find(ctx, space, title):
    """Find a page by title in a space."""
    client = _get_client(ctx)
    page = client.get_page_by_title(space, title)
    if page:
        ctx.obj["formatter"].output(normalize_page(page))
    else:
        ctx.obj["formatter"].error(AgentixError(f"Page '{title}' not found in space '{space}'"))
        ctx.exit(1)
