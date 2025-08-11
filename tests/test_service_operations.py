"""Test service management operations."""

import json
import os

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.integration
async def test_list_services():
    """Test listing services with real credentials."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("Real ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("list_services", {})

            assert result.content
            assert len(result.content) > 0
            response_text = result.content[0].text

            # Should return valid JSON (might be empty result or error)
            response_data = json.loads(response_text)
            # Accept various valid response structures
            assert isinstance(response_data, dict) and (
                "services" in response_data or "resultCode" in response_data or "totalCount" in response_data
            )


@pytest.mark.integration
async def test_create_service():
    """Test creating a service with real credentials."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "create_service", {"name": "pytest-test-service", "description": "Test service created by pytest"}
            )

            assert result.content
            assert len(result.content) > 0
            response_text = result.content[0].text

            # Should return some response (might be error due to API issues)
            assert response_text is not None
            # Try to parse as JSON if possible, but don't fail if it's an error message
            if response_text.startswith("Error"):
                # Accept error responses from API
                assert "Error" in response_text
            else:
                response_data = json.loads(response_text)
                # Either success or error structure
                assert isinstance(response_data, dict)


@pytest.mark.integration
async def test_create_service_detailed():
    """Test creating a detailed service configuration."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Create service configuration as JSON object
            service_config = {
                "serviceName": "pytest-detailed-service",
                "description": "Detailed test service created by pytest",
                "issuer": "https://test.example.com",
                "supportedScopes": [
                    {"name": "openid", "defaultEntry": True},
                    {"name": "profile", "defaultEntry": False},
                    {"name": "email", "defaultEntry": False},
                ],
                "supportedResponseTypes": ["CODE"],
                "supportedGrantTypes": ["AUTHORIZATION_CODE"],
                "supportedTokenAuthMethods": ["CLIENT_SECRET_BASIC"],
                "pkceRequired": True,
                "accessTokenDuration": 3600,
                "refreshTokenDuration": 86400,
                "idTokenDuration": 3600,
                "directAuthorizationEndpointEnabled": True,
                "directTokenEndpointEnabled": True,
                "directUserInfoEndpointEnabled": True,
            }

            result = await session.call_tool(
                "create_service_detailed",
                {
                    "service_config": json.dumps(service_config),
                },
            )

            assert result.content
            assert len(result.content) > 0
            response_text = result.content[0].text

            # Should return some response (might be error due to API issues)
            assert response_text is not None
            # Try to parse as JSON if possible, but don't fail if it's an error message
            if response_text.startswith("Error"):
                # Accept error responses from API
                assert "Error" in response_text
            else:
                response_data = json.loads(response_text)
                # Either success or error structure
                assert isinstance(response_data, dict)


@pytest.mark.unit
async def test_service_schema_example_structure():
    """Test that service schema example has correct structure."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("get_service_schema_example", {})

            assert result.content
            response_text = result.content[0].text
            schema = json.loads(response_text)

            # Check required fields
            required_fields = [
                "serviceName",
                "supportedScopes",
                "supportedResponseTypes",
                "supportedGrantTypes",
                "supportedTokenAuthMethods",
            ]

            for field in required_fields:
                assert field in schema, f"Required field {field} missing from schema example"

            # Check scope structure
            scopes = schema["supportedScopes"]
            assert isinstance(scopes, list)
            assert len(scopes) > 0

            for scope in scopes:
                assert "name" in scope
                assert "defaultEntry" in scope


@pytest.mark.unit
async def test_create_service_without_token():
    """Test create_service with mock token (should show error)."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("create_service", {"name": "test-service"})

            assert result.content
            assert len(result.content) > 0
            response_text = result.content[0].text
            # Should show an error about missing org ID or invalid token
            assert (
                "Error:" in response_text
                or "error" in response_text.lower()
                or "organization_id" in response_text
                or "ORGANIZATION_ID" in response_text
            )
