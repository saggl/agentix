"""Tests for Bitbucket CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from agentix.cli import cli


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture
def mock_bitbucket_client():
    with patch("agentix.bitbucket.commands.resolve_auth") as mock_auth, \
         patch("agentix.bitbucket.commands.BitbucketClient") as mock_cls:
        mock_auth.return_value = MagicMock(
            base_url="https://bitbucket.example.com",
            user="test-user",
            token="test-token",
            auth_type="bearer",
        )
        client = MagicMock()
        mock_cls.return_value = client
        yield client


# -- Project tests --


def test_project_list(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_projects.return_value = [
        {"key": "PROJ1", "name": "Project 1", "id": 1, "description": "Desc 1", "public": False, "type": "NORMAL"},
        {"key": "PROJ2", "name": "Project 2", "id": 2, "description": "Desc 2", "public": True, "type": "NORMAL"},
    ]

    result = runner.invoke(cli, ["bitbucket", "project", "list"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["key"] == "PROJ1"


def test_project_get(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_project.return_value = {
        "key": "PROJ",
        "name": "My Project",
        "id": 123,
        "description": "Project description",
        "public": False,
        "type": "NORMAL",
    }

    result = runner.invoke(cli, ["bitbucket", "project", "get", "PROJ"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["key"] == "PROJ"
    assert data["name"] == "My Project"


# -- Repository tests --


def test_repo_list(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_repositories.return_value = [
        {"slug": "repo1", "name": "Repo 1", "state": "AVAILABLE", "project": {"key": "PROJ"}},
        {"slug": "repo2", "name": "Repo 2", "state": "AVAILABLE", "project": {"key": "PROJ"}},
    ]

    result = runner.invoke(cli, ["bitbucket", "repo", "list", "--project", "PROJ"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["slug"] == "repo1"


def test_repo_get(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_repository.return_value = {
        "id": 456,
        "slug": "my-repo",
        "name": "My Repo",
        "description": "Repo desc",
        "state": "AVAILABLE",
        "public": True,
        "forkable": True,
        "project": {"key": "PROJ", "name": "Project"},
        "links": {"clone": []},
    }

    result = runner.invoke(cli, ["bitbucket", "repo", "get", "PROJ", "my-repo"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["slug"] == "my-repo"


def test_repo_create(runner, mock_bitbucket_client):
    mock_bitbucket_client.create_repository.return_value = {
        "slug": "new-repo",
        "name": "New Repo",
        "id": 789,
        "project": {"key": "PROJ"},
        "links": {"clone": []},
        "state": "AVAILABLE",
        "public": False,
        "forkable": True,
    }

    result = runner.invoke(cli, [
        "bitbucket", "repo", "create",
        "--project", "PROJ",
        "--name", "New Repo",
        "--description", "Test repo"
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["slug"] == "new-repo"


# -- Branch tests --


def test_branch_list(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_branches.return_value = [
        {"id": "refs/heads/main", "displayId": "main", "type": "BRANCH", "latestCommit": "abc", "isDefault": True},
        {"id": "refs/heads/develop", "displayId": "develop", "type": "BRANCH", "latestCommit": "def", "isDefault": False},
    ]

    result = runner.invoke(cli, ["bitbucket", "branch", "list", "PROJ", "my-repo"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2
    assert data[0]["displayId"] == "main"


def test_branch_get(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_branch.return_value = {
        "id": "refs/heads/main",
        "displayId": "main",
        "type": "BRANCH",
        "latestCommit": "abc123",
        "isDefault": True,
    }

    result = runner.invoke(cli, ["bitbucket", "branch", "get", "PROJ", "my-repo", "main"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["displayId"] == "main"


def test_branch_create(runner, mock_bitbucket_client):
    mock_bitbucket_client.create_branch.return_value = {
        "id": "refs/heads/feature",
        "displayId": "feature",
        "type": "BRANCH",
        "latestCommit": "abc123",
        "isDefault": False,
    }

    result = runner.invoke(cli, [
        "bitbucket", "branch", "create",
        "PROJ", "my-repo",
        "--name", "feature",
        "--from", "main"
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_branch_delete(runner, mock_bitbucket_client):
    mock_bitbucket_client.delete_branch.return_value = None

    result = runner.invoke(cli, [
        "bitbucket", "branch", "delete",
        "PROJ", "my-repo", "old-branch",
        "--yes"
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_branch_default(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_default_branch.return_value = {
        "id": "refs/heads/main",
        "displayId": "main",
        "type": "BRANCH",
        "latestCommit": "abc123",
        "isDefault": True,
    }

    result = runner.invoke(cli, ["bitbucket", "branch", "default", "PROJ", "my-repo"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["displayId"] == "main"


# -- Pull Request tests --


def test_pr_list(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_pull_requests.return_value = [
        {
            "id": 1,
            "title": "PR 1",
            "state": "OPEN",
            "updatedDate": 1640000000000,
            "author": {"user": {"displayName": "John"}},
            "fromRef": {"displayId": "feature"},
            "toRef": {"displayId": "main"},
        },
    ]

    result = runner.invoke(cli, ["bitbucket", "pr", "list", "PROJ", "my-repo", "--state", "OPEN"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["id"] == 1


def test_pr_get(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_pull_request.return_value = {
        "id": 1,
        "version": 0,
        "title": "My PR",
        "description": "PR desc",
        "state": "OPEN",
        "open": True,
        "closed": False,
        "createdDate": 1640000000000,
        "updatedDate": 1640001000000,
        "author": {"user": {"name": "jdoe", "displayName": "John", "emailAddress": "john@example.com"}},
        "fromRef": {"id": "refs/heads/feature", "displayId": "feature", "latestCommit": "abc", "repository": {"slug": "my-repo"}},
        "toRef": {"id": "refs/heads/main", "displayId": "main", "latestCommit": "def", "repository": {"slug": "my-repo"}},
        "reviewers": [],
    }

    result = runner.invoke(cli, ["bitbucket", "pr", "get", "PROJ", "my-repo", "1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == 1
    assert data["title"] == "My PR"


def test_pr_create(runner, mock_bitbucket_client):
    mock_bitbucket_client.create_pull_request.return_value = {
        "id": 2,
        "version": 0,
        "title": "New PR",
        "description": "PR description",
        "state": "OPEN",
        "open": True,
        "closed": False,
        "createdDate": 1640000000000,
        "updatedDate": 1640000000000,
        "author": {"user": {"name": "jdoe", "displayName": "John", "emailAddress": "john@example.com"}},
        "fromRef": {"id": "refs/heads/feature", "displayId": "feature", "latestCommit": "abc", "repository": {"slug": "my-repo"}},
        "toRef": {"id": "refs/heads/main", "displayId": "main", "latestCommit": "def", "repository": {"slug": "my-repo"}},
        "reviewers": [],
    }

    result = runner.invoke(cli, [
        "bitbucket", "pr", "create",
        "PROJ", "my-repo",
        "--title", "New PR",
        "--from", "feature",
        "--to", "main"
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True
    assert data["data"]["id"] == 2


def test_pr_merge(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_pull_request.return_value = {"version": 0}
    mock_bitbucket_client.merge_pull_request.return_value = {"state": "MERGED"}

    result = runner.invoke(cli, [
        "bitbucket", "pr", "merge",
        "PROJ", "my-repo", "1",
        "--yes"
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_pr_approve(runner, mock_bitbucket_client):
    mock_bitbucket_client.approve_pull_request.return_value = {"approved": True}

    result = runner.invoke(cli, ["bitbucket", "pr", "approve", "PROJ", "my-repo", "1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_pr_decline(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_pull_request.return_value = {"version": 0}
    mock_bitbucket_client.decline_pull_request.return_value = {"state": "DECLINED"}

    result = runner.invoke(cli, [
        "bitbucket", "pr", "decline",
        "PROJ", "my-repo", "1",
        "--yes"
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_pr_comment(runner, mock_bitbucket_client):
    mock_bitbucket_client.add_pr_comment.return_value = {"id": 123}

    result = runner.invoke(cli, [
        "bitbucket", "pr", "comment",
        "PROJ", "my-repo", "1",
        "--text", "Looks good!"
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


def test_pr_activities(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_pr_activities.return_value = [
        {
            "id": 1,
            "createdDate": 1640000000000,
            "action": "COMMENTED",
            "commentAction": "ADDED",
            "user": {"name": "jdoe", "displayName": "John"},
            "comment": {"id": 10, "text": "Comment", "author": {"displayName": "John"}, "createdDate": 1640000000000, "updatedDate": 1640000000000},
        },
    ]

    result = runner.invoke(cli, ["bitbucket", "pr", "activities", "PROJ", "my-repo", "1"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1


# -- Commit tests --


def test_commit_list(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_commits.return_value = [
        {"id": "abc123", "displayId": "abc123", "message": "Commit 1", "authorTimestamp": 1640000000000, "author": {"name": "John"}},
        {"id": "def456", "displayId": "def456", "message": "Commit 2", "authorTimestamp": 1640001000000, "author": {"name": "Jane"}},
    ]

    result = runner.invoke(cli, ["bitbucket", "commit", "list", "PROJ", "my-repo"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2


def test_commit_get(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_commit.return_value = {
        "id": "abc123",
        "displayId": "abc123",
        "message": "Commit message",
        "authorTimestamp": 1640000000000,
        "committerTimestamp": 1640000000000,
        "author": {"name": "John", "emailAddress": "john@example.com"},
        "committer": {"name": "John", "emailAddress": "john@example.com"},
        "parents": [],
    }

    result = runner.invoke(cli, ["bitbucket", "commit", "get", "PROJ", "my-repo", "abc123"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == "abc123"


def test_commit_changes(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_commit_changes.return_value = [
        {"path": "file1.py"},
        {"path": "file2.py"},
    ]

    result = runner.invoke(cli, ["bitbucket", "commit", "changes", "PROJ", "my-repo", "abc123"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 2


def test_commit_diff(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_commit_diff.return_value = {"diffs": []}

    result = runner.invoke(cli, ["bitbucket", "commit", "diff", "PROJ", "my-repo", "abc123"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "diffs" in data


# -- Build status tests --


def test_build_status(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_commit_build_status.return_value = [
        {
            "state": "SUCCESSFUL",
            "key": "build-1",
            "name": "CI Build",
            "url": "https://ci.example.com",
            "description": "Build passed",
            "dateAdded": 1640000000000,
        },
    ]

    result = runner.invoke(cli, ["bitbucket", "build", "status", "abc123"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["state"] == "SUCCESSFUL"


def test_build_set(runner, mock_bitbucket_client):
    mock_bitbucket_client.set_commit_build_status.return_value = {
        "state": "SUCCESSFUL",
        "key": "build-1",
        "name": "CI Build",
        "url": "https://ci.example.com",
        "description": "Build passed",
        "dateAdded": 1640000000000,
    }

    result = runner.invoke(cli, [
        "bitbucket", "build", "set", "abc123",
        "--state", "SUCCESSFUL",
        "--key", "build-1",
        "--name", "CI Build",
        "--url", "https://ci.example.com"
    ])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["success"] is True


# -- User tests --


def test_user_me(runner, mock_bitbucket_client):
    mock_bitbucket_client.get_current_user.return_value = {
        "name": "jdoe",
        "emailAddress": "john@example.com",
        "id": 123,
        "displayName": "John Doe",
        "active": True,
        "slug": "jdoe",
        "type": "NORMAL",
    }

    result = runner.invoke(cli, ["bitbucket", "user", "me"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["name"] == "jdoe"
