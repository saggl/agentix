"""Tests for HTTP client."""

import pytest
import responses

from agentix.core.exceptions import (
    AuthenticationError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
)
from agentix.core.http import BaseHTTPClient


@pytest.fixture
def client():
    return BaseHTTPClient(
        base_url="https://api.example.com",
        auth=("user", "token"),
    )


@responses.activate
def test_get_success(client):
    responses.add(
        responses.GET,
        "https://api.example.com/test",
        json={"result": "ok"},
        status=200,
    )
    data = client.get("/test")
    assert data["result"] == "ok"


@responses.activate
def test_post_json(client):
    responses.add(
        responses.POST,
        "https://api.example.com/create",
        json={"id": 1},
        status=201,
    )
    data = client.post("/create", json={"name": "test"})
    assert data["id"] == 1


@responses.activate
def test_delete_204(client):
    responses.add(
        responses.DELETE,
        "https://api.example.com/item/1",
        status=204,
    )
    result = client.delete("/item/1")
    assert result is None


@responses.activate
def test_401_raises_auth_error(client):
    responses.add(
        responses.GET,
        "https://api.example.com/secret",
        status=401,
    )
    with pytest.raises(AuthenticationError):
        client.get("/secret")


@responses.activate
def test_403_raises_auth_error(client):
    responses.add(
        responses.GET,
        "https://api.example.com/forbidden",
        status=403,
    )
    with pytest.raises(AuthenticationError):
        client.get("/forbidden")


@responses.activate
def test_404_raises_not_found(client):
    responses.add(
        responses.GET,
        "https://api.example.com/missing",
        status=404,
    )
    with pytest.raises(NotFoundError):
        client.get("/missing")


@responses.activate
def test_429_raises_rate_limit(client):
    responses.add(
        responses.GET,
        "https://api.example.com/limited",
        status=429,
    )
    with pytest.raises(RateLimitError):
        client.get("/limited")


@responses.activate
def test_500_raises_server_error(client):
    responses.add(
        responses.GET,
        "https://api.example.com/broken",
        body="Internal Server Error",
        status=500,
    )
    with pytest.raises(ServerError):
        client.get("/broken")


def test_connection_error_raises_network_error(client):
    # No mock = connection refused
    with pytest.raises(NetworkError):
        client.get("/unreachable")


@responses.activate
def test_url_construction(client):
    responses.add(
        responses.GET,
        "https://api.example.com/path/to/resource",
        json={},
        status=200,
    )
    client.get("/path/to/resource")
    assert responses.calls[0].request.url == "https://api.example.com/path/to/resource"


@responses.activate
def test_absolute_url_passthrough(client):
    responses.add(
        responses.GET,
        "https://other.example.com/resource",
        json={},
        status=200,
    )
    client.get("https://other.example.com/resource")
    assert responses.calls[0].request.url == "https://other.example.com/resource"


@responses.activate
def test_paginate(client):
    responses.add(
        responses.GET,
        "https://api.example.com/items",
        json={"values": [{"id": 1}, {"id": 2}], "startAt": 0, "maxResults": 2, "total": 3},
        status=200,
    )
    responses.add(
        responses.GET,
        "https://api.example.com/items",
        json={"values": [{"id": 3}], "startAt": 2, "maxResults": 2, "total": 3},
        status=200,
    )
    items = list(client.paginate("/items", page_size=2))
    assert len(items) == 3
    assert items[2]["id"] == 3


@responses.activate
def test_paginate_max_results(client):
    responses.add(
        responses.GET,
        "https://api.example.com/items",
        json={"values": [{"id": 1}, {"id": 2}, {"id": 3}], "startAt": 0, "maxResults": 3, "total": 10},
        status=200,
    )
    items = list(client.paginate("/items", page_size=3, max_results=2))
    assert len(items) == 2
