"""HTTP client for Authlete API."""

import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from ..config import AuthleteConfig
from ..logging import get_logger, log_request_response

# Set up logger with PII masking
logger = get_logger(__name__)

_DEFAULT_MAX_ATTEMPTS = max(1, int(os.getenv("AUTHLETE_API_MAX_RETRIES", "3")))
_DEFAULT_BACKOFF_SECONDS = float(os.getenv("AUTHLETE_API_RETRY_BACKOFF_SECONDS", "0.5"))
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_ACCESS_RIGHT_ERROR_CODES = tuple(
    code.strip() for code in os.getenv("AUTHLETE_API_RETRY_ERROR_CODES", "A457101").split(",") if code.strip()
)


def _is_retryable_http_error(exc: httpx.HTTPStatusError) -> bool:
    """Return True when the HTTP error merits a retry."""

    response = exc.response
    if response is None:
        return True

    status = response.status_code
    if status in _RETRYABLE_STATUS_CODES:
        return True

    if status == 403:
        message_candidates: list[str] = []
        try:
            payload = response.json()
        except json.JSONDecodeError:
            payload = None

        if isinstance(payload, dict):
            message_candidates.extend(
                str(payload.get(key, "")) for key in ("resultMessage", "message", "error_description")
            )
        elif payload is not None:
            message_candidates.append(str(payload))

        message_candidates.append(response.text)
        message_candidates.append(str(exc))

        combined = " ".join(filter(None, message_candidates))
        return any(code in combined for code in _ACCESS_RIGHT_ERROR_CODES)

    return False


def _should_retry(exc: Exception) -> bool:
    """Determine whether the given exception should trigger a retry."""

    if isinstance(exc, httpx.HTTPStatusError):
        return _is_retryable_http_error(exc)

    if isinstance(exc, httpx.RequestError):
        return True

    return False


async def _call_with_retry(
    operation: Callable[[], Awaitable[Any]],
    *,
    retry: bool,
    max_retries: int | None,
    backoff_seconds: float | None,
    context: str,
) -> Any:
    """Invoke *operation* with retry logic when enabled."""

    max_attempts = max(1, max_retries if max_retries is not None else _DEFAULT_MAX_ATTEMPTS)
    backoff = backoff_seconds if backoff_seconds is not None else _DEFAULT_BACKOFF_SECONDS

    attempt = 0
    while True:
        attempt += 1
        try:
            return await operation()
        except Exception as exc:  # noqa: BLE001 - propagate original exception after retry evaluation
            if not (retry and attempt < max_attempts and _should_retry(exc)):
                raise

            delay = max(0.0, backoff * attempt)
            logger.warning(
                "authlete_api_retry: context=%s attempt=%s/%s delay=%.2fs error=%s",
                context,
                attempt,
                max_attempts,
                delay,
                str(exc),
            )
            await asyncio.sleep(delay)


async def _send_http_request(
    method: str, url: str, headers: dict[str, str], data: dict[str, Any] | None = None
) -> httpx.Response:
    """Send an HTTP request using httpx.AsyncClient."""

    async with httpx.AsyncClient() as client:
        method_upper = method.upper()
        if method_upper == "GET":
            return await client.get(url, headers=headers)
        if method_upper == "POST":
            return await client.post(url, headers=headers, json=data)
        if method_upper == "PUT":
            return await client.put(url, headers=headers, json=data)
        if method_upper == "DELETE":
            return await client.delete(url, headers=headers)
        raise ValueError(f"Unsupported HTTP method: {method}")


def _process_response(
    method: str,
    url: str,
    response: httpx.Response,
    *,
    idp: bool = False,
) -> dict[str, Any]:
    """Convert an httpx.Response into a structured result or raise."""

    target = f"{url} (IdP API)" if idp else url

    if response.status_code >= 400:
        error_detail = response.text
        try:
            error_json = response.json()
            if "resultMessage" in error_json:
                prefix = "Authlete IdP API Error" if idp else "Authlete API Error"
                error_detail = f"{prefix}: {error_json['resultMessage']}"
        except json.JSONDecodeError:
            pass

        log_request_response(
            logger,
            method,
            target,
            status_code=response.status_code,
            error=httpx.HTTPStatusError(error_detail, request=response.request, response=response),
        )
        raise httpx.HTTPStatusError(error_detail, request=response.request, response=response)

    if response.status_code == 204:
        message = "Service deleted successfully" if idp else "Operation completed successfully"
        result = {"success": True, "message": message}
        log_request_response(logger, method, target, response_data=result, status_code=response.status_code)
        return result

    try:
        result = response.json()
        log_request_response(logger, method, target, response_data=result, status_code=response.status_code)
        return result
    except json.JSONDecodeError:
        if 200 <= response.status_code < 300:
            result = {
                "success": True,
                "message": f"Operation completed with status {response.status_code}",
            }
        else:
            result = {"text": response.text, "status_code": response.status_code}
        log_request_response(logger, method, target, response_data=result, status_code=response.status_code)
        return result


async def make_authlete_request(
    method: str,
    endpoint: str,
    config: AuthleteConfig,
    data: dict[str, Any] | None = None,
    *,
    retry: bool = True,
    max_retries: int | None = None,
    backoff_seconds: float | None = None,
) -> dict[str, Any]:
    """Make a request to the Authlete API."""

    url = f"{config.base_url}/api/{endpoint}"

    headers = {"Authorization": f"Bearer {config.access_token}", "Content-Type": "application/json"}

    async def _operation() -> dict[str, Any]:
        log_request_response(logger, method, url, request_data=data)
        response = await _send_http_request(method, url, headers, data)
        return _process_response(method, url, response)

    return await _call_with_retry(
        _operation,
        retry=retry,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
        context=f"API {method} {endpoint}",
    )


async def make_authlete_request_with_dynamic_server(
    method: str,
    endpoint: str,
    access_token: str,
    data: dict[str, Any] | None = None,
    *,
    retry: bool = True,
    max_retries: int | None = None,
    backoff_seconds: float | None = None,
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

    config = AuthleteConfig(access_token=access_token, base_url=api_url)
    return await make_authlete_request(
        method,
        endpoint,
        config,
        data,
        retry=retry,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
    )


async def make_authlete_idp_request(
    endpoint: str,
    method: str = "GET",
    access_token: str | None = None,
    data: dict[str, Any] | None = None,
    config: AuthleteConfig | None = None,
    *,
    retry: bool = True,
    max_retries: int | None = None,
    backoff_seconds: float | None = None,
) -> dict[str, Any]:
    """Make a request to the Authlete IdP API."""
    from ..config import AUTHLETE_IDP_URL

    if config:
        base_url = config.idp_url
        token = config.access_token
    else:
        base_url = AUTHLETE_IDP_URL
        token = access_token

    url = f"{base_url}/api/{endpoint}"

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def _operation() -> dict[str, Any]:
        log_request_response(logger, method, f"{url} (IdP API)", request_data=data)
        response = await _send_http_request(method, url, headers, data)
        return _process_response(method, url, response, idp=True)

    return await _call_with_retry(
        _operation,
        retry=retry,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
        context=f"IdP {method} {endpoint}",
    )


async def make_authlete_request_with_retry(
    method: str,
    endpoint: str,
    config: AuthleteConfig,
    data: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Convenience wrapper that always enables retry behaviour."""

    return await make_authlete_request(method, endpoint, config, data, retry=True, **kwargs)


async def make_authlete_idp_request_with_retry(
    endpoint: str,
    method: str = "GET",
    access_token: str | None = None,
    data: dict[str, Any] | None = None,
    config: AuthleteConfig | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Convenience wrapper that always enables retry behaviour for IdP calls."""

    return await make_authlete_idp_request(
        endpoint,
        method=method,
        access_token=access_token,
        data=data,
        config=config,
        retry=True,
        **kwargs,
    )
