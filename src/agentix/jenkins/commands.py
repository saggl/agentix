"""CLI commands for Jenkins integration."""

import click

from agentix.core.auth import resolve_auth
from agentix.jenkins.client import JenkinsClient
from agentix.jenkins.models import (
    normalize_artifact,
    normalize_build,
    normalize_build_brief,
    normalize_job,
    normalize_job_detail,
    normalize_node,
    normalize_queue_item,
    normalize_stage,
    normalize_test_case,
    normalize_test_result,
)


def _get_client(ctx: click.Context) -> JenkinsClient:
    auth = resolve_auth(
        "jenkins",
        ctx.obj["config_manager"],
        profile_name=ctx.obj["profile"],
    )
    return JenkinsClient(auth.base_url, auth.user, auth.token, auth.auth_type)


@click.group("jenkins")
def jenkins_group():
    """Jenkins CI/CD."""
    pass


# -- Job commands --


@jenkins_group.group("job")
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


# -- Build commands --


@jenkins_group.group("build")
def build_group():
    """Manage builds."""
    pass


@build_group.command("trigger")
@click.argument("job_name")
@click.option("--param", "-P", multiple=True, help="Build parameter (KEY=VALUE).")
@click.option("--wait", is_flag=True, help="Wait for build to complete.")
@click.option("--timeout", default=300, type=int, help="Wait timeout in seconds (default: 300).")
@click.pass_context
def build_trigger(ctx, job_name, param, wait, timeout):
    """Trigger a build."""
    client = _get_client(ctx)
    params = {}
    for p in param:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k] = v

    queue_id = client.trigger_build(job_name, params=params or None)

    if wait and queue_id:
        ctx.obj["formatter"].success(
            f"Build queued (queue ID: {queue_id}). Waiting...",
        )
        result = client.wait_for_build(job_name, queue_id, timeout=timeout)
        ctx.obj["formatter"].output(normalize_build(result))
    else:
        ctx.obj["formatter"].success(
            f"Build triggered for {job_name}",
            data={"queue_id": queue_id},
        )


@build_group.command("status")
@click.argument("job_name")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.pass_context
def build_status(ctx, job_name, build_number):
    """Get build status."""
    client = _get_client(ctx)
    build = client.get_build(job_name, build_number)
    ctx.obj["formatter"].output(normalize_build(build))


@build_group.command("log")
@click.argument("job_name")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.option("--tail", "-t", type=int, help="Show last N lines.")
@click.pass_context
def build_log(ctx, job_name, build_number, tail):
    """Get build console log."""
    client = _get_client(ctx)
    log = client.get_build_log(job_name, build_number, tail=tail)
    print(log)


@build_group.command("list")
@click.argument("job_name")
@click.option("--max-results", default=10, type=int, help="Max results.")
@click.pass_context
def build_list(ctx, job_name, max_results):
    """List recent builds."""
    client = _get_client(ctx)
    builds = client.get_builds(job_name, max_results=max_results)
    ctx.obj["formatter"].output([normalize_build_brief(b) for b in builds])


@build_group.command("abort")
@click.argument("job_name")
@click.argument("build_number", type=int)
@click.pass_context
def build_abort(ctx, job_name, build_number):
    """Abort a running build."""
    client = _get_client(ctx)
    client.abort_build(job_name, build_number)
    ctx.obj["formatter"].success(f"Aborted build #{build_number} of {job_name}")


@build_group.command("artifacts")
@click.argument("job_name")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.pass_context
def build_artifacts(ctx, job_name, build_number):
    """List build artifacts."""
    client = _get_client(ctx)
    artifacts = client.get_build_artifacts(job_name, build_number=build_number)
    ctx.obj["formatter"].output([normalize_artifact(a) for a in artifacts])


@build_group.command("download")
@click.argument("job_name")
@click.option("--artifact", "-a", "artifact_path", required=True, help="Artifact relative path.")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.option("--output", "-o", help="Output file path (default: stdout).")
@click.pass_context
def build_download(ctx, job_name, artifact_path, build_number, output):
    """Download a build artifact."""
    client = _get_client(ctx)

    if output:
        # Use streaming download for files to avoid loading into memory
        client.download_artifact_to_file(
            job_name, artifact_path, output, build_number=build_number
        )
        ctx.obj["formatter"].success(f"Downloaded to {output}")
    else:
        # For stdout, load into memory (typically for small files piped to other commands)
        content = client.download_artifact(job_name, artifact_path, build_number=build_number)
        import sys
        sys.stdout.buffer.write(content)


# -- Test commands --


@jenkins_group.group("test")
def test_group():
    """Manage test results."""
    pass


@test_group.command("results")
@click.argument("job_name")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.pass_context
def test_results(ctx, job_name, build_number):
    """Get test results summary."""
    client = _get_client(ctx)
    results = client.get_test_results(job_name, build_number)
    ctx.obj["formatter"].output(normalize_test_result(results))


@test_group.command("failures")
@click.argument("job_name")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.pass_context
def test_failures(ctx, job_name, build_number):
    """Get failed test cases."""
    client = _get_client(ctx)
    failures = client.get_test_failures(job_name, build_number)
    ctx.obj["formatter"].output([normalize_test_case(f) for f in failures])


# -- Pipeline commands --


@jenkins_group.group("pipeline")
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
    print(log)


# -- Queue commands --


@jenkins_group.group("queue")
def queue_group():
    """Manage build queue."""
    pass


@queue_group.command("list")
@click.pass_context
def queue_list(ctx):
    """List queued builds."""
    client = _get_client(ctx)
    items = client.get_queue()
    ctx.obj["formatter"].output([normalize_queue_item(i) for i in items])


@queue_group.command("cancel")
@click.argument("queue_id", type=int)
@click.pass_context
def queue_cancel(ctx, queue_id):
    """Cancel a queued build."""
    client = _get_client(ctx)
    client.cancel_queue_item(queue_id)
    ctx.obj["formatter"].success(f"Cancelled queue item {queue_id}")


# -- Node commands --


@jenkins_group.group("node")
def node_group():
    """Manage nodes."""
    pass


@node_group.command("list")
@click.pass_context
def node_list(ctx):
    """List nodes."""
    client = _get_client(ctx)
    nodes = client.get_nodes()
    ctx.obj["formatter"].output([normalize_node(n) for n in nodes])


@node_group.command("get")
@click.argument("node_name")
@click.pass_context
def node_get(ctx, node_name):
    """Get node details."""
    client = _get_client(ctx)
    node = client.get_node(node_name)
    ctx.obj["formatter"].output(normalize_node(node))
