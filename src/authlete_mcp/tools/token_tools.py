"""Token management tools for Authlete MCP Server."""

import json

from mcp.server.fastmcp import Context

from ..api.client import make_authlete_request
from ..config import DEFAULT_API_KEY, AuthleteConfig


async def list_issued_tokens(
    service_api_key: str = "", subject: str = "", client_identifier: str = "", ctx: Context = None
) -> str:
    """List issued tokens for a service.

    Args:
        service_api_key: Service API key (required)
        subject: Subject to filter by (optional)
        client_identifier: Client identifier to filter by (optional)
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for token operations"

    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=service_api_key)

    # Build URL with query parameters
    url = "auth/token/get/list"
    query_params = []
    if subject:
        query_params.append(f"subject={subject}")
    if client_identifier:
        query_params.append(f"clientIdentifier={client_identifier}")

    if query_params:
        url += "?" + "&".join(query_params)

    try:
        result = await make_authlete_request("GET", url, config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing issued tokens: {str(e)}"


async def create_access_token(service_api_key: str = "", token_data: str = "{}", ctx: Context = None) -> str:
    """Create an access token.

    Args:
        service_api_key: Service API key (required)
        token_data: JSON string with token creation parameters
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for token operations"

    try:
        data = json.loads(token_data)
    except json.JSONDecodeError as e:
        return f"Error parsing token data JSON: {str(e)}"

    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=service_api_key)

    try:
        result = await make_authlete_request("POST", "auth/token/create", config, data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error creating access token: {str(e)}"


async def update_access_token(
    service_api_key: str = "", access_token: str = "", token_data: str = "{}", ctx: Context = None
) -> str:
    """Update an access token.

    Args:
        service_api_key: Service API key (required)
        access_token: Access token to update (required)
        token_data: JSON string with token update parameters
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for token operations"

    if not access_token:
        return "Error: access_token parameter is required"

    try:
        data = json.loads(token_data)
    except json.JSONDecodeError as e:
        return f"Error parsing token data JSON: {str(e)}"

    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=service_api_key)

    try:
        result = await make_authlete_request("POST", f"auth/token/update/{access_token}", config, data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error updating access token: {str(e)}"


async def revoke_access_token(service_api_key: str = "", access_token: str = "", ctx: Context = None) -> str:
    """Revoke an access token.

    Args:
        service_api_key: Service API key (required)
        access_token: Access token to revoke (required)
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for token operations"

    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    if not access_token:
        return "Error: access_token parameter is required"

    config = AuthleteConfig(api_key=service_api_key)

    try:
        result = await make_authlete_request("DELETE", f"auth/token/delete/{access_token}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error revoking access token: {str(e)}"


async def delete_access_token(service_api_key: str = "", access_token: str = "", ctx: Context = None) -> str:
    """Delete an access token.

    Args:
        service_api_key: Service API key (required)
        access_token: Access token to delete (required)
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for token operations"

    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    if not access_token:
        return "Error: access_token parameter is required"

    config = AuthleteConfig(api_key=service_api_key)

    try:
        result = await make_authlete_request("DELETE", f"auth/token/delete/{access_token}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error deleting access token: {str(e)}"
