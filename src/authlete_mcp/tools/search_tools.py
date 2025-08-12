"""Search and schema tools for Authlete MCP Server."""

import json
import logging

from mcp.server.fastmcp import Context

from ..models.base import filter_body_content, filter_description
from ..search import get_searcher

logger = logging.getLogger(__name__)


async def search_apis(
    query: str = "",
    path_query: str = "",
    description_query: str = "",
    tag_filter: str = "",
    method_filter: str = "",
    limit: int = 5,
    ctx: Context = None,
) -> str:
    """Natural language API search. Semantic matching like 'revoke token' → 'This API revokes access tokens'. Returns description truncated to ~100 chars. Use get_api_detail for full information.

    Search types are mutually exclusive and executed in priority order:
    1. query (natural language search) - highest priority
    2. path_query (path-based search) - medium priority
    3. description_query (description search) - lowest priority
    Only the highest priority non-empty parameter will be used for searching.

    Args:
        query: Natural language search query (e.g., 'revoke token', 'create client', 'user authentication')
        path_query: API path search (e.g., '/api/auth/token')
        description_query: Description search (e.g., 'revokes access tokens')
        tag_filter: Tag filter (e.g., 'Token Operations', 'Authorization') - applies to query and description_query
        method_filter: HTTP method filter (GET, POST, PUT, DELETE) - applies to all search types
        limit: Maximum number of results (default: 5, max: 100)
    """

    try:
        logger.info(
            f"🔍 search_apis called: query={repr(query)}, path_query={repr(path_query)}, description_query={repr(description_query)}"
        )

        searcher = get_searcher()

        # Validate limit
        if limit < 1 or limit > 100:
            limit = 5

        # Check which search will be executed
        if query and query.strip():
            logger.info("  - Executing natural language search")
        elif path_query and path_query.strip():
            logger.info("  - Executing path search")
        elif description_query and description_query.strip():
            logger.info("  - Executing description search")
        else:
            logger.info("  - No search (all parameters empty)")
            return "No APIs found matching the search criteria."

        results = await searcher.search_apis(
            query=query,
            path_query=path_query,
            description_query=description_query,
            tag_filter=tag_filter,
            method_filter=method_filter,
            limit=limit,
        )

        logger.info(f"  - Search completed: {len(results) if results else 0} results found")

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
    path: str = "",
    method: str = "",
    operation_id: str = "",
    language: str = "",
    description_style: str = "summary_and_headers",
    line_start: int = 1,
    line_end: int = 100,
    request_body_style: str = "none",
    response_body_style: str = "none",
    ctx: Context = None,
) -> str:
    """Get detailed information for specific API (parameters, request/response, sample code). Provide either operation_id OR both path and method.

    Args:
        path: API path (required if operation_id not provided)
        method: HTTP method (required if operation_id not provided)
        operation_id: Operation ID (alternative to path+method)
        language: Sample code language (curl, javascript, python, java, etc.)
        description_style: Description filtering style (summary_and_headers, full, none, line_range)
        line_start: Start line for line_range style (1-indexed)
        line_end: End line for line_range style (1-indexed)
        request_body_style: Request body filtering style (none, full, schema_only)
        response_body_style: Response body filtering style (none, full, schema_only)
    """

    try:
        searcher = get_searcher()

        # Parameters already come as strings, no conversion needed
        op_id = operation_id
        api_path = path
        api_method = method
        search_language = language

        # Check for empty values after conversion
        if not op_id.strip() and (not api_path.strip() or not api_method.strip()):
            return "Either 'operation_id' or both 'path' and 'method' parameters are required."

        detail = await searcher.get_api_detail(api_path, api_method, op_id, search_language)

        if not detail:
            identifier = op_id or f"{api_method} {api_path}"
            return f"API details not found: {identifier}"

        # Apply description filtering
        if "description" in detail and detail["description"]:
            line_range = (line_start, line_end) if description_style == "line_range" else None
            filtered_description = filter_description(detail["description"], description_style, line_range)
            detail["description"] = filtered_description

        # Apply request body filtering
        if "request_body" in detail and detail["request_body"]:
            filtered_request_body = filter_body_content(detail["request_body"], request_body_style)
            detail["request_body"] = filtered_request_body

        # Apply response body filtering
        if "responses" in detail and detail["responses"]:
            if isinstance(detail["responses"], dict):
                filtered_responses = {}
                for status_code, response_data in detail["responses"].items():
                    if isinstance(response_data, dict):
                        filtered_responses[status_code] = filter_body_content(response_data, response_body_style)
                    else:
                        # For string responses, apply filtering
                        if response_body_style == "none":
                            filtered_responses[status_code] = None
                        elif response_body_style == "schema_only":
                            # Try to parse string as JSON and simplify if possible
                            try:
                                parsed_response = (
                                    json.loads(response_data) if isinstance(response_data, str) else response_data
                                )
                                if isinstance(parsed_response, dict):
                                    filtered_responses[status_code] = filter_body_content(
                                        parsed_response, response_body_style
                                    )
                                else:
                                    # If not a dict, show simplified info
                                    filtered_responses[status_code] = {"type": "string", "content": "simplified"}
                            except (json.JSONDecodeError, TypeError):
                                # If parsing fails, show as string type
                                filtered_responses[status_code] = {"type": "string", "content": "simplified"}
                        else:
                            # For "full", keep as is
                            filtered_responses[status_code] = response_data
                detail["responses"] = filtered_responses
            else:
                # Handle case where responses is not a dict
                if response_body_style == "none":
                    detail["responses"] = None

        return json.dumps(detail, ensure_ascii=False, indent=2)

    except FileNotFoundError as e:
        return (
            f"Search database not found: {str(e)}\nPlease run 'uv run python scripts/create_search_database.py' first"
        )
    except Exception as e:
        return f"Detail retrieval error: {str(e)}"


async def get_sample_code(
    language: str,
    path: str = "",
    method: str = "",
    operation_id: str = "",
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

        if not language or not language.strip():
            return "language parameter is required."

        # Parameters already come as strings, no conversion needed
        op_id = operation_id
        api_path = path
        api_method = method

        # Check for empty values after conversion
        if not op_id.strip() and (not api_path.strip() or not api_method.strip()):
            return "Either 'operation_id' or both 'path' and 'method' parameters are required."

        detail = await searcher.get_api_detail(api_path, api_method, op_id, language)

        if not detail or not detail.get("sample_code"):
            identifier = op_id or f"{api_method} {api_path}"
            return f"Sample code not found: {identifier} ({language})"

        return detail["sample_code"]

    except FileNotFoundError as e:
        return (
            f"Search database not found: {str(e)}\nPlease run 'uv run python scripts/create_search_database.py' first"
        )
    except Exception as e:
        return f"Sample code retrieval error: {str(e)}"


async def list_schemas(
    query: str = "",
    limit: int = 20,
    ctx: Context = None,
) -> str:
    """List or search schemas from the API specification.

    Args:
        query: Search query (searches schema name, title, description; returns all schemas if omitted)
        limit: Maximum number of results (default: 20, max: 100)
    """
    try:
        # Validate limit range
        limit = max(1, min(limit, 100))

        searcher = get_searcher()
        # Parameter already comes as string, no conversion needed
        schemas = searcher.search_schemas(query=query, schema_type=None, limit=limit)

        if not schemas:
            return "No schemas found matching the specified criteria."

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
    """Get detailed information for a specific schema.

    Args:
        schema_name: Schema name (e.g., 'AccessToken', 'Client', 'Service')
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
