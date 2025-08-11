"""Test JOSE operations for Authlete MCP Server."""

import json
import os

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.integration
async def test_generate_jose():
    """Test generating JOSE without service_api_key."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    jose_data = {"payload": {"sub": "test_subject"}, "algorithm": "ES256"}

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("generate_jose", {"jose_data": json.dumps(jose_data)})

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_generate_jose_without_token():
    """Test generating JOSE without valid token."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={},  # No token
    )

    jose_data = {"payload": {"sub": "test_subject"}, "algorithm": "ES256"}

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "generate_jose", {"service_api_key": "", "jose_data": json.dumps(jose_data)}
            )

            assert result.content
            response_text = result.content[0].text
            assert "Error: service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_generate_jose_invalid_json():
    """Test generating JOSE with invalid JSON."""
    server_params = StdioServerParameters(command="uv", args=["run", "python", "main.py"], env={})

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "generate_jose", {"service_api_key": "test_service_key", "jose_data": "invalid json"}
            )

            assert result.content
            response_text = result.content[0].text
            assert "Error parsing JOSE data JSON" in response_text


@pytest.mark.integration
async def test_verify_jose():
    """Test verifying JOSE without service_api_key."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    # Sample JWT token for testing
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("verify_jose", {"jose_token": test_token})

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_verify_jose_without_token():
    """Test verifying JOSE without valid token."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={},  # No token
    )

    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("verify_jose", {"service_api_key": "", "jose_token": test_token})

            assert result.content
            response_text = result.content[0].text
            assert "Error: service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_verify_jose_missing_token():
    """Test verifying JOSE without jose_token parameter."""
    server_params = StdioServerParameters(command="uv", args=["run", "python", "main.py"], env={})

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("verify_jose", {"service_api_key": "test_service_key"})

            assert result.content
            response_text = result.content[0].text
            assert "jose_token parameter is required" in response_text
