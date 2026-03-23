"""Repository commands for Bitbucket."""

from agentix.bitbucket.models import normalize_repository, normalize_repository_brief
from ._common import _get_client, click


@click.group("repo")
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
