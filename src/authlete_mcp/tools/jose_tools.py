"""JOSE (JSON Object Signing and Encryption) tools for Authlete MCP Server."""

import json

from mcp.server.fastmcp import Context

from ..api.client import make_authlete_request
from ..config import DEFAULT_API_KEY, AuthleteConfig


async def generate_jose(service_api_key: str = "", jose_data: str = "{}", ctx: Context = None) -> str:
    """Generate JOSE (JSON Web Signature/Encryption) object.

    Args:
        service_api_key: Service API key (required)
        jose_data: JSON string with JOSE generation parameters
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for JOSE operations"

    try:
        data = json.loads(jose_data)
    except json.JSONDecodeError as e:
        return f"Error parsing JOSE data JSON: {str(e)}"

    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=service_api_key)

    try:
        result = await make_authlete_request("POST", "jose/create", config, data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error generating JOSE object: {str(e)}"


async def verify_jose(service_api_key: str = "", jose_token: str = "", ctx: Context = None) -> str:
    """Verify JOSE (JSON Web Signature/Encryption) object.

    Args:
        service_api_key: Service API key (required)
        jose_token: JOSE token to verify (required)
    """
    if not service_api_key:
        return "Error: service_api_key parameter is required for JOSE operations"

    if not jose_token:
        return "Error: jose_token parameter is required"

    if not DEFAULT_API_KEY:
        return "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"

    config = AuthleteConfig(api_key=service_api_key)

    # Create verification request payload
    data = {"token": jose_token}

    try:
        result = await make_authlete_request("POST", "jose/verify", config, data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error verifying JOSE object: {str(e)}"
