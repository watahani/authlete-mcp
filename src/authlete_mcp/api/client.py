"""HTTP client for Authlete API."""

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

    try:
        # Use structured logging with PII masking
        log_request_response(logger, method, url, request_data=data)

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
    method: str, endpoint: str, config: AuthleteConfig, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Make a request to the Authlete IdP API."""

    url = f"{config.idp_url}/api/{endpoint}"

    try:
        # Use structured logging with PII masking
        log_request_response(logger, method, f"{url} (IdP API)", request_data=data)

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
