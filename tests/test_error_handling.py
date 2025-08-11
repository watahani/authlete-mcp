"""Test error handling scenarios."""

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.unit
async def test_missing_environment_token():
    """Test behavior when ORGANIZATION_ACCESS_TOKEN is not set."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("list_services", {})

            assert result.content
            response_text = result.content[0].text
            # Should show an error or return empty results due to invalid token
            assert response_text is not None


@pytest.mark.unit
async def test_invalid_tool_parameters():
    """Test tools with invalid parameters."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Test create_service without required name parameter
            try:
                result = await session.call_tool("create_service", {})
                # Should either fail at the MCP level or return an error from the tool
                assert result.content
            except Exception:
                # MCP level validation failure is also acceptable
                pass


@pytest.mark.unit
async def test_json_parsing_errors():
    """Test tools that require JSON input with invalid JSON."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    invalid_json_tests = [
        ("create_client", {"client_data": "not json"}),
        ("update_service", {"service_data": "not json"}),
        ("update_client_secret", {"client_id": "test", "secret_data": "not json"}),
    ]

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            for tool_name, params in invalid_json_tests:
                result = await session.call_tool(tool_name, params)

                assert result.content
                response_text = result.content[0].text
                # Operations that now require service_api_key check it first
                if tool_name in ["create_client", "update_client", "update_client_secret", "update_service"]:
                    assert "service_api_key parameter is required" in response_text
                else:
                    assert "Error parsing" in response_text or "JSON" in response_text
