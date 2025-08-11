"""Test token management operations for Authlete MCP Server."""

import json
import os

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.integration
async def test_list_issued_tokens():
    """Test listing issued tokens without service_api_key."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("list_issued_tokens", {})

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_list_issued_tokens_without_token():
    """Test listing issued tokens without valid token."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={},  # No token
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("list_issued_tokens", {"service_api_key": ""})

            assert result.content
            response_text = result.content[0].text
            assert "Error: service_api_key parameter is required" in response_text


@pytest.mark.integration
async def test_create_access_token():
    """Test creating access token without service_api_key."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    token_data = {"subject": "test_subject", "scopes": ["openid", "profile"]}

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("create_access_token", {"token_data": json.dumps(token_data)})

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_create_access_token_invalid_json():
    """Test creating access token with invalid JSON."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={},  # No token
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "create_access_token", {"service_api_key": "test_service_key", "token_data": "invalid json"}
            )

            assert result.content
            response_text = result.content[0].text
            assert "Error parsing token data JSON" in response_text


@pytest.mark.integration
async def test_update_access_token():
    """Test updating access token without service_api_key."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("update_access_token", {"access_token": "test_token"})

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_update_access_token_missing_params():
    """Test updating access token with missing parameters."""
    server_params = StdioServerParameters(command="uv", args=["run", "python", "main.py"], env={})

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Missing access_token
            result = await session.call_tool(
                "update_access_token", {"service_api_key": "test_service_key", "token_data": "{}"}
            )

            assert result.content
            response_text = result.content[0].text
            assert "access_token parameter is required" in response_text


@pytest.mark.integration
async def test_revoke_access_token():
    """Test revoking access token without service_api_key."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("revoke_access_token", {"access_token": "test_token"})

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.integration
async def test_delete_access_token():
    """Test deleting access token without service_api_key."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("delete_access_token", {"access_token": "test_token"})

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text
