"""Tests for generic Authlete API retry behaviour."""

import asyncio

import httpx
import pytest

from src.authlete_mcp.api.client import (
    AuthleteConfig,
    make_authlete_idp_request,
    make_authlete_request,
)


class DummyAsyncClient:
    """Minimal AsyncClient stub to control responses."""

    def __init__(self, responders):
        self._responders = responders
        self.calls = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: D401 - context manager protocol
        return False

    def _next(self, method: str, url: str) -> httpx.Response:
        if self.calls >= len(self._responders):
            raise AssertionError("No responder available for call")
        responder = self._responders[self.calls]
        self.calls += 1
        return responder(method, url)

    async def get(self, url, headers=None):  # noqa: D401 - httpx.AsyncClient compatibility
        return self._next("GET", url)

    async def post(self, url, headers=None, json=None):  # noqa: D401
        return self._next("POST", url)

    async def put(self, url, headers=None, json=None):  # noqa: D401
        return self._next("PUT", url)

    async def delete(self, url, headers=None):  # noqa: D401
        return self._next("DELETE", url)


def _response(
    status_code: int, method: str, url: str, *, text: str | None = None, json_body: dict | None = None
) -> httpx.Response:
    request = httpx.Request(method, url)
    if json_body is not None:
        return httpx.Response(status_code, request=request, json=json_body)
    return httpx.Response(status_code, request=request, text=text or "")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_make_authlete_request_retries_access_right_error(monkeypatch):
    """403 with access-right error should trigger retries until success."""

    url = "https://example.com/api/test/client/create"

    responders = [
        lambda method, target: _response(
            403,
            method,
            url,
            text="Authlete API Error: [A457101] (/client/create) Function requires access rights ([CREATE_CLIENT])",
        ),
        lambda method, target: _response(
            403,
            method,
            url,
            json_body={"resultMessage": "[A457101] Function requires access rights"},
        ),
        lambda method, target: _response(200, method, url, json_body={"clientId": "client-123"}),
    ]

    dummy_client = DummyAsyncClient(responders)
    monkeypatch.setattr(httpx, "AsyncClient", lambda: dummy_client)

    sleep_calls: list[float] = []

    async def fake_sleep(delay: float):
        sleep_calls.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    config = AuthleteConfig(access_token="token", base_url="https://example.com")
    result = await make_authlete_request("POST", "test/client/create", config, {"foo": "bar"})

    assert result["clientId"] == "client-123"
    assert dummy_client.calls == 3
    assert sleep_calls  # ensure retry wait executed


@pytest.mark.asyncio
@pytest.mark.unit
async def test_make_authlete_request_no_retry_on_other_error(monkeypatch):
    """Non-retryable errors should surface immediately."""

    url = "https://example.com/api/test"
    responders = [lambda method, target: _response(400, method, url, text="Bad request")]
    dummy_client = DummyAsyncClient(responders)
    monkeypatch.setattr(httpx, "AsyncClient", lambda: dummy_client)

    config = AuthleteConfig(access_token="token", base_url="https://example.com")

    with pytest.raises(httpx.HTTPStatusError):
        await make_authlete_request("GET", "test", config, retry=True)

    assert dummy_client.calls == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_make_authlete_request_respects_retry_flag(monkeypatch):
    """retry=False should avoid retry behaviour even for retryable errors."""

    url = "https://example.com/api/test"
    responders = [
        lambda method, target: _response(
            403,
            method,
            url,
            text="Authlete API Error: [A457101] Function requires access rights",
        )
    ]
    dummy_client = DummyAsyncClient(responders)
    monkeypatch.setattr(httpx, "AsyncClient", lambda: dummy_client)

    config = AuthleteConfig(access_token="token", base_url="https://example.com")

    with pytest.raises(httpx.HTTPStatusError):
        await make_authlete_request("POST", "test", config, retry=False)

    assert dummy_client.calls == 1


@pytest.mark.asyncio
@pytest.mark.unit
async def test_make_authlete_idp_request_retries(monkeypatch):
    """IdP requests use the same retry path."""

    url = "https://idp.example.com/api/service"
    responders = [
        lambda method, target: _response(
            500,
            method,
            url,
            text="Server error",
        ),
        lambda method, target: _response(200, method, url, json_body={"status": "ok"}),
    ]
    dummy_client = DummyAsyncClient(responders)
    monkeypatch.setattr(httpx, "AsyncClient", lambda: dummy_client)

    sleep_calls: list[float] = []

    async def fake_sleep(delay: float):
        sleep_calls.append(delay)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    result = await make_authlete_idp_request(
        "service",
        method="POST",
        access_token="token",
        data={"foo": "bar"},
    )

    assert result["status"] == "ok"
    assert dummy_client.calls == 2
    assert sleep_calls
