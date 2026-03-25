"""Tests for Jira client."""

import json

import pytest
import responses

from agentix.jira.client import JiraClient


@pytest.fixture
def jira():
    """Cloud client (API v3, ADF text fields)."""
    return JiraClient(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="test-token",
    )


@pytest.fixture
def jira_v2():
    """Server/DC client (API v2, plain-text fields)."""
    return JiraClient(
        base_url="https://jira.example.com",
        email="user@example.com",
        api_token="bearer-token",
        auth_type="bearer",
    )


@responses.activate
def test_get_issue(jira):
    responses.add(
        responses.GET,
        "https://test.atlassian.net/rest/api/3/issue/PROJ-1",
        json={
            "key": "PROJ-1",
            "id": "10001",
            "fields": {
                "summary": "Test issue",
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
            },
        },
        status=200,
    )
    issue = jira.get_issue("PROJ-1")
    assert issue["key"] == "PROJ-1"
    assert issue["fields"]["summary"] == "Test issue"


@responses.activate
def test_search_issues(jira):
    responses.add(
        responses.POST,
        "https://test.atlassian.net/rest/api/3/search",
        json={
            "issues": [
                {"key": "PROJ-1", "fields": {"summary": "Issue 1"}},
                {"key": "PROJ-2", "fields": {"summary": "Issue 2"}},
            ],
            "total": 2,
            "startAt": 0,
            "maxResults": 50,
        },
        status=200,
    )
    result = jira.search_issues('project = "PROJ"')
    assert len(result["issues"]) == 2


@responses.activate
def test_create_issue(jira):
    responses.add(
        responses.POST,
        "https://test.atlassian.net/rest/api/3/issue",
        json={"key": "PROJ-3", "id": "10003", "self": "https://..."},
        status=201,
    )
    result = jira.create_issue(
        project="PROJ",
        summary="New issue",
        issue_type="Task",
        description="A description",
    )
    assert result["key"] == "PROJ-3"

    # Verify request body
    body = responses.calls[0].request.body
    import json
    parsed = json.loads(body)
    assert parsed["fields"]["project"]["key"] == "PROJ"
    assert parsed["fields"]["summary"] == "New issue"


@responses.activate
def test_get_transitions(jira):
    responses.add(
        responses.GET,
        "https://test.atlassian.net/rest/api/3/issue/PROJ-1/transitions",
        json={
            "transitions": [
                {"id": "11", "name": "Start Progress", "to": {"name": "In Progress"}},
                {"id": "21", "name": "Done", "to": {"name": "Done"}},
            ]
        },
        status=200,
    )
    transitions = jira.get_transitions("PROJ-1")
    assert len(transitions) == 2
    assert transitions[0]["name"] == "Start Progress"


@responses.activate
def test_get_comments(jira):
    responses.add(
        responses.GET,
        "https://test.atlassian.net/rest/api/3/issue/PROJ-1/comment",
        json={
            "comments": [
                {
                    "id": "1",
                    "body": {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Hello"}]}]},
                    "author": {"displayName": "Alice"},
                }
            ]
        },
        status=200,
    )
    comments = jira.get_comments("PROJ-1")
    assert len(comments) == 1


@responses.activate
def test_get_projects(jira):
    responses.add(
        responses.GET,
        "https://test.atlassian.net/rest/api/3/project",
        json=[
            {"key": "PROJ", "name": "Test Project", "id": "10000"},
        ],
        status=200,
    )
    projects = jira.get_projects()
    assert len(projects) == 1
    assert projects[0]["key"] == "PROJ"


@responses.activate
def test_get_boards(jira):
    responses.add(
        responses.GET,
        "https://test.atlassian.net/rest/agile/1.0/board",
        json={
            "values": [{"id": 1, "name": "Board 1", "type": "scrum"}],
            "startAt": 0,
            "maxResults": 50,
            "total": 1,
        },
        status=200,
    )
    boards = jira.get_boards()
    assert len(boards) == 1
    assert boards[0]["name"] == "Board 1"


# -- API version flag tests --


def test_cloud_client_uses_v3(jira):
    assert jira._is_cloud is True
    assert jira._api == "/rest/api/3"


def test_server_client_uses_v2(jira_v2):
    assert jira_v2._is_cloud is False
    assert jira_v2._api == "/rest/api/2"


# -- Text field formatting tests --


def test_text_field_cloud_returns_adf(jira):
    result = jira._text_field("hello")
    assert result["type"] == "doc"
    assert result["content"][0]["content"][0]["text"] == "hello"


def test_text_field_server_returns_plain_string(jira_v2):
    result = jira_v2._text_field("hello")
    assert result == "hello"


@responses.activate
def test_create_issue_v2_sends_plain_description(jira_v2):
    responses.add(
        responses.POST,
        "https://jira.example.com/rest/api/2/issue",
        json={"key": "PROJ-1", "id": "10001", "self": "https://..."},
        status=201,
    )
    jira_v2.create_issue(
        project="PROJ",
        summary="Test",
        issue_type="Task",
        description="A plain description",
    )
    parsed = json.loads(responses.calls[0].request.body)
    assert parsed["fields"]["description"] == "A plain description"


@responses.activate
def test_create_issue_v3_sends_adf_description(jira):
    responses.add(
        responses.POST,
        "https://test.atlassian.net/rest/api/3/issue",
        json={"key": "PROJ-1", "id": "10001", "self": "https://..."},
        status=201,
    )
    jira.create_issue(
        project="PROJ",
        summary="Test",
        issue_type="Task",
        description="An ADF description",
    )
    parsed = json.loads(responses.calls[0].request.body)
    desc = parsed["fields"]["description"]
    assert desc["type"] == "doc"
    assert desc["content"][0]["content"][0]["text"] == "An ADF description"


@responses.activate
def test_add_comment_v2_sends_plain_body(jira_v2):
    responses.add(
        responses.POST,
        "https://jira.example.com/rest/api/2/issue/PROJ-1/comment",
        json={"id": "1"},
        status=201,
    )
    jira_v2.add_comment("PROJ-1", "plain comment")
    parsed = json.loads(responses.calls[0].request.body)
    assert parsed["body"] == "plain comment"


@responses.activate
def test_add_comment_v3_sends_adf_body(jira):
    responses.add(
        responses.POST,
        "https://test.atlassian.net/rest/api/3/issue/PROJ-1/comment",
        json={"id": "1"},
        status=201,
    )
    jira.add_comment("PROJ-1", "adf comment")
    parsed = json.loads(responses.calls[0].request.body)
    assert parsed["body"]["type"] == "doc"
    assert parsed["body"]["content"][0]["content"][0]["text"] == "adf comment"


@responses.activate
def test_transition_with_comment_v2_sends_plain(jira_v2):
    responses.add(
        responses.POST,
        "https://jira.example.com/rest/api/2/issue/PROJ-1/transitions",
        status=204,
    )
    jira_v2.transition_issue("PROJ-1", "11", comment="plain transition comment")
    parsed = json.loads(responses.calls[0].request.body)
    assert parsed["update"]["comment"][0]["add"]["body"] == "plain transition comment"
