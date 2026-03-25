"""Metadata commands for Jira."""

from agentix.core.exceptions import NotFoundError
from ._common import _get_client, click, error_exit, output


@click.group("metadata")
def metadata_group():
    """Get field metadata for issues."""
    pass


@metadata_group.command("edit")
@click.argument("issue_key")
@click.pass_context
def metadata_edit(ctx, issue_key):
    """Get available fields for editing an issue."""
    client = _get_client(ctx)
    metadata = client.get_issue_edit_metadata(issue_key)
    output(ctx, metadata)


@metadata_group.command("create")
@click.option("--project", "-p", multiple=True, help="Project key (can specify multiple).")
@click.option("--issue-type", "-t", multiple=True, help="Issue type name (can specify multiple).")
@click.pass_context
def metadata_create(ctx, project, issue_type):
    """Get available fields for creating issues."""
    client = _get_client(ctx)
    project_keys = list(project) if project else None
    issue_types = list(issue_type) if issue_type else None
    try:
        metadata = client.get_create_metadata(project_keys=project_keys, issue_type_names=issue_types)
    except NotFoundError:
        from agentix.core.exceptions import AgentixError
        error_exit(
            ctx,
            AgentixError(
                "The createmeta endpoint is not available on this Jira instance. "
                "This endpoint was removed in Jira Server/DC 9.x. "
                "Use 'agentix jira metadata edit <ISSUE_KEY>' instead."
            ),
        )
        return
    output(ctx, metadata)
