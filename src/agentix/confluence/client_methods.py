"""Confluence client method mixins."""

from typing import Any, Dict, Iterator, List, Optional


class ConfluenceMethods:
    # -- Pages --

    def get_page(
        self,
        page_id: str,
        body_format: str = "storage",
    ) -> Dict[str, Any]:
        if not self._is_cloud:
            params = {"expand": "body.storage,version"}
            return self.http.get(f"{self._v1}/content/{page_id}", params=params)
        params = {"body-format": body_format}
        return self.http.get(f"{self._v2}/pages/{page_id}", params=params)

    def get_page_by_title(
        self,
        space_key: str,
        title: str,
    ) -> Optional[Dict[str, Any]]:
        """Find a page by its title in a space."""
        results = list(self.search_cql(
            f'space = "{space_key}" AND title = "{title}"',
            max_results=1,
        ))
        return results[0] if results else None

    def search_pages(
        self,
        query: str,
        space_key: Optional[str] = None,
        max_results: int = 25,
    ) -> List[Dict[str, Any]]:
        cql = f'type = page AND text ~ "{query}"'
        if space_key:
            cql = f'space = "{space_key}" AND {cql}'
        return list(self.search_cql(cql, max_results=max_results))

    def create_page(
        self,
        space_id: str,
        title: str,
        body: str,
        parent_id: Optional[str] = None,
        body_format: str = "storage",
    ) -> Dict[str, Any]:
        if not self._is_cloud:
            # v1: space_id is actually a space key for Server/DC
            payload: Dict[str, Any] = {
                "type": "page",
                "title": title,
                "space": {"key": space_id},
                "body": {"storage": {"value": body, "representation": body_format}},
            }
            if parent_id:
                payload["ancestors"] = [{"id": parent_id}]
            return self.http.post(f"{self._v1}/content", json=payload)

        payload = {
            "spaceId": space_id,
            "title": title,
            "body": {
                "representation": body_format,
                "value": body,
            },
            "status": "current",
        }
        if parent_id:
            payload["parentId"] = parent_id
        return self.http.post(f"{self._v2}/pages", json=payload)

    def update_page(
        self,
        page_id: str,
        title: str,
        body: str,
        version_number: int,
        body_format: str = "storage",
        version_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self._is_cloud:
            payload: Dict[str, Any] = {
                "type": "page",
                "title": title,
                "body": {"storage": {"value": body, "representation": body_format}},
                "version": {"number": version_number},
            }
            if version_message:
                payload["version"]["message"] = version_message
            return self.http.put(f"{self._v1}/content/{page_id}", json=payload)

        payload = {
            "id": page_id,
            "title": title,
            "body": {
                "representation": body_format,
                "value": body,
            },
            "version": {
                "number": version_number,
            },
            "status": "current",
        }
        if version_message:
            payload["version"]["message"] = version_message
        return self.http.put(f"{self._v2}/pages/{page_id}", json=payload)

    def update_page_auto(
        self,
        page_id: str,
        title: str,
        body: str,
        body_format: str = "storage",
        version_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update page, auto-incrementing the version number."""
        current = self.get_page(page_id)
        current_version = current.get("version", {}).get("number", 1)
        return self.update_page(
            page_id, title, body, current_version + 1,
            body_format=body_format, version_message=version_message,
        )

    def delete_page(self, page_id: str) -> None:
        if not self._is_cloud:
            self.http.delete(f"{self._v1}/content/{page_id}")
        else:
            self.http.delete(f"{self._v2}/pages/{page_id}")

    def move_page(
        self,
        page_id: str,
        target_parent_id: str,
        position: str = "append",
    ) -> Dict[str, Any]:
        return self.http.put(
            f"{self._v1}/content/{page_id}/move/{position}/{target_parent_id}",
        )

    def get_page_children(
        self,
        page_id: str,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        if not self._is_cloud:
            return list(
                self.http.paginate(
                    f"{self._v1}/content/{page_id}/child/page",
                    results_key="results",
                    start_key="start",
                    max_key="limit",
                    total_key="size",
                    page_size=25,
                    max_results=max_results,
                )
            )
        return list(
            self.http.paginate_cursor(
                f"{self._v2}/pages/{page_id}/children",
                max_results=max_results,
            )
        )

    # -- Comments --

    def get_page_comments(self, page_id: str) -> List[Dict[str, Any]]:
        if not self._is_cloud:
            return list(
                self.http.paginate(
                    f"{self._v1}/content/{page_id}/child/comment",
                    params={"expand": "body.storage,version"},
                    results_key="results",
                    start_key="start",
                    max_key="limit",
                    total_key="size",
                    page_size=25,
                )
            )
        return list(
            self.http.paginate_cursor(
                f"{self._v2}/pages/{page_id}/footer-comments"
            )
        )

    def add_page_comment(
        self, page_id: str, body: str, body_format: str = "storage"
    ) -> Dict[str, Any]:
        if not self._is_cloud:
            return self.http.post(
                f"{self._v1}/content",
                json={
                    "type": "comment",
                    "container": {"id": page_id, "type": "page"},
                    "body": {"storage": {"value": body, "representation": body_format}},
                },
            )
        return self.http.post(
            f"{self._v2}/pages/{page_id}/footer-comments",
            json={
                "body": {
                    "representation": body_format,
                    "value": body,
                },
            },
        )

    def get_comment(self, comment_id: str) -> Dict[str, Any]:
        if not self._is_cloud:
            # v1: comments are content items
            params = {"expand": "body.storage,version"}
            return self.http.get(f"{self._v1}/content/{comment_id}", params=params)
        return self.http.get(f"{self._v2}/footer-comments/{comment_id}")

    # -- Attachments --

    def get_page_attachments(self, page_id: str) -> List[Dict[str, Any]]:
        if not self._is_cloud:
            return list(
                self.http.paginate(
                    f"{self._v1}/content/{page_id}/child/attachment",
                    results_key="results",
                    start_key="start",
                    max_key="limit",
                    total_key="size",
                    page_size=25,
                )
            )
        return list(
            self.http.paginate_cursor(
                f"{self._v2}/pages/{page_id}/attachments"
            )
        )

    def add_page_attachment(
        self, page_id: str, file_path: str
    ) -> Dict[str, Any]:
        with open(file_path, "rb") as f:
            return self.http.post(
                f"{self._v1}/content/{page_id}/child/attachment",
                files={"file": f},
                headers={"X-Atlassian-Token": "nocheck"},
            )

    def get_attachment_content(self, attachment_id: str) -> bytes:
        # v1 attachment download
        resp = self.http.get_raw(
            f"{self._v1}/content/{attachment_id}/download"
        )
        resp.raise_for_status()
        return resp.content

    # -- Spaces --

    def get_spaces(self, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        if not self._is_cloud:
            return list(
                self.http.paginate(
                    f"{self._v1}/space",
                    results_key="results",
                    start_key="start",
                    max_key="limit",
                    total_key="size",
                    page_size=25,
                    max_results=max_results,
                )
            )
        return list(
            self.http.paginate_cursor(
                f"{self._v2}/spaces", max_results=max_results
            )
        )

    def get_space(self, space_id: str) -> Dict[str, Any]:
        if not self._is_cloud:
            return self.http.get(f"{self._v1}/space/{space_id}")
        return self.http.get(f"{self._v2}/spaces/{space_id}")

    def get_space_by_key(self, space_key: str) -> Optional[Dict[str, Any]]:
        """Find space by its key."""
        if not self._is_cloud:
            # v1: just use get_space which takes space key directly
            return self.get_space(space_key)
        params = {"keys": space_key}
        results = list(
            self.http.paginate_cursor(f"{self._v2}/spaces", params=params)
        )
        return results[0] if results else None

    # -- CQL Search --

    def search_cql(
        self,
        cql: str,
        max_results: int = 25,
    ) -> Iterator[Dict[str, Any]]:
        """Search using Confluence Query Language."""
        params = {"cql": cql, "limit": max_results}
        data = self.http.get(f"{self._v1}/content/search", params=params)
        results = data.get("results", [])
        for item in results:
            yield item
