"""Tests for Confluence client."""

import json

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
    """Test listing spaces with bearer auth (v1 offset-based pagination)."""
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/space",
        json={
            "results": [
                {"id": "s1", "name": "Space 1", "key": "SP1"},
            ],
            "start": 0,
            "limit": 25,
            "size": 1,
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


# -- _is_cloud flag tests --


def test_cloud_client_flag(confluence):
    assert confluence._is_cloud is True


def test_server_client_flag(confluence_bearer):
    assert confluence_bearer._is_cloud is False


# -- Server/DC (v1) endpoint tests --


@responses.activate
def test_get_page_children_bearer(confluence_bearer):
    """v1: GET /rest/api/content/{id}/child/page with offset pagination."""
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content/123/child/page",
        json={
            "results": [
                {"id": "c1", "title": "Child 1", "type": "page"},
                {"id": "c2", "title": "Child 2", "type": "page"},
            ],
            "start": 0,
            "limit": 25,
            "size": 2,
        },
        status=200,
    )
    children = confluence_bearer.get_page_children("123")
    assert len(children) == 2
    assert children[0]["id"] == "c1"


@responses.activate
def test_get_page_comments_bearer(confluence_bearer):
    """v1: GET /rest/api/content/{id}/child/comment with offset pagination."""
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content/123/child/comment",
        json={
            "results": [
                {"id": "cm1", "body": {"storage": {"value": "<p>Hi</p>"}}, "created": "2024-01-01"},
            ],
            "start": 0,
            "limit": 25,
            "size": 1,
        },
        status=200,
    )
    comments = confluence_bearer.get_page_comments("123")
    assert len(comments) == 1
    assert comments[0]["id"] == "cm1"


@responses.activate
def test_add_page_comment_bearer(confluence_bearer):
    """v1: POST /rest/api/content with type=comment and container."""
    responses.add(
        responses.POST,
        "https://confluence.example.com/rest/api/content",
        json={"id": "cm2", "type": "comment"},
        status=200,
    )
    result = confluence_bearer.add_page_comment("123", "<p>test comment</p>")
    assert result["id"] == "cm2"

    parsed = json.loads(responses.calls[0].request.body)
    assert parsed["type"] == "comment"
    assert parsed["container"]["id"] == "123"
    assert parsed["body"]["storage"]["value"] == "<p>test comment</p>"


@responses.activate
def test_get_comment_bearer(confluence_bearer):
    """v1: GET /rest/api/content/{comment_id} (comments are content items)."""
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content/cm1",
        json={
            "id": "cm1",
            "type": "comment",
            "body": {"storage": {"value": "<p>A comment</p>"}},
            "version": {"number": 1},
        },
        status=200,
    )
    comment = confluence_bearer.get_comment("cm1")
    assert comment["id"] == "cm1"
    assert comment["type"] == "comment"


@responses.activate
def test_get_page_attachments_bearer(confluence_bearer):
    """v1: GET /rest/api/content/{id}/child/attachment with offset pagination."""
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content/123/child/attachment",
        json={
            "results": [
                {"id": "a1", "title": "file.pdf", "mediaType": "application/pdf"},
            ],
            "start": 0,
            "limit": 25,
            "size": 1,
        },
        status=200,
    )
    attachments = confluence_bearer.get_page_attachments("123")
    assert len(attachments) == 1
    assert attachments[0]["title"] == "file.pdf"


@responses.activate
def test_create_page_bearer(confluence_bearer):
    """v1: POST /rest/api/content with space.key and ancestors."""
    responses.add(
        responses.POST,
        "https://confluence.example.com/rest/api/content",
        json={"id": "999", "title": "New Page", "type": "page"},
        status=200,
    )
    result = confluence_bearer.create_page(
        space_id="GENAI",
        title="New Page",
        body="<p>content</p>",
        parent_id="123",
    )
    assert result["id"] == "999"

    parsed = json.loads(responses.calls[0].request.body)
    assert parsed["type"] == "page"
    assert parsed["space"]["key"] == "GENAI"
    assert parsed["ancestors"] == [{"id": "123"}]
    assert parsed["body"]["storage"]["value"] == "<p>content</p>"


@responses.activate
def test_create_page_bearer_no_parent(confluence_bearer):
    """v1: create page without parent omits ancestors."""
    responses.add(
        responses.POST,
        "https://confluence.example.com/rest/api/content",
        json={"id": "998", "title": "Root Page"},
        status=200,
    )
    confluence_bearer.create_page(space_id="GENAI", title="Root Page", body="<p>x</p>")

    parsed = json.loads(responses.calls[0].request.body)
    assert "ancestors" not in parsed
    assert parsed["space"]["key"] == "GENAI"


@responses.activate
def test_update_page_bearer(confluence_bearer):
    """v1: PUT /rest/api/content/{id} with v1 payload."""
    responses.add(
        responses.PUT,
        "https://confluence.example.com/rest/api/content/123",
        json={"id": "123", "title": "Updated", "version": {"number": 3}},
        status=200,
    )
    result = confluence_bearer.update_page(
        page_id="123",
        title="Updated",
        body="<p>new</p>",
        version_number=3,
    )
    assert result["title"] == "Updated"

    parsed = json.loads(responses.calls[0].request.body)
    assert parsed["type"] == "page"
    assert parsed["body"]["storage"]["value"] == "<p>new</p>"
    assert parsed["version"]["number"] == 3
    assert "id" not in parsed  # v1 doesn't include id in body


@responses.activate
def test_delete_page_bearer(confluence_bearer):
    """v1: DELETE /rest/api/content/{id}."""
    responses.add(
        responses.DELETE,
        "https://confluence.example.com/rest/api/content/123",
        status=204,
    )
    confluence_bearer.delete_page("123")
    assert len(responses.calls) == 1


@responses.activate
def test_get_space_by_key_bearer(confluence_bearer):
    """v1: delegates to get_space which uses /rest/api/space/{key}."""
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/space/GENAI",
        json={"id": "12345", "key": "GENAI", "name": "RAISE"},
        status=200,
    )
    space = confluence_bearer.get_space_by_key("GENAI")
    assert space["key"] == "GENAI"
    assert space["name"] == "RAISE"


@responses.activate
def test_update_page_auto_bearer(confluence_bearer):
    """v1: auto-increment uses v1 get_page then v1 update_page."""
    # get_page (v1)
    responses.add(
        responses.GET,
        "https://confluence.example.com/rest/api/content/123",
        json={"id": "123", "version": {"number": 5}, "body": {"storage": {"value": ""}}},
        status=200,
    )
    # update_page (v1)
    responses.add(
        responses.PUT,
        "https://confluence.example.com/rest/api/content/123",
        json={"id": "123", "title": "Auto", "version": {"number": 6}},
        status=200,
    )
    result = confluence_bearer.update_page_auto("123", "Auto", "<p>body</p>")
    assert result["version"]["number"] == 6

    parsed = json.loads(responses.calls[1].request.body)
    assert parsed["version"]["number"] == 6
    assert parsed["type"] == "page"
