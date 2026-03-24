"""Build commands for Jenkins."""

import json
from pathlib import Path

from agentix.core.exceptions import AgentixError
from agentix.jenkins.models import (
    normalize_artifact,
    normalize_build,
    normalize_build_brief,
    normalize_change,
    normalize_stage,
)
from ._common import _get_client, click


@click.group("build")
def build_group():
    """Manage builds."""
    pass


def _parse_params(param, params_file):
    params = {}
    for p in param:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k] = v

    if params_file:
        path = Path(params_file)
        content = path.read_text(encoding="utf-8").strip()
        if path.suffix.lower() == ".json":
            data = json.loads(content) if content else {}
            if isinstance(data, dict):
                params.update({str(k): str(v) for k, v in data.items()})
        else:
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                params[k.strip()] = v.strip()
    return params


@build_group.command("trigger")
@click.argument("job_name")
@click.option("--param", "-P", multiple=True, help="Build parameter (KEY=VALUE).")
@click.option("--params-file", type=click.Path(exists=True), help="Load build parameters from .env or .json file.")
@click.option("--wait", is_flag=True, help="Wait for build to complete.")
@click.option("--timeout", default=300, type=int, help="Wait timeout in seconds (default: 300).")
@click.pass_context
def build_trigger(ctx, job_name, param, params_file, wait, timeout):
    """Trigger a build."""
    client = _get_client(ctx)
    params = _parse_params(param, params_file)

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
    click.echo(log)


@build_group.command("list")
@click.argument("job_name")
@click.option("--max-results", default=10, type=click.IntRange(1), help="Max results.")
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


@build_group.command("wait")
@click.argument("job_name")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.option("--timeout", default=300, type=int, help="Wait timeout in seconds (default: 300).")
@click.pass_context
def build_wait(ctx, job_name, build_number, timeout):
    """Wait for a build to complete."""
    client = _get_client(ctx)
    build = client.wait_for_build_result(job_name, build_number=build_number, timeout=timeout)
    normalized = normalize_build(build)
    ctx.obj["formatter"].output(normalized)

    result = (build.get("result") or "").upper()
    if result and result not in {"SUCCESS"}:
        ctx.exit(1)


@build_group.command("latest-failed")
@click.argument("job_name")
@click.pass_context
def build_latest_failed(ctx, job_name):
    """Get latest failed build."""
    client = _get_client(ctx)
    build = client.get_latest_build_by_result(job_name, "FAILURE")
    if not build:
        ctx.obj["formatter"].output({"message": "No failed build found."})
        return
    ctx.obj["formatter"].output(normalize_build(build))


@build_group.command("latest-success")
@click.argument("job_name")
@click.pass_context
def build_latest_success(ctx, job_name):
    """Get latest successful build."""
    client = _get_client(ctx)
    build = client.get_latest_build_by_result(job_name, "SUCCESS")
    if not build:
        ctx.obj["formatter"].output({"message": "No successful build found."})
        return
    ctx.obj["formatter"].output(normalize_build(build))


@build_group.command("failed-stage")
@click.argument("job_name")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.pass_context
def build_failed_stage(ctx, job_name, build_number):
    """List failed pipeline stages for a build."""
    client = _get_client(ctx)
    stages = client.get_pipeline_stages(job_name, build_number)
    failed = [s for s in stages if str(s.get("status", "")).upper() in {"FAILED", "FAILURE", "ABORTED"}]
    ctx.obj["formatter"].output([normalize_stage(s) for s in failed])


def _failed_stages(client, job_name, build_number):
    stages = client.get_pipeline_stages(job_name, build_number)
    return [s for s in stages if str(s.get("status", "")).upper() in {"FAILED", "FAILURE", "ABORTED"}]


@build_group.command("failed-log")
@click.argument("job_name")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.option("--stage", "stage_ref", help="Stage id or name.")
@click.option("--tail", "-t", type=int, help="Show last N lines from stage log.")
@click.pass_context
def build_failed_log(ctx, job_name, build_number, stage_ref, tail):
    """Get logs from failed pipeline stage(s)."""
    client = _get_client(ctx)
    stages = client.get_pipeline_stages(job_name, build_number)

    selected = []
    if stage_ref:
        for s in stages:
            if str(s.get("id")) == stage_ref or str(s.get("name", "")).lower() == stage_ref.lower():
                selected = [s]
                break
    else:
        selected = _failed_stages(client, job_name, build_number)

    logs = []
    for s in selected:
        sid = str(s.get("id", ""))
        if not sid:
            continue
        text = client.get_stage_log(job_name, sid, build_number)
        if tail:
            lines = text.splitlines()
            text = "\n".join(lines[-tail:])
        logs.append({
            "stage": normalize_stage(s),
            "log": text,
        })

    ctx.obj["formatter"].output(logs)


@build_group.command("failure-summary")
@click.argument("job_name")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.pass_context
def build_failure_summary(ctx, job_name, build_number):
    """Summarize failing stages and tests for a build."""
    client = _get_client(ctx)
    build = client.get_build(job_name, build_number)
    failed = _failed_stages(client, job_name, build_number)

    errors = []
    for s in failed:
        sid = str(s.get("id", ""))
        if not sid:
            continue
        log = client.get_stage_log(job_name, sid, build_number)
        snippet = "\n".join(log.splitlines()[-10:])
        errors.append({"stage": s.get("name", sid), "snippet": snippet})

    tests = {"total": 0, "failed": 0, "skipped": 0}
    try:
        tr = client.get_test_results(job_name, build_number)
        tests = {
            "total": tr.get("totalCount", 0),
            "failed": tr.get("failCount", 0),
            "skipped": tr.get("skipCount", 0),
        }
    except AgentixError:
        pass

    changes = [normalize_change(c) for c in client.get_build_changes(job_name, build_number)]

    summary = {
        "job": job_name,
        "build_number": build.get("number"),
        "result": build.get("result"),
        "url": build.get("url"),
        "failed_stages": [normalize_stage(s) for s in failed],
        "errors": errors,
        "tests": tests,
        "changes": changes,
    }
    ctx.obj["formatter"].output(summary)


@build_group.command("debug")
@click.argument("job_name")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.option("--latest-failed", is_flag=True, help="Use latest failed build.")
@click.option("--tail", "-t", type=int, default=50, help="Tail lines for failed stage logs.")
@click.pass_context
def build_debug(ctx, job_name, build_number, latest_failed, tail):
    """Produce a debug bundle for a build failure."""
    client = _get_client(ctx)

    if latest_failed:
        b = client.get_latest_build_by_result(job_name, "FAILURE")
        if not b:
            ctx.obj["formatter"].output({"message": "No failed build found."})
            return
        build_number = b.get("number")

    build = client.get_build(job_name, build_number)
    failed = _failed_stages(client, job_name, build_number)

    stage_logs = []
    for s in failed:
        sid = str(s.get("id", ""))
        if not sid:
            continue
        log = client.get_stage_log(job_name, sid, build_number)
        if tail:
            log = "\n".join(log.splitlines()[-tail:])
        stage_logs.append({"stage": normalize_stage(s), "log": log})

    failures = []
    try:
        failures = client.get_test_failures(job_name, build_number)
    except AgentixError:
        pass

    changes = [normalize_change(c) for c in client.get_build_changes(job_name, build_number)]

    ctx.obj["formatter"].output(
        {
            "job": job_name,
            "build": normalize_build(build),
            "failed_stages": [normalize_stage(s) for s in failed],
            "stage_logs": stage_logs,
            "test_failures": failures,
            "changes": changes,
        }
    )


@build_group.command("changes")
@click.argument("job_name")
@click.option("--build-number", "-n", type=int, help="Build number (default: latest).")
@click.pass_context
def build_changes(ctx, job_name, build_number):
    """List changelog entries for a build."""
    client = _get_client(ctx)
    changes = client.get_build_changes(job_name, build_number)
    ctx.obj["formatter"].output([normalize_change(c) for c in changes])


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
