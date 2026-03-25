"""Confluence REST API client."""

from typing import Optional

import requests

from agentix.confluence.client_methods import ConfluenceMethods
from agentix.core.http import BaseHTTPClient


def _parse_confluence_error(response: requests.Response) -> Optional[str]:
    """Parse Confluence error payloads into a concise message."""
    try:
        body = response.json()
    except ValueError:
        return None

    if not isinstance(body, dict):
        return None

    if isinstance(body.get("message"), str) and body["message"].strip():
        return body["message"]

    if isinstance(body.get("data"), dict):
        data = body["data"]
        if isinstance(data.get("authorized"), bool) and data.get("authorized") is False:
            return "Not authorized"

    return None


class ConfluenceClient(ConfluenceMethods):
    """Confluence REST API client (Cloud v2 + legacy v1)."""

    def __init__(self, base_url: str, email: str, api_token: str, auth_type: str = "basic"):
        self.http = BaseHTTPClient(
            base_url=base_url,
            auth=(email, api_token),
            auth_type=auth_type,
            headers={"Content-Type": "application/json"},
            error_parser=_parse_confluence_error,
        )
        self.auth_type = auth_type
        # Confluence Cloud uses v2 API, Server/DC uses v1 API
        self._is_cloud = auth_type != "bearer"
        self._v2 = "/api/v2"
        self._v1 = "/rest/api"

