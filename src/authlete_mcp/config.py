"""Configuration for Authlete MCP Server."""

import logging
import os
from typing import Any

from pydantic import BaseModel, Field

# Configuration constants
AUTHLETE_API_URL = os.getenv("AUTHLETE_API_URL", "https://jp.authlete.com")
AUTHLETE_IDP_URL = os.getenv("AUTHLETE_IDP_URL", "https://login.authlete.com")
DEFAULT_API_SERVER_ID = os.getenv("AUTHLETE_API_SERVER_ID", "53285")
ORGANIZATION_ACCESS_TOKEN = os.getenv("ORGANIZATION_ACCESS_TOKEN", "")
DEFAULT_ORGANIZATION_ID = os.getenv("ORGANIZATION_ID", "")

# Global state for current API server configuration
_current_api_server: dict | None = None

logger = logging.getLogger(__name__)


class AuthleteConfig(BaseModel):
    """Configuration for Authlete API."""

    access_token: str = Field(..., description="Organization access token")
    base_url: str = Field(default=AUTHLETE_API_URL, description="Authlete API URL")
    idp_url: str = Field(default=AUTHLETE_IDP_URL, description="Authlete IdP URL")
    api_server_id: str = Field(default=DEFAULT_API_SERVER_ID, description="API Server ID")


def set_current_api_server(api_server_id: int, api_server_url: str, description: str = "") -> None:
    """Set the current API server configuration for all Authlete API calls."""
    global _current_api_server
    _current_api_server = {"id": api_server_id, "url": api_server_url, "description": description}
    logger.info(f"API server set to: {api_server_url} (ID: {api_server_id})")


def get_current_api_server() -> dict | None:
    """Get the current API server configuration."""
    return _current_api_server


def clear_current_api_server() -> None:
    """Clear the current API server configuration."""
    global _current_api_server
    _current_api_server = None
    logger.info("API server configuration cleared")


async def auto_detect_api_server_from_url() -> dict | None:
    """Auto-detect API server ID from AUTHLETE_API_URL by querying available servers."""
    if not ORGANIZATION_ACCESS_TOKEN:
        return None

    try:
        from .api.client import make_authlete_idp_request

        response = await make_authlete_idp_request(
            endpoint="apiserver",
            method="GET",
            access_token=ORGANIZATION_ACCESS_TOKEN,
        )

        if not response or len(response) == 0:
            return None

        # Find server that matches AUTHLETE_API_URL
        target_url = AUTHLETE_API_URL.rstrip("/")
        for server in response:
            server_url = server["apiServerUrl"].rstrip("/")
            if server_url == target_url:
                return {"id": server["id"], "url": server["apiServerUrl"], "description": server.get("description", "")}

        return None

    except Exception as e:
        logger.error(f"Failed to auto-detect API server: {e}")
        return None


async def ensure_api_server_configured() -> str | None:
    """Ensure API server is configured, auto-detect if possible, or return error message."""
    current_server = get_current_api_server()

    if current_server:
        return None  # Already configured

    # Try to auto-detect from AUTHLETE_API_URL
    detected_server = await auto_detect_api_server_from_url()
    if detected_server:
        set_current_api_server(
            api_server_id=detected_server["id"],
            api_server_url=detected_server["url"],
            description=detected_server.get("description", ""),
        )
        logger.info(f"Auto-detected API server from AUTHLETE_API_URL: {detected_server['url']}")
        return None  # Successfully configured

    # Cannot auto-detect, return error message
    return (
        "No API server is currently configured. "
        "Please use the 'list_api_servers' tool to see available options, "
        "then use 'set_api_server' to configure your preferred API server."
    )


async def configure_api_server_by_id(
    api_server_id: str | int,
) -> tuple[dict[str, Any] | None, str | None]:
    """Configure the current API server using an explicit server ID."""

    if not ORGANIZATION_ACCESS_TOKEN:
        return None, "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    try:
        from .api.client import make_authlete_idp_request

        response = await make_authlete_idp_request(
            endpoint="apiserver",
            method="GET",
            access_token=ORGANIZATION_ACCESS_TOKEN,
        )
    except Exception as exc:
        logger.error(f"Failed to fetch API servers: {exc}")
        return None, f"Error setting API server: {exc}"

    if not response:
        return None, "Error: No API servers found for this organization"

    target_server: dict[str, Any] | None = None
    available_ids: list[str] = []
    for server in response:
        server_id = str(server.get("id"))
        if server_id:
            available_ids.append(server_id)
        if server_id == str(api_server_id):
            target_server = server

    if not target_server:
        available_ids.sort()
        available = ", ".join(available_ids)
        return (
            None,
            f"Error: API server with ID '{api_server_id}' not found. Available API server IDs: {available}",
        )

    set_current_api_server(
        api_server_id=int(target_server["id"]),
        api_server_url=target_server.get("apiServerUrl", ""),
        description=target_server.get("description", ""),
    )

    return target_server, None


async def ensure_api_server_ready(
    explicit_api_server_id: str | int | None = None,
) -> tuple[int | None, str | None]:
    """Ensure an API server ID is available, honoring explicit overrides."""

    if explicit_api_server_id not in (None, ""):
        server_info, error = await configure_api_server_by_id(explicit_api_server_id)
        if error:
            return None, error
        return int(server_info["id"]), None

    error_msg = await ensure_api_server_configured()
    if error_msg:
        if DEFAULT_API_SERVER_ID:
            server_info, error = await configure_api_server_by_id(DEFAULT_API_SERVER_ID)
            if error:
                return None, error
            return int(server_info["id"]), None
        return None, error_msg

    api_server_id = get_api_server_id()
    if api_server_id is None:
        return None, "Unable to determine API server ID"

    return int(api_server_id), None


def get_api_server_url() -> str | None:
    """Get the current API server URL, or None if not configured."""
    current_server = get_current_api_server()
    return current_server["url"] if current_server else None


def get_api_server_id() -> int | None:
    """Get the current API server ID, or None if not configured."""
    current_server = get_current_api_server()
    return current_server["id"] if current_server else None


def check_deprecated_env_vars() -> None:
    """Check for deprecated environment variables and warn users."""
    if os.getenv("AUTHLETE_API_SERVER_ID"):
        logger.warning(
            "AUTHLETE_API_SERVER_ID environment variable is deprecated. "
            "Use the 'list_api_servers' and 'set_api_server' tools instead for dynamic API server selection."
        )
