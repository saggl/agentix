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


def test_jira_metadata_edit(runner, mock_jira_client):
    mock_jira_client.get_issue_edit_metadata.return_value = {
        "fields": {
            "summary": {"required": True, "schema": {"type": "string"}},
            "description": {"required": False, "schema": {"type": "string"}},
        }
    }

    result = runner.invoke(cli, ["jira", "metadata", "edit", "PROJ-123"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "fields" in data
    assert "summary" in data["fields"]
    mock_jira_client.get_issue_edit_metadata.assert_called_once_with("PROJ-123")


def test_jira_metadata_create(runner, mock_jira_client):
    mock_jira_client.get_create_metadata.return_value = {
        "projects": [
            {
                "key": "PROJ",
                "issuetypes": [
                    {"name": "Bug", "fields": {"summary": {"required": True}}}
                ],
            }
        ]
    }

    result = runner.invoke(
        cli,
        ["jira", "metadata", "create", "--project", "PROJ", "--issue-type", "Bug"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "projects" in data
    mock_jira_client.get_create_metadata.assert_called_once_with(
        project_keys=["PROJ"], issue_type_names=["Bug"]
    )


def test_jira_metadata_create_no_filters(runner, mock_jira_client):
    mock_jira_client.get_create_metadata.return_value = {"projects": []}

    result = runner.invoke(cli, ["jira", "metadata", "create"])
    assert result.exit_code == 0
    mock_jira_client.get_create_metadata.assert_called_once_with(
        project_keys=None, issue_type_names=None
    )


def test_jira_component_list(runner, mock_jira_client):
    mock_jira_client.get_project_components.return_value = [
        {
            "id": "10001",
            "name": "Backend",
            "description": "Backend code",
            "lead": {"displayName": "John Doe"},
            "project": "PROJ",
        },
        {
            "id": "10002",
            "name": "Frontend",
            "description": "UI code",
            "lead": {"displayName": "Jane Smith"},
            "project": "PROJ",
        },
    ]

    result = runner.invoke(cli, ["jira", "component", "list", "--project", "PROJ"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["name"] == "Backend"
    mock_jira_client.get_project_components.assert_called_once_with("PROJ")


def test_jira_component_create(runner, mock_jira_client):
    mock_jira_client.create_component.return_value = {
        "id": "10003",
        "name": "API",
        "project": "PROJ",
    }

    result = runner.invoke(
        cli,
        [
            "jira",
            "component",
            "create",
            "--project",
            "PROJ",
            "--name",
            "API",
            "--description",
            "API layer",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["name"] == "API"
    mock_jira_client.create_component.assert_called_once_with(
        "PROJ", "API", description="API layer", lead_account_id=None
    )


def test_jira_component_update(runner, mock_jira_client):
    mock_jira_client.update_component.return_value = {
        "id": "10001",
        "name": "Backend Updated",
    }

    result = runner.invoke(
        cli,
        ["jira", "component", "update", "10001", "--name", "Backend Updated"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    mock_jira_client.update_component.assert_called_once_with(
        "10001", name="Backend Updated", description=None, lead_account_id=None
    )


def test_jira_component_delete(runner, mock_jira_client):
    result = runner.invoke(
        cli, ["jira", "component", "delete", "10001", "--yes"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    mock_jira_client.delete_component.assert_called_once_with("10001")


def test_jira_version_list(runner, mock_jira_client):
    mock_jira_client.get_project_versions.return_value = [
        {
            "id": "10100",
            "name": "v1.0",
            "description": "First release",
            "released": True,
            "archived": False,
            "releaseDate": "2026-01-15",
        },
        {
            "id": "10101",
            "name": "v2.0",
            "description": "Second release",
            "released": False,
            "archived": False,
        },
    ]

    result = runner.invoke(cli, ["jira", "version", "list", "--project", "PROJ"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["name"] == "v1.0"
    assert data[0]["released"] is True
    mock_jira_client.get_project_versions.assert_called_once_with("PROJ")


def test_jira_version_create(runner, mock_jira_client):
    mock_jira_client.create_version.return_value = {
        "id": "10102",
        "name": "v3.0",
        "project": "PROJ",
    }

    result = runner.invoke(
        cli,
        [
            "jira",
            "version",
            "create",
            "--project",
            "PROJ",
            "--name",
            "v3.0",
            "--release-date",
            "2026-12-31",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["name"] == "v3.0"
    mock_jira_client.create_version.assert_called_once_with(
        "PROJ",
        "v3.0",
        description=None,
        start_date=None,
        release_date="2026-12-31",
        released=False,
    )


def test_jira_version_update(runner, mock_jira_client):
    mock_jira_client.update_version.return_value = {
        "id": "10100",
        "name": "v1.0",
        "released": True,
    }

    result = runner.invoke(
        cli,
        ["jira", "version", "update", "10100", "--released", "true"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    mock_jira_client.update_version.assert_called_once_with(
        "10100", name=None, description=None, released=True, release_date=None
    )


def test_jira_version_delete(runner, mock_jira_client):
    result = runner.invoke(cli, ["jira", "version", "delete", "10100", "--yes"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    mock_jira_client.delete_version.assert_called_once_with("10100")


def test_jira_version_archive(runner, mock_jira_client):
    mock_jira_client.archive_version.return_value = {
        "id": "10100",
        "name": "v1.0",
        "archived": True,
    }

    result = runner.invoke(cli, ["jira", "version", "archive", "10100"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    mock_jira_client.archive_version.assert_called_once_with("10100")


def test_table_output(runner, mock_jira_client):
    mock_jira_client.get_projects.return_value = [
        {"key": "PROJ", "name": "My Project", "id": "10000", "style": "classic"},
    ]

    result = runner.invoke(cli, ["--format", "table", "jira", "project", "list"])
    assert result.exit_code == 0
    assert "PROJ" in result.output
    assert "My Project" in result.output
