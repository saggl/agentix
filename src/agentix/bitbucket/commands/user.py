"""User commands for Bitbucket."""

from agentix.core.exceptions import AgentixError
from agentix.bitbucket.models import normalize_user
from ._common import _get_client, click


@click.group("user")
def user_group():
    """User information."""
    pass


@user_group.command("me")
@click.pass_context
def user_me(ctx):
    """Get current user information."""
    client = _get_client(ctx)
    user = client.get_current_user()
    if user:
        ctx.obj["formatter"].output(normalize_user(user))
    else:
        ctx.obj["formatter"].error(
            AgentixError("Unable to retrieve user information.")
        )
