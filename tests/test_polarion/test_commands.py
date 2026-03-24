"""Tests for Polarion CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agentix.cli import cli


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture
def mock_polarion_client():
    with patch("agentix.polarion.commands.resolve_auth") as mock_auth, \
         patch("agentix.polarion.commands.PolarionClient") as mock_cls:
        mock_auth.return_value = MagicMock(
            base_url="https://polarion.example.com/polarion",
            user="testuser",
            token="test-token",
            auth_type="token",
        )
        client = MagicMock()
        mock_cls.return_value = client
        yield client


def test_polarion_project_get(runner, mock_polarion_client):
    mock_polarion_client.get_project.return_value = {
        "id": "MyProject",
        "name": "My Project",
        "tracker_prefix": "MP",
    }

    result = runner.invoke(cli, ["polarion", "project", "get", "MyProject"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "MyProject"
    assert data["name"] == "My Project"
    assert data["tracker_prefix"] == "MP"


def test_polarion_project_users(runner, mock_polarion_client):
    mock_polarion_client.get_project_users.return_value = [
        {"id": "jdoe", "name": "John Doe", "email": "jdoe@example.com"},
        {"id": "asmith", "name": "Alice Smith", "email": "asmith@example.com"},
    ]

    result = runner.invoke(cli, ["polarion", "project", "users", "MyProject"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["id"] == "jdoe"
    assert data[1]["name"] == "Alice Smith"


def test_polarion_workitem_get(runner, mock_polarion_client):
    mock_polarion_client.get_workitem.return_value = {
        "id": "REQ-123",
        "title": "Implement login",
        "type": "requirement",
        "status": "open",
        "priority": "high",
        "severity": "must_have",
        "created": "2024-01-01 10:00:00",
        "updated": "2024-01-02 12:00:00",
        "description": "Implement user login",
    }

    result = runner.invoke(cli, ["polarion", "workitem", "get", "MyProject", "REQ-123"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "REQ-123"
    assert data["title"] == "Implement login"
    assert data["type"] == "requirement"


def test_polarion_workitem_list(runner, mock_polarion_client):
    mock_polarion_client.search_workitems.return_value = [
        {
            "id": "REQ-1",
            "title": "First requirement",
            "type": "requirement",
            "status": "open",
            "priority": "high",
            "severity": "",
            "created": "",
            "updated": "",
            "description": "",
        },
        {
            "id": "REQ-2",
            "title": "Second requirement",
            "type": "requirement",
            "status": "closed",
            "priority": "low",
            "severity": "",
            "created": "",
            "updated": "",
            "description": "",
        },
    ]

    result = runner.invoke(cli, ["polarion", "workitem", "list", "MyProject", "--query", "type:requirement"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["id"] == "REQ-1"
    assert data[1]["status"] == "closed"
    # Brief format should not include description
    assert "description" not in data[0]


def test_polarion_workitem_create(runner, mock_polarion_client):
    mock_polarion_client.create_workitem.return_value = {
        "id": "REQ-999",
        "title": "New requirement",
        "type": "requirement",
        "status": "draft",
        "priority": "",
        "severity": "",
        "created": "2024-03-01 09:00:00",
        "updated": "",
        "description": "",
    }

    result = runner.invoke(cli, [
        "polarion", "workitem", "create", "MyProject",
        "--type", "requirement", "--title", "New requirement",
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["data"]["id"] == "REQ-999"


def test_polarion_workitem_delete(runner, mock_polarion_client):
    result = runner.invoke(cli, ["polarion", "workitem", "delete", "MyProject", "REQ-123", "--yes"])
    assert result.exit_code == 0
    mock_polarion_client.delete_workitem.assert_called_once_with("MyProject", "REQ-123")


def test_polarion_workitem_actions(runner, mock_polarion_client):
    mock_polarion_client.get_workitem_actions.return_value = [
        {"actionId": "1", "nativeActionId": "start_progress", "actionName": "Start Progress"},
        {"actionId": "2", "nativeActionId": "resolve", "actionName": "Resolve"},
    ]

    result = runner.invoke(cli, ["polarion", "workitem", "actions", "MyProject", "REQ-123"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["native_action_id"] == "start_progress"


def test_polarion_workitem_action(runner, mock_polarion_client):
    result = runner.invoke(cli, ["polarion", "workitem", "action", "MyProject", "REQ-123", "start_progress"])
    assert result.exit_code == 0
    mock_polarion_client.perform_workitem_action.assert_called_once_with("MyProject", "REQ-123", "start_progress")


def test_polarion_document_get(runner, mock_polarion_client):
    mock_polarion_client.get_document.return_value = {
        "title": "System Requirements",
        "module_name": "SysReq",
        "module_folder": "_default",
    }

    result = runner.invoke(cli, ["polarion", "document", "get", "MyProject", "_default/SysReq"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["title"] == "System Requirements"


def test_polarion_document_spaces(runner, mock_polarion_client):
    mock_polarion_client.get_document_spaces.return_value = ["_default", "design", "test"]

    result = runner.invoke(cli, ["polarion", "document", "spaces", "MyProject"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "_default" in data


def test_polarion_document_list(runner, mock_polarion_client):
    mock_polarion_client.get_documents_in_space.return_value = [
        {"title": "Doc A", "module_name": "DocA", "module_folder": "_default"},
        {"title": "Doc B", "module_name": "DocB", "module_folder": "_default"},
    ]

    result = runner.invoke(cli, ["polarion", "document", "list", "MyProject", "--space", "_default"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2


def test_polarion_testrun_get(runner, mock_polarion_client):
    mock_polarion_client.get_testrun.return_value = {
        "id": "TR-001",
        "title": "Sprint 1 Tests",
        "created": "2024-01-15 08:00:00",
        "is_template": False,
    }

    result = runner.invoke(cli, ["polarion", "testrun", "get", "MyProject", "TR-001"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "TR-001"
    assert data["is_template"] is False


def test_polarion_testrun_list(runner, mock_polarion_client):
    mock_polarion_client.search_testruns.return_value = [
        {"id": "TR-001", "title": "Sprint 1 Tests", "created": "", "is_template": False},
    ]

    result = runner.invoke(cli, ["polarion", "testrun", "list", "MyProject"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1


def test_polarion_plan_get(runner, mock_polarion_client):
    mock_polarion_client.get_plan.return_value = {
        "id": "release-1.0",
        "name": "Release 1.0",
        "start_date": "2024-01-01",
        "due_date": "2024-06-30",
    }

    result = runner.invoke(cli, ["polarion", "plan", "get", "MyProject", "release-1.0"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "release-1.0"
    assert data["name"] == "Release 1.0"


def test_polarion_plan_list(runner, mock_polarion_client):
    mock_polarion_client.search_plans.return_value = [
        {"id": "release-1.0", "name": "Release 1.0", "start_date": "", "due_date": ""},
    ]

    result = runner.invoke(cli, ["polarion", "plan", "list", "MyProject"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1


def test_polarion_enum_get(runner, mock_polarion_client):
    mock_polarion_client.get_enum.return_value = ["open", "in_progress", "closed", "rejected"]

    result = runner.invoke(cli, ["polarion", "enum", "MyProject", "requirement-status"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "open" in data
    assert "closed" in data
