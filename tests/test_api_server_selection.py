import importlib
import json
from typing import Any

import pytest

ENV_KEYS = [
    "AUTHLETE_API_SERVER_ID",
    "AUTHLETE_API_URL",
    "AUTHLETE_BASE_URL",
    "ORGANIZATION_ACCESS_TOKEN",
    "ORGANIZATION_ID",
]


def reload_modules(monkeypatch: pytest.MonkeyPatch, env: dict[str, str | None]):
    """Reload config and tool modules with the specified environment overrides."""
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    for key, value in env.items():
        if value is not None:
            monkeypatch.setenv(key, value)

    import src.authlete_mcp.config as config_module
    import src.authlete_mcp.tools.service_tools as service_module
    import src.authlete_mcp.tools.utility_tools as utility_module

    config = importlib.reload(config_module)
    utility_tools = importlib.reload(utility_module)
    service_tools = importlib.reload(service_module)
    config.clear_current_api_server()
    return config, utility_tools, service_tools


@pytest.mark.asyncio
async def test_env_default_api_server_used(monkeypatch: pytest.MonkeyPatch):
    config, _, _ = reload_modules(
        monkeypatch,
        {
            "AUTHLETE_API_SERVER_ID": "12345",
            "AUTHLETE_API_URL": "https://env.example",
            "ORGANIZATION_ACCESS_TOKEN": "token",
            "ORGANIZATION_ID": "999",
        },
    )

    import src.authlete_mcp.api.client as api_client

    calls: list[tuple[str, str, Any]] = []

    async def fake_make_authlete_idp_request(
        endpoint: str,
        method: str = "GET",
        access_token: str | None = None,
        data: dict[str, Any] | None = None,
        config: Any = None,
    ) -> Any:
        calls.append((endpoint, method, data))
        if endpoint == "apiserver" and method == "GET":
            return [
                {
                    "id": 12345,
                    "apiServerUrl": "https://env.example",
                }
            ]
        raise AssertionError(f"Unexpected call: {endpoint} {method}")

    monkeypatch.setattr(api_client, "make_authlete_idp_request", fake_make_authlete_idp_request)

    api_server_id, error = await config.ensure_api_server_ready()

    assert error is None
    assert api_server_id == 12345
    current = config.get_current_api_server()
    assert current == {"id": 12345, "url": "https://env.example", "description": ""}
    assert calls and calls[0][0] == "apiserver"


@pytest.mark.asyncio
async def test_env_base_url_fallback(monkeypatch: pytest.MonkeyPatch):
    config, _, _ = reload_modules(
        monkeypatch,
        {
            "AUTHLETE_BASE_URL": "https://env.example",
            "ORGANIZATION_ACCESS_TOKEN": "token",
            "ORGANIZATION_ID": "999",
        },
    )

    import src.authlete_mcp.api.client as api_client

    async def fake_make_authlete_idp_request(
        endpoint: str,
        method: str = "GET",
        access_token: str | None = None,
        data: dict[str, Any] | None = None,
        config: Any = None,
    ) -> Any:
        assert endpoint == "apiserver"
        return [{"id": 777, "apiServerUrl": "https://env.example"}]

    monkeypatch.setattr(api_client, "make_authlete_idp_request", fake_make_authlete_idp_request)

    api_server_id, error = await config.ensure_api_server_ready()

    assert error is None
    assert api_server_id == 777
    assert config.get_current_api_server()["url"] == "https://env.example"


@pytest.mark.asyncio
async def test_set_api_server_overrides_environment(monkeypatch: pytest.MonkeyPatch):
    config, utility_tools, _ = reload_modules(
        monkeypatch,
        {
            "AUTHLETE_API_SERVER_ID": "12345",
            "AUTHLETE_API_URL": "https://env.example",
            "ORGANIZATION_ACCESS_TOKEN": "token",
            "ORGANIZATION_ID": "999",
        },
    )

    import src.authlete_mcp.api.client as api_client

    async def fake_make_authlete_idp_request(
        endpoint: str,
        method: str = "GET",
        access_token: str | None = None,
        data: dict[str, Any] | None = None,
        config: Any = None,
    ) -> Any:
        if endpoint == "apiserver" and method == "GET":
            return [
                {"id": 12345, "apiServerUrl": "https://env.example"},
                {"id": 67890, "apiServerUrl": "https://override.example"},
            ]
        raise AssertionError(f"Unexpected call: {endpoint} {method}")

    monkeypatch.setattr(api_client, "make_authlete_idp_request", fake_make_authlete_idp_request)

    result = await utility_tools.set_api_server("67890")
    payload = json.loads(result)
    assert payload["apiServerId"] == 67890
    assert payload["apiServerUrl"] == "https://override.example"

    api_server_id, error = await config.ensure_api_server_ready()
    assert error is None
    assert api_server_id == 67890
    current = config.get_current_api_server()
    assert current == {"id": 67890, "url": "https://override.example", "description": ""}


@pytest.mark.asyncio
async def test_tools_fail_without_environment_or_override(monkeypatch: pytest.MonkeyPatch):
    config, _, service_tools = reload_modules(
        monkeypatch,
        {
            "AUTHLETE_API_SERVER_ID": "",
            "AUTHLETE_API_URL": "",
            "ORGANIZATION_ACCESS_TOKEN": "token",
            "ORGANIZATION_ID": "999",
        },
    )

    error_message = (
        "No API server is currently configured. Please use the 'list_api_servers' tool to see available options, "
        "then use 'set_api_server' to configure your preferred API server."
    )

    async def fake_ensure_api_server_configured() -> str:
        return error_message

    monkeypatch.setattr(config, "ensure_api_server_configured", fake_ensure_api_server_configured)

    async def fail_make_authlete_idp_request(*args, **kwargs):  # pragma: no cover - should not be called
        raise AssertionError("IDP request should not be invoked when configuration fails")

    monkeypatch.setattr(service_tools, "make_authlete_idp_request", fail_make_authlete_idp_request)

    create_response = await service_tools.create_service("pytest-service", "desc")
    assert create_response == error_message

    detailed_response = await service_tools.create_service_detailed("{}")
    assert detailed_response == error_message

    delete_response = await service_tools.delete_service("12345")
    assert delete_response == error_message


@pytest.mark.asyncio
async def test_tools_succeed_after_setting_api_server(monkeypatch: pytest.MonkeyPatch):
    config, utility_tools, service_tools = reload_modules(
        monkeypatch,
        {
            "AUTHLETE_API_SERVER_ID": "",
            "AUTHLETE_API_URL": "",
            "ORGANIZATION_ACCESS_TOKEN": "token",
            "ORGANIZATION_ID": "999",
        },
    )

    import src.authlete_mcp.api.client as api_client

    async def fake_make_authlete_idp_request_config(
        endpoint: str,
        method: str = "GET",
        access_token: str | None = None,
        data: dict[str, Any] | None = None,
        config: Any = None,
    ) -> Any:
        if endpoint == "apiserver" and method == "GET":
            return [{"id": 777, "apiServerUrl": "https://manual.example"}]
        raise AssertionError(f"Unexpected config call: {endpoint} {method}")

    monkeypatch.setattr(api_client, "make_authlete_idp_request", fake_make_authlete_idp_request_config)

    service_calls: list[tuple[str, str, dict[str, Any] | None]] = []

    async def fake_make_authlete_idp_request_service(
        endpoint: str,
        method: str = "GET",
        access_token: str | None = None,
        data: dict[str, Any] | None = None,
        config: Any = None,
    ) -> Any:
        service_calls.append((endpoint, method, data))
        if endpoint == "service" and method == "POST":
            assert data is not None
            assert data["apiServerId"] == 777
            return {"apiKey": 555, "message": "Service created"}
        if endpoint == "service/remove" and method == "POST":
            assert data is not None
            assert data["apiServerId"] == 777
            return {"message": "Service deleted successfully"}
        raise AssertionError(f"Unexpected service call: {endpoint} {method}")

    monkeypatch.setattr(service_tools, "make_authlete_idp_request", fake_make_authlete_idp_request_service)

    result = await utility_tools.set_api_server("777")
    payload = json.loads(result)
    assert payload["apiServerId"] == 777

    api_server_id, error = await config.ensure_api_server_ready()
    assert error is None
    assert api_server_id == 777

    create_response = await service_tools.create_service("pytest-service", "desc")
    create_payload = json.loads(create_response)
    assert create_payload["apiKey"] == 555

    detailed_body = json.dumps({"serviceName": "pytest-detailed"})
    detailed_response = await service_tools.create_service_detailed(detailed_body, apiServerId="")
    detailed_payload = json.loads(detailed_response)
    assert detailed_payload["apiKey"] == 555

    delete_response = await service_tools.delete_service("12345")
    delete_payload = json.loads(delete_response)
    assert delete_payload["message"] == "Service deleted successfully"

    assert {call[0] for call in service_calls} == {"service", "service/remove"}
