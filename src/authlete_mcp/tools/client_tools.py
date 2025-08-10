"""Client management tools for Authlete MCP Server."""

import json

import httpx

from ..api import make_authlete_request
from ..config import DEFAULT_API_KEY, AuthleteConfig


async def create_client(client_data: str, service_api_key: str = "") -> str:
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


async def get_client(client_id: str, service_api_key: str = "") -> str:
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


async def list_clients(service_api_key: str = "") -> str:
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


async def update_client(client_id: str, client_data: str, service_api_key: str = "") -> str:
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


async def delete_client(client_id: str, service_api_key: str = "") -> str:
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


async def rotate_client_secret(client_id: str, service_api_key: str = "") -> str:
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


async def update_client_secret(client_id: str, secret_data: str, service_api_key: str = "") -> str:
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


async def update_client_lock(client_id: str, lock_flag: bool, service_api_key: str = "") -> str:
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


async def get_authorized_applications(
    subject: str = "",
    service_api_key: str = "",
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
        result = await make_authlete_request("GET", f"auth/authorization/application/{subject}", config)

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error getting authorized applications: {str(e)}"


async def update_client_tokens(
    subject: str = "",
    client_id: str = "",
    token_data: str = "{}",
    service_api_key: str = "",
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
            "PUT", f"auth/authorization/application/{subject}/{client_id}", config, token_params
        )

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error updating client tokens: {str(e)}"


async def delete_client_tokens(
    subject: str = "",
    client_id: str = "",
    service_api_key: str = "",
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
            return "Error: service_api_key parameter is required"

        if not subject:
            return "Error: subject parameter is required"

        if not client_id:
            return "Error: client_id parameter is required"

        config = AuthleteConfig(api_key=service_api_key)

        # Make request to Authlete API
        result = await make_authlete_request("DELETE", f"auth/authorization/application/{subject}/{client_id}", config)

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error deleting client tokens: {str(e)}"


async def get_granted_scopes(
    subject: str = "",
    client_id: str = "",
    service_api_key: str = "",
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
            return "Error: service_api_key parameter is required"

        if not subject:
            return "Error: subject parameter is required"

        if not client_id:
            return "Error: client_id parameter is required"

        config = AuthleteConfig(api_key=service_api_key)

        # Make request to Authlete API
        result = await make_authlete_request("GET", f"auth/authorization/grant/{subject}/{client_id}", config)

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error getting granted scopes: {str(e)}"


async def delete_granted_scopes(
    subject: str = "",
    client_id: str = "",
    service_api_key: str = "",
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
            return "Error: service_api_key parameter is required"

        if not subject:
            return "Error: subject parameter is required"

        if not client_id:
            return "Error: client_id parameter is required"

        config = AuthleteConfig(api_key=service_api_key)

        # Make request to Authlete API
        result = await make_authlete_request("DELETE", f"auth/authorization/grant/{subject}/{client_id}", config)

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error deleting granted scopes: {str(e)}"


async def get_requestable_scopes(
    client_id: str = "",
    service_api_key: str = "",
) -> str:
    """Get requestable scopes for a client.

    Args:
        client_id: Client ID (required)
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            return "Error: service_api_key parameter is required"

        if not client_id:
            return "Error: client_id parameter is required"

        config = AuthleteConfig(api_key=service_api_key)

        # Make request to Authlete API
        result = await make_authlete_request("GET", f"client/requestable_scopes/{client_id}", config)

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error getting requestable scopes: {str(e)}"


async def update_requestable_scopes(
    client_id: str = "",
    scopes_data: str = "{}",
    service_api_key: str = "",
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
            return "Error: service_api_key parameter is required"

        if not client_id:
            return "Error: client_id parameter is required"

        # Parse scopes data
        try:
            scopes_params = json.loads(scopes_data)
        except json.JSONDecodeError as e:
            return f"Error parsing scopes data JSON: {str(e)}"

        config = AuthleteConfig(api_key=service_api_key)

        # Make request to Authlete API
        result = await make_authlete_request("PUT", f"client/requestable_scopes/{client_id}", config, scopes_params)

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error updating requestable scopes: {str(e)}"


async def delete_requestable_scopes(
    client_id: str = "",
    service_api_key: str = "",
) -> str:
    """Delete requestable scopes for a client.

    Args:
        client_id: Client ID (required)
        service_api_key: Service API key (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            return "Error: service_api_key parameter is required"

        if not client_id:
            return "Error: client_id parameter is required"

        config = AuthleteConfig(api_key=service_api_key)

        # Make request to Authlete API
        result = await make_authlete_request("DELETE", f"client/requestable_scopes/{client_id}", config)

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error deleting requestable scopes: {str(e)}"
