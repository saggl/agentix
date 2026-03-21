"""Tests for Jira CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agentix.cli import cli


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture
def mock_jira_client():
    with patch("agentix.jira.commands.resolve_auth") as mock_auth, \
         patch("agentix.jira.commands.JiraClient") as mock_cls:
        mock_auth.return_value = MagicMock(
            base_url="https://test.atlassian.net",
            user="test@example.com",
            token="test-token",
        )
        client = MagicMock()
        mock_cls.return_value = client
        yield client


def test_jira_issue_list(runner, mock_jira_client):
    mock_jira_client.search_issues.return_value = {
        "issues": [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Test issue",
                    "status": {"name": "Open"},
                    "issuetype": {"name": "Bug"},
                    "priority": {"name": "High"},
                    "assignee": {"displayName": "Alice"},
                },
            }
        ],
        "total": 1,
    }

    result = runner.invoke(cli, ["jira", "issue", "list", "--project", "PROJ"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["key"] == "PROJ-1"
    assert data[0]["status"] == "Open"


def test_jira_issue_get(runner, mock_jira_client):
    mock_jira_client.get_issue.return_value = {
        "key": "PROJ-1",
        "id": "10001",
        "fields": {
            "summary": "Detailed issue",
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Story"},
            "priority": {"name": "Medium"},
            "assignee": {"displayName": "Bob"},
            "reporter": {"displayName": "Alice"},
            "labels": ["backend"],
            "created": "2024-01-01T00:00:00.000+0000",
            "updated": "2024-01-02T00:00:00.000+0000",
            "description": None,
        },
    }

    result = runner.invoke(cli, ["jira", "issue", "get", "PROJ-1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["key"] == "PROJ-1"
    assert data["assignee"] == "Bob"


def test_jira_issue_create(runner, mock_jira_client):
    mock_jira_client.create_issue.return_value = {
        "key": "PROJ-5",
        "id": "10005",
        "self": "https://test.atlassian.net/rest/api/3/issue/10005",
    }

    result = runner.invoke(
        cli,
        ["jira", "issue", "create", "--project", "PROJ", "--summary", "New bug", "--type", "Bug"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["key"] == "PROJ-5"


def test_jira_search(runner, mock_jira_client):
    mock_jira_client.search_issues.return_value = {
        "issues": [
            {
                "key": "PROJ-1",
                "fields": {
                    "summary": "Found issue",
                    "status": {"name": "Open"},
                    "issuetype": {"name": "Task"},
                    "priority": {"name": "Low"},
                    "assignee": None,
                },
            }
        ],
        "total": 1,
    }

    result = runner.invoke(cli, ["jira", "search", 'project = "PROJ"'])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1


def test_jira_project_list(runner, mock_jira_client):
    mock_jira_client.get_projects.return_value = [
        {"key": "PROJ", "name": "My Project", "id": "10000", "style": "classic"},
    ]

    result = runner.invoke(cli, ["jira", "project", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data[0]["key"] == "PROJ"


def test_jira_transition_list(runner, mock_jira_client):
    mock_jira_client.get_transitions.return_value = [
        {"id": "11", "name": "Start", "to": {"name": "In Progress"}},
        {"id": "21", "name": "Done", "to": {"name": "Done"}},
    ]

    result = runner.invoke(cli, ["jira", "issue", "transition", "PROJ-1", "--list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2


def test_table_output(runner, mock_jira_client):
    mock_jira_client.get_projects.return_value = [
        {"key": "PROJ", "name": "My Project", "id": "10000", "style": "classic"},
    ]

    result = runner.invoke(cli, ["--format", "table", "jira", "project", "list"])
    assert result.exit_code == 0
    assert "PROJ" in result.output
    assert "My Project" in result.output
