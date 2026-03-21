"""Tests for Confluence CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agentix.cli import cli


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture
def mock_confluence_client():
    with patch("agentix.confluence.commands.resolve_auth") as mock_auth, \
         patch("agentix.confluence.commands.ConfluenceClient") as mock_cls:
        mock_auth.return_value = MagicMock(
            base_url="https://test.atlassian.net/wiki",
            user="test@example.com",
            token="test-token",
            auth_type="basic",
        )
        client = MagicMock()
        mock_cls.return_value = client
        yield client


def test_confluence_page_get(runner, mock_confluence_client):
    mock_confluence_client.get_page.return_value = {
        "id": "123456",
        "title": "Test Page",
        "body": {"storage": {"value": "<p>Content</p>"}},
        "version": {"number": 5},
        "_links": {"webui": "/pages/123456"},
    }

    result = runner.invoke(cli, ["confluence", "page", "get", "123456"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "123456"
    assert data["title"] == "Test Page"


def test_confluence_page_search(runner, mock_confluence_client):
    mock_confluence_client.search_pages.return_value = [
        {
            "id": "111",
            "title": "Result 1",
            "type": "page",
            "_links": {"webui": "/pages/111"},
        },
        {
            "id": "222",
            "title": "Result 2",
            "type": "page",
            "_links": {"webui": "/pages/222"},
        },
    ]

    result = runner.invoke(cli, ["confluence", "page", "search", "--query", "test"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["id"] == "111"


def test_confluence_page_search_with_space(runner, mock_confluence_client):
    mock_confluence_client.search_pages.return_value = [
        {"id": "333", "title": "Space Result", "_links": {"webui": "/pages/333"}},
    ]

    result = runner.invoke(
        cli,
        ["confluence", "page", "search", "--query", "test", "--space", "ENG"],
    )
    assert result.exit_code == 0
    mock_confluence_client.search_pages.assert_called_once_with(
        "test", space_key="ENG", max_results=25
    )


def test_confluence_page_create(runner, mock_confluence_client):
    mock_confluence_client.create_page.return_value = {
        "id": "789",
        "title": "New Page",
    }

    result = runner.invoke(
        cli,
        [
            "confluence",
            "page",
            "create",
            "--space-id",
            "12345",
            "--title",
            "New Page",
            "--body",
            "<p>Content</p>",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["id"] == "789"


def test_confluence_page_update(runner, mock_confluence_client):
    mock_confluence_client.update_page_auto.return_value = {
        "id": "123",
        "title": "Updated Page",
        "version": {"number": 6},
    }

    result = runner.invoke(
        cli,
        [
            "confluence",
            "page",
            "update",
            "123",
            "--title",
            "Updated Page",
            "--body",
            "<p>New content</p>",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_confluence_page_delete_with_confirm(runner, mock_confluence_client):
    result = runner.invoke(
        cli,
        ["confluence", "page", "delete", "123", "--yes"],
    )
    assert result.exit_code == 0
    mock_confluence_client.delete_page.assert_called_once_with("123")


def test_confluence_page_move(runner, mock_confluence_client):
    result = runner.invoke(
        cli,
        ["confluence", "page", "move", "123", "--target-parent", "456"],
    )
    assert result.exit_code == 0
    mock_confluence_client.move_page.assert_called_once_with("123", "456")


def test_confluence_comment_list(runner, mock_confluence_client):
    mock_confluence_client.get_page_comments.return_value = [
        {"id": "c1", "body": {"storage": {"value": "Comment 1"}}},
        {"id": "c2", "body": {"storage": {"value": "Comment 2"}}},
    ]

    result = runner.invoke(cli, ["confluence", "comment", "list", "123"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2


def test_confluence_comment_add(runner, mock_confluence_client):
    mock_confluence_client.add_page_comment.return_value = {
        "id": "c3",
        "body": {"storage": {"value": "New comment"}},
    }

    result = runner.invoke(
        cli,
        ["confluence", "comment", "add", "123", "--body", "<p>New comment</p>"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_confluence_comment_get(runner, mock_confluence_client):
    mock_confluence_client.get_comment.return_value = {
        "id": "c1",
        "body": {"storage": {"value": "Comment text"}},
    }

    result = runner.invoke(cli, ["confluence", "comment", "get", "c1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "c1"


def test_confluence_attachment_list(runner, mock_confluence_client):
    mock_confluence_client.get_page_attachments.return_value = [
        {
            "id": "att1",
            "title": "file1.pdf",
            "fileSize": 1024,
            "mediaType": "application/pdf",
        },
        {
            "id": "att2",
            "title": "image.png",
            "fileSize": 2048,
            "mediaType": "image/png",
        },
    ]

    result = runner.invoke(cli, ["confluence", "attachment", "list", "123"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2


def test_confluence_space_list(runner, mock_confluence_client):
    mock_confluence_client.get_spaces.return_value = [
        {"id": "s1", "name": "Engineering", "key": "ENG"},
        {"id": "s2", "name": "Marketing", "key": "MKT"},
    ]

    result = runner.invoke(cli, ["confluence", "space", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["key"] == "ENG"


def test_confluence_space_get(runner, mock_confluence_client):
    mock_confluence_client.get_space.return_value = {
        "id": "12345",
        "name": "Engineering",
        "key": "ENG",
    }

    result = runner.invoke(cli, ["confluence", "space", "get", "12345"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "12345"
    assert data["key"] == "ENG"


def test_confluence_search_cql(runner, mock_confluence_client):
    mock_confluence_client.search_cql.return_value = [
        {"id": "p1", "title": "Page 1", "type": "page"},
        {"id": "p2", "title": "Page 2", "type": "page"},
    ]

    result = runner.invoke(
        cli,
        ["confluence", "search", 'type = page AND title ~ "test"'],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2


def test_confluence_table_format(runner, mock_confluence_client):
    mock_confluence_client.get_spaces.return_value = [
        {"id": "s1", "name": "Engineering", "key": "ENG"},
    ]

    result = runner.invoke(cli, ["--format", "table", "confluence", "space", "list"])
    assert result.exit_code == 0

    # Table format should contain headers
    assert "name" in result.output or "Name" in result.output
