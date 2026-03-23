"""Jenkins REST API client."""

from typing import Any, Dict, Optional
from urllib.parse import quote as urlquote

import requests

from agentix.core.http import BaseHTTPClient
from agentix.jenkins.client_methods import JenkinsMethods


def _parse_jenkins_error(response: requests.Response) -> Optional[str]:
    """Parse Jenkins error payloads into a concise message."""
    # Jenkins often returns plain text/HTML; rely on generic parser fallback.
    try:
        body = response.json()
    except ValueError:
        return None

    if isinstance(body, dict):
        if isinstance(body.get("message"), str) and body["message"].strip():
            return body["message"]
        if isinstance(body.get("error"), str) and body["error"].strip():
            return body["error"]

    return None


class JenkinsClient(JenkinsMethods):
    """Jenkins REST API client."""

    def __init__(self, base_url: str, username: str, api_token: str, auth_type: str = "basic"):
        self.http = BaseHTTPClient(
            base_url=base_url,
            auth=(username, api_token),
            auth_type=auth_type,
            error_parser=_parse_jenkins_error,
        )
        self._crumb: Optional[Dict[str, str]] = None

    def _job_path(self, job_name: str) -> str:
        """Convert job name (possibly with folders) to Jenkins API path."""
        parts = job_name.strip("/").split("/")
        return "/".join(f"job/{urlquote(p, safe='')}" for p in parts)

    def _get_crumb(self) -> Dict[str, str]:
        """Fetch CSRF crumb token (cached per client instance)."""
        if self._crumb is None:
            try:
                data = self.http.get("/crumbIssuer/api/json")
                self._crumb = {
                    data["crumbRequestField"]: data["crumb"]
                }
            except Exception:
                self._crumb = {}
        return self._crumb

    def _post_with_crumb(self, path: str, **kwargs: Any) -> Any:
        """POST with CSRF crumb header."""
        crumb = self._get_crumb()
        headers = kwargs.pop("headers", {})
        headers.update(crumb)
        return self.http.post(path, headers=headers, **kwargs)

