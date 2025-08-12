"""Configuration for Authlete MCP Server."""

import os

from pydantic import BaseModel, Field

# Configuration constants
AUTHLETE_API_URL = os.getenv("AUTHLETE_API_URL", "https://jp.authlete.com")
AUTHLETE_IDP_URL = os.getenv("AUTHLETE_IDP_URL", "https://login.authlete.com")
DEFAULT_API_SERVER_ID = os.getenv("AUTHLETE_API_SERVER_ID", "53285")
ORGANIZATION_ACCESS_TOKEN = os.getenv("ORGANIZATION_ACCESS_TOKEN", "")
DEFAULT_ORGANIZATION_ID = os.getenv("ORGANIZATION_ID", "")


class AuthleteConfig(BaseModel):
    """Configuration for Authlete API."""

    api_key: str = Field(..., description="Organization access token")
    base_url: str = Field(default=AUTHLETE_API_URL, description="Authlete API URL")
    idp_url: str = Field(default=AUTHLETE_IDP_URL, description="Authlete IdP URL")
    api_server_id: str = Field(default=DEFAULT_API_SERVER_ID, description="API Server ID")
