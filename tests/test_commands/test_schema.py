"""Tests for schema command."""

import json

import pytest
from click.testing import CliRunner

from agentix.cli import cli


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


def test_schema_root_command(runner):
    """Test schema command for root agentix command."""
    result = runner.invoke(cli, ["schema"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["command"] == "agentix"
    assert data["description"] == "agentix — Unified CLI for Jira, Confluence, Jenkins, and Bitbucket."
    assert "arguments" in data
    assert "options" in data
    assert "subcommands" in data

    # Verify expected subcommands exist
    subcommand_names = [sc["name"] for sc in data["subcommands"]]
    assert "jira" in subcommand_names
    assert "confluence" in subcommand_names
    assert "jenkins" in subcommand_names
    assert "bitbucket" in subcommand_names
    assert "config" in subcommand_names
    assert "schema" in subcommand_names
    assert "self-update" in subcommand_names
    assert "update" in subcommand_names

    # Verify global options
    option_names = [opt["name"] for opt in data["options"]]
    assert "profile" in option_names
    assert "output_format" in option_names
    assert "verbose" in option_names


def test_schema_jira_command(runner):
    """Test schema command for jira subcommand."""
    result = runner.invoke(cli, ["schema", "jira"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["command"] == "agentix jira"
    assert data["description"] == "Jira issue tracking."

    # Verify jira subcommands
    subcommand_names = [sc["name"] for sc in data["subcommands"]]
    assert "issue" in subcommand_names
    assert "project" in subcommand_names
    assert "board" in subcommand_names
    assert "sprint" in subcommand_names


def test_schema_specific_command(runner):
    """Test schema command for specific command with arguments."""
    result = runner.invoke(cli, ["schema", "jira", "issue", "get"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["command"] == "agentix jira issue get"
    assert data["description"] == "Get issue details."

    # Verify arguments
    assert len(data["arguments"]) == 1
    arg = data["arguments"][0]
    assert arg["name"] == "issue_key"
    assert arg["type"] == "string"
    assert arg["required"] is True

    # No subcommands for leaf command
    assert len(data["subcommands"]) == 0


def test_schema_command_with_options(runner):
    """Test schema command for command with options."""
    result = runner.invoke(cli, ["schema", "jira", "issue", "list"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["command"] == "agentix jira issue list"

    # Verify options exist
    option_names = [opt["name"] for opt in data["options"]]
    assert "project" in option_names
    assert "jql" in option_names
    assert "assignee" in option_names
    assert "status" in option_names

    # Check option details
    project_opt = next(opt for opt in data["options"] if opt["name"] == "project")
    assert project_opt["type"] == "string"
    assert project_opt["required"] is False
    assert "--project" in project_opt["flags"]
    assert "-p" in project_opt["flags"]


def test_schema_full_flag(runner):
    """Test schema command with --full flag for nested tree."""
    result = runner.invoke(cli, ["schema", "--full", "jira", "issue"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["command"] == "agentix jira issue"

    # With --full, subcommands should have full schema, not just names
    assert len(data["subcommands"]) > 0
    first_subcommand = data["subcommands"][0]

    # Full schema has "command" field instead of just "name"
    assert "command" in first_subcommand
    assert "arguments" in first_subcommand
    assert "options" in first_subcommand


def test_schema_table_format(runner):
    """Test schema command with table output format."""
    result = runner.invoke(cli, ["--format", "table", "schema", "jira"])
    assert result.exit_code == 0

    # Table format should contain field names
    assert "Field" in result.output
    assert "Value" in result.output
    assert "command" in result.output
    assert "agentix jira" in result.output


def test_schema_nonexistent_command(runner):
    """Test schema command for nonexistent command."""
    result = runner.invoke(cli, ["schema", "nonexistent"])

    # Should exit with error code
    assert result.exit_code != 0

    # Exception should be raised with appropriate message
    assert result.exception is not None
    assert "Command not found" in str(result.exception)
    assert "nonexistent" in str(result.exception)


def test_schema_nested_group(runner):
    """Test schema for nested command group."""
    result = runner.invoke(cli, ["schema", "jira", "issue"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["command"] == "agentix jira issue"
    assert data["description"] == "Manage Jira issues."

    # Verify it has subcommands (get, list, create, etc.)
    assert len(data["subcommands"]) > 0
    subcommand_names = [sc["name"] for sc in data["subcommands"]]
    assert "get" in subcommand_names
    assert "list" in subcommand_names
    assert "create" in subcommand_names


def test_schema_choice_type(runner):
    """Test schema correctly identifies choice types."""
    result = runner.invoke(cli, ["schema"])
    assert result.exit_code == 0

    data = json.loads(result.output)

    # Find the --format option
    format_opt = next(
        opt for opt in data["options"]
        if opt["name"] == "output_format"
    )

    assert format_opt["type"] == "choice"
    assert "choices" in format_opt
    assert "json" in format_opt["choices"]
    assert "table" in format_opt["choices"]


def test_schema_flag_type(runner):
    """Test schema correctly identifies flag options."""
    result = runner.invoke(cli, ["schema"])
    assert result.exit_code == 0

    data = json.loads(result.output)

    # Find the --verbose flag
    verbose_opt = next(
        opt for opt in data["options"]
        if opt["name"] == "verbose"
    )

    assert verbose_opt["is_flag"] is True
    assert verbose_opt["type"] == "boolean"
    assert verbose_opt["default"] is False


def test_schema_integer_type(runner):
    """Test schema correctly identifies integer types."""
    result = runner.invoke(cli, ["schema", "jira", "issue", "list"])
    assert result.exit_code == 0

    data = json.loads(result.output)

    # Find the --max-results option
    max_results_opt = next(
        (opt for opt in data["options"] if opt["name"] == "max_results"),
        None
    )

    if max_results_opt:
        assert max_results_opt["type"] == "integer"
        assert isinstance(max_results_opt["default"], int)


def test_schema_help_text(runner):
    """Test schema command --help."""
    result = runner.invoke(cli, ["schema", "--help"])
    assert result.exit_code == 0

    assert "Get JSON schema for agentix commands" in result.output
    assert "Examples:" in result.output
    assert "--full" in result.output
