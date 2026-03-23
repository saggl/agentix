"""Component commands for Jira."""

from agentix.jira.models import normalize_component
from ._common import _get_client, click


@click.group("component")
def component_group():
    """Manage project components."""
    pass


@component_group.command("list")
@click.option("--project", "-p", required=True, help="Project key.")
@click.pass_context
def component_list(ctx, project):
    """List components in a project."""
    client = _get_client(ctx)
    components = client.get_project_components(project)
    ctx.obj["formatter"].output([normalize_component(c) for c in components])


@component_group.command("create")
@click.option("--project", "-p", required=True, help="Project key.")
@click.option("--name", "-n", required=True, help="Component name.")
@click.option("--description", "-d", help="Component description.")
@click.option("--lead", help="Lead account ID.")
@click.pass_context
def component_create(ctx, project, name, description, lead):
    """Create a project component."""
    client = _get_client(ctx)
    result = client.create_component(
        project, name, description=description, lead_account_id=lead
    )
    ctx.obj["formatter"].success(
        f"Created component '{name}' in {project}",
        data={"id": result.get("id"), "name": result.get("name")},
    )


@component_group.command("update")
@click.argument("component_id")
@click.option("--name", "-n", help="New component name.")
@click.option("--description", "-d", help="New description.")
@click.option("--lead", help="New lead account ID.")
@click.pass_context
def component_update(ctx, component_id, name, description, lead):
    """Update a component."""
    client = _get_client(ctx)
    result = client.update_component(
        component_id, name=name, description=description, lead_account_id=lead
    )
    ctx.obj["formatter"].success(
        f"Updated component {component_id}", data=normalize_component(result)
    )


@component_group.command("delete")
@click.argument("component_id")
@click.option("--yes", is_flag=True, help="Skip confirmation.")
@click.pass_context
def component_delete(ctx, component_id, yes):
    """Delete a component."""
    if not yes:
        click.confirm(f"Delete component {component_id}?", abort=True)
    client = _get_client(ctx)
    client.delete_component(component_id)
    ctx.obj["formatter"].success(f"Deleted component {component_id}")
