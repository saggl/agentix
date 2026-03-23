"""Search command for Confluence."""

from agentix.confluence.models import normalize_page_brief
from ._common import _get_client, click


@click.command("search")
@click.argument("cql")
@click.option("--max-results", default=25, type=click.IntRange(1), help="Max results.")
@click.pass_context
def confluence_search(ctx, cql, max_results):
    """Search with CQL (Confluence Query Language)."""
    client = _get_client(ctx)
    results = list(client.search_cql(cql, max_results=max_results))
    ctx.obj["formatter"].output([normalize_page_brief(r) for r in results])
