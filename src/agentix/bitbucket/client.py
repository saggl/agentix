"""Bitbucket REST API client."""

from typing import List, Optional

import requests

from agentix.bitbucket.client_methods import BitbucketMethods
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


class BitbucketClient(BitbucketMethods):
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
