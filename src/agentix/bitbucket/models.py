"""Response normalization for Bitbucket API data."""

from typing import Any, Dict


def normalize_project(project: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a Bitbucket project into a clean dict."""
    return {
        "key": project.get("key", ""),
        "id": project.get("id", ""),
        "name": project.get("name", ""),
        "description": project.get("description", ""),
        "public": project.get("public", False),
        "type": project.get("type", ""),
    }


def normalize_repository(repo: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a Bitbucket repository into a clean dict."""
    project = repo.get("project", {})
    links = repo.get("links", {})
    clone_links = links.get("clone", [])

    clone_urls = {}
    for clone_link in clone_links:
        name = clone_link.get("name", "").lower()
        clone_urls[name] = clone_link.get("href", "")

    return {
        "id": repo.get("id", ""),
        "slug": repo.get("slug", ""),
        "name": repo.get("name", ""),
        "description": repo.get("description", ""),
        "state": repo.get("state", ""),
        "public": repo.get("public", False),
        "forkable": repo.get("forkable", False),
        "project_key": project.get("key", ""),
        "project_name": project.get("name", ""),
        "clone_urls": clone_urls,
    }


def normalize_repository_brief(repo: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal repository representation for lists."""
    project = repo.get("project", {})
    return {
        "slug": repo.get("slug", ""),
        "name": repo.get("name", ""),
        "project_key": project.get("key", ""),
        "state": repo.get("state", ""),
    }


def normalize_branch(branch: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a Bitbucket branch into a clean dict."""
    return {
        "id": branch.get("id", ""),
        "displayId": branch.get("displayId", ""),
        "type": branch.get("type", ""),
        "latestCommit": branch.get("latestCommit", ""),
        "latestChangeset": branch.get("latestChangeset", ""),
        "isDefault": branch.get("isDefault", False),
    }


def normalize_pull_request(pr: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a Bitbucket pull request into a clean dict."""
    author = pr.get("author", {}).get("user", {})
    from_ref = pr.get("fromRef", {})
    to_ref = pr.get("toRef", {})

    reviewers = []
    for reviewer in pr.get("reviewers", []):
        user = reviewer.get("user", {})
        reviewers.append({
            "name": user.get("name", ""),
            "displayName": user.get("displayName", ""),
            "approved": reviewer.get("approved", False),
            "status": reviewer.get("status", ""),
        })

    return {
        "id": pr.get("id", ""),
        "version": pr.get("version", 0),
        "title": pr.get("title", ""),
        "description": pr.get("description", ""),
        "state": pr.get("state", ""),
        "open": pr.get("open", False),
        "closed": pr.get("closed", False),
        "createdDate": pr.get("createdDate", 0),
        "updatedDate": pr.get("updatedDate", 0),
        "author": {
            "name": author.get("name", ""),
            "displayName": author.get("displayName", ""),
            "emailAddress": author.get("emailAddress", ""),
        },
        "fromRef": {
            "id": from_ref.get("id", ""),
            "displayId": from_ref.get("displayId", ""),
            "latestCommit": from_ref.get("latestCommit", ""),
            "repository": from_ref.get("repository", {}).get("slug", ""),
        },
        "toRef": {
            "id": to_ref.get("id", ""),
            "displayId": to_ref.get("displayId", ""),
            "latestCommit": to_ref.get("latestCommit", ""),
            "repository": to_ref.get("repository", {}).get("slug", ""),
        },
        "reviewers": reviewers,
    }


def normalize_pull_request_brief(pr: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal pull request representation for lists."""
    author = pr.get("author", {}).get("user", {})
    from_ref = pr.get("fromRef", {})
    to_ref = pr.get("toRef", {})

    return {
        "id": pr.get("id", ""),
        "title": pr.get("title", ""),
        "state": pr.get("state", ""),
        "author": author.get("displayName", ""),
        "fromBranch": from_ref.get("displayId", ""),
        "toBranch": to_ref.get("displayId", ""),
        "updatedDate": pr.get("updatedDate", 0),
    }


def normalize_commit(commit: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a Bitbucket commit into a clean dict."""
    author = commit.get("author", {})
    committer = commit.get("committer", {})

    return {
        "id": commit.get("id", ""),
        "displayId": commit.get("displayId", ""),
        "message": commit.get("message", ""),
        "authorTimestamp": commit.get("authorTimestamp", 0),
        "committerTimestamp": commit.get("committerTimestamp", 0),
        "author": {
            "name": author.get("name", ""),
            "emailAddress": author.get("emailAddress", ""),
        },
        "committer": {
            "name": committer.get("name", ""),
            "emailAddress": committer.get("emailAddress", ""),
        },
        "parents": [p.get("id", "") for p in commit.get("parents", [])],
    }


def normalize_commit_brief(commit: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal commit representation for lists."""
    author = commit.get("author", {})

    return {
        "id": commit.get("displayId", commit.get("id", "")),
        "message": commit.get("message", "").split("\n")[0],  # First line only
        "author": author.get("name", ""),
        "timestamp": commit.get("authorTimestamp", 0),
    }


def normalize_activity(activity: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a PR activity/comment into a clean dict."""
    user = activity.get("user", {})
    comment = activity.get("comment", {})

    result = {
        "id": activity.get("id", ""),
        "createdDate": activity.get("createdDate", 0),
        "action": activity.get("action", ""),
        "commentAction": activity.get("commentAction", ""),
    }

    if user:
        result["user"] = {
            "name": user.get("name", ""),
            "displayName": user.get("displayName", ""),
        }

    if comment:
        result["comment"] = {
            "id": comment.get("id", ""),
            "text": comment.get("text", ""),
            "author": comment.get("author", {}).get("displayName", ""),
            "createdDate": comment.get("createdDate", 0),
            "updatedDate": comment.get("updatedDate", 0),
        }

    return result


def normalize_build_status(status: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a build status into a clean dict."""
    return {
        "state": status.get("state", ""),
        "key": status.get("key", ""),
        "name": status.get("name", ""),
        "url": status.get("url", ""),
        "description": status.get("description", ""),
        "dateAdded": status.get("dateAdded", 0),
    }


def normalize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a Bitbucket user into a clean dict."""
    return {
        "name": user.get("name", ""),
        "emailAddress": user.get("emailAddress", ""),
        "id": user.get("id", ""),
        "displayName": user.get("displayName", ""),
        "active": user.get("active", True),
        "slug": user.get("slug", ""),
        "type": user.get("type", ""),
    }


def normalize_file(file_info: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten a file/directory entry into a clean dict."""
    return {
        "path": file_info.get("path", {}).get("toString", ""),
        "type": file_info.get("type", ""),
        "size": file_info.get("size", 0),
    }
