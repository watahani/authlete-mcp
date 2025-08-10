"""API search engine using DuckDB."""

import json
import logging
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)

# Initialize global searcher
_searcher = None


def get_searcher() -> "AuthleteApiSearcher":
    """Get or create the global searcher instance"""
    global _searcher
    if _searcher is None:
        try:
            _searcher = AuthleteApiSearcher()
        except FileNotFoundError as e:
            logger.warning(f"Search functionality not available: {e}")
            raise
    return _searcher


class AuthleteApiSearcher:
    """Enhanced API search engine (DuckDB-based)"""

    def __init__(self, db_path: str = "resources/authlete_apis.duckdb"):
        """Initialize the searcher

        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path = Path(db_path)
        self.conn = None

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Search database not found: {db_path}\n"
                f"Please run 'uv run python scripts/create_search_database.py' first"
            )

        logger.info(f"Search database found: {db_path}")

    def _ensure_connection(self):
        """Ensure database connection is established"""
        if self.conn is None:
            self.conn = duckdb.connect(str(self.db_path))
            logger.info(f"Search database connected: {self.db_path}")

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
            self._ensure_connection()

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
            self._ensure_connection()

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

    def search_schemas(
        self, query: str | None = None, schema_type: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """スキーマを検索する

        Args:
            query: 検索クエリ (schema名、title、descriptionを検索)
            schema_type: スキーマタイプでフィルタリング (object, array, string, etc.)
            limit: 結果の最大数

        Returns:
            マッチしたスキーマのリスト
        """
        try:
            self._ensure_connection()
            if not query and not schema_type:
                # パラメータが無い場合は全スキーマを返す
                result = self.conn.execute(
                    """
                    SELECT schema_name, schema_type, title, description, 0 as score
                    FROM api_schemas
                    ORDER BY schema_name ASC
                    LIMIT ?
                    """,
                    [limit],
                ).fetchall()
            else:
                where_conditions = []
                params = []

                # クエリ検索の追加
                if query:
                    try:
                        # FTS検索を試行
                        fts_result = self.conn.execute(
                            """
                            SELECT s.schema_name, s.schema_type, s.title, s.description, fts.score
                            FROM api_schemas s
                            JOIN (SELECT rowid, score FROM fts_main_api_schemas(?)) fts
                            ON s.id = fts.rowid
                            WHERE 1=1
                            """
                            + (" AND s.schema_type = ?" if schema_type else "")
                            + """
                            ORDER BY fts.score DESC
                            LIMIT ?
                            """,
                            [query] + ([schema_type] if schema_type else []) + [limit],
                        ).fetchall()

                        if fts_result:
                            result = fts_result
                        else:
                            # FTS検索で結果がない場合はLIKE検索
                            words = query.lower().split()
                            like_conditions = []
                            for word in words:
                                like_conditions.append("LOWER(search_content) LIKE ?")
                                params.append(f"%{word}%")

                            where_conditions.append(f"({' OR '.join(like_conditions)})")

                    except Exception:
                        # FTSが使えない場合はLIKE検索にフォールバック
                        words = query.lower().split()
                        like_conditions = []
                        for word in words:
                            like_conditions.append("LOWER(search_content) LIKE ?")
                            params.append(f"%{word}%")

                        where_conditions.append(f"({' OR '.join(like_conditions)})")

                # スキーマタイプフィルタの追加
                if schema_type:
                    where_conditions.append("schema_type = ?")
                    params.append(schema_type)

                # FTSで結果がない場合のみ実行
                if not ("result" in locals() and result):
                    where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                    result = self.conn.execute(
                        f"""
                        SELECT schema_name, schema_type, title, description, 0 as score
                        FROM api_schemas
                        WHERE {where_clause}
                        ORDER BY schema_name ASC
                        LIMIT ?
                        """,
                        params + [limit],
                    ).fetchall()

            # 結果をdictのリストに変換
            schemas = []
            for row in result:
                schema_name, schema_type, title, description, score = row
                schemas.append(
                    {
                        "schema_name": schema_name,
                        "schema_type": schema_type or "object",
                        "title": title or "",
                        "description": description or "",
                        "score": score,
                    }
                )

            return schemas

        except Exception as e:
            logger.error(f"Schema search error: {str(e)}")
            return []

    def get_schema_detail(self, schema_name: str) -> dict[str, Any] | None:
        """特定のスキーマの詳細情報を取得する

        Args:
            schema_name: スキーマ名

        Returns:
            スキーマの詳細情報またはNone
        """
        try:
            self._ensure_connection()
            result = self.conn.execute(
                """
                SELECT schema_name, schema_type, title, description,
                       properties, required_fields, example_value
                FROM api_schemas
                WHERE schema_name = ?
                """,
                [schema_name],
            ).fetchone()

            if not result:
                return None

            (
                schema_name,
                schema_type,
                title,
                description,
                properties,
                required_fields,
                example_value,
            ) = result

            # JSON文字列をパース
            try:
                properties_dict = json.loads(properties) if properties else {}
            except json.JSONDecodeError:
                properties_dict = {}

            try:
                example_obj = json.loads(example_value) if example_value else None
            except json.JSONDecodeError:
                example_obj = example_value if example_value else None

            return {
                "schema_name": schema_name,
                "schema_type": schema_type or "object",
                "title": title or "",
                "description": description or "",
                "properties": properties_dict,
                "required_fields": required_fields or [],
                "example": example_obj,
            }

        except Exception as e:
            logger.error(f"Schema detail retrieval error: {str(e)}")
            return None
