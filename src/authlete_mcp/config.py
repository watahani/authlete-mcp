"""Configuration for Authlete MCP Server."""

import logging
import os

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
