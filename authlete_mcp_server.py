"""Authlete MCP Server

A Model Context Protocol server that provides tools for managing Authlete services and clients,
along with advanced API search functionality.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

import duckdb
import httpx
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("Authlete Management and API Search Server")

# Configuration
AUTHLETE_BASE_URL = os.getenv("AUTHLETE_BASE_URL", "https://jp.authlete.com")
AUTHLETE_IDP_URL = os.getenv("AUTHLETE_IDP_URL", "https://login.authlete.com")
DEFAULT_API_SERVER_ID = os.getenv("AUTHLETE_API_SERVER_ID", "53285")
DEFAULT_API_KEY = os.getenv("ORGANIZATION_ACCESS_TOKEN", "")
DEFAULT_ORGANIZATION_ID = os.getenv("ORGANIZATION_ID", "")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


class AuthleteApiSearcher:
    """Enhanced API search engine (DuckDB-based)"""

    def __init__(self, db_path: str = "resources/authlete_apis.duckdb"):
        """Initialize the searcher

        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path = Path(db_path)
        self.conn = None

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Search database not found: {db_path}\n"
                f"Please run 'uv run python scripts/create_search_database.py' first"
            )

        logger.info(f"Search database found: {db_path}")

    def _ensure_connection(self):
        """Ensure database connection is established"""
        if self.conn is None:
            self.conn = duckdb.connect(str(self.db_path))
            logger.info(f"Search database connected: {self.db_path}")

    async def search_apis(
        self,
        query: str | None = None,
        path_query: str | None = None,
        description_query: str | None = None,
        tag_filter: str | None = None,
        method_filter: str | None = None,
        mode: str = "natural",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Search APIs

        Args:
            query: Natural language query
            path_query: API path search
            description_query: Description search
            tag_filter: Tag filtering
            method_filter: HTTP method filtering
            mode: Search mode (kept for compatibility, actually uses natural language search)
            limit: Maximum number of results

        Returns:
            List of search results
        """
        if not any([query, path_query, description_query]):
            return []

        try:
            self._ensure_connection()

            # Execute search
            if query and len(query.strip()) > 0:
                results = await self._natural_language_search(query, tag_filter, method_filter, limit)
            elif path_query:
                results = await self._path_search(path_query, method_filter, limit)
            elif description_query:
                results = await self._description_search(description_query, tag_filter, method_filter, limit)
            else:
                results = []

            return results

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []

    async def _natural_language_search(
        self, query: str, tag_filter: str | None, method_filter: str | None, limit: int
    ) -> list[dict[str, Any]]:
        """Natural language search"""

        # Split query into words
        query_words = query.lower().split()

        # Build WHERE conditions
        where_conditions = []
        params = []

        # OR search for each word (natural language matching)
        word_conditions = []
        for word in query_words:
            word_conditions.append("LOWER(search_content) LIKE ?")
            params.append(f"%{word}%")

        if word_conditions:
            where_conditions.append(f"({' OR '.join(word_conditions)})")

        # Filter conditions
        if method_filter:
            where_conditions.append("method = ?")
            params.append(method_filter.upper())

        if tag_filter:
            where_conditions.append("tags LIKE ?")
            params.append(f"%{tag_filter}%")

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Query with relevance score calculation (summary/path priority)
        sql = f"""
        SELECT
            path, method, operation_id, summary, description, tags,
            sample_languages, sample_codes,
            (
                CASE
                    -- Complete phrase match (highest score)
                    WHEN LOWER(search_content) LIKE ? THEN 150
                    -- Summary partial match (very high score)
                    WHEN LOWER(summary) LIKE ? THEN 120
                    -- Path match (high score)
                    WHEN LOWER(path) LIKE ? THEN 100
                    -- Description partial match (medium score)
                    WHEN LOWER(description) LIKE ? THEN 80
                    ELSE 10
                END +
                -- Bonus points from individual word matches (high points for summary/path)
                {self._build_enhanced_word_score_expression(query_words)}
            ) as relevance_score
        FROM api_endpoints
        WHERE {where_clause}
        ORDER BY relevance_score DESC, path ASC
        LIMIT ?
        """

        # Build parameter list
        score_params = [f"%{query.lower()}%"] * 4  # Complete phrase, description, summary, path
        all_params = score_params + params + [limit]

        result = self.conn.execute(sql, all_params).fetchall()

        return self._format_search_results(result)

    def _build_enhanced_word_score_expression(self, words: list[str]) -> str:
        """Build enhanced word matching score expression (summary/path priority)"""
        expressions = []
        for word in words:
            # Escape words to avoid SQL injection
            escaped_word = word.replace("'", "''")
            # Give high scores for summary/path matches
            expressions.append(f"""
                CASE
                    WHEN LOWER(summary) LIKE '%{escaped_word}%' THEN 15
                    WHEN LOWER(path) LIKE '%{escaped_word}%' THEN 12
                    WHEN LOWER(description) LIKE '%{escaped_word}%' THEN 8
                    WHEN LOWER(search_content) LIKE '%{escaped_word}%' THEN 5
                    ELSE 0
                END
            """)
        return " + ".join(expressions) if expressions else "0"

    async def _path_search(self, path_query: str, method_filter: str | None, limit: int) -> list[dict[str, Any]]:
        """Path-specific search"""

        where_conditions = ["LOWER(path) LIKE ?"]
        params = [f"%{path_query.lower()}%"]

        if method_filter:
            where_conditions.append("method = ?")
            params.append(method_filter.upper())

        where_clause = " AND ".join(where_conditions)

        sql = f"""
        SELECT
            path, method, operation_id, summary, description, tags,
            sample_languages, sample_codes,
            CASE
                WHEN path = ? THEN 100
                WHEN LOWER(path) LIKE ? THEN 80
                ELSE 50
            END as relevance_score
        FROM api_endpoints
        WHERE {where_clause}
        ORDER BY relevance_score DESC, path ASC
        LIMIT ?
        """

        score_params = [path_query, f"%{path_query.lower()}%"]
        all_params = score_params + params + [limit]

        result = self.conn.execute(sql, all_params).fetchall()
        return self._format_search_results(result)

    async def _description_search(
        self, desc_query: str, tag_filter: str | None, method_filter: str | None, limit: int
    ) -> list[dict[str, Any]]:
        """Description-specific search"""

        where_conditions = ["(LOWER(summary) LIKE ? OR LOWER(description) LIKE ?)"]
        params = [f"%{desc_query.lower()}%", f"%{desc_query.lower()}%"]

        if method_filter:
            where_conditions.append("method = ?")
            params.append(method_filter.upper())

        if tag_filter:
            where_conditions.append("tags LIKE ?")
            params.append(f"%{tag_filter}%")

        where_clause = " AND ".join(where_conditions)

        sql = f"""
        SELECT
            path, method, operation_id, summary, description, tags,
            sample_languages, sample_codes,
            CASE
                WHEN LOWER(summary) LIKE ? THEN 100
                WHEN LOWER(description) LIKE ? THEN 90
                ELSE 30
            END as relevance_score
        FROM api_endpoints
        WHERE {where_clause}
        ORDER BY relevance_score DESC, path ASC
        LIMIT ?
        """

        score_params = [f"%{desc_query.lower()}%", f"%{desc_query.lower()}%"]
        all_params = score_params + params + [limit]

        result = self.conn.execute(sql, all_params).fetchall()
        return self._format_search_results(result)

    def _format_search_results(self, results: list[tuple]) -> list[dict[str, Any]]:
        """Format search results"""
        formatted = []

        for row in results:
            path, method, operation_id, summary, description, tags, sample_languages, sample_codes, score = row

            # Handle tags and sample_languages (already as lists from DuckDB)
            tags_list = tags if tags else []
            sample_languages_list = sample_languages if sample_languages else []

            # Truncate description to first 100 characters for search results
            truncated_description = (description or "")[:100]
            if len(description or "") > 100:
                truncated_description += "..."

            formatted.append(
                {
                    "path": path,
                    "method": method,
                    "operation_id": operation_id,
                    "summary": summary or "",
                    "description": truncated_description,
                    "tags": tags_list,
                    "sample_languages": sample_languages_list,
                    "score": float(score),
                }
            )

        return formatted

    async def get_api_detail(
        self, path: str = None, method: str = None, operation_id: str = None, language: str | None = None
    ) -> dict[str, Any] | None:
        """Get detailed information for a specific API by path+method or operationId"""

        try:
            self._ensure_connection()

            if operation_id:
                # Search by operationId
                result = self.conn.execute(
                    """
                    SELECT path, method, operation_id, summary, description, tags,
                           parameters, request_body, responses, sample_codes
                    FROM api_endpoints
                    WHERE operation_id = ?
                """,
                    [operation_id],
                ).fetchone()
            elif path and method:
                # Search by path and method
                result = self.conn.execute(
                    """
                    SELECT path, method, operation_id, summary, description, tags,
                           parameters, request_body, responses, sample_codes
                    FROM api_endpoints
                    WHERE path = ? AND method = ?
                """,
                    [path, method.upper()],
                ).fetchone()
            else:
                return None

            if not result:
                return None

            (
                api_path,
                api_method,
                operation_id,
                summary,
                description,
                tags,
                parameters,
                request_body,
                responses,
                sample_codes,
            ) = result

            # Parse JSON data (tags are already lists from DuckDB)
            tags_list = tags if tags else []
            try:
                parameters_list = json.loads(parameters) if parameters else []
                request_body_obj = json.loads(request_body) if request_body else None
                responses_obj = json.loads(responses) if responses else {}
                sample_codes_dict = json.loads(sample_codes) if sample_codes else {}
            except json.JSONDecodeError:
                parameters_list = []
                request_body_obj = None
                responses_obj = {}
                sample_codes_dict = {}

            # Get sample code
            sample_code = sample_codes_dict.get(language) if language else None

            return {
                "path": api_path,
                "method": api_method,
                "operation_id": operation_id,
                "summary": summary or "",
                "description": description or "",
                "tags": tags_list,
                "parameters": parameters_list,
                "request_body": request_body_obj,
                "responses": responses_obj,
                "sample_code": sample_code,
            }

        except Exception as e:
            logger.error(f"API detail retrieval error: {str(e)}")
            return None


# Initialize global searcher
_searcher = None


def get_searcher() -> AuthleteApiSearcher:
    """Get or create the global searcher instance"""
    global _searcher
    if _searcher is None:
        try:
            _searcher = AuthleteApiSearcher()
        except FileNotFoundError as e:
            logger.warning(f"Search functionality not available: {e}")
            raise
    return _searcher


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
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"
        
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
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"
        
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
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"
        
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
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"
        
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
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"
        
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
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"
        
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
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"
        
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
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"
        
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


# API Search Tools
@mcp.tool()
async def search_apis(
    query: str = None,
    path_query: str = None,
    description_query: str = None,
    tag_filter: str = None,
    method_filter: str = None,
    mode: str = "natural",
    limit: int = 20,
    ctx: Context = None,
) -> str:
    """Natural language API search. Semantic matching like 'revoke token' → 'This API revokes access tokens'. Returns description truncated to ~100 chars. Use get_api_detail for full information.

    Args:
        query: Natural language search query (e.g., 'revoke token', 'create client', 'user authentication')
        path_query: API path search (e.g., '/api/auth/token')
        description_query: Description search (e.g., 'revokes access tokens')
        tag_filter: Tag filter (e.g., 'Token Operations', 'Authorization')
        method_filter: HTTP method filter (GET, POST, PUT, DELETE)
        mode: Search mode (for compatibility, actually uses natural language search)
        limit: Maximum number of results (default: 20, max: 100)
    """

    try:
        searcher = get_searcher()

        # Validate limit
        if limit < 1 or limit > 100:
            limit = 20

        results = await searcher.search_apis(
            query=query,
            path_query=path_query,
            description_query=description_query,
            tag_filter=tag_filter,
            method_filter=method_filter,
            mode=mode,
            limit=limit,
        )

        if not results:
            return "No APIs found matching the search criteria."

        return json.dumps(results, ensure_ascii=False, indent=2)

    except FileNotFoundError as e:
        return (
            f"Search database not found: {str(e)}\nPlease run 'uv run python scripts/create_search_database.py' first"
        )
    except Exception as e:
        return f"Search error: {str(e)}"


@mcp.tool()
async def get_api_detail(
    path: str = None,
    method: str = None,
    operation_id: str = None,
    language: str = None,
    ctx: Context = None,
) -> str:
    """Get detailed information for specific API (parameters, request/response, sample code). Provide either operation_id OR both path and method.

    Args:
        path: API path (required if operation_id not provided)
        method: HTTP method (required if operation_id not provided)
        operation_id: Operation ID (alternative to path+method)
        language: Sample code language (curl, javascript, python, java, etc.)
    """

    try:
        searcher = get_searcher()

        if not operation_id and (not path or not method):
            return "Either 'operation_id' or both 'path' and 'method' parameters are required."

        detail = await searcher.get_api_detail(path, method, operation_id, language)

        if not detail:
            identifier = operation_id or f"{method} {path}"
            return f"API details not found: {identifier}"

        return json.dumps(detail, ensure_ascii=False, indent=2)

    except FileNotFoundError as e:
        return (
            f"Search database not found: {str(e)}\nPlease run 'uv run python scripts/create_search_database.py' first"
        )
    except Exception as e:
        return f"Detail retrieval error: {str(e)}"


@mcp.tool()
async def get_sample_code(
    language: str,
    path: str = None,
    method: str = None,
    operation_id: str = None,
    ctx: Context = None,
) -> str:
    """Get sample code for specific API in specified language. Provide language and either operation_id OR both path and method.

    Args:
        language: Programming language (curl, javascript, python, java, etc.)
        path: API path (required if operation_id not provided)
        method: HTTP method (required if operation_id not provided)
        operation_id: Operation ID (alternative to path+method)
    """

    try:
        searcher = get_searcher()

        if not language:
            return "language parameter is required."

        if not operation_id and (not path or not method):
            return "Either 'operation_id' or both 'path' and 'method' parameters are required."

        detail = await searcher.get_api_detail(path, method, operation_id, language)

        if not detail or not detail.get("sample_code"):
            identifier = operation_id or f"{method} {path}"
            return f"Sample code not found: {identifier} ({language})"

        return detail["sample_code"]

    except FileNotFoundError as e:
        return (
            f"Search database not found: {str(e)}\nPlease run 'uv run python scripts/create_search_database.py' first"
        )
    except Exception as e:
        return f"Sample code retrieval error: {str(e)}"


# Extended Client Operations
@mcp.tool()
async def get_authorized_applications(
    subject: str = "",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Get authorized applications for a subject.

    Args:
        subject: Subject to get applications for (required)
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            return "Error: service_api_key parameter is required"
            
        if not subject:
            return "Error: subject parameter is required"

        # Check if organization token is available for extended operations
        if not DEFAULT_API_KEY:
            return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "GET", 
            f"auth/authorization/application/{subject}",
            config
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error getting authorized applications: {str(e)}"


@mcp.tool()
async def update_client_tokens(
    subject: str = "",
    client_id: str = "",
    token_data: str = "{}",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Update client tokens for a subject.

    Args:
        subject: Subject (required)
        client_id: Client ID (required)
        token_data: JSON string with token update parameters
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            return "Error: service_api_key parameter is required"

        if not subject or not client_id:
            return "Error: subject and client_id parameters are required"

        # Parse token data
        try:
            token_params = json.loads(token_data)
        except json.JSONDecodeError as e:
            return f"Error parsing token data JSON: {str(e)}"
            
        # Check if organization token is available for extended operations
        if not DEFAULT_API_KEY:
            return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "PUT",
            f"auth/authorization/application/{subject}/{client_id}",
            config,
            token_params
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error updating client tokens: {str(e)}"


@mcp.tool()
async def delete_client_tokens(
    subject: str = "",
    client_id: str = "",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Delete client tokens for a subject.

    Args:
        subject: Subject (required)
        client_id: Client ID (required)
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            if not DEFAULT_API_KEY:
                return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"
            service_api_key = DEFAULT_API_KEY

        if not subject:
            return "Error: subject parameter is required"

        if not client_id:
            return "Error: client_id parameter is required"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "DELETE",
            f"auth/authorization/application/{subject}/{client_id}",
            config
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error deleting client tokens: {str(e)}"


@mcp.tool()
async def get_granted_scopes(
    subject: str = "",
    client_id: str = "",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Get granted scopes for a client and subject.

    Args:
        subject: Subject (required)
        client_id: Client ID (required)  
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            if not DEFAULT_API_KEY:
                return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"
            service_api_key = DEFAULT_API_KEY

        if not subject:
            return "Error: subject parameter is required"

        if not client_id:
            return "Error: client_id parameter is required"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "GET",
            f"auth/authorization/grant/{subject}/{client_id}",
            config
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error getting granted scopes: {str(e)}"


@mcp.tool()
async def delete_granted_scopes(
    subject: str = "",
    client_id: str = "",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Delete granted scopes for a client and subject.

    Args:
        subject: Subject (required)
        client_id: Client ID (required)
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            if not DEFAULT_API_KEY:
                return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"
            service_api_key = DEFAULT_API_KEY

        if not subject:
            return "Error: subject parameter is required"

        if not client_id:
            return "Error: client_id parameter is required"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "DELETE",
            f"auth/authorization/grant/{subject}/{client_id}",
            config
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error deleting granted scopes: {str(e)}"


@mcp.tool()
async def get_requestable_scopes(
    client_id: str = "",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Get requestable scopes for a client.

    Args:
        client_id: Client ID (required)
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            if not DEFAULT_API_KEY:
                return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"
            service_api_key = DEFAULT_API_KEY

        if not client_id:
            return "Error: client_id parameter is required"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "GET",
            f"client/requestable_scopes/{client_id}",
            config
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error getting requestable scopes: {str(e)}"


@mcp.tool()
async def update_requestable_scopes(
    client_id: str = "",
    scopes_data: str = "{}",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Update requestable scopes for a client.

    Args:
        client_id: Client ID (required)
        scopes_data: JSON string with scopes data
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            if not DEFAULT_API_KEY:
                return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"
            service_api_key = DEFAULT_API_KEY

        if not client_id:
            return "Error: client_id parameter is required"

        # Parse scopes data
        try:
            scopes_params = json.loads(scopes_data)
        except json.JSONDecodeError as e:
            return f"Error parsing scopes data JSON: {str(e)}"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "PUT",
            f"client/requestable_scopes/{client_id}",
            config,
            scopes_params
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error updating requestable scopes: {str(e)}"


@mcp.tool()
async def delete_requestable_scopes(
    client_id: str = "",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Delete requestable scopes for a client.

    Args:
        client_id: Client ID (required)
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            if not DEFAULT_API_KEY:
                return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"
            service_api_key = DEFAULT_API_KEY

        if not client_id:
            return "Error: client_id parameter is required"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "DELETE",
            f"client/requestable_scopes/{client_id}",
            config
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error deleting requestable scopes: {str(e)}"


# Token Operations
@mcp.tool()
async def list_issued_tokens(
    subject: str = "",
    client_identifier: str = "",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """List issued tokens for a service.

    Args:
        subject: Subject to filter by (optional)
        client_identifier: Client identifier to filter by (optional)
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            return "Error: service_api_key parameter is required"
            
        # Check if organization token is available for token operations
        if not DEFAULT_API_KEY:
            return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Build query parameters
        params = {}
        if subject:
            params["subject"] = subject
        if client_identifier:
            params["clientIdentifier"] = client_identifier
        
        # Make request to Authlete API
        endpoint = "auth/token/get/list"
        if params:
            from urllib.parse import urlencode
            endpoint += f"?{urlencode(params)}"
        
        result = await make_authlete_request("GET", endpoint, config)
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error listing issued tokens: {str(e)}"


@mcp.tool()
async def create_access_token(
    token_data: str = "{}",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Create an access token.

    Args:
        token_data: JSON string with token creation parameters
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            if not DEFAULT_API_KEY:
                return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"
            service_api_key = DEFAULT_API_KEY

        # Parse token data
        try:
            token_params = json.loads(token_data)
        except json.JSONDecodeError as e:
            return f"Error parsing token data JSON: {str(e)}"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "POST",
            "auth/token/create",
            config,
            token_params
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error creating access token: {str(e)}"


@mcp.tool()
async def update_access_token(
    access_token: str = "",
    token_data: str = "{}",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Update an access token.

    Args:
        access_token: Access token to update (required)
        token_data: JSON string with token update parameters
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            if not DEFAULT_API_KEY:
                return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"
            service_api_key = DEFAULT_API_KEY

        if not access_token:
            return "Error: access_token parameter is required"

        # Parse token data
        try:
            token_params = json.loads(token_data)
        except json.JSONDecodeError as e:
            return f"Error parsing token data JSON: {str(e)}"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "PUT",
            f"auth/token/update/{access_token}",
            config,
            token_params
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error updating access token: {str(e)}"


@mcp.tool()
async def revoke_access_token(
    access_token: str = "",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Revoke an access token.

    Args:
        access_token: Access token to revoke (required)
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            if not DEFAULT_API_KEY:
                return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"
            service_api_key = DEFAULT_API_KEY

        if not access_token:
            return "Error: access_token parameter is required"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "POST",
            f"auth/token/revoke/{access_token}",
            config
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error revoking access token: {str(e)}"


@mcp.tool()
async def delete_access_token(
    access_token: str = "",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Delete an access token.

    Args:
        access_token: Access token to delete (required)
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            if not DEFAULT_API_KEY:
                return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"
            service_api_key = DEFAULT_API_KEY

        if not access_token:
            return "Error: access_token parameter is required"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "DELETE",
            f"auth/token/delete/{access_token}",
            config
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error deleting access token: {str(e)}"


# JOSE Operations
@mcp.tool()
async def generate_jose(
    jose_data: str = "{}",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Generate JOSE (JSON Web Signature/Encryption) object.

    Args:
        jose_data: JSON string with JOSE generation parameters
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            return "Error: service_api_key parameter is required"

        # Parse JOSE data
        try:
            jose_params = json.loads(jose_data)
        except json.JSONDecodeError as e:
            return f"Error parsing JOSE data JSON: {str(e)}"
            
        # Check if organization token is available for JOSE operations
        if not DEFAULT_API_KEY:
            return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "POST",
            "jose/generate",
            config,
            jose_params
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error generating JOSE: {str(e)}"


@mcp.tool()
async def verify_jose(
    jose_token: str = "",
    service_api_key: str = "",
    ctx: Context = None,
) -> str:
    """Verify JOSE (JSON Web Signature/Encryption) object.

    Args:
        jose_token: JOSE token to verify (required)
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            return "Error: service_api_key parameter is required"

        if not jose_token:
            return "Error: jose_token parameter is required"
            
        # Check if organization token is available for JOSE operations
        if not DEFAULT_API_KEY:
            return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

        config = AuthleteConfig(api_key=service_api_key)
        
        # Make request to Authlete API
        result = await make_authlete_request(
            "POST",
            "jose/verify",
            config,
            {"jose": jose_token}
        )
        
        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error verifying JOSE: {str(e)}"


if __name__ == "__main__":
    mcp.run()
