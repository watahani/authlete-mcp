"""Configuration for Authlete MCP Server."""

import os

from pydantic import BaseModel, Field

# Configuration constants
AUTHLETE_BASE_URL = os.getenv("AUTHLETE_BASE_URL", "https://jp.authlete.com")
AUTHLETE_IDP_URL = os.getenv("AUTHLETE_IDP_URL", "https://login.authlete.com")
DEFAULT_API_SERVER_ID = os.getenv("AUTHLETE_API_SERVER_ID", "53285")
DEFAULT_API_KEY = os.getenv("ORGANIZATION_ACCESS_TOKEN", "")
DEFAULT_ORGANIZATION_ID = os.getenv("ORGANIZATION_ID", "")


class AuthleteConfig(BaseModel):
    """Configuration for Authlete API."""

    api_key: str = Field(..., description="Organization access token")
    base_url: str = Field(default=AUTHLETE_BASE_URL, description="Authlete base URL")
    idp_url: str = Field(default=AUTHLETE_IDP_URL, description="Authlete IdP URL")
    api_server_id: str = Field(default=DEFAULT_API_SERVER_ID, description="API Server ID")
