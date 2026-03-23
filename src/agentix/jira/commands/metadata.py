"""Metadata commands for Jira."""

from ._common import _get_client, click


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
    ctx.obj["formatter"].output(metadata)


@metadata_group.command("create")
@click.option("--project", "-p", multiple=True, help="Project key (can specify multiple).")
@click.option("--issue-type", "-t", multiple=True, help="Issue type name (can specify multiple).")
@click.pass_context
def metadata_create(ctx, project, issue_type):
    """Get available fields for creating issues."""
    client = _get_client(ctx)
    project_keys = list(project) if project else None
    issue_types = list(issue_type) if issue_type else None
    metadata = client.get_create_metadata(project_keys=project_keys, issue_type_names=issue_types)
    ctx.obj["formatter"].output(metadata)
