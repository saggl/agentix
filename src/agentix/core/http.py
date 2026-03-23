"""HTTP client wrapper for agentix."""

import logging
import random
import time
from typing import Any, Callable, Dict, Iterator, Optional, Tuple, Union

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
        auth_type: str = "basic",
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        max_retries: int = 2,
        retry_backoff_base: float = 0.25,
        retry_backoff_max: float = 2.0,
        error_parser: Optional[Callable[[requests.Response], Optional[str]]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self.retry_backoff_base = max(0.0, retry_backoff_base)
        self.retry_backoff_max = max(0.0, retry_backoff_max)
        self.error_parser = error_parser
        self.session = requests.Session()

        if auth:
            if auth_type == "bearer":
                # For bearer auth, auth tuple is (unused, token)
                # Set the Authorization header directly
                self.session.headers["Authorization"] = f"Bearer {auth[1]}"
            else:
                # Default to Basic auth
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

    def _default_error_message(self, response: requests.Response) -> str:
        """Extract a useful error message from common JSON error payloads."""
        try:
            body = response.json()
        except ValueError:
            return response.text

        if isinstance(body, dict):
            # Jira-style: {"errorMessages": [...], "errors": {...}}
            if "errorMessages" in body and isinstance(body["errorMessages"], list):
                messages = [str(m) for m in body["errorMessages"] if m]
                if messages:
                    return "; ".join(messages)

            if "errors" in body and isinstance(body["errors"], dict):
                messages = [f"{k}: {v}" for k, v in body["errors"].items() if v]
                if messages:
                    return "; ".join(messages)

            # Bitbucket/Jenkins/Confluence common variants
            for key in ("message", "error", "detail"):
                value = body.get(key)
                if isinstance(value, str) and value.strip():
                    return value

        if isinstance(body, list):
            messages = [str(item) for item in body if item]
            if messages:
                return "; ".join(messages)

        return response.text

    def _parse_error_message(self, response: requests.Response) -> str:
        """Parse an API error message using service-specific parser if configured."""
        if self.error_parser is not None:
            try:
                parsed = self.error_parser(response)
                if parsed:
                    return parsed
            except (AttributeError, KeyError, TypeError, ValueError) as e:
                logger.debug("Custom error parser failed: %s", e)

        msg = self._default_error_message(response)
        return msg or response.text

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
            msg = self._parse_error_message(response)
            raise AgentixError(
                f"HTTP {response.status_code}: {msg}",
                status_code=response.status_code,
            )

        if not response.content:
            return None

        # Try to parse as JSON first (regardless of Content-Type header)
        # This handles cases where APIs return JSON without proper headers
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return response.json()

        # If Content-Type isn't set, try parsing as JSON anyway
        try:
            return response.json()
        except ValueError:
            # If JSON parsing fails, return as text
            return response.text

    def _is_retryable_method(self, method: str) -> bool:
        return method.upper() in {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}

    def _should_retry_status(self, status_code: int) -> bool:
        return status_code == 429 or status_code >= 500

    def _sleep_for_retry(self, attempt: int) -> None:
        if self.retry_backoff_base <= 0:
            return
        # Exponential backoff with a small jitter to avoid synchronized retries.
        delay = min(
            self.retry_backoff_max,
            self.retry_backoff_base * (2 ** max(0, attempt - 1)),
        )
        jitter = delay * random.uniform(0.0, 0.2)
        time.sleep(delay + jitter)

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        kwargs.setdefault("timeout", self.timeout)
        url = self._url(path)
        retryable = self._is_retryable_method(method)

        for attempt in range(1, self.max_retries + 2):
            try:
                response = self.session.request(method, url, **kwargs)
            except requests.ConnectionError as e:
                if retryable and attempt <= self.max_retries:
                    logger.debug(
                        "Retrying %s %s after connection error (attempt %d/%d)",
                        method,
                        url,
                        attempt,
                        self.max_retries + 1,
                    )
                    self._sleep_for_retry(attempt)
                    continue
                raise NetworkError(f"Connection failed: {e}") from e
            except requests.Timeout as e:
                if retryable and attempt <= self.max_retries:
                    logger.debug(
                        "Retrying %s %s after timeout (attempt %d/%d)",
                        method,
                        url,
                        attempt,
                        self.max_retries + 1,
                    )
                    self._sleep_for_retry(attempt)
                    continue
                raise NetworkError(f"Request timed out: {e}") from e
            except requests.RequestException as e:
                raise NetworkError(f"Request failed: {e}") from e

            if retryable and self._should_retry_status(response.status_code) and attempt <= self.max_retries:
                logger.debug(
                    "Retrying %s %s after HTTP %d (attempt %d/%d)",
                    method,
                    url,
                    response.status_code,
                    attempt,
                    self.max_retries + 1,
                )
                self._sleep_for_retry(attempt)
                continue

            return self._handle_response(response)

        # Should be unreachable due to returns/raises above.
        raise NetworkError("Request failed after retries")

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
