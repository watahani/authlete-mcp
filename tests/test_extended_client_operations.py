"""Test extended client management operations for Authlete MCP Server."""

import json
import os

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.integration
async def test_get_authorized_applications():
    """Test getting authorized applications without service_api_key."""
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

            result = await session.call_tool("get_authorized_applications", {"subject": "test_subject"})

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_get_authorized_applications_missing_subject():
    """Test getting authorized applications without subject."""
    server_params = StdioServerParameters(command="uv", args=["run", "python", "main.py"], env={})

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("get_authorized_applications", {"service_api_key": "test_service_key"})

            assert result.content
            response_text = result.content[0].text
            assert "subject parameter is required" in response_text


@pytest.mark.integration
async def test_update_client_tokens():
    """Test updating client tokens without service_api_key."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    token_data = {"scopes": ["openid", "profile"]}

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "update_client_tokens",
                {"subject": "test_subject", "client_id": "test_client_id", "token_data": json.dumps(token_data)},
            )

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_update_client_tokens_missing_params():
    """Test updating client tokens with missing parameters."""
    server_params = StdioServerParameters(command="uv", args=["run", "python", "main.py"], env={})

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "update_client_tokens",
                {
                    "service_api_key": "test_service_key",
                    "subject": "test_subject",
                    # Missing client_id
                },
            )

            assert result.content
            response_text = result.content[0].text
            assert "subject and client_id parameters are required" in response_text


@pytest.mark.integration
async def test_delete_client_tokens():
    """Test deleting client tokens without service_api_key."""
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

            result = await session.call_tool(
                "delete_client_tokens", {"subject": "test_subject", "client_id": "test_client_id"}
            )

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.integration
async def test_get_granted_scopes():
    """Test getting granted scopes without service_api_key."""
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

            result = await session.call_tool(
                "get_granted_scopes", {"subject": "test_subject", "client_id": "test_client_id"}
            )

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.integration
async def test_delete_granted_scopes():
    """Test deleting granted scopes without service_api_key."""
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

            result = await session.call_tool(
                "delete_granted_scopes", {"subject": "test_subject", "client_id": "test_client_id"}
            )

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.integration
async def test_get_requestable_scopes():
    """Test getting requestable scopes without service_api_key."""
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

            result = await session.call_tool("get_requestable_scopes", {"client_id": "test_client_id"})

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_get_requestable_scopes_missing_client_id():
    """Test getting requestable scopes without client_id."""
    server_params = StdioServerParameters(command="uv", args=["run", "python", "main.py"], env={})

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("get_requestable_scopes", {"service_api_key": "test_service_key"})

            assert result.content
            response_text = result.content[0].text
            assert "client_id parameter is required" in response_text


@pytest.mark.integration
async def test_update_requestable_scopes():
    """Test updating requestable scopes without service_api_key."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    scopes_data = {"scopes": ["openid", "profile", "email"]}

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "update_requestable_scopes", {"client_id": "test_client_id", "scopes_data": json.dumps(scopes_data)}
            )

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_update_requestable_scopes_invalid_json():
    """Test updating requestable scopes with invalid JSON."""
    server_params = StdioServerParameters(command="uv", args=["run", "python", "main.py"], env={})

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "update_requestable_scopes",
                {"service_api_key": "test_service_key", "client_id": "test_client_id", "scopes_data": "invalid json"},
            )

            assert result.content
            response_text = result.content[0].text
            assert "Error parsing scopes data JSON" in response_text


@pytest.mark.integration
async def test_delete_requestable_scopes():
    """Test deleting requestable scopes without service_api_key."""
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

            result = await session.call_tool("delete_requestable_scopes", {"client_id": "test_client_id"})

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text
