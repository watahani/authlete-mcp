"""
Authlete API Search Server のテスト

新しいPython版OpenAPI検索MCPサーバーの機能をテストします。
"""

import json
from pathlib import Path

import pytest

from authlete_api_search_server import AuthleteApiSearcher, SearchMode


class TestAuthleteApiSearcher:
    """AuthleteApiSearcher のテストクラス"""

    @pytest.fixture
    def mock_openapi_spec(self):
        """モック用のOpenAPI仕様書"""
        return {
            "openapi": "3.0.3",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/api/auth/authorization": {
                    "post": {
                        "operationId": "authorization",
                        "summary": "Authorization Endpoint",
                        "description": "Process authorization requests",
                        "tags": ["Authorization"],
                        "parameters": [
                            {"name": "response_type", "in": "query", "required": True, "schema": {"type": "string"}}
                        ],
                        "requestBody": {
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {"type": "object", "properties": {"client_id": {"type": "string"}}}
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {"application/json": {"schema": {"type": "object"}}},
                            }
                        },
                        "x-code-samples": [
                            {"lang": "curl", "source": "curl -X POST /api/auth/authorization"},
                            {"lang": "javascript", "source": "fetch('/api/auth/authorization', {method: 'POST'})"},
                        ],
                    }
                },
                "/api/auth/token": {
                    "post": {
                        "operationId": "token",
                        "summary": "Token Endpoint",
                        "description": "Exchange authorization code for tokens",
                        "tags": ["Token"],
                        "responses": {"200": {"description": "Token response"}},
                        "x-code-samples": [{"lang": "python", "source": "requests.post('/api/auth/token')"}],
                    }
                },
                "/api/auth/revocation": {
                    "post": {
                        "operationId": "revocation",
                        "summary": "Token Revocation",
                        "description": "Revoke access or refresh tokens",
                        "tags": ["Token"],
                        "responses": {"200": {"description": "Revocation success"}},
                        "x-code-samples": [],
                    }
                },
            },
        }

    @pytest.fixture
    def searcher(self, tmp_path, mock_openapi_spec):
        """テスト用のAuthleteApiSearcherインスタンス"""
        # 一時的なOpenAPI仕様書ファイルを作成
        spec_file = tmp_path / "test_spec.json"
        with open(spec_file, "w", encoding="utf-8") as f:
            json.dump(mock_openapi_spec, f, ensure_ascii=False, indent=2)

        return AuthleteApiSearcher(str(spec_file))

    @pytest.mark.asyncio
    async def test_load_api_doc(self, searcher):
        """API仕様書の読み込みテスト"""
        await searcher.load_api_doc()

        assert searcher.api_doc is not None
        assert "paths" in searcher.api_doc
        assert len(searcher._search_index) == 3  # 3つのエンドポイント

    @pytest.mark.asyncio
    async def test_search_apis_partial_match(self, searcher):
        """部分一致検索のテスト"""
        results = await searcher.search_apis(query="authorization", mode=SearchMode.PARTIAL)

        assert len(results) >= 1
        assert any("authorization" in r.path for r in results)
        assert any(r.method == "POST" for r in results)

    @pytest.mark.asyncio
    async def test_search_apis_path_query(self, searcher):
        """パス検索のテスト"""
        results = await searcher.search_apis(path_query="/api/auth/token", mode=SearchMode.EXACT)

        assert len(results) == 1
        assert results[0].path == "/api/auth/token"
        assert results[0].method == "POST"

    @pytest.mark.asyncio
    async def test_search_apis_description_query(self, searcher):
        """説明検索のテスト"""
        results = await searcher.search_apis(description_query="revoke", mode=SearchMode.PARTIAL)

        assert len(results) >= 1
        revoke_result = next(r for r in results if "revocation" in r.path)
        assert revoke_result is not None
        assert "Token" in revoke_result.tags

    @pytest.mark.asyncio
    async def test_search_apis_fuzzy_match(self, searcher):
        """あいまい検索のテスト"""
        results = await searcher.search_apis(
            query="authorizeation",  # 意図的なスペルミス
            mode=SearchMode.FUZZY,
        )

        assert len(results) >= 1
        # あいまい検索で"authorization"がヒットすることを確認
        auth_result = next((r for r in results if "authorization" in r.path), None)
        assert auth_result is not None

    @pytest.mark.asyncio
    async def test_search_apis_natural_mode(self, searcher):
        """自然言語検索のテスト"""
        results = await searcher.search_apis(
            query="token",  # より単純なクエリに変更
            mode=SearchMode.NATURAL,
        )

        assert len(results) >= 1
        # トークン関連のAPIがヒットすることを確認
        token_results = [r for r in results if "token" in r.path.lower() or "Token" in r.tags]
        assert len(token_results) >= 1

    @pytest.mark.asyncio
    async def test_search_apis_method_filter(self, searcher):
        """HTTPメソッドフィルターのテスト"""
        results = await searcher.search_apis(query="api", method_filter="POST", mode=SearchMode.PARTIAL)

        assert len(results) >= 1
        assert all(r.method == "POST" for r in results)

    @pytest.mark.asyncio
    async def test_search_apis_tag_filter(self, searcher):
        """タグフィルターのテスト"""
        results = await searcher.search_apis(query="api", tag_filter="Token", mode=SearchMode.PARTIAL)

        assert len(results) >= 1
        assert all("Token" in r.tags for r in results)

    @pytest.mark.asyncio
    async def test_search_apis_limit(self, searcher):
        """結果数制限のテスト"""
        results = await searcher.search_apis(query="api", mode=SearchMode.PARTIAL, limit=2)

        assert len(results) <= 2

    @pytest.mark.asyncio
    async def test_search_apis_no_results(self, searcher):
        """検索結果なしのテスト"""
        results = await searcher.search_apis(query="nonexistent_endpoint", mode=SearchMode.PARTIAL)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_get_api_detail(self, searcher):
        """API詳細取得のテスト"""
        detail = await searcher.get_api_detail("/api/auth/authorization", "post")

        assert detail is not None
        assert detail.path == "/api/auth/authorization"
        assert detail.method == "POST"
        assert detail.operation_id == "authorization"
        assert detail.summary == "Authorization Endpoint"
        assert "Authorization" in detail.tags
        assert len(detail.parameters) >= 1
        assert detail.request_body is not None
        assert "200" in detail.responses

    @pytest.mark.asyncio
    async def test_get_api_detail_with_sample_code(self, searcher):
        """サンプルコード付きAPI詳細取得のテスト"""
        detail = await searcher.get_api_detail("/api/auth/authorization", "post", "curl")

        assert detail is not None
        assert detail.sample_code is not None
        assert "curl -X POST" in detail.sample_code

    @pytest.mark.asyncio
    async def test_get_api_detail_nonexistent(self, searcher):
        """存在しないAPI詳細取得のテスト"""
        detail = await searcher.get_api_detail("/nonexistent/path", "get")

        assert detail is None

    @pytest.mark.asyncio
    async def test_get_api_detail_wrong_method(self, searcher):
        """間違ったHTTPメソッドでの詳細取得テスト"""
        detail = await searcher.get_api_detail(
            "/api/auth/authorization",
            "get",  # POSTのみ対応
        )

        assert detail is None

    @pytest.mark.asyncio
    async def test_search_index_building(self, searcher):
        """検索インデックス構築のテスト"""
        await searcher.load_api_doc()

        assert len(searcher._search_index) == 3

        # 各インデックス項目の構造を確認
        index_item = searcher._search_index[0]
        required_keys = [
            "path",
            "method",
            "operation_id",
            "summary",
            "description",
            "tags",
            "sample_languages",
            "search_text",
            "operation",
        ]
        for key in required_keys:
            assert key in index_item

    @pytest.mark.asyncio
    async def test_sample_languages_extraction(self, searcher):
        """サンプルコード言語抽出のテスト"""
        results = await searcher.search_apis(path_query="/api/auth/authorization", mode=SearchMode.EXACT)

        assert len(results) == 1
        result = results[0]
        assert "curl" in result.sample_languages
        assert "javascript" in result.sample_languages

    @pytest.mark.asyncio
    async def test_score_calculation(self, searcher):
        """スコア計算のテスト"""
        results = await searcher.search_apis(query="authorization", mode=SearchMode.FUZZY)

        assert len(results) >= 1
        # スコア順にソートされていることを確認
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    @pytest.mark.asyncio
    async def test_case_insensitive_search(self, searcher):
        """大文字小文字を無視する検索のテスト"""
        results_lower = await searcher.search_apis(query="authorization", mode=SearchMode.PARTIAL)

        results_upper = await searcher.search_apis(query="AUTHORIZATION", mode=SearchMode.PARTIAL)

        results_mixed = await searcher.search_apis(query="Authorization", mode=SearchMode.PARTIAL)

        # 大文字小文字に関係なく同じ結果が得られることを確認
        assert len(results_lower) == len(results_upper) == len(results_mixed)


@pytest.mark.integration
class TestAuthleteApiSearcherIntegration:
    """実際のOpenAPI仕様書を使用する統合テスト"""

    def test_real_openapi_spec_exists(self):
        """実際のOpenAPI仕様書ファイルの存在確認"""
        spec_path = Path(__file__).parent.parent / "resources" / "openapi-spec.json"
        assert spec_path.exists(), f"OpenAPI仕様書が見つかりません: {spec_path}"

    @pytest.mark.asyncio
    async def test_load_real_spec(self):
        """実際のOpenAPI仕様書の読み込みテスト"""
        searcher = AuthleteApiSearcher()
        await searcher.load_api_doc()

        assert searcher.api_doc is not None
        assert "paths" in searcher.api_doc
        assert len(searcher._search_index) > 0

    @pytest.mark.asyncio
    async def test_search_real_apis(self):
        """実際のAPIに対する検索テスト"""
        searcher = AuthleteApiSearcher()

        # よく使われそうなキーワードで検索
        test_queries = ["service", "client", "token", "authorization", "revocation"]

        for query in test_queries:
            results = await searcher.search_apis(query=query, mode=SearchMode.PARTIAL, limit=5)
            # 何らかの結果が得られることを確認
            assert isinstance(results, list)
            # 結果が多すぎないことを確認
            assert len(results) <= 5


if __name__ == "__main__":
    pytest.main([__file__])
