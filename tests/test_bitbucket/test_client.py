"""Tests for Bitbucket API client."""

from unittest.mock import MagicMock, patch

import pytest

from agentix.bitbucket.client import BitbucketClient


@pytest.fixture
def mock_http():
    with patch("agentix.bitbucket.client.BaseHTTPClient") as mock_cls:
        http = MagicMock()
        mock_cls.return_value = http
        yield http


@pytest.fixture
def client(mock_http):
    return BitbucketClient(
        base_url="https://bitbucket.example.com",
        username="test-user",
        api_token="test-token",
        auth_type="bearer",
    )


def test_get_projects(client, mock_http):
    mock_http.paginate.return_value = iter([
        {"key": "PROJ1", "name": "Project 1"},
        {"key": "PROJ2", "name": "Project 2"},
    ])

    result = client.get_projects()
    assert len(result) == 2
    assert result[0]["key"] == "PROJ1"
    mock_http.paginate.assert_called_once()


def test_get_project(client, mock_http):
    mock_http.get.return_value = {"key": "PROJ", "name": "My Project"}

    result = client.get_project("PROJ")
    assert result["key"] == "PROJ"
    mock_http.get.assert_called_once_with("/rest/api/1.0/projects/PROJ")


def test_get_repositories(client, mock_http):
    mock_http.paginate.return_value = iter([
        {"slug": "repo1"},
        {"slug": "repo2"},
    ])

    result = client.get_repositories("PROJ")
    assert len(result) == 2
    mock_http.paginate.assert_called_once()


def test_get_repository(client, mock_http):
    mock_http.get.return_value = {"slug": "my-repo", "name": "My Repo"}

    result = client.get_repository("PROJ", "my-repo")
    assert result["slug"] == "my-repo"
    mock_http.get.assert_called_once_with("/rest/api/1.0/projects/PROJ/repos/my-repo")


def test_create_repository(client, mock_http):
    mock_http.post.return_value = {"slug": "new-repo", "name": "New Repo"}

    result = client.create_repository("PROJ", "New Repo", description="Test repo")
    assert result["slug"] == "new-repo"
    mock_http.post.assert_called_once()


def test_get_branches(client, mock_http):
    mock_http.paginate.return_value = iter([
        {"displayId": "main"},
        {"displayId": "develop"},
    ])

    result = client.get_branches("PROJ", "my-repo")
    assert len(result) == 2
    mock_http.paginate.assert_called_once()


def test_get_branch(client, mock_http):
    mock_http.get.return_value = {
        "values": [{"displayId": "main", "isDefault": True}]
    }

    result = client.get_branch("PROJ", "my-repo", "main")
    assert result["displayId"] == "main"


def test_create_branch(client, mock_http):
    mock_http.post.return_value = {"displayId": "feature-branch"}

    result = client.create_branch("PROJ", "my-repo", "feature-branch", "main")
    assert result["displayId"] == "feature-branch"
    mock_http.post.assert_called_once()


def test_delete_branch(client, mock_http):
    mock_http.get.return_value = {
        "values": [{"id": "refs/heads/old-branch", "displayId": "old-branch"}]
    }
    mock_http.delete.return_value = None

    client.delete_branch("PROJ", "my-repo", "old-branch")
    mock_http.delete.assert_called_once()


def test_delete_branch_not_found(client, mock_http):
    mock_http.get.return_value = {"values": []}

    with pytest.raises(ValueError, match="Branch 'nonexistent' not found"):
        client.delete_branch("PROJ", "my-repo", "nonexistent")


def test_get_pull_requests(client, mock_http):
    mock_http.paginate.return_value = iter([
        {"id": 1, "title": "PR 1"},
        {"id": 2, "title": "PR 2"},
    ])

    result = client.get_pull_requests("PROJ", "my-repo", state="OPEN")
    assert len(result) == 2
    mock_http.paginate.assert_called_once()


def test_get_pull_request(client, mock_http):
    mock_http.get.return_value = {"id": 1, "title": "My PR"}

    result = client.get_pull_request("PROJ", "my-repo", 1)
    assert result["id"] == 1
    mock_http.get.assert_called_once_with(
        "/rest/api/1.0/projects/PROJ/repos/my-repo/pull-requests/1"
    )


def test_create_pull_request(client, mock_http):
    mock_http.post.return_value = {"id": 1, "title": "New PR"}

    result = client.create_pull_request(
        "PROJ", "my-repo", "New PR", "feature", "main",
        description="PR description",
        reviewers=["reviewer1"]
    )
    assert result["id"] == 1
    mock_http.post.assert_called_once()


def test_merge_pull_request(client, mock_http):
    mock_http.post.return_value = {"state": "MERGED"}

    result = client.merge_pull_request("PROJ", "my-repo", 1, 0)
    assert result["state"] == "MERGED"
    mock_http.post.assert_called_once()


def test_approve_pull_request(client, mock_http):
    mock_http.post.return_value = {"approved": True}

    result = client.approve_pull_request("PROJ", "my-repo", 1)
    assert result["approved"] is True


def test_decline_pull_request(client, mock_http):
    mock_http.post.return_value = {"state": "DECLINED"}

    result = client.decline_pull_request("PROJ", "my-repo", 1, 0)
    assert result["state"] == "DECLINED"


def test_get_pr_activities(client, mock_http):
    mock_http.paginate.return_value = iter([
        {"id": 1, "action": "COMMENTED"},
        {"id": 2, "action": "APPROVED"},
    ])

    result = client.get_pr_activities("PROJ", "my-repo", 1)
    assert len(result) == 2


def test_add_pr_comment(client, mock_http):
    mock_http.post.return_value = {"id": 123, "text": "Nice work!"}

    result = client.add_pr_comment("PROJ", "my-repo", 1, "Nice work!")
    assert result["id"] == 123
    mock_http.post.assert_called_once()


def test_get_commits(client, mock_http):
    mock_http.paginate.return_value = iter([
        {"id": "abc123"},
        {"id": "def456"},
    ])

    result = client.get_commits("PROJ", "my-repo", until="main", max_results=10)
    assert len(result) == 2


def test_get_commit(client, mock_http):
    mock_http.get.return_value = {"id": "abc123", "message": "Fix bug"}

    result = client.get_commit("PROJ", "my-repo", "abc123")
    assert result["id"] == "abc123"


def test_get_commit_changes(client, mock_http):
    mock_http.paginate.return_value = iter([
        {"path": "file1.py"},
        {"path": "file2.py"},
    ])

    result = client.get_commit_changes("PROJ", "my-repo", "abc123")
    assert len(result) == 2


def test_get_commit_diff(client, mock_http):
    mock_http.get.return_value = {"diffs": []}

    result = client.get_commit_diff("PROJ", "my-repo", "abc123", path="file.py")
    assert "diffs" in result


def test_get_commit_build_status(client, mock_http):
    mock_http.paginate.return_value = iter([
        {"state": "SUCCESSFUL", "key": "build-1"},
    ])

    result = client.get_commit_build_status("abc123")
    assert len(result) == 1
    assert result[0]["state"] == "SUCCESSFUL"


def test_set_commit_build_status(client, mock_http):
    mock_http.post.return_value = {"state": "SUCCESSFUL", "key": "build-1"}

    result = client.set_commit_build_status(
        "abc123", "SUCCESSFUL", "build-1", "CI Build",
        "https://ci.example.com", "Build passed"
    )
    assert result["state"] == "SUCCESSFUL"
    mock_http.post.assert_called_once()


def test_get_repository_files(client, mock_http):
    mock_http.paginate.return_value = iter([
        {"path": "file1.py"},
        {"path": "file2.py"},
    ])

    result = client.get_repository_files("PROJ", "my-repo", path="src", at="main")
    assert len(result) == 2
