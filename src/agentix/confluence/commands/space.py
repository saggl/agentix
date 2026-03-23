"""Space commands for Confluence."""

from agentix.core.exceptions import AgentixError
from agentix.confluence.models import normalize_space
from ._common import _get_client, click


@click.group("space")
def space_group():
    """Manage spaces."""
    pass


@space_group.command("list")
@click.pass_context
def space_list(ctx):
    """List spaces."""
    client = _get_client(ctx)
    spaces = client.get_spaces()
    ctx.obj["formatter"].output([normalize_space(s) for s in spaces])


@space_group.command("get")
@click.argument("space_id")
@click.pass_context
def space_get(ctx, space_id):
    """Get space details."""
    client = _get_client(ctx)
    space = client.get_space(space_id)
    ctx.obj["formatter"].output(normalize_space(space))


@space_group.command("find")
@click.option("--key", "-k", required=True, help="Space key.")
@click.pass_context
def space_find(ctx, key):
    """Find a space by its key."""
    client = _get_client(ctx)
    space = client.get_space_by_key(key)
    if space:
        ctx.obj["formatter"].output(normalize_space(space))
    else:
        ctx.obj["formatter"].error(AgentixError(f"Space '{key}' not found"))
        ctx.exit(1)
