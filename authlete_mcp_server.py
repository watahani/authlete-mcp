"""Authlete MCP Server

A Model Context Protocol server that provides tools for managing Authlete services and clients.
"""

import json
import os
from typing import Any

import httpx
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("Authlete Management Server")

# Configuration
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


async def make_authlete_request(
    method: str, endpoint: str, config: AuthleteConfig, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Make a request to the Authlete API."""

    url = f"{config.base_url}/api/{endpoint}"
    headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        if method.upper() == "GET":
            response = await client.get(url, headers=headers)
        elif method.upper() == "POST":
            response = await client.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = await client.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    if response.status_code >= 400:
        error_detail = response.text
        try:
            error_json = response.json()
            if "resultMessage" in error_json:
                error_detail = f"Authlete API Error: {error_json['resultMessage']}"
        except json.JSONDecodeError:
            pass
        raise httpx.HTTPStatusError(error_detail, request=response.request, response=response)

    return response.json()


async def make_authlete_idp_request(
    method: str, endpoint: str, config: AuthleteConfig, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Make a request to the Authlete IdP API."""

    url = f"{config.idp_url}/api/{endpoint}"
    headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        if method.upper() == "GET":
            response = await client.get(url, headers=headers)
        elif method.upper() == "POST":
            response = await client.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = await client.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

    if response.status_code >= 400:
        error_detail = response.text
        try:
            error_json = response.json()
            if "resultMessage" in error_json:
                error_detail = f"Authlete IdP API Error: {error_json['resultMessage']}"
        except json.JSONDecodeError:
            pass
        raise httpx.HTTPStatusError(error_detail, request=response.request, response=response)

    # Handle 204 No Content (successful deletion)
    if response.status_code == 204:
        return {"success": True, "message": "Service deleted successfully"}

    # Handle empty response body
    try:
        return response.json()
    except json.JSONDecodeError:
        # If response body is empty but status is success, return success message
        if 200 <= response.status_code < 300:
            return {"success": True, "message": f"Operation completed with status {response.status_code}"}
        return {"error": "Empty response body", "status_code": response.status_code}


# Service Management Tools
@mcp.tool()
async def create_service(name: str, organization_id: str = "", description: str = "", ctx: Context = None) -> str:
    """Create a new Authlete service via IdP with basic configuration.

    Args:
        name: Service name
        organization_id: Organization ID (if empty, uses ORGANIZATION_ID env var)
        description: Service description
    """
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    org_id = organization_id if organization_id else DEFAULT_ORGANIZATION_ID
    if not org_id:
        return "Error: organization_id parameter or ORGANIZATION_ID environment variable must be set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)

    # Create service configuration for IdP API (without number, serviceOwnerNumber, apiKey, cluster)
    service_data = {
        "serviceName": name,
        "description": description,
        "supportedScopes": [
            {"name": "openid", "defaultEntry": False},
            {"name": "profile", "defaultEntry": False},
            {"name": "email", "defaultEntry": False},
        ],
        "supportedResponseTypes": ["CODE"],
        "supportedGrantTypes": ["AUTHORIZATION_CODE"],
        "supportedTokenAuthMethods": ["CLIENT_SECRET_BASIC"],
        "supportedDisplays": ["PAGE"],
        "supportedClaimTypes": ["NORMAL"],
        "supportedClaims": ["sub", "name", "email", "email_verified"],
        "createdAt": 0,
        "modifiedAt": 0,
        "clientsPerDeveloper": 0,
        "directAuthorizationEndpointEnabled": True,
        "directTokenEndpointEnabled": True,
        "directRevocationEndpointEnabled": True,
        "directUserInfoEndpointEnabled": True,
        "directJwksEndpointEnabled": True,
        "directIntrospectionEndpointEnabled": True,
        "singleAccessTokenPerSubject": False,
        "pkceRequired": False,
        "pkceS256Required": False,
        "refreshTokenKept": False,
        "refreshTokenDurationKept": False,
        "refreshTokenDurationReset": False,
        "errorDescriptionOmitted": False,
        "errorUriOmitted": False,
        "clientIdAliasEnabled": False,
        "tlsClientCertificateBoundAccessTokens": False,
        "mutualTlsValidatePkiCertChain": False,
        "dynamicRegistrationSupported": False,
        "accessTokenDuration": 86400,
        "refreshTokenDuration": 864000,
        "idTokenDuration": 86400,
        "authorizationResponseDuration": 600,
        "pushedAuthReqDuration": 0,
        "allowableClockSkew": 0,
        "deviceFlowCodeDuration": 600,
        "deviceFlowPollingInterval": 5,
        "userCodeLength": 0,
        "missingClientIdAllowed": False,
        "parRequired": False,
        "requestObjectRequired": False,
        "traditionalRequestObjectProcessingApplied": False,
        "claimShortcutRestrictive": True,
        "scopeRequired": False,
        "nbfOptional": False,
        "issSuppressed": False,
        "tokenExpirationLinked": False,
        "frontChannelRequestObjectEncryptionRequired": False,
        "requestObjectEncryptionAlgMatchRequired": False,
        "requestObjectEncryptionEncMatchRequired": False,
        "hsmEnabled": False,
        "grantManagementActionRequired": False,
        "unauthorizedOnClientConfigSupported": True,
        "dcrScopeUsedAsRequestable": False,
        "loopbackRedirectionUriVariable": True,
        "requestObjectAudienceChecked": True,
        "accessTokenForExternalAttachmentEmbedded": False,
        "refreshTokenIdempotent": False,
        "federationEnabled": False,
        "federationConfigurationDuration": 0,
        "tokenExchangeByIdentifiableClientsOnly": True,
        "tokenExchangeByConfidentialClientsOnly": True,
        "tokenExchangeByPermittedClientsOnly": True,
        "tokenExchangeEncryptedJwtRejected": True,
        "tokenExchangeUnsignedJwtRejected": True,
        "jwtGrantByIdentifiableClientsOnly": True,
        "jwtGrantEncryptedJwtRejected": True,
        "jwtGrantUnsignedJwtRejected": True,
        "dcrDuplicateSoftwareIdBlocked": False,
        "rsResponseSigned": False,
        "openidDroppedOnRefreshWithoutOfflineAccess": False,
        "verifiableCredentialsEnabled": False,
        "credentialOfferDuration": 0,
        "userPinLength": 0,
        "preAuthorizedGrantAnonymousAccessSupported": False,
        "cnonceDuration": 0,
        "credentialTransactionDuration": 0,
        "credentialDuration": 0,
        "idTokenReissuable": False,
        "dpopNonceRequired": False,
        "dpopNonceDuration": 0,
        "clientAssertionAudRestrictedToIssuer": False,
        "nativeSsoSupported": False,
    }

    data = {"apiServerId": int(config.api_server_id), "organizationId": int(org_id), "service": service_data}

    try:
        print(f"DEBUG: Sending request to IdP API with data: {json.dumps(data, indent=2)}")
        result = await make_authlete_idp_request("POST", "service", config, data)
        return json.dumps(result, indent=2)
    except Exception as e:
        print(f"DEBUG: Exception details: {type(e).__name__}: {str(e)}")
        if hasattr(e, "response"):
            print(f"DEBUG: Response status: {e.response.status_code}")
            print(f"DEBUG: Response text: {e.response.text}")
        return f"Error creating service: {str(e)}"


@mcp.tool()
async def create_service_detailed(
    name: str,
    organization_id: str = "",
    description: str = "",
    issuer: str = None,
    authorization_endpoint: str = None,
    token_endpoint: str = None,
    userinfo_endpoint: str = None,
    revocation_endpoint: str = None,
    jwks_uri: str = None,
    supported_scopes: str = "openid,profile,email",
    supported_response_types: str = "CODE",
    supported_grant_types: str = "AUTHORIZATION_CODE",
    supported_token_auth_methods: str = "CLIENT_SECRET_BASIC",
    pkce_required: bool = False,
    pkce_s256_required: bool = False,
    access_token_duration: int = 86400,
    refresh_token_duration: int = 864000,
    id_token_duration: int = 86400,
    direct_authorization_endpoint_enabled: bool = True,
    direct_token_endpoint_enabled: bool = True,
    direct_userinfo_endpoint_enabled: bool = True,
    jwks: str = None,
    ctx: Context = None,
) -> str:
    """Create a new Authlete service via IdP with detailed configuration.

    Args:
        name: Service name
        organization_id: Organization ID (if empty, uses ORGANIZATION_ID env var)
        description: Service description
        issuer: Issuer identifier URL (https:// format)
        authorization_endpoint: Authorization endpoint URL
        token_endpoint: Token endpoint URL
        userinfo_endpoint: UserInfo endpoint URL
        revocation_endpoint: Token revocation endpoint URL
        jwks_uri: JWK Set endpoint URL
        supported_scopes: Comma-separated list of supported scopes (default: "openid,profile,email")
        supported_response_types: Comma-separated response types (default: "CODE")
        supported_grant_types: Comma-separated grant types (default: "AUTHORIZATION_CODE")
        supported_token_auth_methods: Comma-separated auth methods (default: "CLIENT_SECRET_BASIC")
        pkce_required: Whether PKCE is required
        pkce_s256_required: Whether S256 is required for PKCE
        access_token_duration: Access token duration in seconds (default: 86400)
        refresh_token_duration: Refresh token duration in seconds (default: 864000)
        id_token_duration: ID token duration in seconds (default: 86400)
        direct_authorization_endpoint_enabled: Enable direct authorization endpoint
        direct_token_endpoint_enabled: Enable direct token endpoint
        direct_userinfo_endpoint_enabled: Enable direct userinfo endpoint
        jwks: JWK Set document content (JSON string)
    """
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    org_id = organization_id if organization_id else DEFAULT_ORGANIZATION_ID
    if not org_id:
        return "Error: organization_id parameter or ORGANIZATION_ID environment variable must be set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)

    try:
        # Parse supported scopes
        scope_list = []
        for scope_name in supported_scopes.split(","):
            scope_name = scope_name.strip()
            if scope_name:
                scope_list.append({"name": scope_name, "defaultEntry": scope_name == "openid"})

        # Build service configuration
        service_dict = {
            "serviceName": name,
            "description": description,
            "supportedScopes": scope_list,
            "supportedResponseTypes": [t.strip() for t in supported_response_types.split(",") if t.strip()],
            "supportedGrantTypes": [t.strip() for t in supported_grant_types.split(",") if t.strip()],
            "supportedTokenAuthMethods": [t.strip() for t in supported_token_auth_methods.split(",") if t.strip()],
            "pkceRequired": pkce_required,
            "pkceS256Required": pkce_s256_required,
            "accessTokenDuration": access_token_duration,
            "refreshTokenDuration": refresh_token_duration,
            "idTokenDuration": id_token_duration,
            "directAuthorizationEndpointEnabled": direct_authorization_endpoint_enabled,
            "directTokenEndpointEnabled": direct_token_endpoint_enabled,
            "directUserInfoEndpointEnabled": direct_userinfo_endpoint_enabled,
        }

        # Add optional fields if provided
        if issuer:
            service_dict["issuer"] = issuer
        if authorization_endpoint:
            service_dict["authorizationEndpoint"] = authorization_endpoint
        if token_endpoint:
            service_dict["tokenEndpoint"] = token_endpoint
        if userinfo_endpoint:
            service_dict["userInfoEndpoint"] = userinfo_endpoint
        if revocation_endpoint:
            service_dict["revocationEndpoint"] = revocation_endpoint
        if jwks_uri:
            service_dict["jwksUri"] = jwks_uri
        if jwks:
            service_dict["jwks"] = jwks

        data = {"apiServerId": int(config.api_server_id), "organizationId": int(org_id), "service": service_dict}

        result = await make_authlete_idp_request("POST", "service", config, data)
        return json.dumps(result, indent=2)

    except Exception as e:
        return f"Error creating service: {str(e)}"


@mcp.tool()
async def get_service_schema_example(ctx: Context = None) -> str:
    """Get an example of service configuration schema for create_service_detailed.

    This returns a comprehensive JSON example that can be used as a template
    for the service_config parameter in create_service_detailed.
    """

    example_config = {
        "serviceName": "My OIDC Service",
        "description": "A comprehensive OpenID Connect service",
        "issuer": "https://example.com/auth",
        "supportedScopes": [
            {"name": "openid", "defaultEntry": True, "description": "OpenID Connect authentication"},
            {"name": "profile", "defaultEntry": False, "description": "Access to profile information"},
            {"name": "email", "defaultEntry": False, "description": "Access to email address"},
            {"name": "address", "defaultEntry": False, "description": "Access to address information"},
            {"name": "phone", "defaultEntry": False, "description": "Access to phone number"},
            {"name": "offline_access", "defaultEntry": False, "description": "Access to refresh tokens"},
        ],
        "supportedResponseTypes": ["CODE", "ID_TOKEN", "CODE_ID_TOKEN"],
        "supportedGrantTypes": ["AUTHORIZATION_CODE", "CLIENT_CREDENTIALS", "REFRESH_TOKEN"],
        "supportedTokenAuthMethods": ["CLIENT_SECRET_BASIC", "CLIENT_SECRET_POST", "NONE"],
        "authorizationEndpoint": "https://example.com/auth/authorize",
        "tokenEndpoint": "https://example.com/auth/token",
        "userInfoEndpoint": "https://example.com/auth/userinfo",
        "revocationEndpoint": "https://example.com/auth/revoke",
        "jwksUri": "https://example.com/auth/jwks",
        "pkceRequired": True,
        "pkceS256Required": True,
        "accessTokenDuration": 3600,
        "refreshTokenDuration": 86400,
        "idTokenDuration": 3600,
        "directAuthorizationEndpointEnabled": True,
        "directTokenEndpointEnabled": True,
        "directUserInfoEndpointEnabled": True,
    }

    return json.dumps(example_config, indent=2)


@mcp.tool()
async def get_service(service_api_key: str = "", ctx: Context = None) -> str:
    """Get an Authlete service by API key.

    Args:
        service_api_key: Service API key to retrieve (if empty, uses the main token)
    """
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)
    key_to_use = service_api_key if service_api_key else DEFAULT_API_KEY

    try:
        result = await make_authlete_request("GET", f"{key_to_use}/service/get/", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting service: {str(e)}"


@mcp.tool()
async def list_services(ctx: Context = None) -> str:
    """List all Authlete services."""
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)

    try:
        result = await make_authlete_request("GET", "service/get/list", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing services: {str(e)}"


@mcp.tool()
async def update_service(service_data: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Update an Authlete service.

    Args:
        service_data: JSON string containing service data to update
        service_api_key: Service API key (if empty, uses the main token)
    """
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)
    key_to_use = service_api_key if service_api_key else DEFAULT_API_KEY

    try:
        data = json.loads(service_data)
        result = await make_authlete_request("POST", f"{key_to_use}/service/update", config, data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        return f"Error parsing service data JSON: {str(e)}"
    except Exception as e:
        return f"Error updating service: {str(e)}"


@mcp.tool()
async def delete_service(service_id: str, organization_id: str = "", ctx: Context = None) -> str:
    """Delete an Authlete service via IdP.

    Args:
        service_id: Service ID (apiKey) to delete
        organization_id: Organization ID (if empty, uses ORGANIZATION_ID env var)
    """
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    org_id = organization_id if organization_id else DEFAULT_ORGANIZATION_ID
    if not org_id:
        return "Error: organization_id parameter or ORGANIZATION_ID environment variable must be set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)

    # Try with environment variable values first
    data = {"serviceId": int(service_id), "apiServerId": int(config.api_server_id), "organizationId": int(org_id)}

    try:
        result = await make_authlete_idp_request("POST", "service/remove", config, data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error deleting service: {str(e)}"


# Client Management Tools
@mcp.tool()
async def create_client(client_data: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Create a new Authlete client.

    Args:
        client_data: JSON string containing client data
        service_api_key: Service API key (if empty, uses the main token)
    """
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)
    key_to_use = service_api_key if service_api_key else DEFAULT_API_KEY

    try:
        data = json.loads(client_data)
        result = await make_authlete_request("POST", f"{key_to_use}/client/create", config, data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        return f"Error parsing client data JSON: {str(e)}"
    except Exception as e:
        return f"Error creating client: {str(e)}"


@mcp.tool()
async def get_client(client_id: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Get an Authlete client by ID.

    Args:
        client_id: Client ID to retrieve
        service_api_key: Service API key (if empty, uses the main token)
    """
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)
    key_to_use = service_api_key if service_api_key else DEFAULT_API_KEY

    try:
        result = await make_authlete_request("GET", f"{key_to_use}/client/get/{client_id}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting client: {str(e)}"


@mcp.tool()
async def list_clients(service_api_key: str = "", ctx: Context = None) -> str:
    """List all Authlete clients.

    Args:
        service_api_key: Service API key (if empty, uses the main token)
    """
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)
    key_to_use = service_api_key if service_api_key else DEFAULT_API_KEY

    try:
        result = await make_authlete_request("GET", f"{key_to_use}/client/get/list", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing clients: {str(e)}"


@mcp.tool()
async def update_client(client_id: str, client_data: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Update an Authlete client.

    Args:
        client_id: Client ID to update
        client_data: JSON string containing client data to update
        service_api_key: Service API key (if empty, uses the main token)
    """
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)
    key_to_use = service_api_key if service_api_key else DEFAULT_API_KEY

    try:
        data = json.loads(client_data)
        result = await make_authlete_request("POST", f"{key_to_use}/client/update/{client_id}", config, data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        return f"Error parsing client data JSON: {str(e)}"
    except Exception as e:
        return f"Error updating client: {str(e)}"


@mcp.tool()
async def delete_client(client_id: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Delete an Authlete client.

    Args:
        client_id: Client ID to delete
        service_api_key: Service API key (if empty, uses the main token)
    """
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)
    key_to_use = service_api_key if service_api_key else DEFAULT_API_KEY

    try:
        result = await make_authlete_request("DELETE", f"{key_to_use}/client/delete/{client_id}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error deleting client: {str(e)}"


# Additional Client Management Tools
@mcp.tool()
async def rotate_client_secret(client_id: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Rotate an Authlete client secret.

    Args:
        client_id: Client ID
        service_api_key: Service API key (if empty, uses the main token)
    """
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)
    key_to_use = service_api_key if service_api_key else DEFAULT_API_KEY

    try:
        result = await make_authlete_request("GET", f"{key_to_use}/client/secret/refresh/{client_id}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error rotating client secret: {str(e)}"


@mcp.tool()
async def update_client_secret(client_id: str, secret_data: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Update an Authlete client secret.

    Args:
        client_id: Client ID
        secret_data: JSON string containing new secret data
        service_api_key: Service API key (if empty, uses the main token)
    """
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)
    key_to_use = service_api_key if service_api_key else DEFAULT_API_KEY

    try:
        data = json.loads(secret_data)
        result = await make_authlete_request("POST", f"{key_to_use}/client/secret/update/{client_id}", config, data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        return f"Error parsing secret data JSON: {str(e)}"
    except Exception as e:
        return f"Error updating client secret: {str(e)}"


@mcp.tool()
async def update_client_lock(client_id: str, lock_flag: bool, service_api_key: str = "", ctx: Context = None) -> str:
    """Update an Authlete client lock status.

    Args:
        client_id: Client ID
        lock_flag: True to lock, False to unlock
        service_api_key: Service API key (if empty, uses the main token)
    """
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)
    key_to_use = service_api_key if service_api_key else DEFAULT_API_KEY

    data = {"locked": lock_flag}

    try:
        result = await make_authlete_request("POST", f"{key_to_use}/client/lock_flag/update/{client_id}", config, data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error updating client lock: {str(e)}"


@mcp.tool()
async def generate_jwks(
    kty: str = "rsa",
    size: int = 2048,
    use: str | None = None,
    alg: str | None = None,
    kid: str | None = None,
    gen: str = "specified",
    crv: str | None = None,
    x509: bool = False,
    ctx: Context = None,
) -> str:
    """Generate JSON Web Key Set (JWKS) using mkjwk.org API.

    This tool generates cryptographic keys in JWK/JWKS format for use in OAuth 2.0/OpenID Connect implementations.

    Args:
        kty: Key type - "rsa", "ec", "oct", or "okp" (default: "rsa")
        size: Key size in bits for RSA/oct keys (default: 2048, minimum 512, step 8)
        use: Key use - "sig" (signature) or "enc" (encryption), affects available algorithms
        alg: Algorithm for the key (e.g., "RS256", "ES256", "HS256", "EdDSA")
             - RSA sig: RS256,RS384,RS512,PS256,PS384,PS512
             - RSA enc: RSA1_5,RSA-OAEP,RSA-OAEP-256
             - EC sig: ES256,ES384,ES512,ES256K
             - EC enc: ECDH-ES,ECDH-ES+A128KW,ECDH-ES+A192KW,ECDH-ES+A256KW
             - oct sig: HS256,HS384,HS512
             - oct enc: A128KW,A192KW,A256KW,A128GCMKW,A192GCMKW,A256GCMKW,dir
             - okp sig: EdDSA
             - okp enc: ECDH-ES,ECDH-ES+A128KW,ECDH-ES+A192KW,ECDH-ES+A256KW
        kid: Key ID (optional) - identifier for the key
        gen: Key ID generation method - "specified" (use kid param), "sha256", "sha1", "date", "timestamp" (default: "specified")
        crv: Curve for EC/OKP keys - EC: "P-256","P-384","P-521","secp256k1", OKP: "Ed25519","Ed448","X25519","X448"
        x509: Generate X.509 certificate wrapper for RSA/EC keys (default: False)

    Returns:
        JSON string containing generated keys with jwk, jwks, and pub (public key) fields
    """
    try:
        # Build the request URL
        url = f"https://mkjwk.org/jwk/{kty}"
        params = {}

        # Add parameters if provided
        if alg:
            params["alg"] = alg
        if use:
            params["use"] = use
        if kid and gen == "specified":
            params["kid"] = kid
        if gen != "specified":
            params["gen"] = gen

        # Key type specific parameters
        if kty in ["rsa", "ec"]:
            params["x509"] = str(x509).lower()

        if kty in ["rsa", "oct"]:
            params["size"] = str(size)

        if kty in ["ec", "okp"]:
            if not crv:
                return "Error: curve (crv) parameter is required for EC and OKP key types"
            params["crv"] = crv

        # Make the request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            # Return the JSON response
            result = response.json()
            return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON response - {str(e)}"
    except Exception as e:
        return f"Error generating JWKS: {str(e)}"


if __name__ == "__main__":
    mcp.run()
