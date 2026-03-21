"""Tests for Confluence client."""

import pytest
import responses

from agentix.confluence.client import ConfluenceClient


@pytest.fixture
def confluence():
    return ConfluenceClient(
        base_url="https://test.atlassian.net/wiki",
        email="test@example.com",
        api_token="test-token",
    )


@pytest.fixture
def confluence_bearer():
    return ConfluenceClient(
        base_url="https://confluence.example.com",
        email="test@example.com",
        api_token="bearer-token",
        auth_type="bearer",
    )


@responses.activate
def test_get_page_v2(confluence):
    """Test getting page with v2 API (basic auth)."""
    responses.add(
        responses.GET,
        "https://test.atlassian.net/wiki/api/v2/pages/123456",
        json={
            "id": "123456",
            "title": "Test Page",
            "body": {"storage": {"value": "<p>Content</p>"}},
            "version": {"number": 5},
        },
        status=200,
    )
    page = confluence.get_page("123456")
    assert page["id"] == "123456"
    assert page["title"] == "Test Page"


@responses.activate
def test_get_page_bearer(confluence_bearer):
    """Test getting page with v1 API (bearer auth)."""
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content/123456",
        json={
            "id": "123456",
            "title": "Test Page Bearer",
            "body": {"storage": {"value": "<p>Content</p>"}},
            "version": {"number": 2},
        },
        status=200,
    )
    page = confluence_bearer.get_page("123456")
    assert page["id"] == "123456"
    assert page["title"] == "Test Page Bearer"


@responses.activate
def test_search_pages(confluence):
    """Test searching pages."""
    responses.add(
        responses.GET,
        "https://test.atlassian.net/wiki/rest/api/content/search",
        json={
            "results": [
                {"id": "111", "title": "Result 1", "type": "page"},
                {"id": "222", "title": "Result 2", "type": "page"},
            ],
        },
        status=200,
    )
    results = confluence.search_pages("test query")
    assert len(results) == 2
    assert results[0]["id"] == "111"


@responses.activate
def test_search_pages_with_space(confluence):
    """Test searching pages in specific space."""
    responses.add(
        responses.GET,
        "https://test.atlassian.net/wiki/rest/api/content/search",
        json={"results": [{"id": "333", "title": "Space Result"}]},
        status=200,
    )
    results = confluence.search_pages("query", space_key="ENG")
    assert len(results) == 1
    # Verify CQL was constructed correctly (URL-encoded)
    assert "space" in responses.calls[0].request.url
    assert "ENG" in responses.calls[0].request.url


@responses.activate
def test_create_page(confluence):
    """Test creating a new page."""
    responses.add(
        responses.POST,
        "https://test.atlassian.net/wiki/api/v2/pages",
        json={"id": "789", "title": "New Page", "status": "current"},
        status=200,
    )
    result = confluence.create_page(
        space_id="12345",
        title="New Page",
        body="<p>Page content</p>",
    )
    assert result["id"] == "789"
    assert result["title"] == "New Page"

    # Verify request payload
    import json
    body = json.loads(responses.calls[0].request.body)
    assert body["spaceId"] == "12345"
    assert body["title"] == "New Page"
    assert body["body"]["value"] == "<p>Page content</p>"


@responses.activate
def test_create_page_with_parent(confluence):
    """Test creating page with parent."""
    responses.add(
        responses.POST,
        "https://test.atlassian.net/wiki/api/v2/pages",
        json={"id": "890", "title": "Child Page"},
        status=200,
    )
    result = confluence.create_page(
        space_id="12345",
        title="Child Page",
        body="<p>Content</p>",
        parent_id="111",
    )
    assert result["id"] == "890"

    # Verify parentId in payload
    import json
    body = json.loads(responses.calls[0].request.body)
    assert body["parentId"] == "111"


@responses.activate
def test_update_page(confluence):
    """Test updating a page."""
    responses.add(
        responses.PUT,
        "https://test.atlassian.net/wiki/api/v2/pages/123456",
        json={"id": "123456", "title": "Updated", "version": {"number": 6}},
        status=200,
    )
    result = confluence.update_page(
        page_id="123456",
        title="Updated",
        body="<p>New content</p>",
        version_number=6,
    )
    assert result["title"] == "Updated"
    assert result["version"]["number"] == 6


@responses.activate
def test_update_page_auto(confluence):
    """Test auto-increment update."""
    # First call: get current page
    responses.add(
        responses.GET,
        "https://test.atlassian.net/wiki/api/v2/pages/123456",
        json={"id": "123456", "version": {"number": 5}},
        status=200,
    )
    # Second call: update with incremented version
    responses.add(
        responses.PUT,
        "https://test.atlassian.net/wiki/api/v2/pages/123456",
        json={"id": "123456", "title": "Auto Updated", "version": {"number": 6}},
        status=200,
    )

    result = confluence.update_page_auto(
        page_id="123456",
        title="Auto Updated",
        body="<p>Content</p>",
    )
    assert result["version"]["number"] == 6

    # Verify version was incremented
    import json
    update_body = json.loads(responses.calls[1].request.body)
    assert update_body["version"]["number"] == 6


@responses.activate
def test_delete_page(confluence):
    """Test deleting a page."""
    responses.add(
        responses.DELETE,
        "https://test.atlassian.net/wiki/api/v2/pages/123456",
        status=204,
    )
    confluence.delete_page("123456")
    assert len(responses.calls) == 1


@responses.activate
def test_get_page_comments(confluence):
    """Test getting page comments."""
    responses.add(
        responses.GET,
        "https://test.atlassian.net/wiki/api/v2/pages/123456/footer-comments",
        json={
            "results": [
                {"id": "c1", "body": {"storage": {"value": "Comment 1"}}},
                {"id": "c2", "body": {"storage": {"value": "Comment 2"}}},
            ],
            "_links": {},
        },
        status=200,
    )
    comments = confluence.get_page_comments("123456")
    assert len(comments) == 2
    assert comments[0]["id"] == "c1"


@responses.activate
def test_add_page_comment(confluence):
    """Test adding a comment to page."""
    responses.add(
        responses.POST,
        "https://test.atlassian.net/wiki/api/v2/pages/123456/footer-comments",
        json={"id": "c3", "body": {"storage": {"value": "New comment"}}},
        status=200,
    )
    result = confluence.add_page_comment(
        page_id="123456",
        body="<p>New comment</p>",
    )
    assert result["id"] == "c3"


@responses.activate
def test_get_spaces(confluence):
    """Test listing spaces."""
    responses.add(
        responses.GET,
        "https://test.atlassian.net/wiki/api/v2/spaces",
        json={
            "results": [
                {"id": "s1", "name": "Engineering", "key": "ENG"},
                {"id": "s2", "name": "Marketing", "key": "MKT"},
            ],
            "_links": {},
        },
        status=200,
    )
    spaces = confluence.get_spaces()
    assert len(spaces) == 2
    assert spaces[0]["key"] == "ENG"


@responses.activate
def test_get_spaces_bearer(confluence_bearer):
    """Test listing spaces with bearer auth (v1 API)."""
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/space",
        json={
            "results": [
                {"id": "s1", "name": "Space 1", "key": "SP1"},
            ],
            "_links": {},
        },
        status=200,
    )
    spaces = confluence_bearer.get_spaces()
    assert len(spaces) == 1


@responses.activate
def test_get_space(confluence):
    """Test getting single space by ID."""
    responses.add(
        responses.GET,
        "https://test.atlassian.net/wiki/api/v2/spaces/12345",
        json={"id": "12345", "name": "Engineering", "key": "ENG"},
        status=200,
    )
    space = confluence.get_space("12345")
    assert space["id"] == "12345"
    assert space["key"] == "ENG"


@responses.activate
def test_get_space_bearer(confluence_bearer):
    """Test getting space with bearer auth (uses KEY not ID)."""
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/space/ENG",
        json={"id": "12345", "key": "ENG", "name": "Engineering"},
        status=200,
    )
    space = confluence_bearer.get_space("ENG")
    assert space["key"] == "ENG"


@responses.activate
def test_search_cql(confluence):
    """Test CQL search."""
    responses.add(
        responses.GET,
        "https://test.atlassian.net/wiki/rest/api/content/search",
        json={
            "results": [
                {"id": "p1", "title": "Found Page 1"},
                {"id": "p2", "title": "Found Page 2"},
            ],
        },
        status=200,
    )
    results = list(confluence.search_cql('type = page AND title ~ "test"'))
    assert len(results) == 2
    assert results[0]["id"] == "p1"
