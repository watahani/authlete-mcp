"""Base data models for Authlete services."""

from pydantic import BaseModel, Field


class Scope(BaseModel):
    """Scope definition."""

    name: str = Field(..., description="Scope name")
    defaultEntry: bool = Field(False, description="Whether this scope is default")
    description: str | None = Field(None, description="Scope description")


class ServiceDetail(BaseModel):
    """Detailed service configuration based on Authlete Service schema."""

    serviceName: str = Field(..., description="The name of this service")
    description: str | None = Field(None, description="The description about the service")
    issuer: str | None = Field(
        None, description="The issuer identifier of the service. A URL that starts with https://"
    )

    # Supported features
    supportedScopes: list[Scope] | None = Field(None, description="Scopes supported by the service")
    supportedResponseTypes: list[str] | None = Field(
        None, description="Response types supported (e.g., CODE, ID_TOKEN)"
    )
    supportedGrantTypes: list[str] | None = Field(
        None, description="Grant types supported (e.g., AUTHORIZATION_CODE, CLIENT_CREDENTIALS)"
    )
    supportedTokenAuthMethods: list[str] | None = Field(None, description="Token endpoint authentication methods")

    # Endpoints
    authorizationEndpoint: str | None = Field(None, description="Authorization endpoint URL")
    tokenEndpoint: str | None = Field(None, description="Token endpoint URL")
    userInfoEndpoint: str | None = Field(None, description="UserInfo endpoint URL")
    revocationEndpoint: str | None = Field(None, description="Token revocation endpoint URL")
    jwksUri: str | None = Field(None, description="JWK Set endpoint URL")

    # Security settings
    pkceRequired: bool | None = Field(None, description="Whether PKCE is required")
    pkceS256Required: bool | None = Field(None, description="Whether S256 is required for PKCE")

    # Token settings
    accessTokenDuration: int | None = Field(None, description="Access token duration in seconds")
    refreshTokenDuration: int | None = Field(None, description="Refresh token duration in seconds")
    idTokenDuration: int | None = Field(None, description="ID token duration in seconds")

    # Advanced settings
    jwks: str | None = Field(None, description="JWK Set document content")
    directAuthorizationEndpointEnabled: bool | None = Field(None, description="Enable direct authorization endpoint")
    directTokenEndpointEnabled: bool | None = Field(None, description="Enable direct token endpoint")
    directUserInfoEndpointEnabled: bool | None = Field(None, description="Enable direct userinfo endpoint")


class ClientCreateRequest(BaseModel):
    """Request model for creating a client."""

    name: str = Field(..., description="Client name")
    description: str | None = Field(None, description="Client description")
    client_type: str | None = Field(None, description="Client type")
    redirect_uris: list[str] | None = Field(None, description="Redirect URIs")
