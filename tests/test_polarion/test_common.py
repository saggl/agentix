"""Tests for Polarion command common helpers."""

import requests

from agentix.core.exceptions import (
    AuthenticationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from agentix.polarion.commands._common import _call


def test_call_maps_connection_errors_to_network_error():
    def _boom():
        raise requests.exceptions.ConnectionError("connection refused")

    try:
        _call("project list", _boom)
        assert False, "expected NetworkError"
    except NetworkError as exc:
        assert "project list" in str(exc)


def test_call_maps_not_found_messages():
    def _boom():
        raise RuntimeError("404 not found")

    try:
        _call("workitem get", _boom)
        assert False, "expected NotFoundError"
    except NotFoundError:
        pass


def test_call_maps_auth_messages():
    def _boom():
        raise RuntimeError("401 unauthorized")

    try:
        _call("health check", _boom)
        assert False, "expected AuthenticationError"
    except AuthenticationError:
        pass


def test_call_maps_validation_messages():
    def _boom():
        raise RuntimeError("400 invalid query")

    try:
        _call("workitem search", _boom)
        assert False, "expected ValidationError"
    except ValidationError:
        pass


def test_call_maps_rate_limit_messages():
    def _boom():
        raise RuntimeError("429 too many requests")

    try:
        _call("workitem search", _boom)
        assert False, "expected RateLimitError"
    except RateLimitError:
        pass


def test_call_maps_server_error_messages():
    def _boom():
        raise RuntimeError("503 service unavailable")

    try:
        _call("health check", _boom)
        assert False, "expected ServerError"
    except ServerError:
        pass
