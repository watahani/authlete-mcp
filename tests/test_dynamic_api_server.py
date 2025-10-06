"""Tests for dynamic API server selection functionality."""

import json
import os
from unittest.mock import AsyncMock, patch

import pytest

from src.authlete_mcp import config


@pytest.mark.asyncio
@pytest.mark.unit
async def test_api_server_state_management():
    """Test basic API server state management functions."""
    # Clear any existing state
    config.clear_current_api_server()

    # Test initial state
    assert config.get_current_api_server() is None
    assert config.get_api_server_url() is None
    assert config.get_api_server_id() is None

    # Test setting API server
    config.set_current_api_server(
        api_server_id=12345, api_server_url="https://api.example.com", description="Test API Server"
    )

    # Test state after setting
    current = config.get_current_api_server()
    assert current is not None
    assert current["id"] == 12345
    assert current["url"] == "https://api.example.com"
    assert current["description"] == "Test API Server"

    assert config.get_api_server_url() == "https://api.example.com"
    assert config.get_api_server_id() == 12345

    # Test clearing state
    config.clear_current_api_server()
    assert config.get_current_api_server() is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_auto_detect_api_server_from_url():
    """Test auto-detection of API server from AUTHLETE_API_URL."""
    # Mock the make_authlete_idp_request function
    mock_response = [
        {"id": 53285, "apiServerUrl": "https://jp.authlete.com", "description": "JP API Server"},
        {"id": 63294, "apiServerUrl": "https://eu.authlete.com", "description": "EU API Server"},
    ]

    with patch.dict(os.environ, {"ORGANIZATION_ACCESS_TOKEN": "test_token"}):
        with patch("src.authlete_mcp.config.AUTHLETE_API_URL", "https://jp.authlete.com"):
            with patch("src.authlete_mcp.api.client.make_authlete_idp_request", new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response

                result = await config.auto_detect_api_server_from_url()

                assert result is not None
                assert result["id"] == 53285
                assert result["url"] == "https://jp.authlete.com"
                assert result["description"] == "JP API Server"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_auto_detect_api_server_not_found():
    """Test auto-detection when API server URL is not found."""
    mock_response = [{"id": 53285, "apiServerUrl": "https://jp.authlete.com", "description": "JP API Server"}]

    with patch.dict(os.environ, {"ORGANIZATION_ACCESS_TOKEN": "test_token"}):
        # Directly patch the AUTHLETE_API_URL constant in the config module
        with patch("src.authlete_mcp.config.AUTHLETE_API_URL", "https://completely-different.example.com"):
            with patch("src.authlete_mcp.api.client.make_authlete_idp_request", new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response

                result = await config.auto_detect_api_server_from_url()

                assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
async def test_ensure_api_server_configured():
    """Test ensure_api_server_configured function."""
    # Clear any existing state
    config.clear_current_api_server()

    # Test when already configured
    config.set_current_api_server(12345, "https://api.example.com")
    result = await config.ensure_api_server_configured()
    assert result is None  # No error message when already configured

    # Clear state and test auto-detection
    config.clear_current_api_server()

    mock_response = [{"id": 53285, "apiServerUrl": "https://jp.authlete.com", "description": "JP API Server"}]

    with patch.dict(os.environ, {"ORGANIZATION_ACCESS_TOKEN": "test_token"}):
        with patch("src.authlete_mcp.config.AUTHLETE_API_URL", "https://jp.authlete.com"):
            with patch("src.authlete_mcp.api.client.make_authlete_idp_request", new_callable=AsyncMock) as mock_request:
                mock_request.return_value = mock_response

                result = await config.ensure_api_server_configured()

                assert result is None  # No error when auto-detection succeeds
                assert config.get_api_server_id() == 53285
                assert config.get_api_server_url() == "https://jp.authlete.com"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_ensure_api_server_configured_no_auto_detect():
    """Test ensure_api_server_configured when auto-detection fails."""
    config.clear_current_api_server()

    with patch.dict(os.environ, {"ORGANIZATION_ACCESS_TOKEN": "test_token"}):
        with patch("src.authlete_mcp.config.AUTHLETE_API_URL", "https://completely-different.example.com"):
            with patch("src.authlete_mcp.api.client.make_authlete_idp_request", new_callable=AsyncMock) as mock_request:
                mock_request.return_value = []  # No servers found

                result = await config.ensure_api_server_configured()

                assert result is not None
                assert "No API server is currently configured" in result
                assert "list_api_servers" in result


def test_check_deprecated_env_vars(caplog):
    """Test deprecated environment variable warning."""
    with patch.dict(os.environ, {"AUTHLETE_API_SERVER_ID": "12345"}):
        config.check_deprecated_env_vars()

        assert "deprecated" in caplog.text
        assert "AUTHLETE_API_SERVER_ID" in caplog.text


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_api_servers_function():
    """Test list_api_servers function directly."""
    from src.authlete_mcp.tools.utility_tools import list_api_servers

    mock_response = [
        {"id": 53285, "apiServerUrl": "https://jp.authlete.com", "description": "JP API Server"},
        {"id": 63294, "apiServerUrl": "https://eu.authlete.com", "description": "EU API Server"},
    ]

    with patch.dict(os.environ, {"ORGANIZATION_ACCESS_TOKEN": "test_token"}):
        with patch(
            "src.authlete_mcp.tools.utility_tools.make_authlete_idp_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await list_api_servers()

            assert "Error:" not in result
            response_data = json.loads(result)
            assert len(response_data) == 2
            assert response_data[0]["id"] == 53285
            assert response_data[1]["id"] == 63294


@pytest.mark.asyncio
@pytest.mark.unit
async def test_set_api_server_function():
    """Test set_api_server function directly."""
    from src.authlete_mcp.tools.utility_tools import set_api_server

    mock_response = [{"id": 53285, "apiServerUrl": "https://jp.authlete.com", "description": "JP API Server"}]

    with patch.dict(os.environ, {"ORGANIZATION_ACCESS_TOKEN": "test_token"}):
        with patch("src.authlete_mcp.api.client.make_authlete_idp_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            # Clear any existing state
            config.clear_current_api_server()

            result = await set_api_server("53285")

            assert "Error:" not in result
            response_data = json.loads(result)
            assert response_data["message"] == "API server set successfully"
            assert response_data["apiServerId"] == 53285
            assert response_data["apiServerUrl"] == "https://jp.authlete.com"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_set_api_server_invalid_id():
    """Test set_api_server with invalid API server ID."""
    from src.authlete_mcp.tools.utility_tools import set_api_server

    mock_response = [{"id": 53285, "apiServerUrl": "https://jp.authlete.com", "description": "JP API Server"}]

    with patch.dict(os.environ, {"ORGANIZATION_ACCESS_TOKEN": "test_token"}):
        with patch("src.authlete_mcp.api.client.make_authlete_idp_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await set_api_server("99999")

            assert "API server with ID '99999' not found" in result
            assert "Available API server IDs: 53285" in result


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_current_api_server_info_function():
    """Test get_current_api_server_info function directly."""
    from src.authlete_mcp.tools.utility_tools import get_current_api_server_info

    # Test when no API server is configured
    config.clear_current_api_server()
    result = await get_current_api_server_info()

    assert "No API server is currently configured" in result

    # Test when API server is configured
    config.set_current_api_server(12345, "https://api.example.com", "Test Server")
    result = await get_current_api_server_info()

    response_data = json.loads(result)
    assert response_data["message"] == "Current API server configuration"
    assert response_data["apiServerId"] == 12345
    assert response_data["apiServerUrl"] == "https://api.example.com"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_create_service_with_configured_server():
    """Test create_service function with pre-configured API server."""
    from src.authlete_mcp.tools.service_tools import create_service

    # Pre-configure API server
    config.set_current_api_server(53285, "https://jp.authlete.com", "JP API Server")

    # Mock service creation response
    mock_service_response = {"service": {"number": 123456, "serviceName": "Test Service", "apiKey": 987654321}}

    with patch.dict(os.environ, {"ORGANIZATION_ACCESS_TOKEN": "test_token", "ORGANIZATION_ID": "12345"}):
        with patch(
            "src.authlete_mcp.tools.service_tools.make_authlete_idp_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_service_response

            result = await create_service("Test Service", "Test Description")

            assert "Error:" not in result
            response_data = json.loads(result)
            assert response_data["service"]["serviceName"] == "Test Service"
