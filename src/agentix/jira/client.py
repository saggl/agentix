"""Jira REST API client."""

from typing import List, Optional

import requests

from agentix.core.http import BaseHTTPClient
from agentix.jira.client_methods import JiraMethods


def _parse_jira_error(response: requests.Response) -> Optional[str]:
    """Parse Jira error payloads into a concise message."""
    try:
        body = response.json()
    except ValueError:
        return None

    if not isinstance(body, dict):
        return None

    messages: List[str] = []
    if isinstance(body.get("errorMessages"), list):
        messages.extend(str(m) for m in body["errorMessages"] if m)

    if isinstance(body.get("errors"), dict):
        messages.extend(f"{k}: {v}" for k, v in body["errors"].items() if v)

    if messages:
        return "; ".join(messages)

    return None


class JiraClient(JiraMethods):
    """Jira REST API v3 (Cloud) / v2 (Server) client."""

    def __init__(self, base_url: str, email: str, api_token: str, auth_type: str = "basic"):
        self.http = BaseHTTPClient(
            base_url=base_url,
            auth=(email, api_token),
            auth_type=auth_type,
            headers={"Content-Type": "application/json"},
            error_parser=_parse_jira_error,
        )
        # Jira Cloud uses API v3 (ADF text fields), Server/DC uses API v2 (plain text)
        self._is_cloud = auth_type != "bearer"
        self._api = "/rest/api/3" if self._is_cloud else "/rest/api/2"
        self._agile = "/rest/agile/1.0"

