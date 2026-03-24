"""Test result commands for Jenkins."""

from agentix.jenkins.models import normalize_test_case, normalize_test_result
from ._common import _get_client, click


@click.group("test")
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
@click.option("--suite", "suite_filter", help="Filter failures by suite name substring.")
@click.option("--limit", type=click.IntRange(1), help="Maximum number of failures to return.")
@click.option("--include-stacktrace", is_flag=True, help="Include stacktrace/error details.")
@click.pass_context
def test_failures(ctx, job_name, build_number, suite_filter, limit, include_stacktrace):
    """Get failed test cases."""
    client = _get_client(ctx)
    failures = client.get_test_failures(
        job_name,
        build_number,
        suite_filter=suite_filter,
        limit=limit,
    )
    normalized = [normalize_test_case(f) for f in failures]
    if not include_stacktrace:
        for case in normalized:
            case.pop("errorStackTrace", None)
            case.pop("errorDetails", None)
    ctx.obj["formatter"].output(normalized)
