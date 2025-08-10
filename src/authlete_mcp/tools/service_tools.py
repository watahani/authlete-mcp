"""Service management tools for Authlete MCP Server."""

import json

from mcp.server.fastmcp import Context

from ..api.client import make_authlete_idp_request, make_authlete_request
from ..config import DEFAULT_API_KEY, DEFAULT_ORGANIZATION_ID, AuthleteConfig


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


async def update_service(service_data: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Update an Authlete service.

    Args:
        service_data: JSON string containing service data to update
        service_api_key: Service API key (if empty, uses the main token)
    """
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"

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
