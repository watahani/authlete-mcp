#!/usr/bin/env python3
"""
Authlete OpenAPI Search MCP Server

高度な検索機能を提供するAuthlete API仕様書検索MCPサーバー。
- 基本検索：パス・説明による部分一致検索
- あいまい検索：rapidfuzzによる文字列類似度検索
- 詳細検索：リクエスト・レスポンススキーマの詳細情報
- サンプルコード取得：指定言語でのコードサンプル
"""

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import jsonref
from mcp.server import Server
from mcp.types import TextContent, Tool
from rapidfuzz import fuzz


class SearchMode(str, Enum):
    """検索モード"""

    EXACT = "exact"
    PARTIAL = "partial"
    FUZZY = "fuzzy"
    NATURAL = "natural"


@dataclass
class SearchResult:
    """検索結果"""

    path: str
    method: str
    operation_id: str | None
    summary: str | None
    description: str | None
    tags: list[str]
    sample_languages: list[str]
    score: float | None = None


@dataclass
class ApiDetail:
    """API詳細情報"""

    path: str
    method: str
    operation_id: str | None
    summary: str | None
    description: str | None
    parameters: list[dict[str, Any]]
    request_body: dict[str, Any] | None
    responses: dict[str, dict[str, Any]]
    sample_code: str | None
    tags: list[str]


class AuthleteApiSearcher:
    """Authlete API検索エンジン"""

    def __init__(self, api_spec_path: str | None = None):
        """初期化

        Args:
            api_spec_path: OpenAPI仕様書のパス（Noneの場合はデフォルトパス）
        """
        if api_spec_path:
            self.api_spec_path = Path(api_spec_path)
        else:
            # デフォルトパス：resources/openapi-spec.json
            self.api_spec_path = Path(__file__).parent / "resources" / "openapi-spec.json"

        self.api_doc: dict[str, Any] | None = None
        self._search_index: list[dict[str, Any]] = []

    async def load_api_doc(self) -> None:
        """OpenAPI仕様書を読み込み、検索インデックスを構築"""
        if self.api_doc is not None:
            return

        try:
            with open(self.api_spec_path, encoding="utf-8") as f:
                # jsonrefで$refを解決
                self.api_doc = jsonref.load(f)
            await self._build_search_index()
        except Exception as e:
            raise RuntimeError(f"OpenAPI仕様書の読み込みに失敗しました: {str(e)}")

    async def _build_search_index(self) -> None:
        """検索用インデックスを構築"""
        if not self.api_doc or "paths" not in self.api_doc:
            return

        self._search_index = []

        for path, path_item in self.api_doc["paths"].items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if not isinstance(operation, dict) or method.startswith("x-"):
                    continue

                # サンプルコードの言語一覧を取得
                code_samples = operation.get("x-code-samples", [])
                sample_languages = [sample.get("lang", "") for sample in code_samples]

                # 検索用テキストを作成
                search_text_parts = [
                    path,
                    operation.get("summary", ""),
                    operation.get("description", ""),
                    operation.get("operationId", ""),
                ]

                # タグも検索対象に含める
                tags = operation.get("tags", [])
                search_text_parts.extend(tags)

                search_text = " ".join(filter(None, search_text_parts))

                index_item = {
                    "path": path,
                    "method": method.upper(),
                    "operation_id": operation.get("operationId"),
                    "summary": operation.get("summary"),
                    "description": operation.get("description"),
                    "tags": tags,
                    "sample_languages": sample_languages,
                    "search_text": search_text,
                    "operation": operation,
                }

                self._search_index.append(index_item)

    async def search_apis(
        self,
        query: str | None = None,
        path_query: str | None = None,
        description_query: str | None = None,
        tag_filter: str | None = None,
        method_filter: str | None = None,
        mode: SearchMode = SearchMode.PARTIAL,
        limit: int = 20,
    ) -> list[SearchResult]:
        """API検索

        Args:
            query: 総合検索クエリ
            path_query: パス検索クエリ
            description_query: 説明検索クエリ
            tag_filter: タグフィルター
            method_filter: HTTPメソッドフィルター
            mode: 検索モード
            limit: 最大結果数

        Returns:
            検索結果のリスト
        """
        await self.load_api_doc()

        if not any([query, path_query, description_query]):
            return []

        results = []

        for item in self._search_index:
            score = 0.0
            matched = False

            # メソッドフィルター
            if method_filter and item["method"].lower() != method_filter.lower():
                continue

            # タグフィルター
            if tag_filter and tag_filter.lower() not in [tag.lower() for tag in item["tags"]]:
                continue

            # 総合検索
            if query:
                if mode == SearchMode.EXACT:
                    matched = query.lower() in item["search_text"].lower()
                    score = 100.0 if matched else 0.0
                elif mode == SearchMode.PARTIAL:
                    matched = query.lower() in item["search_text"].lower()
                    score = 80.0 if matched else 0.0
                elif mode == SearchMode.FUZZY:
                    score = fuzz.partial_ratio(query.lower(), item["search_text"].lower())
                    matched = score >= 60
                elif mode == SearchMode.NATURAL:
                    # 自然言語検索：複数の指標を組み合わせ
                    token_score = fuzz.token_sort_ratio(query.lower(), item["search_text"].lower())
                    partial_score = fuzz.partial_ratio(query.lower(), item["search_text"].lower())
                    score = (token_score + partial_score) / 2
                    matched = score >= 50

            # パス特化検索
            if path_query:
                path_match = False
                if mode == SearchMode.EXACT:
                    path_match = path_query == item["path"]
                    if path_match:
                        score += 50
                elif mode == SearchMode.PARTIAL:
                    path_match = path_query.lower() in item["path"].lower()
                    if path_match:
                        score += 40
                elif mode in [SearchMode.FUZZY, SearchMode.NATURAL]:
                    path_score = fuzz.ratio(path_query.lower(), item["path"].lower())
                    if path_score >= 70:
                        path_match = True
                        score += path_score / 2

                matched = matched or path_match

            # 説明特化検索
            if description_query:
                desc_text = f"{item['summary']} {item['description']}".strip()
                desc_match = False

                if mode == SearchMode.EXACT:
                    desc_match = description_query.lower() == desc_text.lower()
                    if desc_match:
                        score += 50
                elif mode == SearchMode.PARTIAL:
                    desc_match = description_query.lower() in desc_text.lower()
                    if desc_match:
                        score += 40
                elif mode in [SearchMode.FUZZY, SearchMode.NATURAL]:
                    desc_score = fuzz.partial_ratio(description_query.lower(), desc_text.lower())
                    if desc_score >= 60:
                        desc_match = True
                        score += desc_score / 2

                matched = matched or desc_match

            if matched:
                results.append(
                    SearchResult(
                        path=item["path"],
                        method=item["method"],
                        operation_id=item["operation_id"],
                        summary=item["summary"],
                        description=item["description"],
                        tags=item["tags"],
                        sample_languages=item["sample_languages"],
                        score=score,
                    )
                )

        # スコア順でソート
        results.sort(key=lambda x: x.score or 0, reverse=True)

        return results[:limit]

    async def get_api_detail(self, path: str, method: str, language: str | None = None) -> ApiDetail | None:
        """API詳細情報を取得

        Args:
            path: APIパス
            method: HTTPメソッド
            language: サンプルコード言語

        Returns:
            API詳細情報またはNone
        """
        await self.load_api_doc()

        if not self.api_doc or "paths" not in self.api_doc:
            return None

        path_item = self.api_doc["paths"].get(path)
        if not path_item:
            return None

        operation = path_item.get(method.lower())
        if not operation:
            return None

        # パラメータ情報を取得
        parameters = []
        if "parameters" in operation:
            parameters = operation["parameters"]
        if "parameters" in path_item:
            parameters.extend(path_item["parameters"])

        # サンプルコードを取得
        sample_code = None
        if language:
            code_samples = operation.get("x-code-samples", [])
            for sample in code_samples:
                if sample.get("lang") == language:
                    sample_code = sample.get("source")
                    break

        return ApiDetail(
            path=path,
            method=method.upper(),
            operation_id=operation.get("operationId"),
            summary=operation.get("summary"),
            description=operation.get("description"),
            parameters=parameters,
            request_body=operation.get("requestBody"),
            responses=operation.get("responses", {}),
            sample_code=sample_code,
            tags=operation.get("tags", []),
        )


# MCPサーバー初期化
server = Server("authlete-api-search")
searcher = AuthleteApiSearcher()


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """利用可能なツール一覧を返す"""
    return [
        Tool(
            name="search_apis",
            description="Authlete APIを検索します。柔軟な検索モード（完全一致、部分一致、あいまい一致、自然言語）に対応。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "総合検索クエリ（パス、説明、タグを横断検索）"},
                    "path_query": {"type": "string", "description": "APIパス検索クエリ（例：/api/auth/authorization）"},
                    "description_query": {"type": "string", "description": "説明・概要検索クエリ（例：token revoke）"},
                    "tag_filter": {"type": "string", "description": "タグフィルター（例：Authorization, Token）"},
                    "method_filter": {
                        "type": "string",
                        "description": "HTTPメソッドフィルター（GET, POST, PUT, DELETE）",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["exact", "partial", "fuzzy", "natural"],
                        "description": "検索モード：exact（完全一致）, partial（部分一致）, fuzzy（あいまい一致）, natural（自然言語）",
                        "default": "partial",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "最大結果数（デフォルト：20）",
                        "default": 20,
                        "minimum": 1,
                        "maximum": 100,
                    },
                },
            },
        ),
        Tool(
            name="get_api_detail",
            description="特定のAPIの詳細情報（パラメータ、リクエストボディ、レスポンス、サンプルコード）を取得します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "APIパス（search_apisで取得したpathを使用）"},
                    "method": {"type": "string", "description": "HTTPメソッド（search_apisで取得したmethodを使用）"},
                    "language": {
                        "type": "string",
                        "description": "サンプルコード言語（例：curl, javascript, python, java）",
                    },
                },
                "required": ["path", "method"],
            },
        ),
        Tool(
            name="get_sample_code",
            description="特定のAPIの指定言語でのサンプルコードを取得します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "APIパス"},
                    "method": {"type": "string", "description": "HTTPメソッド"},
                    "language": {
                        "type": "string",
                        "description": "プログラミング言語（例：curl, javascript, python, java）",
                    },
                },
                "required": ["path", "method", "language"],
            },
        ),
        Tool(
            name="suggest_apis",
            description="自然言語での質問に基づいてAuthlete APIを推奨します。",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "自然言語での質問（例：「トークンを無効化したい」「クライアントを作成したい」）",
                    },
                    "limit": {"type": "integer", "description": "最大推奨数", "default": 5},
                },
                "required": ["question"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """ツール呼び出し処理"""

    if name == "search_apis":
        try:
            # 検索パラメータを取得
            query = arguments.get("query")
            path_query = arguments.get("path_query")
            description_query = arguments.get("description_query")
            tag_filter = arguments.get("tag_filter")
            method_filter = arguments.get("method_filter")
            mode_str = arguments.get("mode", "partial")
            limit = arguments.get("limit", 20)

            # 検索モードを変換
            try:
                mode = SearchMode(mode_str)
            except ValueError:
                mode = SearchMode.PARTIAL

            # 検索実行
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
                return [TextContent(type="text", text="検索条件に一致するAPIが見つかりませんでした。")]

            # 結果をJSONで返す
            results_data = [
                {
                    "path": r.path,
                    "method": r.method,
                    "operation_id": r.operation_id,
                    "summary": r.summary,
                    "description": r.description,
                    "tags": r.tags,
                    "sample_languages": r.sample_languages,
                    "score": r.score,
                }
                for r in results
            ]

            return [TextContent(type="text", text=json.dumps(results_data, ensure_ascii=False, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=f"検索エラー: {str(e)}")]

    elif name == "get_api_detail":
        try:
            path = arguments.get("path")
            method = arguments.get("method")
            language = arguments.get("language")

            if not path or not method:
                return [TextContent(type="text", text="pathとmethodパラメータが必要です。")]

            detail = await searcher.get_api_detail(path, method, language)

            if not detail:
                return [TextContent(type="text", text=f"API詳細が見つかりません: {method} {path}")]

            # 詳細情報をJSONで返す
            detail_data = {
                "path": detail.path,
                "method": detail.method,
                "operation_id": detail.operation_id,
                "summary": detail.summary,
                "description": detail.description,
                "parameters": detail.parameters,
                "request_body": detail.request_body,
                "responses": detail.responses,
                "sample_code": detail.sample_code,
                "tags": detail.tags,
            }

            return [TextContent(type="text", text=json.dumps(detail_data, ensure_ascii=False, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=f"詳細取得エラー: {str(e)}")]

    elif name == "get_sample_code":
        try:
            path = arguments.get("path")
            method = arguments.get("method")
            language = arguments.get("language")

            if not all([path, method, language]):
                return [TextContent(type="text", text="path、method、languageパラメータが全て必要です。")]

            detail = await searcher.get_api_detail(path, method, language)

            if not detail or not detail.sample_code:
                return [TextContent(type="text", text=f"サンプルコードが見つかりません: {method} {path} ({language})")]

            return [TextContent(type="text", text=detail.sample_code)]

        except Exception as e:
            return [TextContent(type="text", text=f"サンプルコード取得エラー: {str(e)}")]

    elif name == "suggest_apis":
        try:
            question = arguments.get("question")
            limit = arguments.get("limit", 5)

            if not question:
                return [TextContent(type="text", text="questionパラメータが必要です。")]

            # 自然言語検索で関連APIを検索
            results = await searcher.search_apis(query=question, mode=SearchMode.NATURAL, limit=limit)

            if not results:
                return [TextContent(type="text", text=f"「{question}」に関連するAPIが見つかりませんでした。")]

            # 推奨結果を整形
            suggestions = []
            for r in results:
                suggestion = {
                    "path": r.path,
                    "method": r.method,
                    "summary": r.summary,
                    "description": r.description,
                    "relevance_score": r.score,
                    "tags": r.tags,
                }
                suggestions.append(suggestion)

            return [
                TextContent(
                    type="text",
                    text=json.dumps({"question": question, "suggestions": suggestions}, ensure_ascii=False, indent=2),
                )
            ]

        except Exception as e:
            return [TextContent(type="text", text=f"API推奨エラー: {str(e)}")]

    else:
        return [TextContent(type="text", text=f"未知のツール: {name}")]


async def main():
    """メイン関数"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
