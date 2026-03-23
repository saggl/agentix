"""CLI commands for agentix config management."""

import json

import click
import requests
from requests.auth import HTTPBasicAuth

from agentix.config.models import (
    ConfluenceConfig,
    JenkinsConfig,
    JiraConfig,
)
from agentix.core.exceptions import ConfigError


@click.group("config")
def config_group():
    """Manage agentix configuration."""
    pass


@config_group.command()
@click.pass_context
def init(ctx):
    """Interactive setup wizard."""
    cm = ctx.obj["config_manager"]
    config = cm.config

    profile_name = click.prompt("Profile name", default="default")
    profile = config.get_profile(profile_name)

    # Jira
    if click.confirm("Configure Jira?", default=True):
        profile.jira = _setup_jira()

    # Confluence
    if click.confirm("Configure Confluence?", default=True):
        profile.confluence = _setup_confluence(profile.jira)

    # Jenkins
    if click.confirm("Configure Jenkins?", default=False):
        profile.jenkins = _setup_jenkins()

    config.default_profile = profile_name
    config.profiles[profile_name] = profile
    cm.save(config)

    formatter = ctx.obj["formatter"]
    formatter.success(f"Configuration saved to {cm.config_path}")


def _setup_jira() -> JiraConfig:
    base_url = click.prompt("Jira base URL (e.g., https://company.atlassian.net)")
    email = click.prompt("Jira email")
    api_token = click.prompt("Jira API token", hide_input=True)

    # Validate
    click.echo("Validating credentials... ", nl=False)
    try:
        resp = requests.get(
            f"{base_url.rstrip('/')}/rest/api/3/myself",
            auth=HTTPBasicAuth(email, api_token),
            timeout=10,
        )
        if resp.ok:
            user = resp.json()
            click.echo(f"OK (authenticated as {user.get('displayName', email)})")
        else:
            click.echo(f"Warning: got HTTP {resp.status_code} — credentials may be invalid")
    except requests.RequestException as e:
        click.echo(f"Warning: could not validate — {e}")

    return JiraConfig(base_url=base_url.rstrip("/"), email=email, api_token=api_token)


def _setup_confluence(jira_config: JiraConfig) -> ConfluenceConfig:
    default_url = ""
    default_email = ""
    default_token = ""

    if jira_config.base_url:
        default_url = jira_config.base_url.rstrip("/") + "/wiki"
        default_email = jira_config.email
        default_token = jira_config.api_token

    base_url = click.prompt(
        "Confluence base URL", default=default_url or None
    )
    email = click.prompt("Confluence email", default=default_email or None)
    api_token = click.prompt(
        "Confluence API token (same as Jira for Atlassian Cloud)",
        default=default_token or None,
        hide_input=True,
    )

    return ConfluenceConfig(
        base_url=base_url.rstrip("/"), email=email, api_token=api_token
    )


def _setup_jenkins() -> JenkinsConfig:
    base_url = click.prompt("Jenkins base URL (e.g., https://jenkins.company.com)")
    username = click.prompt("Jenkins username")
    api_token = click.prompt("Jenkins API token", hide_input=True)

    # Validate
    click.echo("Validating credentials... ", nl=False)
    try:
        resp = requests.get(
            f"{base_url.rstrip('/')}/api/json",
            auth=HTTPBasicAuth(username, api_token),
            timeout=10,
        )
        if resp.ok:
            click.echo("OK")
        else:
            click.echo(f"Warning: got HTTP {resp.status_code}")
    except requests.RequestException as e:
        click.echo(f"Warning: could not validate — {e}")

    return JenkinsConfig(
        base_url=base_url.rstrip("/"), username=username, api_token=api_token
    )


@config_group.command()
@click.argument("key")
@click.argument("value")
@click.pass_context
def set(ctx, key, value):
    """Set a config value (e.g., agentix config set profiles.work.jira.base_url https://...)."""
    cm = ctx.obj["config_manager"]
    cm.set_value(key, value)
    ctx.obj["formatter"].success(f"Set {key} = {value}")


@config_group.command()
@click.argument("key")
@click.pass_context
def get(ctx, key):
    """Get a config value."""
    cm = ctx.obj["config_manager"]
    try:
        value = cm.get_value(key)
    except ConfigError as e:
        ctx.obj["formatter"].error(e)
        ctx.exit(2)
        return
    formatter = ctx.obj["formatter"]
    if isinstance(value, dict):
        formatter.output(value)
    else:
        if formatter.fmt == "json":
            print(json.dumps({"key": key, "value": value}))
        else:
            print(value)


@config_group.command()
@click.pass_context
def show(ctx):
    """Show full config with tokens masked."""
    cm = ctx.obj["config_manager"]
    if not cm.exists():
        click.echo("No configuration found. Run 'agentix config init' to create one.")
        ctx.exit(2)
        return
    ctx.obj["formatter"].output(cm.mask_tokens())


@config_group.command()
@click.pass_context
def path(ctx):
    """Print config file path."""
    cm = ctx.obj["config_manager"]
    formatter = ctx.obj["formatter"]
    if formatter.fmt == "json":
        click.echo(json.dumps({"path": str(cm.config_path), "exists": cm.exists()}))
    else:
        click.echo(cm.config_path)
