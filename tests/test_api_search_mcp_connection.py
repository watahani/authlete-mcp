"""
Authlete API Search MCP Server の接続テスト

MCPプロトコル経由での実際の接続と機能テストを行います。
"""

import json

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.asyncio
async def test_api_search_mcp_connection():
    """API検索MCPサーバーへの接続テスト"""

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "authlete_api_search_server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # サーバーを初期化
            await session.initialize()

            # ツール一覧を取得
            tools = await session.list_tools()

            # 期待するツールが存在することを確認
            tool_names = [tool.name for tool in tools.tools]
            expected_tools = ["search_apis", "get_api_detail", "get_sample_code", "suggest_apis"]

            for expected_tool in expected_tools:
                assert expected_tool in tool_names, f"期待するツール '{expected_tool}' が見つかりません"


@pytest.mark.asyncio
async def test_search_apis_tool():
    """search_apis ツールのテスト"""

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "authlete_api_search_server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # 基本的な検索テスト
            result = await session.call_tool("search_apis", {"query": "service", "limit": 5})

            assert len(result.content) > 0
            content = result.content[0]
            assert content.type == "text"

            # JSONレスポンスをパース
            try:
                search_results = json.loads(content.text)
                assert isinstance(search_results, list)
                assert len(search_results) <= 5

                # 結果の構造を確認
                if search_results:
                    first_result = search_results[0]
                    required_fields = ["path", "method", "summary", "description"]
                    for field in required_fields:
                        assert field in first_result

            except json.JSONDecodeError:
                pytest.fail("search_apis の結果がJSONではありません")


@pytest.mark.asyncio
async def test_search_apis_with_filters():
    """フィルター付き検索テスト"""

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "authlete_api_search_server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # メソッドフィルター付き検索
            result = await session.call_tool("search_apis", {"query": "api", "method_filter": "POST", "limit": 10})

            assert len(result.content) > 0
            content = result.content[0]

            try:
                search_results = json.loads(content.text)
                if search_results:  # 結果がある場合
                    # 全ての結果がPOSTメソッドであることを確認
                    for result_item in search_results:
                        assert result_item.get("method") == "POST"

            except json.JSONDecodeError:
                # エラーメッセージの場合はスキップ
                pass


@pytest.mark.asyncio
async def test_search_modes():
    """異なる検索モードのテスト"""

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "authlete_api_search_server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # 各検索モードをテスト
            search_modes = ["exact", "partial", "fuzzy", "natural"]

            for mode in search_modes:
                result = await session.call_tool("search_apis", {"query": "service", "mode": mode, "limit": 3})

                assert len(result.content) > 0
                content = result.content[0]
                assert content.type == "text"

                # 少なくともエラーでない応答が返ることを確認
                assert not content.text.startswith("検索エラー:")


@pytest.mark.asyncio
async def test_get_api_detail_tool():
    """get_api_detail ツールのテスト"""

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "authlete_api_search_server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # まず検索で有効なパスを取得
            search_result = await session.call_tool("search_apis", {"query": "service", "limit": 1})

            search_content = search_result.content[0]

            try:
                search_results = json.loads(search_content.text)
                if search_results:
                    # 最初の結果を使ってAPI詳細を取得
                    first_api = search_results[0]
                    path = first_api["path"]
                    method = first_api["method"]

                    detail_result = await session.call_tool("get_api_detail", {"path": path, "method": method})

                    assert len(detail_result.content) > 0
                    detail_content = detail_result.content[0]
                    assert detail_content.type == "text"

                    # 詳細情報をパース
                    detail_data = json.loads(detail_content.text)
                    assert "path" in detail_data
                    assert "method" in detail_data
                    assert detail_data["path"] == path
                    assert detail_data["method"] == method

            except (json.JSONDecodeError, IndexError):
                # 検索結果がない場合はスキップ
                pass


@pytest.mark.asyncio
async def test_get_sample_code_tool():
    """get_sample_code ツールのテスト"""

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "authlete_api_search_server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # サンプルコード取得のテスト（実際のAPIを使用）
            result = await session.call_tool(
                "get_sample_code", {"path": "/api/{serviceId}/service/get", "method": "GET", "language": "curl"}
            )

            assert len(result.content) > 0
            content = result.content[0]
            assert content.type == "text"

            # エラーでなければサンプルコードまたは「見つかりません」メッセージ
            assert not content.text.startswith("サンプルコード取得エラー:")


@pytest.mark.asyncio
async def test_suggest_apis_tool():
    """suggest_apis ツールのテスト"""

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "authlete_api_search_server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # 自然言語質問による推奨テスト
            questions = ["トークンを無効化したい", "クライアントを作成したい", "認証を行いたい"]

            for question in questions:
                result = await session.call_tool("suggest_apis", {"question": question, "limit": 3})

                assert len(result.content) > 0
                content = result.content[0]
                assert content.type == "text"

                try:
                    suggestion_data = json.loads(content.text)
                    assert "question" in suggestion_data
                    assert "suggestions" in suggestion_data
                    assert suggestion_data["question"] == question
                    assert isinstance(suggestion_data["suggestions"], list)
                    assert len(suggestion_data["suggestions"]) <= 3

                except json.JSONDecodeError:
                    # 結果がない場合のメッセージはスキップ
                    pass


@pytest.mark.asyncio
async def test_error_handling():
    """エラーハンドリングのテスト"""

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "authlete_api_search_server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # 無効なパラメータでget_api_detailを呼び出し
            result = await session.call_tool(
                "get_api_detail",
                {"path": ""},  # methodパラメータが不足
            )

            assert len(result.content) > 0
            content = result.content[0]
            assert content.type == "text"
            assert "pathとmethodパラメータが必要です" in content.text

            # 存在しないAPIの詳細取得
            result = await session.call_tool("get_api_detail", {"path": "/nonexistent/api", "method": "GET"})

            content = result.content[0]
            assert "API詳細が見つかりません" in content.text


@pytest.mark.asyncio
async def test_search_with_no_parameters():
    """パラメータなしでの検索テスト"""

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "authlete_api_search_server.py"],
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # パラメータなしで検索
            result = await session.call_tool("search_apis", {})

            assert len(result.content) > 0
            content = result.content[0]
            assert content.type == "text"
            assert "検索条件に一致するAPIが見つかりませんでした" in content.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
