"""Token management tools for Authlete MCP server."""

import json
from urllib.parse import urlencode

import httpx

from ..api import make_authlete_request
from ..config import ORGANIZATION_ACCESS_TOKEN, AuthleteConfig


async def list_issued_tokens(
    subject: str = "",
    client_identifier: str = "",
    service_api_key: str = "",
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
        if not ORGANIZATION_ACCESS_TOKEN:
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
            endpoint += f"?{urlencode(params)}"

        result = await make_authlete_request("GET", endpoint, config)

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error listing issued tokens: {str(e)}"


async def create_access_token(
    token_data: str = "{}",
    service_api_key: str = "",
) -> str:
    """Create an access token.

    Args:
        token_data: JSON string with token creation parameters
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            return "Error: service_api_key parameter is required"

        # Parse token data
        try:
            token_params = json.loads(token_data)
        except json.JSONDecodeError as e:
            return f"Error parsing token data JSON: {str(e)}"

        config = AuthleteConfig(api_key=service_api_key)

        # Make request to Authlete API
        result = await make_authlete_request("POST", "auth/token/create", config, token_params)

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error creating access token: {str(e)}"


async def update_access_token(
    access_token: str = "",
    token_data: str = "{}",
    service_api_key: str = "",
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
            return "Error: service_api_key parameter is required"

        if not access_token:
            return "Error: access_token parameter is required"

        # Parse token data
        try:
            token_params = json.loads(token_data)
        except json.JSONDecodeError as e:
            return f"Error parsing token data JSON: {str(e)}"

        config = AuthleteConfig(api_key=service_api_key)

        # Make request to Authlete API
        result = await make_authlete_request("PUT", f"auth/token/update/{access_token}", config, token_params)

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error updating access token: {str(e)}"


async def revoke_access_token(
    access_token: str = "",
    service_api_key: str = "",
) -> str:
    """Revoke an access token.

    Args:
        access_token: Access token to revoke (required)
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            return "Error: service_api_key parameter is required"

        if not access_token:
            return "Error: access_token parameter is required"

        config = AuthleteConfig(api_key=service_api_key)

        # Make request to Authlete API
        result = await make_authlete_request("POST", f"auth/token/revoke/{access_token}", config)

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error revoking access token: {str(e)}"


async def delete_access_token(
    access_token: str = "",
    service_api_key: str = "",
) -> str:
    """Delete an access token.

    Args:
        access_token: Access token to delete (required)
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            return "Error: service_api_key parameter is required"

        if not access_token:
            return "Error: access_token parameter is required"

        config = AuthleteConfig(api_key=service_api_key)

        # Make request to Authlete API
        result = await make_authlete_request("DELETE", f"auth/token/delete/{access_token}", config)

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error deleting access token: {str(e)}"
