"""Polarion client wrapper for agentix."""

from polarion.v3.client import PolarionClient

from agentix.core.auth import ServiceAuth


def create_polarion_client(auth: ServiceAuth, verify_ssl: bool = False) -> PolarionClient:
    """Create a PolarionClient from resolved auth credentials."""
    return PolarionClient(
        url=auth.base_url,
        username=auth.user,
        token=auth.token,
        verify_ssl=verify_ssl,
    )
