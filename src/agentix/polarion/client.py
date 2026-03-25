"""Polarion client wrapper for agentix."""

import urllib3

from polarion.v3.client import PolarionClient

from agentix.core.auth import ServiceAuth


def create_polarion_client(auth: ServiceAuth, verify_ssl: bool = False) -> PolarionClient:
    """Create a PolarionClient from resolved auth credentials."""
    if not verify_ssl:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return PolarionClient(
        url=auth.base_url,
        username=auth.user,
        token=auth.token,
        verify_ssl=verify_ssl,
    )
