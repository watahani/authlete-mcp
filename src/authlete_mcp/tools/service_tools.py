"""Service management tools for Authlete MCP Server."""

import json

from mcp.server.fastmcp import Context

from ..api.client import make_authlete_idp_request, make_authlete_request
from ..config import DEFAULT_ORGANIZATION_ID, ORGANIZATION_ACCESS_TOKEN, AuthleteConfig


async def create_service(name: str, description: str = "", ctx: Context = None) -> str:
    """Create a new Authlete service via IdP with basic configuration.

    Args:
        name: Service name
        description: Service description
    """
    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    if not DEFAULT_ORGANIZATION_ID:
        return "Error: ORGANIZATION_ID environment variable must be set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)

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

    data = {
        "apiServerId": int(config.api_server_id),
        "organizationId": int(DEFAULT_ORGANIZATION_ID),
        "service": service_data,
    }

    try:
        result = await make_authlete_idp_request("POST", "service", config, data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error creating service: {str(e)}"


async def create_service_detailed(
    service_config: str,
    ctx: Context = None,
) -> str:
    """Create a new Authlete service via IdP with detailed configuration.

    Args:
        service_config: JSON string containing service configuration following Authlete API service schema
    """
    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    if not DEFAULT_ORGANIZATION_ID:
        return "Error: ORGANIZATION_ID environment variable must be set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)

    try:
        # Parse service configuration JSON
        service_dict = json.loads(service_config)
    except json.JSONDecodeError as e:
        return f"Error parsing service configuration JSON: {str(e)}"

    try:
        # Create the IdP API request payload
        data = {
            "apiServerId": int(config.api_server_id),
            "organizationId": int(DEFAULT_ORGANIZATION_ID),
            "service": service_dict,
        }

        # Send request to Authlete IdP API
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
    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)
    key_to_use = service_api_key if service_api_key else ORGANIZATION_ACCESS_TOKEN

    try:
        result = await make_authlete_request("GET", f"{key_to_use}/service/get/", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting service: {str(e)}"


async def list_services(ctx: Context = None) -> str:
    """List all Authlete services."""
    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)

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

    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)
    key_to_use = service_api_key if service_api_key else ORGANIZATION_ACCESS_TOKEN

    try:
        data = json.loads(service_data)
        result = await make_authlete_request("POST", f"{key_to_use}/service/update", config, data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        return f"Error parsing service data JSON: {str(e)}"
    except Exception as e:
        return f"Error updating service: {str(e)}"


async def delete_service(service_id: str, ctx: Context = None) -> str:
    """Delete an Authlete service via IdP.

    Args:
        service_id: Service ID (apiKey) to delete
    """
    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    if not DEFAULT_ORGANIZATION_ID:
        return "Error: ORGANIZATION_ID environment variable must be set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)

    # Try with environment variable values first
    data = {
        "serviceId": int(service_id),
        "apiServerId": int(config.api_server_id),
        "organizationId": int(DEFAULT_ORGANIZATION_ID),
    }

    try:
        result = await make_authlete_idp_request("POST", "service/remove", config, data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error deleting service: {str(e)}"
