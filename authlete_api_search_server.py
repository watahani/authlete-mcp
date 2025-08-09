#!/usr/bin/env python3
"""
Authlete OpenAPI Search MCP Server

Advanced search functionality for Authlete API documentation.
- Natural language search: semantic matching like "revoke token" → "This API revokes access tokens"
- DuckDB full-text search: fast and accurate search results
- Relevance scoring: results ordered by relevance
- Detailed search: comprehensive API information with request/response schemas
- Sample code retrieval: code samples in specified languages
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import duckdb
from mcp.server import Server
from mcp.types import TextContent, Tool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuthleteApiSearcher:
    """Enhanced API search engine (DuckDB-based)"""

    def __init__(self, db_path: str = "resources/authlete_apis.duckdb"):
        """Initialize the searcher

        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path = Path(db_path)

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Search database not found: {db_path}\n"
                f"Please run 'uv run python scripts/create_search_database.py' first"
            )

        self.conn = duckdb.connect(str(self.db_path))
        logger.info(f"Search database connected: {db_path}")

    async def search_apis(
        self,
        query: str | None = None,
        path_query: str | None = None,
        description_query: str | None = None,
        tag_filter: str | None = None,
        method_filter: str | None = None,
        mode: str = "natural",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Search APIs

        Args:
            query: Natural language query
            path_query: API path search
            description_query: Description search
            tag_filter: Tag filtering
            method_filter: HTTP method filtering
            mode: Search mode (kept for compatibility, actually uses natural language search)
            limit: Maximum number of results

        Returns:
            List of search results
        """
        if not any([query, path_query, description_query]):
            return []

        try:
            # Execute search
            if query and len(query.strip()) > 0:
                results = await self._natural_language_search(query, tag_filter, method_filter, limit)
            elif path_query:
                results = await self._path_search(path_query, method_filter, limit)
            elif description_query:
                results = await self._description_search(description_query, tag_filter, method_filter, limit)
            else:
                results = []

            return results

        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []

    async def _natural_language_search(
        self, query: str, tag_filter: str | None, method_filter: str | None, limit: int
    ) -> list[dict[str, Any]]:
        """Natural language search"""

        # Split query into words
        query_words = query.lower().split()

        # Build WHERE conditions
        where_conditions = []
        params = []

        # OR search for each word (natural language matching)
        word_conditions = []
        for word in query_words:
            word_conditions.append("LOWER(search_content) LIKE ?")
            params.append(f"%{word}%")

        if word_conditions:
            where_conditions.append(f"({' OR '.join(word_conditions)})")

        # Filter conditions
        if method_filter:
            where_conditions.append("method = ?")
            params.append(method_filter.upper())

        if tag_filter:
            where_conditions.append("tags LIKE ?")
            params.append(f"%{tag_filter}%")

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Query with relevance score calculation (summary/path priority)
        sql = f"""
        SELECT
            path, method, operation_id, summary, description, tags,
            sample_languages, sample_codes,
            (
                CASE
                    -- Complete phrase match (highest score)
                    WHEN LOWER(search_content) LIKE ? THEN 150
                    -- Summary partial match (very high score)
                    WHEN LOWER(summary) LIKE ? THEN 120
                    -- Path match (high score)
                    WHEN LOWER(path) LIKE ? THEN 100
                    -- Description partial match (medium score)
                    WHEN LOWER(description) LIKE ? THEN 80
                    ELSE 10
                END +
                -- Bonus points from individual word matches (high points for summary/path)
                {self._build_enhanced_word_score_expression(query_words)}
            ) as relevance_score
        FROM api_endpoints
        WHERE {where_clause}
        ORDER BY relevance_score DESC, path ASC
        LIMIT ?
        """

        # Build parameter list
        score_params = [f"%{query.lower()}%"] * 4  # Complete phrase, description, summary, path
        all_params = score_params + params + [limit]

        result = self.conn.execute(sql, all_params).fetchall()

        return self._format_search_results(result)

    def _build_enhanced_word_score_expression(self, words: list[str]) -> str:
        """Build enhanced word matching score expression (summary/path priority)"""
        expressions = []
        for word in words:
            # Escape words to avoid SQL injection
            escaped_word = word.replace("'", "''")
            # Give high scores for summary/path matches
            expressions.append(f"""
                CASE
                    WHEN LOWER(summary) LIKE '%{escaped_word}%' THEN 15
                    WHEN LOWER(path) LIKE '%{escaped_word}%' THEN 12
                    WHEN LOWER(description) LIKE '%{escaped_word}%' THEN 8
                    WHEN LOWER(search_content) LIKE '%{escaped_word}%' THEN 5
                    ELSE 0
                END
            """)
        return " + ".join(expressions) if expressions else "0"

    async def _path_search(self, path_query: str, method_filter: str | None, limit: int) -> list[dict[str, Any]]:
        """Path-specific search"""

        where_conditions = ["LOWER(path) LIKE ?"]
        params = [f"%{path_query.lower()}%"]

        if method_filter:
            where_conditions.append("method = ?")
            params.append(method_filter.upper())

        where_clause = " AND ".join(where_conditions)

        sql = f"""
        SELECT
            path, method, operation_id, summary, description, tags,
            sample_languages, sample_codes,
            CASE
                WHEN path = ? THEN 100
                WHEN LOWER(path) LIKE ? THEN 80
                ELSE 50
            END as relevance_score
        FROM api_endpoints
        WHERE {where_clause}
        ORDER BY relevance_score DESC, path ASC
        LIMIT ?
        """

        score_params = [path_query, f"%{path_query.lower()}%"]
        all_params = score_params + params + [limit]

        result = self.conn.execute(sql, all_params).fetchall()
        return self._format_search_results(result)

    async def _description_search(
        self, desc_query: str, tag_filter: str | None, method_filter: str | None, limit: int
    ) -> list[dict[str, Any]]:
        """Description-specific search"""

        where_conditions = ["(LOWER(summary) LIKE ? OR LOWER(description) LIKE ?)"]
        params = [f"%{desc_query.lower()}%", f"%{desc_query.lower()}%"]

        if method_filter:
            where_conditions.append("method = ?")
            params.append(method_filter.upper())

        if tag_filter:
            where_conditions.append("tags LIKE ?")
            params.append(f"%{tag_filter}%")

        where_clause = " AND ".join(where_conditions)

        sql = f"""
        SELECT
            path, method, operation_id, summary, description, tags,
            sample_languages, sample_codes,
            CASE
                WHEN LOWER(summary) LIKE ? THEN 100
                WHEN LOWER(description) LIKE ? THEN 90
                ELSE 30
            END as relevance_score
        FROM api_endpoints
        WHERE {where_clause}
        ORDER BY relevance_score DESC, path ASC
        LIMIT ?
        """

        score_params = [f"%{desc_query.lower()}%", f"%{desc_query.lower()}%"]
        all_params = score_params + params + [limit]

        result = self.conn.execute(sql, all_params).fetchall()
        return self._format_search_results(result)

    def _format_search_results(self, results: list[tuple]) -> list[dict[str, Any]]:
        """Format search results"""
        formatted = []

        for row in results:
            path, method, operation_id, summary, description, tags, sample_languages, sample_codes, score = row

            # Handle tags and sample_languages (already as lists from DuckDB)
            tags_list = tags if tags else []
            sample_languages_list = sample_languages if sample_languages else []

            # Truncate description to first 100 characters for search results
            truncated_description = (description or "")[:100]
            if len(description or "") > 100:
                truncated_description += "..."

            formatted.append(
                {
                    "path": path,
                    "method": method,
                    "operation_id": operation_id,
                    "summary": summary or "",
                    "description": truncated_description,
                    "tags": tags_list,
                    "sample_languages": sample_languages_list,
                    "score": float(score),
                }
            )

        return formatted

    async def get_api_detail(
        self, path: str = None, method: str = None, operation_id: str = None, language: str | None = None
    ) -> dict[str, Any] | None:
        """Get detailed information for a specific API by path+method or operationId"""

        try:
            if operation_id:
                # Search by operationId
                result = self.conn.execute(
                    """
                    SELECT path, method, operation_id, summary, description, tags,
                           parameters, request_body, responses, sample_codes
                    FROM api_endpoints
                    WHERE operation_id = ?
                """,
                    [operation_id],
                ).fetchone()
            elif path and method:
                # Search by path and method
                result = self.conn.execute(
                    """
                    SELECT path, method, operation_id, summary, description, tags,
                           parameters, request_body, responses, sample_codes
                    FROM api_endpoints
                    WHERE path = ? AND method = ?
                """,
                    [path, method.upper()],
                ).fetchone()
            else:
                return None

            if not result:
                return None

            (
                api_path,
                api_method,
                operation_id,
                summary,
                description,
                tags,
                parameters,
                request_body,
                responses,
                sample_codes,
            ) = result

            # Parse JSON data (tags are already lists from DuckDB)
            tags_list = tags if tags else []
            try:
                parameters_list = json.loads(parameters) if parameters else []
                request_body_obj = json.loads(request_body) if request_body else None
                responses_obj = json.loads(responses) if responses else {}
                sample_codes_dict = json.loads(sample_codes) if sample_codes else {}
            except json.JSONDecodeError:
                parameters_list = []
                request_body_obj = None
                responses_obj = {}
                sample_codes_dict = {}

            # Get sample code
            sample_code = sample_codes_dict.get(language) if language else None

            return {
                "path": api_path,
                "method": api_method,
                "operation_id": operation_id,
                "summary": summary or "",
                "description": description or "",
                "tags": tags_list,
                "parameters": parameters_list,
                "request_body": request_body_obj,
                "responses": responses_obj,
                "sample_code": sample_code,
            }

        except Exception as e:
            logger.error(f"API detail retrieval error: {str(e)}")
            return None


# Initialize MCP server
server = Server("authlete-api-search")
searcher = None


async def initialize_searcher():
    """Lazy initialization of search engine"""
    global searcher
    if searcher is None:
        try:
            searcher = AuthleteApiSearcher()
            logger.info("API search engine initialization completed")
        except Exception as e:
            logger.error(f"Search engine initialization failed: {str(e)}")
            raise


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Return list of available tools"""
    return [
        Tool(
            name="search_apis",
            description="Natural language API search. Semantic matching like 'revoke token' → 'This API revokes access tokens'. Returns description truncated to ~100 chars. Use get_api_detail for full information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query (e.g., 'revoke token', 'create client', 'user authentication')",
                    },
                    "path_query": {"type": "string", "description": "API path search (e.g., '/api/auth/token')"},
                    "description_query": {
                        "type": "string",
                        "description": "Description search (e.g., 'revokes access tokens')",
                    },
                    "tag_filter": {
                        "type": "string",
                        "description": "Tag filter (e.g., 'Token Operations', 'Authorization')",
                    },
                    "method_filter": {"type": "string", "description": "HTTP method filter (GET, POST, PUT, DELETE)"},
                    "mode": {
                        "type": "string",
                        "enum": ["exact", "partial", "fuzzy", "natural"],
                        "description": "Search mode (for compatibility, actually uses natural language search)",
                        "default": "natural",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 20)",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
            },
        ),
        Tool(
            name="get_api_detail",
            description="Get detailed information for specific API (parameters, request/response, sample code). Provide either operation_id OR both path and method.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "API path (required if operation_id not provided)"},
                    "method": {"type": "string", "description": "HTTP method (required if operation_id not provided)"},
                    "operation_id": {"type": "string", "description": "Operation ID (alternative to path+method)"},
                    "language": {
                        "type": "string",
                        "description": "Sample code language (curl, javascript, python, java, etc.)",
                    },
                },
            },
        ),
        Tool(
            name="get_sample_code",
            description="Get sample code for specific API in specified language. Provide language and either operation_id OR both path and method.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "API path (required if operation_id not provided)"},
                    "method": {"type": "string", "description": "HTTP method (required if operation_id not provided)"},
                    "operation_id": {"type": "string", "description": "Operation ID (alternative to path+method)"},
                    "language": {"type": "string", "description": "Programming language"},
                },
                "required": ["language"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Tool call handling"""

    await initialize_searcher()

    if name == "search_apis":
        try:
            query = arguments.get("query")
            path_query = arguments.get("path_query")
            description_query = arguments.get("description_query")
            tag_filter = arguments.get("tag_filter")
            method_filter = arguments.get("method_filter")
            mode = arguments.get("mode", "natural")
            limit = arguments.get("limit", 20)

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
                return [TextContent(type="text", text="No APIs found matching the search criteria.")]

            return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=f"Search error: {str(e)}")]

    elif name == "get_api_detail":
        try:
            path = arguments.get("path")
            method = arguments.get("method")
            operation_id = arguments.get("operation_id")
            language = arguments.get("language")

            if not operation_id and (not path or not method):
                return [
                    TextContent(
                        type="text", text="Either 'operation_id' or both 'path' and 'method' parameters are required."
                    )
                ]

            detail = await searcher.get_api_detail(path, method, operation_id, language)

            if not detail:
                return [TextContent(type="text", text=f"API details not found: {method} {path}")]

            return [TextContent(type="text", text=json.dumps(detail, ensure_ascii=False, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=f"Detail retrieval error: {str(e)}")]

    elif name == "get_sample_code":
        try:
            path = arguments.get("path")
            method = arguments.get("method")
            operation_id = arguments.get("operation_id")
            language = arguments.get("language")

            if not language:
                return [TextContent(type="text", text="language parameter is required.")]

            if not operation_id and (not path or not method):
                return [
                    TextContent(
                        type="text", text="Either 'operation_id' or both 'path' and 'method' parameters are required."
                    )
                ]

            detail = await searcher.get_api_detail(path, method, operation_id, language)

            if not detail or not detail.get("sample_code"):
                return [TextContent(type="text", text=f"Sample code not found: {method} {path} ({language})")]

            return [TextContent(type="text", text=detail["sample_code"])]

        except Exception as e:
            return [TextContent(type="text", text=f"Sample code retrieval error: {str(e)}")]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Main function"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
