"""Bitbucket REST API client."""

from typing import Any, Dict, List, Optional

import requests

from agentix.core.exceptions import AgentixError
from agentix.core.http import BaseHTTPClient


def _parse_bitbucket_error(response: requests.Response) -> Optional[str]:
    """Parse Bitbucket error payloads into a concise message."""
    try:
        body = response.json()
    except ValueError:
        return None

    if not isinstance(body, dict):
        return None

    errors = body.get("errors")
    if isinstance(errors, list):
        messages: List[str] = []
        for item in errors:
            if isinstance(item, dict):
                msg = item.get("message") or item.get("context")
                if msg:
                    messages.append(str(msg))
            elif item:
                messages.append(str(item))
        if messages:
            return "; ".join(messages)

    if isinstance(body.get("message"), str) and body["message"].strip():
        return body["message"]

    return None


class BitbucketClient:
    """Bitbucket Server/Data Center REST API 1.0 client."""

    def __init__(self, base_url: str, username: str, api_token: str, auth_type: str = "bearer"):
        self.http = BaseHTTPClient(
            base_url=base_url,
            auth=(username, api_token),
            auth_type=auth_type,
            headers={"Content-Type": "application/json"},
            error_parser=_parse_bitbucket_error,
        )
        self._api = "/rest/api/1.0"
        self._build_status = "/rest/build-status/1.0"

    # -- Projects --

    def get_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        return list(
            self.http.paginate(
                f"{self._api}/projects",
                results_key="values",
                start_key="start",
                max_key="limit",
            )
        )

    def get_project(self, project_key: str) -> Dict[str, Any]:
        """Get project details."""
        return self.http.get(f"{self._api}/projects/{project_key}")

    # -- Repositories --

    def get_repositories(self, project_key: str) -> List[Dict[str, Any]]:
        """List repositories in a project."""
        return list(
            self.http.paginate(
                f"{self._api}/projects/{project_key}/repos",
                results_key="values",
                start_key="start",
                max_key="limit",
            )
        )

    def get_repository(self, project_key: str, repo_slug: str) -> Dict[str, Any]:
        """Get repository details."""
        return self.http.get(f"{self._api}/projects/{project_key}/repos/{repo_slug}")

    def create_repository(
        self,
        project_key: str,
        name: str,
        description: Optional[str] = None,
        forkable: bool = True,
        public: bool = False,
    ) -> Dict[str, Any]:
        """Create a new repository."""
        body: Dict[str, Any] = {
            "name": name,
            "forkable": forkable,
            "public": public,
        }
        if description:
            body["description"] = description

        return self.http.post(
            f"{self._api}/projects/{project_key}/repos",
            json=body,
        )

    def get_repository_files(
        self,
        project_key: str,
        repo_slug: str,
        path: Optional[str] = None,
        at: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Browse files in a repository."""
        params: Dict[str, Any] = {}
        if at:
            params["at"] = at

        endpoint = f"{self._api}/projects/{project_key}/repos/{repo_slug}/files"
        if path:
            endpoint = f"{endpoint}/{path}"

        return list(
            self.http.paginate(
                endpoint,
                params=params,
                results_key="values",
                start_key="start",
                max_key="limit",
            )
        )

    # -- Branches --

    def get_branches(
        self,
        project_key: str,
        repo_slug: str,
        filter_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List branches in a repository."""
        params = {}
        if filter_text:
            params["filterText"] = filter_text

        return list(
            self.http.paginate(
                f"{self._api}/projects/{project_key}/repos/{repo_slug}/branches",
                params=params,
                results_key="values",
                start_key="start",
                max_key="limit",
            )
        )

    def get_branch(
        self,
        project_key: str,
        repo_slug: str,
        branch_name: str,
    ) -> Dict[str, Any]:
        """Get branch details."""
        return self.http.get(
            f"{self._api}/projects/{project_key}/repos/{repo_slug}/branches",
            params={"filterText": branch_name, "limit": 1},
        ).get("values", [{}])[0]

    def get_default_branch(
        self,
        project_key: str,
        repo_slug: str,
    ) -> Dict[str, Any]:
        """Get the default branch."""
        return self.http.get(
            f"{self._api}/projects/{project_key}/repos/{repo_slug}/default-branch"
        )

    def create_branch(
        self,
        project_key: str,
        repo_slug: str,
        name: str,
        start_point: str,
    ) -> Dict[str, Any]:
        """Create a new branch."""
        return self.http.post(
            f"{self._api}/projects/{project_key}/repos/{repo_slug}/branches",
            json={
                "name": name,
                "startPoint": start_point,
            },
        )

    def delete_branch(
        self,
        project_key: str,
        repo_slug: str,
        name: str,
    ) -> None:
        """Delete a branch."""
        # Need to get the branch details first to get the commit ID for deletion
        branches = self.http.get(
            f"{self._api}/projects/{project_key}/repos/{repo_slug}/branches",
            params={"filterText": name, "limit": 1},
        ).get("values", [])

        if not branches:
            raise ValueError(f"Branch '{name}' not found")

        branch_id = branches[0].get("id")
        self.http.delete(
            f"{self._api}/projects/{project_key}/repos/{repo_slug}/branches",
            json={"name": branch_id},
        )

    # -- Tags --

    def get_tags(
        self,
        project_key: str,
        repo_slug: str,
        filter_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List tags in a repository."""
        params = {"filterText": filter_text} if filter_text else {}

        return list(
            self.http.paginate(
                f"{self._api}/projects/{project_key}/repos/{repo_slug}/tags",
                params=params,
                results_key="values",
                start_key="start",
                max_key="limit",
            )
        )

    def create_tag(
        self,
        project_key: str,
        repo_slug: str,
        name: str,
        start_point: str,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a lightweight or annotated tag."""
        body: Dict[str, Any] = {
            "name": name,
            "startPoint": start_point,
        }
        if message:
            body["message"] = message
            body["type"] = "ANNOTATED"

        # Tag creation uses Git REST API 1.0
        return self.http.post(
            f"/rest/git/1.0/projects/{project_key}/repos/{repo_slug}/tags",
            json=body,
        )

    # -- Pull Requests --

    def get_pull_requests(
        self,
        project_key: str,
        repo_slug: str,
        state: Optional[str] = None,
        direction: str = "INCOMING",
        at: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List pull requests."""
        params: Dict[str, Any] = {"direction": direction}
        if state:
            params["state"] = state.upper()
        if at:
            params["at"] = at

        return list(
            self.http.paginate(
                f"{self._api}/projects/{project_key}/repos/{repo_slug}/pull-requests",
                params=params,
                results_key="values",
                start_key="start",
                max_key="limit",
            )
        )

    def get_pull_request(
        self,
        project_key: str,
        repo_slug: str,
        pr_id: int,
    ) -> Dict[str, Any]:
        """Get pull request details."""
        return self.http.get(
            f"{self._api}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}"
        )

    def create_pull_request(
        self,
        project_key: str,
        repo_slug: str,
        title: str,
        from_ref: str,
        to_ref: str,
        description: Optional[str] = None,
        reviewers: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a pull request."""
        body: Dict[str, Any] = {
            "title": title,
            "fromRef": {
                "id": f"refs/heads/{from_ref}",
                "repository": {
                    "slug": repo_slug,
                    "project": {"key": project_key},
                },
            },
            "toRef": {
                "id": f"refs/heads/{to_ref}",
                "repository": {
                    "slug": repo_slug,
                    "project": {"key": project_key},
                },
            },
        }

        if description:
            body["description"] = description

        if reviewers:
            body["reviewers"] = [{"user": {"name": r}} for r in reviewers]

        return self.http.post(
            f"{self._api}/projects/{project_key}/repos/{repo_slug}/pull-requests",
            json=body,
        )

    def merge_pull_request(
        self,
        project_key: str,
        repo_slug: str,
        pr_id: int,
        version: int,
    ) -> Dict[str, Any]:
        """Merge a pull request."""
        return self.http.post(
            f"{self._api}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/merge",
            params={"version": version},
        )

    def approve_pull_request(
        self,
        project_key: str,
        repo_slug: str,
        pr_id: int,
    ) -> Dict[str, Any]:
        """Approve a pull request."""
        return self.http.post(
            f"{self._api}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/approve"
        )

    def decline_pull_request(
        self,
        project_key: str,
        repo_slug: str,
        pr_id: int,
        version: int,
    ) -> Dict[str, Any]:
        """Decline a pull request."""
        return self.http.post(
            f"{self._api}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/decline",
            params={"version": version},
        )

    def get_pr_activities(
        self,
        project_key: str,
        repo_slug: str,
        pr_id: int,
    ) -> List[Dict[str, Any]]:
        """Get pull request activities (comments, approvals, etc)."""
        return list(
            self.http.paginate(
                f"{self._api}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/activities",
                results_key="values",
                start_key="start",
                max_key="limit",
            )
        )

    def add_pr_comment(
        self,
        project_key: str,
        repo_slug: str,
        pr_id: int,
        text: str,
    ) -> Dict[str, Any]:
        """Add a comment to a pull request."""
        return self.http.post(
            f"{self._api}/projects/{project_key}/repos/{repo_slug}/pull-requests/{pr_id}/comments",
            json={"text": text},
        )

    # -- Commits --

    def get_commits(
        self,
        project_key: str,
        repo_slug: str,
        until: Optional[str] = None,
        since: Optional[str] = None,
        path: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """List commits."""
        params: Dict[str, Any] = {}
        if until:
            params["until"] = until
        if since:
            params["since"] = since
        if path:
            params["path"] = path

        return list(
            self.http.paginate(
                f"{self._api}/projects/{project_key}/repos/{repo_slug}/commits",
                params=params,
                results_key="values",
                start_key="start",
                max_key="limit",
                max_results=max_results,
            )
        )

    def get_commit(
        self,
        project_key: str,
        repo_slug: str,
        commit_id: str,
    ) -> Dict[str, Any]:
        """Get commit details."""
        return self.http.get(
            f"{self._api}/projects/{project_key}/repos/{repo_slug}/commits/{commit_id}"
        )

    def get_commit_changes(
        self,
        project_key: str,
        repo_slug: str,
        commit_id: str,
    ) -> List[Dict[str, Any]]:
        """Get files changed in a commit."""
        return list(
            self.http.paginate(
                f"{self._api}/projects/{project_key}/repos/{repo_slug}/commits/{commit_id}/changes",
                results_key="values",
                start_key="start",
                max_key="limit",
            )
        )

    def get_commit_diff(
        self,
        project_key: str,
        repo_slug: str,
        commit_id: str,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get diff for a commit."""
        params = {}
        if path:
            params["path"] = path

        return self.http.get(
            f"{self._api}/projects/{project_key}/repos/{repo_slug}/commits/{commit_id}/diff",
            params=params,
        )

    # -- Users --

    def get_current_user(self) -> Dict[str, Any]:
        """Get the authenticated user's info."""
        # Try the user endpoint first (works with PAT)
        try:
            # For bearer auth (PAT), we need to use a different endpoint
            return self.http.get(f"{self._api}/users")
        except AgentixError:
            # Fallback for auth modes/environments where this endpoint is unavailable
            return {}

    # -- Build Status --

    def get_commit_build_status(self, commit_id: str) -> List[Dict[str, Any]]:
        """Get build statuses for a commit."""
        return list(
            self.http.paginate(
                f"{self._build_status}/commits/{commit_id}",
                results_key="values",
                start_key="start",
                max_key="limit",
            )
        )

    def set_commit_build_status(
        self,
        commit_id: str,
        state: str,
        key: str,
        name: str,
        url: str,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Set build status for a commit.

        Args:
            commit_id: The commit hash
            state: Build state (SUCCESSFUL, FAILED, INPROGRESS)
            key: Unique key for this build
            name: Display name
            url: URL to build results
            description: Optional description
        """
        body: Dict[str, Any] = {
            "state": state.upper(),
            "key": key,
            "name": name,
            "url": url,
        }
        if description:
            body["description"] = description

        return self.http.post(
            f"{self._build_status}/commits/{commit_id}",
            json=body,
        )
