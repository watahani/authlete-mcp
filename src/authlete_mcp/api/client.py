"""HTTP client for Authlete API."""

import hashlib
import json
from typing import Any

import httpx

from ..config import AuthleteConfig
from ..logging import get_logger, log_request_response

# Set up logger with PII masking
logger = get_logger(__name__)


async def make_authlete_request(
    method: str, endpoint: str, config: AuthleteConfig, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Make a request to the Authlete API."""

    url = f"{config.base_url}/api/{endpoint}"
    token_hash = hashlib.sha256(config.access_token.encode()).hexdigest()[:10]
    logger.debug(
        "make_authlete_request: method=%s endpoint=%s token_hash=%s",
        method,
        endpoint,
        token_hash,
    )

    try:
        # Use structured logging with PII masking
        log_request_response(logger, method, url, request_data=data)

        headers = {"Authorization": f"Bearer {config.access_token}", "Content-Type": "application/json"}

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

            # Log error response
            log_request_response(
                logger,
                method,
                url,
                status_code=response.status_code,
                error=httpx.HTTPStatusError(error_detail, request=response.request, response=response),
            )
            raise httpx.HTTPStatusError(error_detail, request=response.request, response=response)

        # Handle 204 No Content (successful deletion)
        if response.status_code == 204:
            result = {"success": True, "message": "Operation completed successfully"}
            log_request_response(logger, method, url, response_data=result, status_code=response.status_code)
            return result

        try:
            result = response.json()
            log_request_response(logger, method, url, response_data=result, status_code=response.status_code)
            return result
        except json.JSONDecodeError:
            result = {"text": response.text}
            log_request_response(logger, method, url, response_data=result, status_code=response.status_code)
            return result

    except Exception as e:
        # Log any unexpected errors
        if not isinstance(e, httpx.HTTPStatusError):
            log_request_response(logger, method, url, request_data=data, error=e)
        raise


async def make_authlete_request_with_dynamic_server(
    method: str, endpoint: str, access_token: str, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Make a request to the Authlete API with dynamic server selection."""
    from ..config import ensure_api_server_configured, get_api_server_url

    # Ensure API server is configured
    error_msg = await ensure_api_server_configured()
    if error_msg:
        raise RuntimeError(error_msg)

    api_url = get_api_server_url()
    if not api_url:
        raise RuntimeError("API server URL not available")

    url = f"{api_url}/api/{endpoint}"

    try:
        # Use structured logging with PII masking
        log_request_response(logger, method, url, request_data=data)

        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

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

            # Log error response
            log_request_response(
                logger,
                method,
                url,
                status_code=response.status_code,
                error=httpx.HTTPStatusError(error_detail, request=response.request, response=response),
            )
            raise httpx.HTTPStatusError(error_detail, request=response.request, response=response)

        # Handle 204 No Content (successful deletion)
        if response.status_code == 204:
            result = {"success": True, "message": "Operation completed successfully"}
            log_request_response(logger, method, url, response_data=result, status_code=response.status_code)
            return result

        try:
            result = response.json()
            log_request_response(logger, method, url, response_data=result, status_code=response.status_code)
            return result
        except json.JSONDecodeError:
            result = {"text": response.text}
            log_request_response(logger, method, url, response_data=result, status_code=response.status_code)
            return result

    except Exception as e:
        # Log any unexpected errors
        if not isinstance(e, httpx.HTTPStatusError):
            log_request_response(logger, method, url, request_data=data, error=e)
        raise


async def make_authlete_idp_request(
    endpoint: str,
    method: str = "GET",
    access_token: str | None = None,
    data: dict[str, Any] | None = None,
    config: AuthleteConfig | None = None,
) -> dict[str, Any]:
    """Make a request to the Authlete IdP API."""
    from ..config import AUTHLETE_IDP_URL

    if config:
        base_url = config.idp_url
        token = config.access_token
    else:
        base_url = AUTHLETE_IDP_URL
        token = access_token

    token_hash = hashlib.sha256((token or "").encode()).hexdigest()[:10] if token else "missing"
    logger.debug(
        "make_authlete_idp_request: method=%s endpoint=%s token_hash=%s",
        method,
        endpoint,
        token_hash,
    )

    url = f"{base_url}/api/{endpoint}"

    try:
        # Use structured logging with PII masking
        log_request_response(logger, method, f"{url} (IdP API)", request_data=data)

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

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

            # Log error response
            log_request_response(
                logger,
                method,
                f"{url} (IdP API)",
                status_code=response.status_code,
                error=httpx.HTTPStatusError(error_detail, request=response.request, response=response),
            )
            raise httpx.HTTPStatusError(error_detail, request=response.request, response=response)

        # Handle 204 No Content (successful deletion)
        if response.status_code == 204:
            result = {"success": True, "message": "Service deleted successfully"}
            log_request_response(
                logger, method, f"{url} (IdP API)", response_data=result, status_code=response.status_code
            )
            return result

        # Handle empty response body
        try:
            result = response.json()
            log_request_response(
                logger, method, f"{url} (IdP API)", response_data=result, status_code=response.status_code
            )
            return result
        except json.JSONDecodeError:
            # If response body is empty but status is success, return success message
            if 200 <= response.status_code < 300:
                result = {"success": True, "message": f"Operation completed with status {response.status_code}"}
                log_request_response(
                    logger, method, f"{url} (IdP API)", response_data=result, status_code=response.status_code
                )
                return result
            result = {"error": "Empty response body", "status_code": response.status_code}
            log_request_response(
                logger, method, f"{url} (IdP API)", response_data=result, status_code=response.status_code
            )
            return result

    except Exception as e:
        # Log any unexpected errors
        if not isinstance(e, httpx.HTTPStatusError):
            log_request_response(logger, method, f"{url} (IdP API)", request_data=data, error=e)
        raise
