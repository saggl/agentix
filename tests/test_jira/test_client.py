"""Tests for Jira client."""

import pytest
import responses

from agentix.jira.client import JiraClient


@pytest.fixture
def jira():
    return JiraClient(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="test-token",
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
