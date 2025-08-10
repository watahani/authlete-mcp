"""Search and schema tools for Authlete MCP Server."""

import json

from mcp.server.fastmcp import Context

from ..search import get_searcher


async def search_apis(
    query: str = None,
    path_query: str = None,
    description_query: str = None,
    tag_filter: str = None,
    method_filter: str = None,
    mode: str = "natural",
    limit: int = 20,
    ctx: Context = None,
) -> str:
    """Natural language API search. Semantic matching like 'revoke token' → 'This API revokes access tokens'. Returns description truncated to ~100 chars. Use get_api_detail for full information.

    Args:
        query: Natural language search query (e.g., 'revoke token', 'create client', 'user authentication')
        path_query: API path search (e.g., '/api/auth/token')
        description_query: Description search (e.g., 'revokes access tokens')
        tag_filter: Tag filter (e.g., 'Token Operations', 'Authorization')
        method_filter: HTTP method filter (GET, POST, PUT, DELETE)
        mode: Search mode (for compatibility, actually uses natural language search)
        limit: Maximum number of results (default: 20, max: 100)
    """

    try:
        searcher = get_searcher()

        # Validate limit
        if limit < 1 or limit > 100:
            limit = 20

        results = await searcher.search_apis(
            query=query,
            path_query=path_query,
            description_query=description_query,
            tag_filter=tag_filter,
            method_filter=method_filter,
            mode=mode,
            limit=limit,
        )

        if not results:
            return "No APIs found matching the search criteria."

        return json.dumps(results, ensure_ascii=False, indent=2)

    except FileNotFoundError as e:
        return (
            f"Search database not found: {str(e)}\nPlease run 'uv run python scripts/create_search_database.py' first"
        )
    except Exception as e:
        return f"Search error: {str(e)}"


async def get_api_detail(
    path: str = None,
    method: str = None,
    operation_id: str = None,
    language: str = None,
    ctx: Context = None,
) -> str:
    """Get detailed information for specific API (parameters, request/response, sample code). Provide either operation_id OR both path and method.

    Args:
        path: API path (required if operation_id not provided)
        method: HTTP method (required if operation_id not provided)
        operation_id: Operation ID (alternative to path+method)
        language: Sample code language (curl, javascript, python, java, etc.)
    """

    try:
        searcher = get_searcher()

        if not operation_id and (not path or not method):
            return "Either 'operation_id' or both 'path' and 'method' parameters are required."

        detail = await searcher.get_api_detail(path, method, operation_id, language)

        if not detail:
            identifier = operation_id or f"{method} {path}"
            return f"API details not found: {identifier}"

        return json.dumps(detail, ensure_ascii=False, indent=2)

    except FileNotFoundError as e:
        return (
            f"Search database not found: {str(e)}\nPlease run 'uv run python scripts/create_search_database.py' first"
        )
    except Exception as e:
        return f"Detail retrieval error: {str(e)}"


async def get_sample_code(
    language: str,
    path: str = None,
    method: str = None,
    operation_id: str = None,
    ctx: Context = None,
) -> str:
    """Get sample code for specific API in specified language. Provide language and either operation_id OR both path and method.

    Args:
        language: Programming language (curl, javascript, python, java, etc.)
        path: API path (required if operation_id not provided)
        method: HTTP method (required if operation_id not provided)
        operation_id: Operation ID (alternative to path+method)
    """

    try:
        searcher = get_searcher()

        if not language:
            return "language parameter is required."

        if not operation_id and (not path or not method):
            return "Either 'operation_id' or both 'path' and 'method' parameters are required."

        detail = await searcher.get_api_detail(path, method, operation_id, language)

        if not detail or not detail.get("sample_code"):
            identifier = operation_id or f"{method} {path}"
            return f"Sample code not found: {identifier} ({language})"

        return detail["sample_code"]

    except FileNotFoundError as e:
        return (
            f"Search database not found: {str(e)}\nPlease run 'uv run python scripts/create_search_database.py' first"
        )
    except Exception as e:
        return f"Sample code retrieval error: {str(e)}"


async def list_schemas(
    query: str = None,
    schema_type: str = None,
    limit: int = 20,
    ctx: Context = None,
) -> str:
    """スキーマ一覧を取得または検索する

    Args:
        query: 検索クエリ (スキーマ名、title、descriptionで検索、省略時は全スキーマを返す)
        schema_type: スキーマタイプでフィルタ (object, array, string, etc.)
        limit: 結果の最大数 (デフォルト: 20, 最大: 100)
    """
    try:
        # limitの範囲チェック
        limit = max(1, min(limit, 100))

        searcher = get_searcher()
        schemas = searcher.search_schemas(query=query, schema_type=schema_type, limit=limit)

        if not schemas:
            return "指定された条件にマッチするスキーマが見つかりませんでした。"

        return json.dumps(schemas, ensure_ascii=False, indent=2)

    except FileNotFoundError as e:
        return (
            f"Search database not found: {str(e)}\nPlease run 'uv run python scripts/create_search_database.py' first"
        )
    except Exception as e:
        return f"Schema search error: {str(e)}"


async def get_schema_detail(
    schema_name: str,
    ctx: Context = None,
) -> str:
    """特定のスキーマの詳細情報を取得する

    Args:
        schema_name: スキーマ名 (例: 'AccessToken', 'Client', 'Service')
    """
    try:
        if not schema_name:
            return "schema_name parameter is required."

        searcher = get_searcher()
        schema_detail = searcher.get_schema_detail(schema_name)

        if not schema_detail:
            return f"Schema not found: {schema_name}"

        return json.dumps(schema_detail, ensure_ascii=False, indent=2)

    except FileNotFoundError as e:
        return (
            f"Search database not found: {str(e)}\nPlease run 'uv run python scripts/create_search_database.py' first"
        )
    except Exception as e:
        return f"Schema detail retrieval error: {str(e)}"
