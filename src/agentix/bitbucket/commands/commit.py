"""Commit commands for Bitbucket."""

from agentix.bitbucket.models import normalize_commit, normalize_commit_brief
from ._common import _get_client, click


@click.group("commit")
def commit_group():
    """View commits."""
    pass


@commit_group.command("list")
@click.argument("project_key")
@click.argument("repo_slug")
@click.option("--until", help="Commit ID or branch to list until.")
@click.option("--since", help="Commit ID or branch to list since.")
@click.option("--path", help="Filter by file path.")
@click.option("--max-results", type=int, default=50, help="Maximum number of results.")
@click.pass_context
def commit_list(ctx, project_key, repo_slug, until, since, path, max_results):
    """List commits in a repository."""
    client = _get_client(ctx)
    commits = client.get_commits(project_key, repo_slug, until, since, path, max_results)
    ctx.obj["formatter"].output([normalize_commit_brief(c) for c in commits])


@commit_group.command("get")
@click.argument("project_key")
@click.argument("repo_slug")
@click.argument("commit_id")
@click.pass_context
def commit_get(ctx, project_key, repo_slug, commit_id):
    """Get commit details."""
    client = _get_client(ctx)
    commit = client.get_commit(project_key, repo_slug, commit_id)
    ctx.obj["formatter"].output(normalize_commit(commit))


@commit_group.command("changes")
@click.argument("project_key")
@click.argument("repo_slug")
@click.argument("commit_id")
@click.pass_context
def commit_changes(ctx, project_key, repo_slug, commit_id):
    """Get files changed in a commit."""
    client = _get_client(ctx)
    changes = client.get_commit_changes(project_key, repo_slug, commit_id)
    ctx.obj["formatter"].output(changes)


@commit_group.command("diff")
@click.argument("project_key")
@click.argument("repo_slug")
@click.argument("commit_id")
@click.option("--path", help="Filter diff by file path.")
@click.pass_context
def commit_diff(ctx, project_key, repo_slug, commit_id, path):
    """Get diff for a commit."""
    client = _get_client(ctx)
    diff = client.get_commit_diff(project_key, repo_slug, commit_id, path)
    ctx.obj["formatter"].output(diff)
