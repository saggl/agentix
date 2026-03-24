"""Pipeline commands for Jenkins."""

from agentix.jenkins.models import normalize_stage
from ._common import _get_client, click


@click.group("pipeline")
def pipeline_group():
    """Manage pipeline stages."""
    pass


@pipeline_group.command("stages")
@click.argument("job_name")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.pass_context
def pipeline_stages(ctx, job_name, build_number):
    """Get pipeline stages."""
    client = _get_client(ctx)
    stages = client.get_pipeline_stages(job_name, build_number)
    ctx.obj["formatter"].output([normalize_stage(s) for s in stages])


@pipeline_group.command("log")
@click.argument("job_name")
@click.option("--stage", required=True, help="Stage ID.")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.pass_context
def pipeline_log(ctx, job_name, stage, build_number):
    """Get log for a pipeline stage."""
    client = _get_client(ctx)
    log = client.get_stage_log(job_name, stage, build_number)
    click.echo(log)
