"""Queue commands for Jenkins."""

from agentix.jenkins.models import normalize_queue_item
from ._common import _get_client, click


@click.group("queue")
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
