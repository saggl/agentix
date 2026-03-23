"""Tag commands for Bitbucket."""

from agentix.bitbucket.models import normalize_tag
from ._common import _get_client, click


@click.group("tag")
def tag_group():
    """Manage repository tags."""
    pass


@tag_group.command("list")
@click.argument("project_key")
@click.argument("repo_slug")
@click.option("--filter", help="Filter tags by name.")
@click.pass_context
def tag_list(ctx, project_key, repo_slug, filter):
    """List tags in a repository."""
    client = _get_client(ctx)
    tags = client.get_tags(project_key, repo_slug, filter_text=filter)
    ctx.obj["formatter"].output([normalize_tag(t) for t in tags])


@tag_group.command("create")
@click.argument("project_key")
@click.argument("repo_slug")
@click.option("--name", "-n", required=True, help="Tag name.")
@click.option("--from", "start_point", required=True, help="Commit hash or branch.")
@click.option("--message", "-m", help="Annotation message (creates annotated tag).")
@click.pass_context
def tag_create(ctx, project_key, repo_slug, name, start_point, message):
    """Create a tag."""
    client = _get_client(ctx)
    result = client.create_tag(project_key, repo_slug, name, start_point, message=message)
    tag_type = "Annotated" if message else "Lightweight"
    ctx.obj["formatter"].success(
        f"{tag_type} tag '{name}' created",
        data={"id": result.get("id"), "displayId": result.get("displayId")},
    )
