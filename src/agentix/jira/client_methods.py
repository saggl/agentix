"""Jira client method mixins."""

from typing import Any, Dict, Iterator, List, Optional


class JiraMethods:

    def _text_field(self, text: str) -> Any:
        """Format a text value for the Jira API.

        API v3 (Cloud) uses Atlassian Document Format; API v2 (Server/DC) uses plain strings.
        """
        if getattr(self, "_is_cloud", True):
            return {
                "type": "doc",
                "version": 1,
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": text}]}
                ],
            }
        return text

    # -- Issues --

    def get_issue(
        self, issue_key: str, fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        return self.http.get(f"{self._api}/issue/{issue_key}", params=params)

    def search_issues(
        self,
        jql: str,
        fields: Optional[List[str]] = None,
        max_results: int = 50,
        start_at: int = 0,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {
            "jql": jql,
            "maxResults": max_results,
            "startAt": start_at,
        }
        if fields:
            body["fields"] = fields
        return self.http.post(f"{self._api}/search", json=body)

    def search_issues_all(
        self,
        jql: str,
        fields: Optional[List[str]] = None,
        max_results: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Iterate over all matching issues with automatic pagination."""
        page_size = min(max_results or 50, 50)
        start_at = 0
        yielded = 0

        while True:
            result = self.search_issues(jql, fields, page_size, start_at)
            issues = result.get("issues", [])
            for issue in issues:
                if max_results and yielded >= max_results:
                    return
                yield issue
                yielded += 1

            total = result.get("total", 0)
            start_at += len(issues)
            if not issues or start_at >= total:
                break

    def create_issue(
        self,
        project: str,
        summary: str,
        issue_type: str,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
        **extra_fields: Any,
    ) -> Dict[str, Any]:
        fields: Dict[str, Any] = {
            "project": {"key": project},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        if description:
            fields["description"] = self._text_field(description)
        if assignee:
            fields["assignee"] = {"accountId": assignee}
        if priority:
            fields["priority"] = {"name": priority}
        if labels:
            fields["labels"] = labels
        fields.update(extra_fields)
        return self.http.post(f"{self._api}/issue", json={"fields": fields})

    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> None:
        self.http.put(f"{self._api}/issue/{issue_key}", json={"fields": fields})

    def delete_issue(self, issue_key: str) -> None:
        self.http.delete(f"{self._api}/issue/{issue_key}")

    def assign_issue(self, issue_key: str, account_id: str) -> None:
        self.http.put(
            f"{self._api}/issue/{issue_key}/assignee",
            json={"accountId": account_id},
        )

    # -- Transitions --

    def get_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        data = self.http.get(f"{self._api}/issue/{issue_key}/transitions")
        return data.get("transitions", [])

    def transition_issue(
        self, issue_key: str, transition_id: str, comment: Optional[str] = None
    ) -> None:
        body: Dict[str, Any] = {"transition": {"id": transition_id}}
        if comment:
            body["update"] = {
                "comment": [
                    {"add": {"body": self._text_field(comment)}}
                ]
            }
        self.http.post(f"{self._api}/issue/{issue_key}/transitions", json=body)

    # -- Comments --

    def get_comments(self, issue_key: str) -> List[Dict[str, Any]]:
        data = self.http.get(f"{self._api}/issue/{issue_key}/comment")
        return data.get("comments", [])

    def add_comment(self, issue_key: str, body: str) -> Dict[str, Any]:
        return self.http.post(
            f"{self._api}/issue/{issue_key}/comment",
            json={"body": self._text_field(body)},
        )

    def get_comment(
        self, issue_key: str, comment_id: str
    ) -> Dict[str, Any]:
        return self.http.get(
            f"{self._api}/issue/{issue_key}/comment/{comment_id}"
        )

    # -- Attachments --

    def get_attachments(self, issue_key: str) -> List[Dict[str, Any]]:
        issue = self.get_issue(issue_key, fields=["attachment"])
        return issue.get("fields", {}).get("attachment", [])

    def add_attachment(self, issue_key: str, file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, "rb") as f:
            return self.http.post(
                f"{self._api}/issue/{issue_key}/attachments",
                files={"file": f},
                headers={"X-Atlassian-Token": "no-check"},
            )

    def get_attachment_content(self, attachment_id: str) -> bytes:
        meta = self.http.get(f"{self._api}/attachment/{attachment_id}")
        content_url = meta.get("content", "")
        resp = self.http.get_raw(content_url)
        resp.raise_for_status()
        return resp.content

    def get_issue_edit_metadata(self, issue_key: str) -> Dict[str, Any]:
        """Get metadata for editing an issue (available fields and their allowed values)."""
        return self.http.get(f"{self._api}/issue/{issue_key}/editmeta")

    def get_create_metadata(
        self,
        project_keys: Optional[List[str]] = None,
        issue_type_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get metadata for creating issues (available fields and their allowed values)."""
        params = {}
        if project_keys:
            params["projectKeys"] = ",".join(project_keys)
        if issue_type_names:
            params["issuetypeNames"] = ",".join(issue_type_names)
        return self.http.get(f"{self._api}/issue/createmeta", params=params)

    # -- Sprints (Agile API) --

    def get_boards(
        self, project_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if project_key:
            params["projectKeyOrId"] = project_key
        return list(
            self.http.paginate(f"{self._agile}/board", params=params)
        )

    def get_board(self, board_id: int) -> Dict[str, Any]:
        return self.http.get(f"{self._agile}/board/{board_id}")

    def get_sprints(
        self, board_id: int, state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if state:
            params["state"] = state
        return list(
            self.http.paginate(
                f"{self._agile}/board/{board_id}/sprint", params=params
            )
        )

    def get_sprint(self, sprint_id: int) -> Dict[str, Any]:
        return self.http.get(f"{self._agile}/sprint/{sprint_id}")

    def get_sprint_issues(
        self, sprint_id: int, max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        return list(
            self.http.paginate(
                f"{self._agile}/sprint/{sprint_id}/issue",
                results_key="issues",
                max_results=max_results,
            )
        )

    def get_active_sprint(self, board_id: int) -> Optional[Dict[str, Any]]:
        sprints = self.get_sprints(board_id, state="active")
        return sprints[0] if sprints else None

    # -- Epics --

    def get_epics(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        jql = 'issuetype = Epic'
        if project_key:
            jql = f'project = "{project_key}" AND issuetype = Epic'
        result = self.search_issues(jql, max_results=50)
        return result.get("issues", [])

    def get_epic_issues(
        self, epic_key: str, max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        jql = f'"Epic Link" = "{epic_key}"'
        return list(self.search_issues_all(jql, max_results=max_results))

    # -- Projects --

    def get_projects(self) -> List[Dict[str, Any]]:
        return self.http.get(f"{self._api}/project")

    def get_project(self, project_key: str) -> Dict[str, Any]:
        return self.http.get(f"{self._api}/project/{project_key}")

    # -- Components --

    def get_project_components(self, project_key: str) -> List[Dict[str, Any]]:
        """Get all components in a project."""
        return self.http.get(f"{self._api}/project/{project_key}/components")

    def create_component(
        self,
        project_key: str,
        name: str,
        description: Optional[str] = None,
        lead_account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a component in a project."""
        body: Dict[str, Any] = {
            "name": name,
            "project": project_key,
        }
        if description:
            body["description"] = description
        if lead_account_id:
            body["leadAccountId"] = lead_account_id
        return self.http.post(f"{self._api}/component", json=body)

    def update_component(
        self,
        component_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        lead_account_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a component."""
        body: Dict[str, Any] = {}
        if name:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if lead_account_id:
            body["leadAccountId"] = lead_account_id
        return self.http.put(f"{self._api}/component/{component_id}", json=body)

    def delete_component(self, component_id: str) -> None:
        """Delete a component."""
        self.http.delete(f"{self._api}/component/{component_id}")

    # -- Versions --

    def get_project_versions(self, project_key: str) -> List[Dict[str, Any]]:
        """Get all versions in a project."""
        return self.http.get(f"{self._api}/project/{project_key}/versions")

    def create_version(
        self,
        project_key: str,
        name: str,
        description: Optional[str] = None,
        start_date: Optional[str] = None,
        release_date: Optional[str] = None,
        released: bool = False,
        archived: bool = False,
    ) -> Dict[str, Any]:
        """Create a version in a project."""
        body: Dict[str, Any] = {
            "name": name,
            "project": project_key,
            "released": released,
            "archived": archived,
        }
        if description:
            body["description"] = description
        if start_date:
            body["startDate"] = start_date
        if release_date:
            body["releaseDate"] = release_date
        return self.http.post(f"{self._api}/version", json=body)

    def update_version(
        self,
        version_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        released: Optional[bool] = None,
        archived: Optional[bool] = None,
        release_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a version."""
        body: Dict[str, Any] = {}
        if name:
            body["name"] = name
        if description is not None:
            body["description"] = description
        if released is not None:
            body["released"] = released
        if archived is not None:
            body["archived"] = archived
        if release_date:
            body["releaseDate"] = release_date
        return self.http.put(f"{self._api}/version/{version_id}", json=body)

    def delete_version(self, version_id: str) -> None:
        """Delete a version."""
        self.http.delete(f"{self._api}/version/{version_id}")

    def archive_version(self, version_id: str) -> Dict[str, Any]:
        """Archive a version (convenience method)."""
        return self.update_version(version_id, archived=True)
