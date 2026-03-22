"""CLI commands for Bitbucket integration."""

import click

from agentix.core.auth import resolve_auth
from agentix.core.exceptions import AgentixError
from agentix.bitbucket.client import BitbucketClient
from agentix.bitbucket.models import (
    normalize_activity,
    normalize_branch,
    normalize_build_status,
    normalize_commit,
    normalize_commit_brief,
    normalize_project,
    normalize_pull_request,
    normalize_pull_request_brief,
    normalize_repository,
    normalize_repository_brief,
    normalize_tag,
    normalize_user,
)


def _get_client(ctx: click.Context) -> BitbucketClient:
    auth = resolve_auth(
        "bitbucket",
        ctx.obj["config_manager"],
        profile_name=ctx.obj["profile"],
    )
    return BitbucketClient(auth.base_url, auth.user, auth.token, auth.auth_type)


@click.group("bitbucket")
def bitbucket_group():
    """Bitbucket repository management."""
    pass


# -- Project commands --


@bitbucket_group.group("project")
def project_group():
    """Manage projects."""
    pass


@project_group.command("list")
@click.pass_context
def project_list(ctx):
    """List all projects."""
    client = _get_client(ctx)
    projects = client.get_projects()
    ctx.obj["formatter"].output([normalize_project(p) for p in projects])


@project_group.command("get")
@click.argument("project_key")
@click.pass_context
def project_get(ctx, project_key):
    """Get project details."""
    client = _get_client(ctx)
    project = client.get_project(project_key)
    ctx.obj["formatter"].output(normalize_project(project))


# -- Repository commands --


@bitbucket_group.group("repo")
def repo_group():
    """Manage repositories."""
    pass


@repo_group.command("list")
@click.option("--project", "-p", required=True, help="Project key.")
@click.pass_context
def repo_list(ctx, project):
    """List repositories in a project."""
    client = _get_client(ctx)
    repos = client.get_repositories(project)
    ctx.obj["formatter"].output([normalize_repository_brief(r) for r in repos])


@repo_group.command("get")
@click.argument("project_key")
@click.argument("repo_slug")
@click.pass_context
def repo_get(ctx, project_key, repo_slug):
    """Get repository details."""
    client = _get_client(ctx)
    repo = client.get_repository(project_key, repo_slug)
    ctx.obj["formatter"].output(normalize_repository(repo))


@repo_group.command("create")
@click.option("--project", "-p", required=True, help="Project key.")
@click.option("--name", "-n", required=True, help="Repository name.")
@click.option("--description", "-d", help="Repository description.")
@click.option("--forkable/--no-forkable", default=True, help="Allow forking.")
@click.option("--public/--private", default=False, help="Public or private repository.")
@click.pass_context
def repo_create(ctx, project, name, description, forkable, public):
    """Create a new repository."""
    client = _get_client(ctx)
    repo = client.create_repository(
        project_key=project,
        name=name,
        description=description,
        forkable=forkable,
        public=public,
    )
    ctx.obj["formatter"].success(
        f"Created repository {repo.get('slug', '')}",
        data=normalize_repository(repo),
    )


@repo_group.command("browse")
@click.argument("project_key")
@click.argument("repo_slug")
@click.option("--path", help="Path to browse.")
@click.option("--at", help="Branch or commit to browse at.")
@click.pass_context
def repo_browse(ctx, project_key, repo_slug, path, at):
    """Browse files in a repository."""
    client = _get_client(ctx)
    files = client.get_repository_files(project_key, repo_slug, path, at)
    ctx.obj["formatter"].output(files)


# -- Branch commands --


@bitbucket_group.group("branch")
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


# -- Tag commands --


@bitbucket_group.group("tag")
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


# -- Pull Request commands --


@bitbucket_group.group("pr")
def pr_group():
    """Manage pull requests."""
    pass


@pr_group.command("list")
@click.argument("project_key")
@click.argument("repo_slug")
@click.option("--state", type=click.Choice(["OPEN", "MERGED", "DECLINED", "ALL"], case_sensitive=False), help="Filter by state.")
@click.option("--direction", type=click.Choice(["INCOMING", "OUTGOING"], case_sensitive=False), default="INCOMING", help="PR direction.")
@click.option("--at", help="Filter by branch or commit.")
@click.pass_context
def pr_list(ctx, project_key, repo_slug, state, direction, at):
    """List pull requests."""
    client = _get_client(ctx)
    prs = client.get_pull_requests(project_key, repo_slug, state, direction, at)
    ctx.obj["formatter"].output([normalize_pull_request_brief(pr) for pr in prs])


@pr_group.command("get")
@click.argument("project_key")
@click.argument("repo_slug")
@click.argument("pr_id", type=int)
@click.pass_context
def pr_get(ctx, project_key, repo_slug, pr_id):
    """Get pull request details."""
    client = _get_client(ctx)
    pr = client.get_pull_request(project_key, repo_slug, pr_id)
    ctx.obj["formatter"].output(normalize_pull_request(pr))


@pr_group.command("create")
@click.argument("project_key")
@click.argument("repo_slug")
@click.option("--title", "-t", required=True, help="PR title.")
@click.option("--from", "from_ref", required=True, help="Source branch.")
@click.option("--to", "to_ref", required=True, help="Target branch.")
@click.option("--description", "-d", help="PR description.")
@click.option("--reviewers", "-r", help="Comma-separated list of reviewer usernames.")
@click.pass_context
def pr_create(ctx, project_key, repo_slug, title, from_ref, to_ref, description, reviewers):
    """Create a pull request."""
    client = _get_client(ctx)
    reviewer_list = [r.strip() for r in reviewers.split(",")] if reviewers else None
    pr = client.create_pull_request(
        project_key=project_key,
        repo_slug=repo_slug,
        title=title,
        from_ref=from_ref,
        to_ref=to_ref,
        description=description,
        reviewers=reviewer_list,
    )
    ctx.obj["formatter"].success(
        f"Created pull request #{pr.get('id', '')}",
        data=normalize_pull_request(pr),
    )


@pr_group.command("merge")
@click.argument("project_key")
@click.argument("repo_slug")
@click.argument("pr_id", type=int)
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.pass_context
def pr_merge(ctx, project_key, repo_slug, pr_id, yes):
    """Merge a pull request."""
    client = _get_client(ctx)
    pr = client.get_pull_request(project_key, repo_slug, pr_id)
    version = pr.get("version", 0)

    if not yes:
        click.confirm(f"Merge pull request #{pr_id}?", abort=True)

    result = client.merge_pull_request(project_key, repo_slug, pr_id, version)
    ctx.obj["formatter"].success(
        f"Merged pull request #{pr_id}",
        data={"state": result.get("state", "")},
    )


@pr_group.command("approve")
@click.argument("project_key")
@click.argument("repo_slug")
@click.argument("pr_id", type=int)
@click.pass_context
def pr_approve(ctx, project_key, repo_slug, pr_id):
    """Approve a pull request."""
    client = _get_client(ctx)
    client.approve_pull_request(project_key, repo_slug, pr_id)
    ctx.obj["formatter"].success(f"Approved pull request #{pr_id}")


@pr_group.command("decline")
@click.argument("project_key")
@click.argument("repo_slug")
@click.argument("pr_id", type=int)
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.pass_context
def pr_decline(ctx, project_key, repo_slug, pr_id, yes):
    """Decline a pull request."""
    if not yes:
        click.confirm(f"Decline pull request #{pr_id}?", abort=True)

    client = _get_client(ctx)
    pr = client.get_pull_request(project_key, repo_slug, pr_id)
    version = pr.get("version", 0)

    result = client.decline_pull_request(project_key, repo_slug, pr_id, version)
    ctx.obj["formatter"].success(
        f"Declined pull request #{pr_id}",
        data={"state": result.get("state", "")},
    )


@pr_group.command("comment")
@click.argument("project_key")
@click.argument("repo_slug")
@click.argument("pr_id", type=int)
@click.option("--text", "-t", required=True, help="Comment text.")
@click.pass_context
def pr_comment(ctx, project_key, repo_slug, pr_id, text):
    """Add a comment to a pull request."""
    client = _get_client(ctx)
    comment = client.add_pr_comment(project_key, repo_slug, pr_id, text)
    ctx.obj["formatter"].success(
        f"Added comment to pull request #{pr_id}",
        data={"id": comment.get("id", "")},
    )


@pr_group.command("activities")
@click.argument("project_key")
@click.argument("repo_slug")
@click.argument("pr_id", type=int)
@click.pass_context
def pr_activities(ctx, project_key, repo_slug, pr_id):
    """Get pull request activities and comments."""
    client = _get_client(ctx)
    activities = client.get_pr_activities(project_key, repo_slug, pr_id)
    ctx.obj["formatter"].output([normalize_activity(a) for a in activities])


# -- Commit commands --


@bitbucket_group.group("commit")
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


# -- Build Status commands --


@bitbucket_group.group("build")
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


# -- User commands --


@bitbucket_group.group("user")
def user_group():
    """User information."""
    pass


@user_group.command("me")
@click.pass_context
def user_me(ctx):
    """Get current user information."""
    client = _get_client(ctx)
    user = client.get_current_user()
    if user:
        ctx.obj["formatter"].output(normalize_user(user))
    else:
        ctx.obj["formatter"].error(
            AgentixError("Unable to retrieve user information.")
        )
