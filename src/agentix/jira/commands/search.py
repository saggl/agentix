"""Search command for Jira."""

from ._common import _get_client, click, normalize_issue_brief


@click.command("search")
@click.argument("jql")
@click.option("--max-results", default=50, type=int, help="Max results (default: 50).")
@click.option("--fields", help="Comma-separated field names.")
@click.pass_context
def jira_search(ctx, jql, max_results, fields):
    """Search issues with JQL."""
    client = _get_client(ctx)
    field_list = [f.strip() for f in fields.split(",")] if fields else None
    result = client.search_issues(jql, fields=field_list, max_results=max_results)
    issues = [normalize_issue_brief(i) for i in result.get("issues", [])]
    ctx.obj["formatter"].output(issues)
