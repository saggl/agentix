"""HTTP client wrapper for agentix."""

import logging
from typing import Any, Dict, Iterator, Optional, Tuple, Union

import requests
from requests.auth import HTTPBasicAuth

from agentix import __version__

from .exceptions import (
    AgentixError,
    AuthenticationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

logger = logging.getLogger(__name__)


class BaseHTTPClient:
    """Wraps requests.Session with auth, base_url, retry, and JSON parsing."""

    def __init__(
        self,
        base_url: str,
        auth: Optional[Tuple[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        if auth:
            self.session.auth = HTTPBasicAuth(auth[0], auth[1])

        self.session.headers.update(
            {
                "User-Agent": f"agentix/{__version__}",
                "Accept": "application/json",
            }
        )
        if headers:
            self.session.headers.update(headers)

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def _handle_response(self, response: requests.Response) -> Any:
        logger.debug(
            "%s %s -> %s (%dms)",
            response.request.method,
            response.request.url,
            response.status_code,
            int(response.elapsed.total_seconds() * 1000),
        )

        if response.status_code == 204:
            return None

        if response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed. Check your credentials.",
                status_code=401,
            )
        if response.status_code == 403:
            raise AuthenticationError(
                "Permission denied.",
                status_code=403,
            )
        if response.status_code == 404:
            raise NotFoundError(
                f"Resource not found: {response.url}",
                status_code=404,
            )
        if response.status_code == 429:
            raise RateLimitError(
                "Rate limit exceeded. Try again later.",
                status_code=429,
            )
        if response.status_code >= 500:
            raise ServerError(
                f"Server error: {response.status_code}",
                status_code=response.status_code,
                details={"body": response.text[:500]},
            )
        if not response.ok:
            try:
                body = response.json()
                msg = body.get("errorMessages", [response.text])
                if isinstance(msg, list):
                    msg = "; ".join(msg) if msg else response.text
            except ValueError:
                msg = response.text
            raise AgentixError(
                f"HTTP {response.status_code}: {msg}",
                status_code=response.status_code,
            )

        if not response.content:
            return None

        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        kwargs.setdefault("timeout", self.timeout)
        url = self._url(path)
        try:
            response = self.session.request(method, url, **kwargs)
        except requests.ConnectionError as e:
            raise NetworkError(f"Connection failed: {e}") from e
        except requests.Timeout as e:
            raise NetworkError(f"Request timed out: {e}") from e
        except requests.RequestException as e:
            raise NetworkError(f"Request failed: {e}") from e
        return self._handle_response(response)

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        return self._request("GET", path, params=params)

    def post(
        self,
        path: str,
        json: Optional[Union[Dict, list]] = None,
        data: Any = None,
        files: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        return self._request(
            "POST", path, json=json, data=data, files=files, headers=headers
        )

    def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> Any:
        return self._request("PUT", path, json=json)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)

    def get_raw(self, path: str, **kwargs: Any) -> requests.Response:
        """Get raw response without JSON parsing."""
        kwargs.setdefault("timeout", self.timeout)
        url = self._url(path)
        try:
            return self.session.get(url, **kwargs)
        except requests.RequestException as e:
            raise NetworkError(f"Request failed: {e}") from e

    def paginate(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        results_key: str = "values",
        start_key: str = "startAt",
        max_key: str = "maxResults",
        total_key: str = "total",
        page_size: int = 50,
        max_results: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Offset-based pagination (Jira-style)."""
        params = dict(params or {})
        params[max_key] = page_size
        start = params.get(start_key, 0)
        yielded = 0

        while True:
            params[start_key] = start
            data = self.get(path, params=params)

            items = data.get(results_key, [])
            for item in items:
                if max_results and yielded >= max_results:
                    return
                yield item
                yielded += 1

            total = data.get(total_key)
            start += len(items)

            if not items:
                break
            if total is not None and start >= total:
                break

    def paginate_cursor(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        results_key: str = "results",
        max_results: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Cursor-based pagination (Confluence v2 style)."""
        params = dict(params or {})
        yielded = 0

        while True:
            data = self.get(path, params=params)

            items = data.get(results_key, [])
            for item in items:
                if max_results and yielded >= max_results:
                    return
                yield item
                yielded += 1

            links = data.get("_links", {})
            next_url = links.get("next")
            if not next_url or not items:
                break
            # Next URL is usually absolute — use it directly
            path = next_url
            params = {}
