"""Tests for Confluence model normalization functions."""

from agentix.confluence.models import (
    normalize_attachment,
    normalize_comment,
    normalize_page,
    normalize_page_brief,
    normalize_space,
)


def test_normalize_page_v2():
    """Test normalizing a v2 API page."""
    page = {
        "id": "123456",
        "title": "Test Page",
        "status": "current",
        "spaceId": "789",
        "version": {"number": 5},
        "body": {
            "storage": {"value": "<p>Content here</p>"},
        },
    }
    result = normalize_page(page)
    assert result["id"] == "123456"
    assert result["title"] == "Test Page"
    assert result["spaceId"] == "789"
    assert result["version"] == 5
    assert result["body"] == "<p>Content here</p>"


def test_normalize_page_v1():
    """Test normalizing a v1 API page (uses space.key instead of spaceId)."""
    page = {
        "id": "111",
        "title": "V1 Page",
        "status": "current",
        "space": {"key": "ENG", "name": "Engineering"},
        "version": {"number": 2},
        "body": {
            "storage": {"value": "<p>V1 content</p>"},
        },
    }
    result = normalize_page(page)
    assert result["id"] == "111"
    assert result["spaceId"] == "ENG"  # Extracts from space.key


def test_normalize_page_missing_fields():
    """Test normalizing page with missing fields."""
    page = {"id": "minimal"}
    result = normalize_page(page)
    assert result["id"] == "minimal"
    assert result["title"] == ""
    assert result["body"] == ""


def test_normalize_page_brief():
    """Test normalizing brief page representation."""
    page = {
        "id": "222",
        "title": "Brief Page",
        "status": "current",
        "type": "page",
    }
    result = normalize_page_brief(page)
    assert result["id"] == "222"
    assert result["title"] == "Brief Page"
    assert result["type"] == "page"


def test_normalize_page_brief_v1_search():
    """Test normalizing v1 search result (nested in 'content')."""
    page = {
        "content": {
            "id": "333",
            "title": "Search Result",
            "status": "current",
            "type": "page",
        }
    }
    result = normalize_page_brief(page)
    assert result["id"] == "333"
    assert result["title"] == "Search Result"


def test_normalize_space():
    """Test normalizing space."""
    space = {
        "id": "12345",
        "key": "ENG",
        "name": "Engineering",
        "type": "global",
        "status": "current",
    }
    result = normalize_space(space)
    assert result["id"] == "12345"
    assert result["key"] == "ENG"
    assert result["name"] == "Engineering"


def test_normalize_comment():
    """Test normalizing comment."""
    comment = {
        "id": "c123",
        "body": {
            "storage": {"value": "<p>This is a <strong>comment</strong></p>"},
        },
        "version": {"number": 1},
        "createdAt": "2024-01-01T00:00:00.000Z",
    }
    result = normalize_comment(comment)
    assert result["id"] == "c123"
    assert result["body"] == "This is a comment"  # HTML stripped
    assert result["version"] == 1


def test_normalize_comment_empty_body():
    """Test normalizing comment with no body."""
    comment = {"id": "c456"}
    result = normalize_comment(comment)
    assert result["id"] == "c456"
    assert result["body"] == ""


def test_normalize_attachment():
    """Test normalizing attachment."""
    attachment = {
        "id": "att1",
        "title": "document.pdf",
        "mediaType": "application/pdf",
        "fileSize": 102400,
        "status": "current",
    }
    result = normalize_attachment(attachment)
    assert result["id"] == "att1"
    assert result["title"] == "document.pdf"
    assert result["mediaType"] == "application/pdf"
    assert result["fileSize"] == 102400


def test_normalize_attachment_missing_fields():
    """Test normalizing attachment with missing fields."""
    attachment = {"id": "att2"}
    result = normalize_attachment(attachment)
    assert result["id"] == "att2"
    assert result["title"] == ""
    assert result["fileSize"] == 0
