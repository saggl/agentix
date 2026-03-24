"""Tests for Polarion client wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from agentix.polarion.client import PolarionClient


@pytest.fixture
def mock_polarion():
    with patch("agentix.polarion.client.Polarion") as mock_cls:
        polarion_instance = MagicMock()
        mock_cls.return_value = polarion_instance
        yield mock_cls, polarion_instance


def test_client_init_with_token(mock_polarion):
    mock_cls, _ = mock_polarion
    PolarionClient("https://polarion.example.com/polarion", "user", "my-token", "token")
    mock_cls.assert_called_once_with(
        "https://polarion.example.com/polarion", "user", token="my-token"
    )


def test_client_init_with_password(mock_polarion):
    mock_cls, _ = mock_polarion
    PolarionClient("https://polarion.example.com/polarion", "user", "my-pass", "password")
    mock_cls.assert_called_once_with(
        "https://polarion.example.com/polarion", "user", password="my-pass"
    )


def test_get_project(mock_polarion):
    _, polarion_instance = mock_polarion
    project = MagicMock()
    project.id = "TestProj"
    project.name = "Test Project"
    project.tracker_prefix = "TP"
    polarion_instance.get_project.return_value = project

    client = PolarionClient("https://example.com/polarion", "user", "token")
    result = client.get_project("TestProj")

    assert result == {"id": "TestProj", "name": "Test Project", "tracker_prefix": "TP"}


def test_get_project_users(mock_polarion):
    _, polarion_instance = mock_polarion
    project = MagicMock()
    user1 = MagicMock()
    user1.id = "jdoe"
    user1.name = "John Doe"
    user1.email = "jdoe@example.com"
    project.get_users.return_value = [user1]
    polarion_instance.get_project.return_value = project

    client = PolarionClient("https://example.com/polarion", "user", "token")
    result = client.get_project_users("TestProj")

    assert len(result) == 1
    assert result[0]["id"] == "jdoe"


def test_get_workitem(mock_polarion):
    _, polarion_instance = mock_polarion
    project = MagicMock()
    wi = MagicMock()
    wi._id = "REQ-1"
    wi.title = "Test requirement"
    wi.type = {"id": "requirement"}
    wi.status = {"id": "open"}
    wi.priority = {"id": "high"}
    wi.severity = {"id": "must_have"}
    wi.created = "2024-01-01"
    wi.updated = "2024-01-02"
    wi.get_description.return_value = "A description"
    project.get_workitem.return_value = wi
    polarion_instance.get_project.return_value = project

    client = PolarionClient("https://example.com/polarion", "user", "token")
    result = client.get_workitem("TestProj", "REQ-1")

    assert result["id"] == "REQ-1"
    assert result["title"] == "Test requirement"
    assert result["type"] == "requirement"
    assert result["description"] == "A description"


def test_search_workitems(mock_polarion):
    _, polarion_instance = mock_polarion
    project = MagicMock()
    wi = MagicMock()
    wi._id = "REQ-1"
    wi.title = "Test"
    wi.type = {"id": "requirement"}
    wi.status = {"id": "open"}
    wi.priority = None
    wi.severity = None
    wi.created = None
    wi.updated = None
    wi.get_description.return_value = None
    project.search_workitems_full.return_value = [wi]
    polarion_instance.get_project.return_value = project

    client = PolarionClient("https://example.com/polarion", "user", "token")
    result = client.search_workitems("TestProj", "type:requirement", limit=50)

    assert len(result) == 1
    assert result[0]["id"] == "REQ-1"
    project.search_workitems_full.assert_called_once_with("type:requirement", "Created", 50)


def test_create_workitem(mock_polarion):
    _, polarion_instance = mock_polarion
    project = MagicMock()
    wi = MagicMock()
    wi._id = "REQ-999"
    wi.title = "New item"
    wi.type = {"id": "requirement"}
    wi.status = {"id": "draft"}
    wi.priority = None
    wi.severity = None
    wi.created = None
    wi.updated = None
    wi.get_description.return_value = None
    project.create_workitem.return_value = wi
    polarion_instance.get_project.return_value = project

    client = PolarionClient("https://example.com/polarion", "user", "token")
    result = client.create_workitem("TestProj", "requirement", {"title": "New item"})

    assert result["id"] == "REQ-999"
    project.create_workitem.assert_called_once_with("requirement", {"title": "New item"})


def test_delete_workitem(mock_polarion):
    _, polarion_instance = mock_polarion
    project = MagicMock()
    wi = MagicMock()
    project.get_workitem.return_value = wi
    polarion_instance.get_project.return_value = project

    client = PolarionClient("https://example.com/polarion", "user", "token")
    client.delete_workitem("TestProj", "REQ-1")

    wi.delete.assert_called_once()


def test_get_document_spaces(mock_polarion):
    _, polarion_instance = mock_polarion
    project = MagicMock()
    project.get_document_spaces.return_value = ["_default", "design"]
    polarion_instance.get_project.return_value = project

    client = PolarionClient("https://example.com/polarion", "user", "token")
    result = client.get_document_spaces("TestProj")

    assert result == ["_default", "design"]


def test_get_enum(mock_polarion):
    _, polarion_instance = mock_polarion
    project = MagicMock()
    project.get_enum.return_value = ["open", "closed"]
    polarion_instance.get_project.return_value = project

    client = PolarionClient("https://example.com/polarion", "user", "token")
    result = client.get_enum("TestProj", "requirement-status")

    assert result == ["open", "closed"]


def test_close(mock_polarion):
    _, polarion_instance = mock_polarion
    client = PolarionClient("https://example.com/polarion", "user", "token")
    client.close()
    polarion_instance.close.assert_called_once()
