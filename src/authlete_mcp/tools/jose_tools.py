"""JOSE (JSON Web Signature/Encryption) tools for Authlete MCP Server."""

import json

import httpx

from ..api import make_authlete_request
from ..config import DEFAULT_API_KEY, AuthleteConfig


async def generate_jose(
    jose_data: str = "{}",
    service_api_key: str = "",
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
        result = await make_authlete_request("POST", "jose/generate", config, jose_params)

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error generating JOSE: {str(e)}"


async def verify_jose(
    jose_token: str = "",
    service_api_key: str = "",
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
        result = await make_authlete_request("POST", "jose/verify", config, {"jose": jose_token})

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except Exception as e:
        return f"Error verifying JOSE: {str(e)}"
