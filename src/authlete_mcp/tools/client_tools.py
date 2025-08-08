"""Client management tools for Authlete MCP Server."""

import json

from mcp.server.fastmcp import Context

from ..api.client import make_authlete_request
from ..config import DEFAULT_API_KEY, AuthleteConfig


async def create_client(client_data: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Create a new Authlete client."""
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)

    try:
        data = json.loads(client_data)
        result = await make_authlete_request("POST", f"{service_api_key}/client/create", config, data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        return f"Error parsing client data JSON: {str(e)}"
    except Exception as e:
        return f"Error creating client: {str(e)}"


async def get_client(client_id: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Get an Authlete client by ID."""
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)

    try:
        result = await make_authlete_request("GET", f"{service_api_key}/client/get/{client_id}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting client: {str(e)}"


async def list_clients(service_api_key: str = "", ctx: Context = None) -> str:
    """List all Authlete clients."""
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)

    try:
        result = await make_authlete_request("GET", f"{service_api_key}/client/get/list", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing clients: {str(e)}"


async def update_client(client_id: str, client_data: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Update an Authlete client."""
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)

    try:
        data = json.loads(client_data)
        result = await make_authlete_request("POST", f"{service_api_key}/client/update/{client_id}", config, data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        return f"Error parsing client data JSON: {str(e)}"
    except Exception as e:
        return f"Error updating client: {str(e)}"


async def delete_client(client_id: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Delete an Authlete client."""
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)

    try:
        result = await make_authlete_request("DELETE", f"{service_api_key}/client/delete/{client_id}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error deleting client: {str(e)}"


async def rotate_client_secret(client_id: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Rotate an Authlete client secret."""
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)

    try:
        result = await make_authlete_request("GET", f"{service_api_key}/client/secret/refresh/{client_id}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error rotating client secret: {str(e)}"


async def update_client_secret(client_id: str, secret_data: str, service_api_key: str = "", ctx: Context = None) -> str:
    """Update an Authlete client secret."""
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)

    try:
        data = json.loads(secret_data)
        result = await make_authlete_request(
            "POST", f"{service_api_key}/client/secret/update/{client_id}", config, data
        )
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        return f"Error parsing secret data JSON: {str(e)}"
    except Exception as e:
        return f"Error updating client secret: {str(e)}"


async def update_client_lock(client_id: str, lock_flag: bool, service_api_key: str = "", ctx: Context = None) -> str:
    """Update an Authlete client lock status."""
    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    config = AuthleteConfig(api_key=DEFAULT_API_KEY)

    data = {"locked": lock_flag}

    try:
        result = await make_authlete_request(
            "POST", f"{service_api_key}/client/lock_flag/update/{client_id}", config, data
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error updating client lock: {str(e)}"


async def get_authorized_applications(service_api_key: str = "", subject: str = "", ctx: Context = None) -> str:
    """Get authorized applications for a subject.

    Args:
        service_api_key: Service API key (required)
        subject: Subject to get applications for (required)
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    if not subject:
        return "Error: subject parameter is required"

    config = AuthleteConfig(api_key=service_api_key)

    try:
        result = await make_authlete_request("GET", f"client/authorization/get/list?subject={subject}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting authorized applications: {str(e)}"


async def update_client_tokens(
    service_api_key: str = "", subject: str = "", client_id: str = "", token_data: str = "{}", ctx: Context = None
) -> str:
    """Update client tokens for a subject.

    Args:
        service_api_key: Service API key (required)
        subject: Subject (required)
        client_id: Client ID (required)
        token_data: JSON string with token update parameters
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    if not subject or not client_id:
        return "Error: subject and client_id parameters are required"

    try:
        data = json.loads(token_data)
    except json.JSONDecodeError as e:
        return f"Error parsing token data JSON: {str(e)}"

    config = AuthleteConfig(api_key=service_api_key)

    try:
        result = await make_authlete_request(
            "POST", f"client/authorization/update/{client_id}?subject={subject}", config, data
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error updating client tokens: {str(e)}"


async def delete_client_tokens(
    service_api_key: str = "", subject: str = "", client_id: str = "", ctx: Context = None
) -> str:
    """Delete client tokens for a subject.

    Args:
        service_api_key: Service API key (required)
        subject: Subject (required)
        client_id: Client ID (required)
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    if not subject or not client_id:
        return "Error: subject and client_id parameters are required"

    config = AuthleteConfig(api_key=service_api_key)

    try:
        result = await make_authlete_request(
            "DELETE", f"client/authorization/delete/{client_id}?subject={subject}", config
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error deleting client tokens: {str(e)}"


async def get_granted_scopes(
    service_api_key: str = "", subject: str = "", client_id: str = "", ctx: Context = None
) -> str:
    """Get granted scopes for a client and subject.

    Args:
        service_api_key: Service API key (required)
        subject: Subject (required)
        client_id: Client ID (required)
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    if not subject or not client_id:
        return "Error: subject and client_id parameters are required"

    config = AuthleteConfig(api_key=service_api_key)

    try:
        result = await make_authlete_request("GET", f"client/granted_scopes/get/{client_id}?subject={subject}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting granted scopes: {str(e)}"


async def delete_granted_scopes(
    service_api_key: str = "", subject: str = "", client_id: str = "", ctx: Context = None
) -> str:
    """Delete granted scopes for a client and subject.

    Args:
        service_api_key: Service API key (required)
        subject: Subject (required)
        client_id: Client ID (required)
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    if not subject or not client_id:
        return "Error: subject and client_id parameters are required"

    config = AuthleteConfig(api_key=service_api_key)

    try:
        result = await make_authlete_request(
            "DELETE", f"client/granted_scopes/delete/{client_id}?subject={subject}", config
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error deleting granted scopes: {str(e)}"


async def get_requestable_scopes(service_api_key: str = "", client_id: str = "", ctx: Context = None) -> str:
    """Get requestable scopes for a client.

    Args:
        service_api_key: Service API key (required)
        client_id: Client ID (required)
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    if not client_id:
        return "Error: client_id parameter is required"

    config = AuthleteConfig(api_key=service_api_key)

    try:
        result = await make_authlete_request("GET", f"client/extension/requestable_scopes/get/{client_id}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting requestable scopes: {str(e)}"


async def update_requestable_scopes(
    service_api_key: str = "", client_id: str = "", scopes_data: str = "{}", ctx: Context = None
) -> str:
    """Update requestable scopes for a client.

    Args:
        service_api_key: Service API key (required)
        client_id: Client ID (required)
        scopes_data: JSON string with scopes data
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    if not client_id:
        return "Error: client_id parameter is required"

    try:
        data = json.loads(scopes_data)
    except json.JSONDecodeError as e:
        return f"Error parsing scopes data JSON: {str(e)}"

    config = AuthleteConfig(api_key=service_api_key)

    try:
        result = await make_authlete_request(
            "POST", f"client/extension/requestable_scopes/update/{client_id}", config, data
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error updating requestable scopes: {str(e)}"


async def delete_requestable_scopes(service_api_key: str = "", client_id: str = "", ctx: Context = None) -> str:
    """Delete requestable scopes for a client.

    Args:
        service_api_key: Service API key (required)
        client_id: Client ID (required)
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for client operations"

    if not client_id:
        return "Error: client_id parameter is required"

    config = AuthleteConfig(api_key=service_api_key)

    try:
        result = await make_authlete_request(
            "DELETE", f"client/extension/requestable_scopes/delete/{client_id}", config
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error deleting requestable scopes: {str(e)}"
