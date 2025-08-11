"""HTTP client for Authlete API."""

import json
import logging
from typing import Any

import httpx

from ..config import AuthleteConfig

# Set up logger
logger = logging.getLogger(__name__)


async def make_authlete_request(
    method: str, endpoint: str, config: AuthleteConfig, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Make a request to the Authlete API."""

    url = f"{config.base_url}/api/{endpoint}"
    headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}

    # Debug logging
    logger.info(f"HTTP {method} {url}")
    logger.info(f"Headers: {headers}")
    if data:
        logger.info(f"Request body: {json.dumps(data, indent=2)}")

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

    # Debug response logging
    logger.info(f"Response status: {response.status_code}")
    logger.info(f"Response headers: {dict(response.headers)}")
    try:
        response_body = response.json()
        logger.info(f"Response body: {json.dumps(response_body, indent=2)}")
    except json.JSONDecodeError:
        logger.info(f"Response text: {response.text}")

    if response.status_code >= 400:
        error_detail = response.text
        try:
            error_json = response.json()
            if "resultMessage" in error_json:
                error_detail = f"Authlete API Error: {error_json['resultMessage']}"
        except json.JSONDecodeError:
            pass
        raise httpx.HTTPStatusError(error_detail, request=response.request, response=response)

    # Handle 204 No Content (successful deletion)
    if response.status_code == 204:
        return {"success": True, "message": "Operation completed successfully"}

    return response.json()


async def make_authlete_idp_request(
    method: str, endpoint: str, config: AuthleteConfig, data: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Make a request to the Authlete IdP API."""

    url = f"{config.idp_url}/api/{endpoint}"
    headers = {"Authorization": f"Bearer {config.api_key}", "Content-Type": "application/json"}

    # Debug logging
    logger.info(f"HTTP {method} {url} (IdP API)")
    logger.info(f"Headers: {headers}")
    if data:
        logger.info(f"Request body: {json.dumps(data, indent=2)}")

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

    # Debug response logging
    logger.info(f"Response status: {response.status_code} (IdP API)")
    logger.info(f"Response headers: {dict(response.headers)}")
    try:
        response_body = response.json()
        logger.info(f"Response body: {json.dumps(response_body, indent=2)}")
    except json.JSONDecodeError:
        logger.info(f"Response text: {response.text}")

    if response.status_code >= 400:
        error_detail = response.text
        try:
            error_json = response.json()
            if "resultMessage" in error_json:
                error_detail = f"Authlete IdP API Error: {error_json['resultMessage']}"
        except json.JSONDecodeError:
            pass
        raise httpx.HTTPStatusError(error_detail, request=response.request, response=response)

    # Handle 204 No Content (successful deletion)
    if response.status_code == 204:
        return {"success": True, "message": "Service deleted successfully"}

    # Handle empty response body
    try:
        return response.json()
    except json.JSONDecodeError:
        # If response body is empty but status is success, return success message
        if 200 <= response.status_code < 300:
            return {"success": True, "message": f"Operation completed with status {response.status_code}"}
        return {"error": "Empty response body", "status_code": response.status_code}
