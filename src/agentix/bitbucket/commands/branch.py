"""Branch commands for Bitbucket."""

from agentix.bitbucket.models import normalize_branch
from ._common import _get_client, click


@click.group("branch")
def branch_group():
    """Manage branches."""
    pass


@branch_group.command("list")
@click.argument("project_key")
@click.argument("repo_slug")
@click.option("--filter", "filter_text", help="Filter branches by name.")
@click.pass_context
def branch_list(ctx, project_key, repo_slug, filter_text):
    """List branches in a repository."""
    client = _get_client(ctx)
    branches = client.get_branches(project_key, repo_slug, filter_text)
    ctx.obj["formatter"].output([normalize_branch(b) for b in branches])


@branch_group.command("get")
@click.argument("project_key")
@click.argument("repo_slug")
@click.argument("branch_name")
@click.pass_context
def branch_get(ctx, project_key, repo_slug, branch_name):
    """Get branch details."""
    client = _get_client(ctx)
    branch = client.get_branch(project_key, repo_slug, branch_name)
    ctx.obj["formatter"].output(normalize_branch(branch))


@branch_group.command("create")
@click.argument("project_key")
@click.argument("repo_slug")
@click.option("--name", "-n", required=True, help="Branch name.")
@click.option("--from", "start_point", required=True, help="Start point (branch, tag, or commit).")
@click.pass_context
def branch_create(ctx, project_key, repo_slug, name, start_point):
    """Create a new branch."""
    client = _get_client(ctx)
    branch = client.create_branch(project_key, repo_slug, name, start_point)
    ctx.obj["formatter"].success(
        f"Created branch {name}",
        data=normalize_branch(branch),
    )


@branch_group.command("delete")
@click.argument("project_key")
@click.argument("repo_slug")
@click.argument("branch_name")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.pass_context
def branch_delete(ctx, project_key, repo_slug, branch_name, yes):
    """Delete a branch."""
    if not yes:
        click.confirm(f"Delete branch {branch_name}?", abort=True)
    client = _get_client(ctx)
    client.delete_branch(project_key, repo_slug, branch_name)
    ctx.obj["formatter"].success(f"Deleted branch {branch_name}")


@branch_group.command("default")
@click.argument("project_key")
@click.argument("repo_slug")
@click.pass_context
def branch_default(ctx, project_key, repo_slug):
    """Get the default branch."""
    client = _get_client(ctx)
    branch = client.get_default_branch(project_key, repo_slug)
    ctx.obj["formatter"].output(normalize_branch(branch))
