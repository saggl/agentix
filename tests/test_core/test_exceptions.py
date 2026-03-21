"""Tests for core exceptions."""

from agentix.core.exceptions import (
    AgentixError,
    AuthenticationError,
    ConfigError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)


def test_base_error_to_dict():
    err = AgentixError("Something went wrong", status_code=400)
    d = err.to_dict()
    assert d["error"] is True
    assert d["error_type"] == "AgentixError"
    assert d["message"] == "Something went wrong"
    assert d["status_code"] == 400


def test_error_with_details():
    err = AgentixError("fail", details={"url": "http://example.com"})
    d = err.to_dict()
    assert d["details"]["url"] == "http://example.com"


def test_error_without_status_code():
    err = AgentixError("no status")
    d = err.to_dict()
    assert "status_code" not in d


def test_exit_codes():
    assert ConfigError("x").exit_code == 2
    assert AuthenticationError("x").exit_code == 2
    assert NotFoundError("x").exit_code == 4
    assert ValidationError("x").exit_code == 3
    assert RateLimitError("x").exit_code == 5
    assert ServerError("x").exit_code == 1


def test_error_inheritance():
    err = NotFoundError("not found", status_code=404)
    assert isinstance(err, AgentixError)
    assert str(err) == "not found"
