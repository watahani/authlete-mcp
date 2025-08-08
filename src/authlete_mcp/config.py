"""Configuration management for Authlete MCP Server."""

import os

from pydantic import BaseModel, Field


class AuthleteConfig(BaseModel):
    """Configuration for Authlete API."""

    api_key: str = Field(..., description="Organization access token")
    base_url: str = Field(default="https://jp.authlete.com", description="Authlete base URL")
    idp_url: str = Field(default="https://login.authlete.com", description="Authlete IdP URL")
    api_server_id: str = Field(default="53285", description="API Server ID")


def get_config() -> AuthleteConfig:
    """Get configuration from environment variables."""
    return AuthleteConfig(
        api_key=os.getenv("ORGANIZATION_ACCESS_TOKEN", ""),
        base_url=os.getenv("AUTHLETE_BASE_URL", "https://jp.authlete.com"),
        idp_url=os.getenv("AUTHLETE_IDP_URL", "https://login.authlete.com"),
        api_server_id=os.getenv("AUTHLETE_API_SERVER_ID", "53285"),
    )


# Global configuration constants
DEFAULT_API_KEY = os.getenv("ORGANIZATION_ACCESS_TOKEN", "")
DEFAULT_ORGANIZATION_ID = os.getenv("ORGANIZATION_ID", "")
AUTHLETE_BASE_URL = os.getenv("AUTHLETE_BASE_URL", "https://jp.authlete.com")
AUTHLETE_IDP_URL = os.getenv("AUTHLETE_IDP_URL", "https://login.authlete.com")
DEFAULT_API_SERVER_ID = os.getenv("AUTHLETE_API_SERVER_ID", "53285")
