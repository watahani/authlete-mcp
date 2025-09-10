"""JOSE (JSON Web Signature/Encryption) tools for Authlete MCP Server."""

import json

import httpx

from ..api import make_authlete_request
from ..config import ORGANIZATION_ACCESS_TOKEN, AuthleteConfig


async def generate_jose(
    payload: str = "{}",
    algorithm: str = "ES256",
    jwk: str = "",
) -> str:
    """Generate JOSE (JSON Web Signature/Encryption) object using mkjose.org API.

    Args:
        payload: JSON string containing JWT payload (e.g., '{"sub": "user123", "exp": 1234567890}')
        algorithm: Signing algorithm (e.g., "ES256", "RS256", "HS256")
        jwk: JSON Web Key for signing as JSON string (required for ES256/RS256)
    """

    try:
        # Validate payload is valid JSON
        try:
            json.loads(payload)  # Just validate, don't store
        except json.JSONDecodeError as e:
            return f"Error parsing payload JSON: {str(e)}"

        # Validate JWK if provided
        if jwk:
            try:
                json.loads(jwk)  # Just validate, don't store
            except json.JSONDecodeError as e:
                return f"Error parsing JWK JSON: {str(e)}"

        # Make request to mkjose.org API (external service)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Convert parameters to form data format expected by mkjose.org
        form_data = {
            "payload": payload,
            "signing-alg": algorithm,
        }

        if jwk:
            form_data["jwk-signing-alg"] = jwk

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://mkjose.org/api/jose/generate",
                headers=headers,
                data=form_data,
            )
            response.raise_for_status()

            # mkjose.org may return plain text or JSON
            try:
                result = response.json()
            except json.JSONDecodeError:
                # If not JSON, return the text response
                result = {"jwt": response.text.strip()}

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
        service_api_key: Service ID (also known as Service API Key) (required)
    """

    try:
        # Validate required parameters
        if not service_api_key:
            return "Error: service_api_key parameter is required"

        if not jose_token:
            return "Error: jose_token parameter is required"

        # Check if organization token is available for JOSE operations
        if not ORGANIZATION_ACCESS_TOKEN:
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
