"""Pull request commands for Bitbucket."""

from agentix.bitbucket.models import (
    normalize_activity,
    normalize_pull_request,
    normalize_pull_request_brief,
)
from ._common import _get_client, click


@click.group("pr")
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
