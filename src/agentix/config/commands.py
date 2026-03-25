"""CLI commands for agentix config management."""

import json

import click
import requests
from requests.auth import HTTPBasicAuth

from agentix.config.models import (
    BitbucketConfig,
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
        profile.confluence = _setup_confluence()

    # Jenkins
    if click.confirm("Configure Jenkins?", default=False):
        profile.jenkins = _setup_jenkins()

    # Bitbucket
    if click.confirm("Configure Bitbucket?", default=False):
        profile.bitbucket = _setup_bitbucket()

    config.default_profile = profile_name
    config.profiles[profile_name] = profile
    cm.save(config)

    formatter = ctx.obj["formatter"]
    formatter.success(f"Configuration saved to {cm.config_path}")


def _is_jira_cloud(base_url: str) -> bool:
    return ".atlassian.net" in base_url.lower()


def _setup_jira() -> JiraConfig:
    base_url = click.prompt("Jira base URL (e.g., https://company.atlassian.net)")
    base_url = base_url.rstrip("/")
    is_cloud = _is_jira_cloud(base_url)

    if is_cloud:
        email = click.prompt("Jira email")
        api_token = click.prompt("Jira API token", hide_input=True)
        auth_type = "basic"
    else:
        click.echo("Detected Jira Server/Data Center.")
        api_token = click.prompt("Jira Personal Access Token (PAT)", hide_input=True)
        email = ""
        auth_type = "bearer"

    # Validate
    click.echo("Validating credentials... ", nl=False)
    try:
        if is_cloud:
            resp = requests.get(
                f"{base_url}/rest/api/3/myself",
                auth=HTTPBasicAuth(email, api_token),
                timeout=10,
            )
        else:
            resp = requests.get(
                f"{base_url}/rest/api/2/myself",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=10,
            )
        if resp.ok:
            user = resp.json()
            display = user.get("displayName", email or "user")
            click.echo(f"OK (authenticated as {display})")
        else:
            click.echo(f"Warning: got HTTP {resp.status_code} — credentials may be invalid")
    except requests.RequestException as e:
        click.echo(f"Warning: could not validate — {e}")

    return JiraConfig(base_url=base_url, email=email, api_token=api_token, auth_type=auth_type)


def _is_confluence_cloud(base_url: str) -> bool:
    return ".atlassian.net" in base_url.lower()


def _setup_confluence() -> ConfluenceConfig:
    base_url = click.prompt(
        "Confluence base URL (e.g., https://confluence.company.com)"
    )
    base_url = base_url.rstrip("/")
    is_cloud = _is_confluence_cloud(base_url)

    if not is_cloud:
        click.echo("Detected Confluence Server/Data Center.")
        api_token = click.prompt("Confluence Personal Access Token (PAT)", hide_input=True)
        email = ""
        auth_type = "bearer"
    else:
        email = click.prompt("Confluence email")
        api_token = click.prompt("Confluence API token", hide_input=True)
        auth_type = "basic"

    # Validate
    click.echo("Validating credentials... ", nl=False)
    try:
        if is_cloud:
            resp = requests.get(
                f"{base_url}/rest/api/user/current",
                auth=HTTPBasicAuth(email, api_token),
                timeout=10,
            )
        else:
            resp = requests.get(
                f"{base_url}/rest/api/user/current",
                headers={"Authorization": f"Bearer {api_token}"},
                timeout=10,
            )
        if resp.ok:
            user = resp.json()
            display = user.get("displayName", email or "user")
            click.echo(f"OK (authenticated as {display})")
        else:
            click.echo(f"Warning: got HTTP {resp.status_code} — credentials may be invalid")
    except requests.RequestException as e:
        click.echo(f"Warning: could not validate — {e}")

    return ConfluenceConfig(
        base_url=base_url, email=email, api_token=api_token, auth_type=auth_type
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


def _setup_bitbucket() -> BitbucketConfig:
    base_url = click.prompt(
        "Bitbucket base URL (e.g., https://bitbucket.company.com)"
    )
    base_url = base_url.rstrip("/")
    api_token = click.prompt("Bitbucket Personal Access Token (PAT)", hide_input=True)

    # Validate
    click.echo("Validating credentials... ", nl=False)
    try:
        resp = requests.get(
            f"{base_url}/rest/api/1.0/users",
            headers={"Authorization": f"Bearer {api_token}"},
            params={"limit": 1},
            timeout=10,
        )
        if resp.ok:
            click.echo("OK")
        else:
            click.echo(f"Warning: got HTTP {resp.status_code} — credentials may be invalid")
    except requests.RequestException as e:
        click.echo(f"Warning: could not validate — {e}")

    return BitbucketConfig(base_url=base_url, api_token=api_token)


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
            click.echo(json.dumps({"key": key, "value": value}))
        else:
            click.echo(value)


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
