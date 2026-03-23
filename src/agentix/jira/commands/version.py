"""Version commands for Jira."""

from agentix.jira.models import normalize_version
from ._common import _get_client, click, output, success


@click.group("version")
def version_group():
    """Manage project versions."""
    pass


@version_group.command("list")
@click.option("--project", "-p", required=True, help="Project key.")
@click.pass_context
def version_list(ctx, project):
    """List versions in a project."""
    client = _get_client(ctx)
    versions = client.get_project_versions(project)
    output(ctx, [normalize_version(v) for v in versions])


@version_group.command("create")
@click.option("--project", "-p", required=True, help="Project key.")
@click.option("--name", "-n", required=True, help="Version name.")
@click.option("--description", "-d", help="Version description.")
@click.option("--start-date", help="Start date (YYYY-MM-DD).")
@click.option("--release-date", help="Release date (YYYY-MM-DD).")
@click.option("--released", is_flag=True, help="Mark as released.")
@click.pass_context
def version_create(ctx, project, name, description, start_date, release_date, released):
    """Create a project version."""
    client = _get_client(ctx)
    result = client.create_version(
        project,
        name,
        description=description,
        start_date=start_date,
        release_date=release_date,
        released=released,
    )
    success(ctx, 
        f"Created version '{name}' in {project}",
        data={"id": result.get("id"), "name": result.get("name")},
    )


@version_group.command("update")
@click.argument("version_id")
@click.option("--name", "-n", help="New version name.")
@click.option("--description", "-d", help="New description.")
@click.option("--released", type=bool, help="Released status (true/false).")
@click.option("--release-date", help="Release date (YYYY-MM-DD).")
@click.pass_context
def version_update(ctx, version_id, name, description, released, release_date):
    """Update a version."""
    client = _get_client(ctx)
    result = client.update_version(
        version_id,
        name=name,
        description=description,
        released=released,
        release_date=release_date,
    )
    success(ctx, 
        f"Updated version {version_id}", data=normalize_version(result)
    )


@version_group.command("delete")
@click.argument("version_id")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.pass_context
def version_delete(ctx, version_id, yes):
    """Delete a version."""
    if not yes:
        click.confirm(f"Delete version {version_id}?", abort=True)
    client = _get_client(ctx)
    client.delete_version(version_id)
    success(ctx, f"Deleted version {version_id}")


@version_group.command("archive")
@click.argument("version_id")
@click.pass_context
def version_archive(ctx, version_id):
    """Archive a version."""
    client = _get_client(ctx)
    result = client.archive_version(version_id)
    success(ctx, 
        f"Archived version {version_id}", data=normalize_version(result)
    )
