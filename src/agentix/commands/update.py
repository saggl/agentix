"""Update command for agentix."""

import click

from agentix.core.update import detect_installation_method, perform_upgrade


@click.command("update")
@click.option(
    "--method",
    type=click.Choice(["auto", "uv", "pip"]),
    default="auto",
    show_default=True,
    help="Installation method used for upgrade.",
)
@click.pass_context
def update_command(ctx, method):
    """Update agentix immediately."""
    selected_method = detect_installation_method() if method == "auto" else method
    perform_upgrade(selected_method)
    ctx.obj["formatter"].success(
        f"Started background upgrade using {selected_method}.",
        data={"method": selected_method},
    )
