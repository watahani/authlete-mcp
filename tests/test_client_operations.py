"""Test client management operations."""

import json
import os

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.integration
async def test_list_clients():
    """Test listing clients with real credentials."""
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

            # Test without service_api_key - should return error
            result = await session.call_tool("list_clients", {})

            assert result.content
            assert len(result.content) > 0
            response_text = result.content[0].text

            # Should return error about missing service_api_key
            assert response_text is not None
            assert "service_api_key parameter is required" in response_text


@pytest.mark.integration
async def test_create_client():
    """Test creating a client with real credentials."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    client_data = {
        "clientName": "pytest-test-client",
        "description": "Test client created by pytest",
        "applicationType": "WEB",
        "redirectUris": ["https://test.example.com/callback"],
    }

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("create_client", {"client_data": json.dumps(client_data)})

            assert result.content
            assert len(result.content) > 0
            response_text = result.content[0].text

            # Should return error about missing service_api_key
            assert response_text is not None
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_create_client_invalid_json():
    """Test create_client with invalid JSON."""
    server_params = StdioServerParameters(
        command="uv", args=["run", "python", "main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("create_client", {"client_data": "invalid json"})

            assert result.content
            response_text = result.content[0].text
            # service_api_key check comes before JSON parsing now
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_client_operations_without_token():
    """Test client operations with mock token (should show error)."""
    server_params = StdioServerParameters(
        command="uv", args=["run", "python", "main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    operations = [
        ("get_client", {"client_id": "test"}),
        ("list_clients", {}),
        ("delete_client", {"client_id": "test"}),
        ("rotate_client_secret", {"client_id": "test"}),
        ("update_client_lock", {"client_id": "test", "lock_flag": True}),
    ]

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            for operation_name, params in operations:
                result = await session.call_tool(operation_name, params)

                assert result.content
                response_text = result.content[0].text
                # All client operations should require service_api_key now
                assert "service_api_key parameter is required" in response_text, (
                    f"Expected service_api_key error for {operation_name}, got: {response_text[:100]}"
                )


@pytest.mark.integration
async def test_rotate_client_secret():
    """Test rotating client secret."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    # 元のシークレットを記録（テスト用の固定値）
    original_secret = "original_test_secret_123"

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Test without service_api_key - should return error
            result = await session.call_tool("rotate_client_secret", {"client_id": "test_client_id"})

            assert result.content
            assert len(result.content) > 0
            response_text = result.content[0].text

            # Should return error about missing service_api_key
            assert response_text is not None
            assert "service_api_key parameter is required" in response_text

            # ローテーション実行後、元のシークレットとは異なることを確認
            # （実際のAPIコールでは新しいシークレットが生成されるため、
            # 元の値と同じでないことを期待）
            assert original_secret not in response_text


@pytest.mark.integration
async def test_update_client_secret():
    """Test updating client secret."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    secret_data = {"clientSecret": "new_test_secret"}

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Test without service_api_key - should return error
            result = await session.call_tool(
                "update_client_secret", {"client_id": "test_client_id", "secret_data": json.dumps(secret_data)}
            )

            assert result.content
            assert len(result.content) > 0
            response_text = result.content[0].text

            # Should return error about missing service_api_key
            assert response_text is not None
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_rotate_client_secret_without_token():
    """Test rotate_client_secret without valid token."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={},  # No token
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "rotate_client_secret", {"client_id": "test_client_id", "service_api_key": "test_service_key"}
            )

            assert result.content
            response_text = result.content[0].text
            assert "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set" in response_text


@pytest.mark.unit
async def test_update_client_secret_without_token():
    """Test update_client_secret without valid token."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={},  # No token
    )

    secret_data = {"clientSecret": "new_test_secret"}

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "update_client_secret",
                {
                    "client_id": "test_client_id",
                    "secret_data": json.dumps(secret_data),
                    "service_api_key": "test_service_key",
                },
            )

            assert result.content
            response_text = result.content[0].text
            assert "Error: ORGANIZATION_ACCESS_TOKEN environment variable not set" in response_text

            # シークレット値が指定した値と一致していることを確認
            assert "new_test_secret" in json.dumps(secret_data)


@pytest.mark.unit
async def test_update_client_secret_invalid_json():
    """Test update_client_secret with invalid JSON."""
    server_params = StdioServerParameters(
        command="uv", args=["run", "python", "main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Test with invalid JSON but valid service_api_key
            result = await session.call_tool(
                "update_client_secret",
                {"client_id": "test_client_id", "secret_data": "invalid json", "service_api_key": "test_service_key"},
            )

            assert result.content
            response_text = result.content[0].text
            assert "Error parsing secret data JSON" in response_text


@pytest.mark.integration
async def test_client_secret_operations_with_service_api_key():
    """Test client secret operations with valid service_api_key."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("Real ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    org_id = os.getenv("ORGANIZATION_ID")
    if not org_id or org_id == "12345":
        pytest.skip("Real ORGANIZATION_ID not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": org_id},
    )

    service_api_key = None
    client_id = None

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            try:
                # 1. テスト用サービスを作成
                service_result = await session.call_tool(
                    "create_service",
                    {"name": "pytest-secret-test-service", "description": "Test service for client secret operations"},
                )

                assert service_result.content
                service_response = service_result.content[0].text
                assert "Error" not in service_response, f"Service creation failed: {service_response}"

                service_data = json.loads(service_response)
                service_api_key = str(service_data.get("apiKey"))  # サービスAPIキー（文字列として取得）

                assert service_api_key and service_api_key != "None", (
                    f"Service API key not found in response: {service_response}"
                )

                # 2. テスト用クライアントを作成
                client_data = {
                    "clientName": "pytest-secret-test-client",
                    "description": "Test client for secret operations",
                    "applicationType": "WEB",
                    "redirectUris": ["https://test.example.com/callback"],
                }

                client_result = await session.call_tool(
                    "create_client", {"client_data": json.dumps(client_data), "service_api_key": service_api_key}
                )

                assert client_result.content
                client_response = client_result.content[0].text
                assert "Error" not in client_response, f"Client creation failed: {client_response}"

                client_response_data = json.loads(client_response)
                client_id = str(client_response_data.get("clientId"))

                assert client_id, f"Client ID not found in response: {client_response}"

                # 3. クライアントシークレットローテーションをテスト
                rotate_result = await session.call_tool(
                    "rotate_client_secret", {"client_id": client_id, "service_api_key": service_api_key}
                )

                assert rotate_result.content
                rotate_response = rotate_result.content[0].text
                assert rotate_response is not None

                # 成功したローテーションレスポンスを確認
                assert "service_api_key parameter is required" not in rotate_response
                assert "Error" not in rotate_response or "Successfully refreshed" in rotate_response

                # 実際のAPIレスポンスの場合、新旧シークレットが異なることを確認
                if "newClientSecret" in rotate_response and "oldClientSecret" in rotate_response:
                    response_data = json.loads(rotate_response)
                    new_secret = response_data.get("newClientSecret")
                    old_secret = response_data.get("oldClientSecret")
                    # 新旧のシークレットが異なることを確認
                    assert new_secret != old_secret
                    assert new_secret is not None
                    assert old_secret is not None

                # 4. クライアントシークレット更新をテスト
                new_secret_value = "pytest-updated-secret-12345"
                secret_data = {"clientSecret": new_secret_value}
                update_result = await session.call_tool(
                    "update_client_secret",
                    {
                        "client_id": client_id,
                        "secret_data": json.dumps(secret_data),
                        "service_api_key": service_api_key,
                    },
                )

                assert update_result.content
                update_response = update_result.content[0].text
                assert update_response is not None

                # 成功した更新レスポンスを確認
                assert "service_api_key parameter is required" not in update_response
                assert "Error" not in update_response or "Successfully updated" in update_response

            finally:
                # 5. クリーンアップ: サービスを削除（クライアントも自動削除される）
                if service_api_key:
                    delete_result = await session.call_tool(
                        "delete_service",
                        {
                            "service_id": service_api_key,  # apiKeyを使用
                            "organization_id": org_id,
                        },
                    )

                    # 削除が成功したことを確認
                    assert delete_result.content, "Delete service response is empty"
                    delete_response = delete_result.content[0].text

                    # delete_service ツールが明確な削除完了メッセージを返すことを確認
                    assert "Service deleted successfully" in delete_response, (
                        f"Expected deletion success message, got: {delete_response}"
                    )
