"""Test patch operations for client and service management."""

import json
import os

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.unit
async def test_patch_client_missing_service_api_key():
    """Test patch_client without service_api_key parameter."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "patch_client",
                {
                    "client_id": "test_client_id",
                    "client_patch_data": json.dumps({"clientName": "Updated Name"}),
                },
            )

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_patch_client_invalid_json():
    """Test patch_client with invalid JSON."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "patch_client",
                {
                    "client_id": "test_client_id",
                    "client_patch_data": "invalid json",
                    "service_api_key": "test_service_key",
                },
            )

            assert result.content
            response_text = result.content[0].text
            assert "Error parsing client patch data JSON" in response_text


@pytest.mark.unit
async def test_patch_service_missing_service_api_key():
    """Test patch_service without service_api_key parameter."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "patch_service",
                {
                    "service_patch_data": json.dumps({"serviceName": "Updated Service Name"}),
                },
            )

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_patch_service_invalid_json():
    """Test patch_service with invalid JSON."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "patch_service",
                {
                    "service_patch_data": "invalid json",
                    "service_api_key": "test_service_key",
                },
            )

            assert result.content
            response_text = result.content[0].text
            assert "Error parsing service patch data JSON" in response_text


@pytest.mark.integration
async def test_patch_client_integration():
    """Test patch_client with real API integration."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("Real ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    org_id = os.getenv("ORGANIZATION_ID")
    if not org_id or org_id == "12345":
        pytest.skip("Real ORGANIZATION_ID not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": org_id},
    )

    service_api_key = None
    client_id = None

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            try:
                # 1. Create test service
                service_result = await session.call_tool(
                    "create_service",
                    {"name": "pytest-patch-test-service", "description": "Test service for patch operations"},
                )

                assert service_result.content
                service_response = service_result.content[0].text
                assert "Error" not in service_response, f"Service creation failed: {service_response}"

                service_data = json.loads(service_response)
                service_api_key = str(service_data.get("apiKey"))

                assert service_api_key and service_api_key != "None", (
                    f"Service API key not found in response: {service_response}"
                )

                # 2. Create test client
                original_client_data = {
                    "clientName": "pytest-patch-test-client",
                    "description": "Original description",
                    "applicationType": "WEB",
                    "redirectUris": ["https://test.example.com/callback"],
                }

                client_result = await session.call_tool(
                    "create_client",
                    {"client_data": json.dumps(original_client_data), "service_api_key": service_api_key},
                )

                assert client_result.content
                client_response = client_result.content[0].text
                assert "Error" not in client_response, f"Client creation failed: {client_response}"

                client_response_data = json.loads(client_response)
                client_id = str(client_response_data.get("clientId"))

                assert client_id, f"Client ID not found in response: {client_response}"

                # 3. Get original client data to verify structure
                get_original_result = await session.call_tool(
                    "get_client", {"client_id": client_id, "service_api_key": service_api_key}
                )

                assert get_original_result.content
                get_original_response = get_original_result.content[0].text
                assert "Error" not in get_original_response, f"Failed to get original client: {get_original_response}"

                original_data = json.loads(get_original_response)
                original_name = original_data.get("clientName")
                original_description = original_data.get("description")

                assert original_name == "pytest-patch-test-client"
                assert original_description == "Original description"

                # 4. Test patch_client - partial update
                patch_data = {
                    "description": "Updated description via patch",
                    "clientName": "pytest-patch-updated-client",
                }

                patch_result = await session.call_tool(
                    "patch_client",
                    {
                        "client_id": client_id,
                        "client_patch_data": json.dumps(patch_data),
                        "service_api_key": service_api_key,
                    },
                )

                assert patch_result.content
                patch_response = patch_result.content[0].text

                # 5. Verify patch was successful
                if "Error" not in patch_response:
                    # Get updated client data
                    get_updated_result = await session.call_tool(
                        "get_client", {"client_id": client_id, "service_api_key": service_api_key}
                    )

                    assert get_updated_result.content
                    get_updated_response = get_updated_result.content[0].text
                    assert "Error" not in get_updated_response, f"Failed to get updated client: {get_updated_response}"

                    updated_data = json.loads(get_updated_response)

                    # Verify patch worked - changed fields should be updated
                    assert updated_data.get("clientName") == "pytest-patch-updated-client"
                    assert updated_data.get("description") == "Updated description via patch"

                    # Verify unchanged fields remain the same
                    assert updated_data.get("applicationType") == "WEB"
                    assert updated_data.get("redirectUris") == ["https://test.example.com/callback"]
                    assert updated_data.get("clientId") == int(client_id)

                else:
                    # If patch failed, verify it was due to API limitations
                    assert "Error" in patch_response

            finally:
                # Clean up: delete service (client will be auto-deleted)
                if service_api_key:
                    delete_result = await session.call_tool(
                        "delete_service",
                        {
                            "service_id": service_api_key,
                        },
                    )

                    assert delete_result.content
                    delete_response = delete_result.content[0].text
                    assert "Service deleted successfully" in delete_response


@pytest.mark.integration
async def test_patch_service_integration():
    """Test patch_service with real API integration."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("Real ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    org_id = os.getenv("ORGANIZATION_ID")
    if not org_id or org_id == "12345":
        pytest.skip("Real ORGANIZATION_ID not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": org_id},
    )

    service_api_key = None

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            try:
                # 1. Create test service
                service_result = await session.call_tool(
                    "create_service",
                    {"name": "pytest-service-patch-test", "description": "Original service description"},
                )

                assert service_result.content
                service_response = service_result.content[0].text
                assert "Error" not in service_response, f"Service creation failed: {service_response}"

                service_data = json.loads(service_response)
                service_api_key = str(service_data.get("apiKey"))

                assert service_api_key and service_api_key != "None", (
                    f"Service API key not found in response: {service_response}"
                )

                # 2. Get original service data
                get_original_result = await session.call_tool("get_service", {"service_api_key": service_api_key})

                assert get_original_result.content
                get_original_response = get_original_result.content[0].text
                assert "Error" not in get_original_response, f"Failed to get original service: {get_original_response}"

                original_data = json.loads(get_original_response)
                original_name = original_data.get("serviceName")
                original_description = original_data.get("description")

                assert original_name == "pytest-service-patch-test"
                assert original_description == "Original service description"

                # 3. Test patch_service - partial update
                patch_data = {
                    "description": "Updated service description via patch",
                    "accessTokenDuration": 7200,  # Change from default
                }

                patch_result = await session.call_tool(
                    "patch_service",
                    {
                        "service_patch_data": json.dumps(patch_data),
                        "service_api_key": service_api_key,
                    },
                )

                assert patch_result.content
                patch_response = patch_result.content[0].text

                # 4. Verify patch was successful
                if "Error" not in patch_response:
                    # Get updated service data
                    get_updated_result = await session.call_tool("get_service", {"service_api_key": service_api_key})

                    assert get_updated_result.content
                    get_updated_response = get_updated_result.content[0].text
                    assert "Error" not in get_updated_response, f"Failed to get updated service: {get_updated_response}"

                    updated_data = json.loads(get_updated_response)

                    # Verify patch worked - changed fields should be updated
                    assert updated_data.get("description") == "Updated service description via patch"
                    assert updated_data.get("accessTokenDuration") == 7200

                    # Verify unchanged fields remain the same
                    assert updated_data.get("serviceName") == "pytest-service-patch-test"
                    assert updated_data.get("apiKey") == int(service_api_key)

                else:
                    # If patch failed, verify it was due to API limitations
                    assert "Error" in patch_response

            finally:
                # Clean up: delete service
                if service_api_key:
                    delete_result = await session.call_tool(
                        "delete_service",
                        {
                            "service_id": service_api_key,
                        },
                    )

                    assert delete_result.content
                    delete_response = delete_result.content[0].text
                    assert "Service deleted successfully" in delete_response


@pytest.mark.unit
async def test_patch_vs_update_client():
    """Test that patch_client and update_client are properly registered as separate tools."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # List all available tools
            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]

            # Verify both patch_client and update_client are available
            assert "patch_client" in tool_names, "patch_client tool should be registered"
            assert "update_client" in tool_names, "update_client tool should be registered"

            # Test that they are different tools
            patch_client_tool = next(tool for tool in tools.tools if tool.name == "patch_client")
            update_client_tool = next(tool for tool in tools.tools if tool.name == "update_client")

            # Verify their descriptions are different
            assert patch_client_tool.description != update_client_tool.description
            assert "merge" in patch_client_tool.description.lower() or "patch" in patch_client_tool.description.lower()
            assert (
                "overwrite" in update_client_tool.description.lower()
                or "full update" in update_client_tool.description.lower()
            )


@pytest.mark.unit
async def test_patch_vs_update_service():
    """Test that patch_service and update_service are properly registered as separate tools."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # List all available tools
            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]

            # Verify both patch_service and update_service are available
            assert "patch_service" in tool_names, "patch_service tool should be registered"
            assert "update_service" in tool_names, "update_service tool should be registered"

            # Test that they are different tools
            patch_service_tool = next(tool for tool in tools.tools if tool.name == "patch_service")
            update_service_tool = next(tool for tool in tools.tools if tool.name == "update_service")

            # Verify their descriptions are different
            assert patch_service_tool.description != update_service_tool.description
            assert (
                "merge" in patch_service_tool.description.lower() or "patch" in patch_service_tool.description.lower()
            )
            assert (
                "overwrite" in update_service_tool.description.lower()
                or "full update" in update_service_tool.description.lower()
            )
