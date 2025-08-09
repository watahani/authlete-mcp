"""Client-related models for Authlete API."""

from pydantic import BaseModel, Field


class ClientCreateRequest(BaseModel):
    """Request model for creating a client."""

    name: str = Field(..., description="Client name")
    description: str | None = Field(None, description="Client description")
    client_type: str | None = Field(None, description="Client type")
    redirect_uris: list[str] | None = Field(None, description="Redirect URIs")
