"""Build status commands for Bitbucket."""

from agentix.bitbucket.models import normalize_build_status
from ._common import _get_client, click


@click.group("build")
def build_group():
    """Manage build statuses."""
    pass


@build_group.command("status")
@click.argument("commit_id")
@click.pass_context
def build_status(ctx, commit_id):
    """Get build statuses for a commit."""
    client = _get_client(ctx)
    statuses = client.get_commit_build_status(commit_id)
    ctx.obj["formatter"].output([normalize_build_status(s) for s in statuses])


@build_group.command("set")
@click.argument("commit_id")
@click.option("--state", required=True, type=click.Choice(["SUCCESSFUL", "FAILED", "INPROGRESS"], case_sensitive=False), help="Build state.")
@click.option("--key", required=True, help="Unique build key.")
@click.option("--name", required=True, help="Build name.")
@click.option("--url", required=True, help="URL to build results.")
@click.option("--description", "-d", help="Build description.")
@click.pass_context
def build_set(ctx, commit_id, state, key, name, url, description):
    """Set build status for a commit."""
    client = _get_client(ctx)
    status = client.set_commit_build_status(
        commit_id=commit_id,
        state=state,
        key=key,
        name=name,
        url=url,
        description=description,
    )
    ctx.obj["formatter"].success(
        f"Set build status for commit {commit_id}",
        data=normalize_build_status(status),
    )
