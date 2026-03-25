"""Tests for Polarion client wrapper."""

from unittest.mock import MagicMock, patch

from agentix.polarion.client import create_polarion_client


@patch("agentix.polarion.client.PolarionClient")
def test_create_client_with_token(mock_cls):
    auth = MagicMock(
        base_url="https://polarion.example.com/polarion",
        user="testuser",
        token="test-pat",
    )
    create_polarion_client(auth)
    mock_cls.assert_called_once_with(
        url="https://polarion.example.com/polarion",
        username="testuser",
        token="test-pat",
        verify_ssl=False,
    )


@patch("agentix.polarion.client.PolarionClient")
def test_create_client_verify_ssl_passthrough(mock_cls):
    auth = MagicMock(
        base_url="https://polarion.example.com/polarion",
        user="testuser",
        token="test-pat",
    )
    create_polarion_client(auth, verify_ssl=True)
    mock_cls.assert_called_once_with(
        url="https://polarion.example.com/polarion",
        username="testuser",
        token="test-pat",
        verify_ssl=True,
    )
