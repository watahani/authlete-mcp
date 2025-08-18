"""Client management tools for Authlete MCP Server."""

import json

import httpx

from ..api import make_authlete_request
from ..config import AuthleteConfig


async def create_client(client_data: str, service_api_key: str = "") -> str:
    """Create a new Authlete client.

    Args:
        client_data: JSON string containing client data
        service_api_key: Service ID (also known as Service API Key, required for URL path)
    """
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"

    # Use organization token for authentication, service_api_key for URL path
    from ..config import ORGANIZATION_ACCESS_TOKEN, AuthleteConfig

    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)

    try:
        data = json.loads(client_data)
        # Use the correct endpoint format: {service_api_key}/client/create
        result = await make_authlete_request("POST", f"{service_api_key}/client/create", config, data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        return f"Error parsing client data JSON: {str(e)}"
    except Exception as e:
        return f"Error creating client: {str(e)}"


async def get_client(client_id: str, service_api_key: str = "") -> str:
    """Get an Authlete client by ID.

    Args:
        client_id: Client ID to retrieve
        service_api_key: Service ID (also known as Service API Key, required for URL path)
    """
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"

    # Use organization token for authentication, service_api_key for URL path
    from ..config import ORGANIZATION_ACCESS_TOKEN

    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)

    try:
        result = await make_authlete_request("GET", f"{service_api_key}/client/get/{client_id}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting client: {str(e)}"


async def list_clients(service_api_key: str = "") -> str:
    """List all Authlete clients.

    Args:
        service_api_key: Service ID (also known as Service API Key, required for URL path)
    """
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"

    # Use organization token for authentication, service_api_key for URL path
    from ..config import ORGANIZATION_ACCESS_TOKEN

    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)

    try:
        result = await make_authlete_request("GET", f"{service_api_key}/client/get/list", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error listing clients: {str(e)}"


async def patch_client(client_id: str, client_patch_data: str, service_api_key: str = "") -> str:
    """Patch an Authlete client by merging new data with existing configuration.

    This function first retrieves the current client data, merges it with the provided
    patch data, and then performs a full update with the merged configuration.

    Args:
        client_id: Client ID to patch
        client_patch_data: JSON string containing fields to update (partial data)
        service_api_key: Service ID (also known as Service API Key, required for URL path)
    """
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"

    try:
        # Parse patch data
        patch_data = json.loads(client_patch_data)
    except json.JSONDecodeError as e:
        return f"Error parsing client patch data JSON: {str(e)}"

    try:
        # Get current client data
        current_result = await get_client(client_id, service_api_key)

        # Check if get_client returned an error
        if current_result.startswith("Error"):
            return f"Error getting current client data: {current_result}"

        # Parse current client data
        current_data = json.loads(current_result)

        # Merge patch data with current data
        merged_data = {**current_data, **patch_data}

        # Convert merged data back to JSON string and call update_client
        merged_data_str = json.dumps(merged_data)
        return await update_client(client_id, merged_data_str, service_api_key)

    except json.JSONDecodeError as e:
        return f"Error parsing current client data JSON: {str(e)}"
    except Exception as e:
        return f"Error patching client: {str(e)}"


async def update_client(client_id: str, client_data: str, service_api_key: str = "") -> str:
    """Update an Authlete client.

    Note: This is a full update operation that overwrites the entire client configuration.
    If you want to update only specific fields, use patch_client instead to merge with existing data.

    Args:
        client_id: Client ID to update
        client_data: JSON string containing complete client data (overwrites all fields)
        service_api_key: Service ID (also known as Service API Key, required for URL path)
    """
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"

    # Use organization token for authentication, service_api_key for URL path
    from ..config import ORGANIZATION_ACCESS_TOKEN

    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)

    try:
        data = json.loads(client_data)
        result = await make_authlete_request("POST", f"{service_api_key}/client/update/{client_id}", config, data)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError as e:
        return f"Error parsing client data JSON: {str(e)}"
    except Exception as e:
        return f"Error updating client: {str(e)}"


async def delete_client(client_id: str, service_api_key: str = "") -> str:
    """Delete an Authlete client.

    Args:
        client_id: Client ID to delete
        service_api_key: Service ID (also known as Service API Key, required for URL path)
    """
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"

    # Use organization token for authentication, service_api_key for URL path
    from ..config import ORGANIZATION_ACCESS_TOKEN

    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)

    try:
        result = await make_authlete_request("DELETE", f"{service_api_key}/client/delete/{client_id}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error deleting client: {str(e)}"


async def rotate_client_secret(client_id: str, service_api_key: str = "") -> str:
    """Rotate an Authlete client secret.

    Args:
        client_id: Client ID
        service_api_key: Service ID (also known as Service API Key, required for URL path)
    """
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"

    # Use organization token for authentication, service_api_key for URL path
    from ..config import ORGANIZATION_ACCESS_TOKEN

    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)

    try:
        result = await make_authlete_request("GET", f"{service_api_key}/client/secret/refresh/{client_id}", config)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error rotating client secret: {str(e)}"


async def update_client_secret(client_id: str, secret_data: str, service_api_key: str = "") -> str:
    """Update an Authlete client secret.

    Note: This is a full update operation for client secret configuration.

    Args:
        client_id: Client ID
        secret_data: JSON string containing new secret data
        service_api_key: Service ID (also known as Service API Key, required for URL path)
    """
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"

    # Use organization token for authentication, service_api_key for URL path
    from ..config import ORGANIZATION_ACCESS_TOKEN

    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)

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


async def update_client_lock(client_id: str, lock_flag: bool, service_api_key: str = "") -> str:
    """Update an Authlete client lock status.

    Note: This updates only the lock status of the client.

    Args:
        client_id: Client ID
        lock_flag: True to lock, False to unlock
        service_api_key: Service ID (also known as Service API Key, required for URL path)
    """
    # Validate required parameters
    if not service_api_key:
        return "Error: service_api_key parameter is required"

    # Use organization token for authentication, service_api_key for URL path
    from ..config import ORGANIZATION_ACCESS_TOKEN

    if not ORGANIZATION_ACCESS_TOKEN:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=ORGANIZATION_ACCESS_TOKEN)

    data = {"locked": lock_flag}

    try:
        result = await make_authlete_request(
            "POST", f"{service_api_key}/client/lock_flag/update/{client_id}", config, data
        )
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
        service_api_key: Service ID (also known as Service API Key, required for URL path)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            return "Error: service_api_key parameter is required"

        if not subject:
            return "Error: subject parameter is required"

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

    Note: This is a full update operation for client tokens.

    Args:
        subject: Subject (required)
        client_id: Client ID (required)
        token_data: JSON string with token update parameters
        service_api_key: Service ID (also known as Service API Key, required for URL path)
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
        service_api_key: Service ID (also known as Service API Key, required for URL path)
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
        service_api_key: Service ID (also known as Service API Key, required for URL path)
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
        service_api_key: Service ID (also known as Service API Key, required for URL path)
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
        service_api_key: Service ID (also known as Service API Key, required for URL path)
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

    Note: This is a full update operation that overwrites all requestable scopes.

    Args:
        client_id: Client ID (required)
        scopes_data: JSON string with scopes data
        service_api_key: Service ID (also known as Service API Key, required for URL path)
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
        service_api_key: Service ID (also known as Service API Key, required for URL path)
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
