"""Simple MCP connection test without complex fixtures."""

import json

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.unit
async def test_basic_connection():
    """Test basic MCP server connection."""
    server_params = StdioServerParameters(
        command="uv", args=["run", "python", "main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize session
            result = await session.initialize()
            assert result.serverInfo.name == "Authlete Management and API Search Server"

            # List tools
            tools = await session.list_tools()
            assert len(tools.tools) > 0

            tool_names = [tool.name for tool in tools.tools]
            assert "list_services" in tool_names
            assert "create_service" in tool_names


@pytest.mark.unit
async def test_schema_example():
    """Test get_service_schema_example tool."""
    server_params = StdioServerParameters(
        command="uv", args=["run", "python", "main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Call schema example tool
            result = await session.call_tool("get_service_schema_example", {})
            assert result.content

            response_text = result.content[0].text
            schema = json.loads(response_text)

            # Check required fields
            assert "serviceName" in schema
            assert "supportedScopes" in schema
            assert isinstance(schema["supportedScopes"], list)


@pytest.mark.unit
async def test_error_handling():
    """Test error handling with invalid parameters."""
    server_params = StdioServerParameters(
        command="uv", args=["run", "python", "main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Test with invalid JSON
            result = await session.call_tool("create_client", {"client_data": "invalid json"})
            assert result.content

            response_text = result.content[0].text
            # Client operations now check service_api_key first
            assert "service_api_key parameter is required" in response_text

            # Test service operation (should get API error with mock token)
            result = await session.call_tool("list_services", {})
            assert result.content
            # Should get some response (error or empty result)
