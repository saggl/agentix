"""Node commands for Jenkins."""

from agentix.jenkins.models import normalize_node
from ._common import _get_client, click


@click.group("node")
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
