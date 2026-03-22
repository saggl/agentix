"""Tests for Bitbucket model normalization functions."""

from agentix.bitbucket.models import (
    normalize_activity,
    normalize_branch,
    normalize_build_status,
    normalize_commit,
    normalize_commit_brief,
    normalize_project,
    normalize_pull_request,
    normalize_pull_request_brief,
    normalize_repository,
    normalize_repository_brief,
    normalize_user,
)


def test_normalize_project():
    raw = {
        "key": "PROJ",
        "id": 123,
        "name": "Project Name",
        "description": "Project description",
        "public": False,
        "type": "NORMAL",
    }
    result = normalize_project(raw)
    assert result["key"] == "PROJ"
    assert result["name"] == "Project Name"
    assert result["public"] is False


def test_normalize_repository():
    raw = {
        "id": 456,
        "slug": "my-repo",
        "name": "My Repository",
        "description": "Repo description",
        "state": "AVAILABLE",
        "public": True,
        "forkable": True,
        "project": {"key": "PROJ", "name": "Project Name"},
        "links": {
            "clone": [
                {"name": "http", "href": "https://bitbucket.example.com/scm/proj/my-repo.git"},
                {"name": "ssh", "href": "ssh://git@bitbucket.example.com:7999/proj/my-repo.git"},
            ]
        },
    }
    result = normalize_repository(raw)
    assert result["slug"] == "my-repo"
    assert result["project_key"] == "PROJ"
    assert result["clone_urls"]["http"] == "https://bitbucket.example.com/scm/proj/my-repo.git"
    assert result["clone_urls"]["ssh"] == "ssh://git@bitbucket.example.com:7999/proj/my-repo.git"


def test_normalize_repository_brief():
    raw = {
        "slug": "my-repo",
        "name": "My Repository",
        "state": "AVAILABLE",
        "project": {"key": "PROJ"},
    }
    result = normalize_repository_brief(raw)
    assert result["slug"] == "my-repo"
    assert result["project_key"] == "PROJ"
    assert "description" not in result


def test_normalize_branch():
    raw = {
        "id": "refs/heads/main",
        "displayId": "main",
        "type": "BRANCH",
        "latestCommit": "abc123",
        "isDefault": True,
    }
    result = normalize_branch(raw)
    assert result["displayId"] == "main"
    assert result["isDefault"] is True
    assert result["latestCommit"] == "abc123"


def test_normalize_pull_request():
    raw = {
        "id": 1,
        "version": 0,
        "title": "Feature branch",
        "description": "PR description",
        "state": "OPEN",
        "open": True,
        "closed": False,
        "createdDate": 1640000000000,
        "updatedDate": 1640001000000,
        "author": {
            "user": {
                "name": "jdoe",
                "displayName": "John Doe",
                "emailAddress": "john@example.com",
            }
        },
        "fromRef": {
            "id": "refs/heads/feature",
            "displayId": "feature",
            "latestCommit": "def456",
            "repository": {"slug": "my-repo"},
        },
        "toRef": {
            "id": "refs/heads/main",
            "displayId": "main",
            "latestCommit": "abc123",
            "repository": {"slug": "my-repo"},
        },
        "reviewers": [
            {
                "user": {"name": "reviewer", "displayName": "Reviewer Name"},
                "approved": True,
                "status": "APPROVED",
            }
        ],
    }
    result = normalize_pull_request(raw)
    assert result["id"] == 1
    assert result["title"] == "Feature branch"
    assert result["author"]["displayName"] == "John Doe"
    assert result["fromRef"]["displayId"] == "feature"
    assert result["toRef"]["displayId"] == "main"
    assert len(result["reviewers"]) == 1
    assert result["reviewers"][0]["approved"] is True


def test_normalize_pull_request_brief():
    raw = {
        "id": 1,
        "title": "Feature branch",
        "state": "OPEN",
        "updatedDate": 1640001000000,
        "author": {"user": {"displayName": "John Doe"}},
        "fromRef": {"displayId": "feature"},
        "toRef": {"displayId": "main"},
    }
    result = normalize_pull_request_brief(raw)
    assert result["id"] == 1
    assert result["title"] == "Feature branch"
    assert result["author"] == "John Doe"
    assert result["fromBranch"] == "feature"
    assert result["toBranch"] == "main"


def test_normalize_commit():
    raw = {
        "id": "abc123def456",
        "displayId": "abc123d",
        "message": "Commit message\n\nDetailed description",
        "authorTimestamp": 1640000000000,
        "committerTimestamp": 1640001000000,
        "author": {"name": "John Doe", "emailAddress": "john@example.com"},
        "committer": {"name": "John Doe", "emailAddress": "john@example.com"},
        "parents": [{"id": "parent123"}],
    }
    result = normalize_commit(raw)
    assert result["displayId"] == "abc123d"
    assert result["message"] == "Commit message\n\nDetailed description"
    assert result["author"]["name"] == "John Doe"
    assert len(result["parents"]) == 1


def test_normalize_commit_brief():
    raw = {
        "id": "abc123def456",
        "displayId": "abc123d",
        "message": "First line\nSecond line",
        "authorTimestamp": 1640000000000,
        "author": {"name": "John Doe"},
    }
    result = normalize_commit_brief(raw)
    assert result["id"] == "abc123d"
    assert result["message"] == "First line"  # Only first line
    assert result["author"] == "John Doe"


def test_normalize_activity():
    raw = {
        "id": 789,
        "createdDate": 1640000000000,
        "action": "COMMENTED",
        "commentAction": "ADDED",
        "user": {"name": "jdoe", "displayName": "John Doe"},
        "comment": {
            "id": 101,
            "text": "This looks good!",
            "author": {"displayName": "John Doe"},
            "createdDate": 1640000000000,
            "updatedDate": 1640001000000,
        },
    }
    result = normalize_activity(raw)
    assert result["action"] == "COMMENTED"
    assert result["user"]["displayName"] == "John Doe"
    assert result["comment"]["text"] == "This looks good!"


def test_normalize_build_status():
    raw = {
        "state": "SUCCESSFUL",
        "key": "build-1",
        "name": "CI Build",
        "url": "https://ci.example.com/build/1",
        "description": "Build passed",
        "dateAdded": 1640000000000,
    }
    result = normalize_build_status(raw)
    assert result["state"] == "SUCCESSFUL"
    assert result["key"] == "build-1"
    assert result["name"] == "CI Build"


def test_normalize_user():
    raw = {
        "name": "jdoe",
        "emailAddress": "john@example.com",
        "id": 123,
        "displayName": "John Doe",
        "active": True,
        "slug": "jdoe",
        "type": "NORMAL",
    }
    result = normalize_user(raw)
    assert result["name"] == "jdoe"
    assert result["displayName"] == "John Doe"
    assert result["active"] is True


def test_normalize_project_with_missing_fields():
    raw = {"key": "PROJ"}
    result = normalize_project(raw)
    assert result["key"] == "PROJ"
    assert result["name"] == ""
    assert result["description"] == ""


def test_normalize_repository_with_missing_links():
    raw = {
        "slug": "my-repo",
        "name": "My Repository",
        "project": {},
        "links": {},
    }
    result = normalize_repository(raw)
    assert result["slug"] == "my-repo"
    assert result["clone_urls"] == {}
