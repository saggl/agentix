"""Health check commands for Polarion."""

from ._common import _get_client, click


@click.group("health")
def health_group():
    """Polarion server health checks."""
    pass


@health_group.command("check")
@click.pass_context
def health_check(ctx):
    """Run a health check against the Polarion server."""
    client = _get_client(ctx)
    result = client.healthcheck()
    ctx.obj["formatter"].output(result)


@health_group.command("capabilities")
@click.pass_context
def health_capabilities(ctx):
    """Show Polarion server capabilities."""
    client = _get_client(ctx)
    result = client.capabilities()
    ctx.obj["formatter"].output(result)
