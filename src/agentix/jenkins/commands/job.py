"""Job commands for Jenkins."""

from agentix.jenkins.models import normalize_job, normalize_job_detail
from ._common import _get_client, click


@click.group("job")
def job_group():
    """Manage Jenkins jobs."""
    pass


@job_group.command("list")
@click.option("--folder", "-f", help="Folder path.")
@click.pass_context
def job_list(ctx, folder):
    """List jobs."""
    client = _get_client(ctx)
    jobs = client.get_jobs(folder=folder)
    ctx.obj["formatter"].output([normalize_job(j) for j in jobs])


@job_group.command("get")
@click.argument("job_name")
@click.pass_context
def job_get(ctx, job_name):
    """Get job details."""
    client = _get_client(ctx)
    job = client.get_job(job_name)
    ctx.obj["formatter"].output(normalize_job_detail(job))


@job_group.command("config")
@click.argument("job_name")
@click.pass_context
def job_config(ctx, job_name):
    """Get job configuration XML."""
    client = _get_client(ctx)
    xml = client.get_job_config(job_name)
    print(xml)


@job_group.command("enable")
@click.argument("job_name")
@click.pass_context
def job_enable(ctx, job_name):
    """Enable a job."""
    client = _get_client(ctx)
    client.enable_job(job_name)
    ctx.obj["formatter"].success(f"Enabled job {job_name}")


@job_group.command("disable")
@click.argument("job_name")
@click.pass_context
def job_disable(ctx, job_name):
    """Disable a job."""
    client = _get_client(ctx)
    client.disable_job(job_name)
    ctx.obj["formatter"].success(f"Disabled job {job_name}")
