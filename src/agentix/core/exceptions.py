"""Exception hierarchy for agentix."""

from typing import Any, Dict, Optional


class AgentixError(Exception):
    """Base exception for all agentix errors."""

    exit_code = 1

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "error": True,
            "error_type": type(self).__name__,
            "message": str(self),
        }
        if self.status_code is not None:
            d["status_code"] = self.status_code
        if self.details:
            d["details"] = self.details
        return d


class ConfigError(AgentixError):
    """Configuration file missing, malformed, or incomplete."""

    exit_code = 2


class AuthenticationError(AgentixError):
    """Authentication failed (401/403 or missing credentials)."""

    exit_code = 2


class NotFoundError(AgentixError):
    """Resource not found (404)."""

    exit_code = 4


class ValidationError(AgentixError):
    """Invalid input (bad JQL, missing required field)."""

    exit_code = 3


class RateLimitError(AgentixError):
    """Rate limit exceeded (429)."""

    exit_code = 5


class ServerError(AgentixError):
    """Remote server error (5xx)."""

    exit_code = 1


class NetworkError(AgentixError):
    """Connection refused, timeout, DNS failure."""

    exit_code = 1
