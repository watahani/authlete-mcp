#!/usr/bin/env python3
"""
OpenAPI仕様書からBM25検索用DuckDBデータベースを構築するスクリプト

DuckDBのFull Text Search (FTS)機能を使用してBM25ベースの検索インデックスを作成します。
"""

import json
import logging
from pathlib import Path
from typing import Any

import duckdb
import jsonref

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenAPISearchDatabase:
    """OpenAPI仕様書から検索用データベースを構築するクラス"""

    def __init__(self, db_path: str = "resources/authlete_apis.duckdb"):
        """初期化

        Args:
            db_path: DuckDBデータベースファイルのパス
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(str(self.db_path))

    def setup_database_schema(self) -> None:
        """データベーススキーマとFTSインデックスを作成"""
        logger.info("データベーススキーマを作成中...")

        # まず、既存のテーブルがあれば削除
        self.conn.execute("DROP TABLE IF EXISTS api_endpoints")
        self.conn.execute("DROP TABLE IF EXISTS api_schemas")

        # API エンドポイント用のテーブル作成
        self.conn.execute("""
            CREATE TABLE api_endpoints (
                id INTEGER PRIMARY KEY,
                path VARCHAR NOT NULL,
                method VARCHAR NOT NULL,
                operation_id VARCHAR,
                summary VARCHAR,
                description TEXT,
                tags VARCHAR[], -- JSON array as text
                parameters TEXT, -- JSON as text
                request_body TEXT, -- JSON as text
                responses TEXT, -- JSON as text
                sample_languages VARCHAR[], -- Available sample code languages
                sample_codes TEXT, -- JSON object with language -> code mapping
                search_content TEXT NOT NULL, -- Combined searchable text
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # API スキーマ用のテーブル作成
        self.conn.execute("CREATE SEQUENCE IF NOT EXISTS api_schemas_seq START 1")
        self.conn.execute("""
            CREATE TABLE api_schemas (
                id INTEGER PRIMARY KEY DEFAULT nextval('api_schemas_seq'),
                schema_name VARCHAR NOT NULL,
                schema_type VARCHAR, -- object, array, string, etc.
                title VARCHAR,
                description TEXT,
                properties TEXT, -- JSON properties as text
                required_fields VARCHAR[], -- Array of required field names
                example_value TEXT, -- JSON example
                search_content TEXT NOT NULL, -- Combined searchable text
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # FTSインデックスの作成 (BM25対応)
        logger.info("FTSインデックスを作成中...")

        try:
            # DuckDBのFTSエクステンションをロード
            self.conn.execute("INSTALL fts")
            self.conn.execute("LOAD fts")

            # search_contentフィールドにFTSインデックスを作成
            self.conn.execute("""
                PRAGMA create_fts_index(
                    'api_endpoints',
                    'id',
                    'search_content'
                )
            """)

            # スキーマテーブル用のFTSインデックス作成
            self.conn.execute("""
                PRAGMA create_fts_index(
                    'api_schemas',
                    'id',
                    'search_content'
                )
            """)
            logger.info("FTSインデックス作成成功")
        except Exception as e:
            logger.warning(f"FTSインデックス作成失敗（通常検索を使用）: {str(e)}")

        logger.info("データベーススキーマ作成完了")

    def extract_api_data(self, openapi_spec_path: str) -> list[dict[str, Any]]:
        """OpenAPI仕様書からAPI情報を抽出

        Args:
            openapi_spec_path: OpenAPI仕様書のパス

        Returns:
            API情報のリスト
        """
        logger.info(f"OpenAPI仕様書を読み込み中: {openapi_spec_path}")

        with open(openapi_spec_path, encoding="utf-8") as f:
            api_doc = jsonref.load(f)

        api_data = []
        api_id = 1

        if "paths" not in api_doc:
            logger.warning("OpenAPI仕様書にpathsセクションが見つかりません")
            return api_data

        for path, path_item in api_doc["paths"].items():
            if not isinstance(path_item, dict):
                continue

            for method, operation in path_item.items():
                if not isinstance(operation, dict) or method.startswith("x-"):
                    continue

                # 基本情報の抽出
                operation_id = operation.get("operationId")
                summary = operation.get("summary", "")
                description = operation.get("description", "")
                tags = operation.get("tags", [])

                # パラメータ情報の統合
                parameters = []
                if "parameters" in operation:
                    parameters.extend(operation["parameters"])
                if "parameters" in path_item:
                    parameters.extend(path_item["parameters"])

                # リクエストボディ
                request_body = operation.get("requestBody")

                # レスポンス
                responses = operation.get("responses", {})

                # サンプルコードの抽出
                code_samples = operation.get("x-code-samples", [])
                sample_languages = []
                sample_codes = {}

                for sample in code_samples:
                    lang = sample.get("lang", "")
                    source = sample.get("source", "")
                    if lang:
                        sample_languages.append(lang)
                        sample_codes[lang] = source

                # 検索用コンテンツの構築（リクエスト・レスポンスを除外し、重要度順に構築）
                search_content_parts = [
                    # 最重要：パスとサマリー
                    path,
                    summary,
                    # 重要：説明とオペレーションID
                    description,
                    operation_id or "",
                    # 中程度：メソッドとタグ
                    method.upper(),
                    " ".join(tags),
                ]

                # パラメータ名のみ含める（説明は除外してノイズを減らす）
                for param in parameters:
                    if isinstance(param, dict):
                        param_name = param.get("name", "")
                        if param_name:
                            search_content_parts.append(param_name)

                search_content = " ".join(filter(None, search_content_parts))

                api_data.append(
                    {
                        "id": api_id,
                        "path": path,
                        "method": method.upper(),
                        "operation_id": operation_id,
                        "summary": summary or "",
                        "description": description or "",
                        "tags": json.dumps(tags),
                        "parameters": json.dumps(parameters),
                        "request_body": json.dumps(request_body, default=str) if request_body else None,
                        "responses": json.dumps(responses, default=str),
                        "sample_languages": json.dumps(sample_languages),
                        "sample_codes": json.dumps(sample_codes),
                        "search_content": search_content,
                    }
                )

                api_id += 1

        logger.info(f"抽出したAPI数: {len(api_data)}")
        return api_data

    def insert_api_data(self, api_data: list[dict[str, Any]]) -> None:
        """APIデータをデータベースに挿入

        Args:
            api_data: 挿入するAPIデータのリスト
        """
        logger.info("APIデータをデータベースに挿入中...")

        # バッチ挿入のためのプレースホルダー
        placeholders = ", ".join(["?" for _ in range(13)])  # 13個のカラム

        insert_sql = f"""
            INSERT INTO api_endpoints (
                id, path, method, operation_id, summary, description, tags,
                parameters, request_body, responses, sample_languages,
                sample_codes, search_content
            ) VALUES ({placeholders})
        """

        # データを挿入用のタプルのリストに変換
        insert_data = []
        for item in api_data:
            insert_data.append(
                (
                    item["id"],
                    item["path"],
                    item["method"],
                    item["operation_id"],
                    item["summary"],
                    item["description"],
                    item["tags"],
                    item["parameters"],
                    item["request_body"],
                    item["responses"],
                    item["sample_languages"],
                    item["sample_codes"],
                    item["search_content"],
                )
            )

        # バッチ挿入実行
        self.conn.executemany(insert_sql, insert_data)
        self.conn.commit()

        logger.info(f"データベースに {len(api_data)} 件のAPIを挿入完了")

    def optimize_database(self) -> None:
        """データベースを最適化"""
        logger.info("データベースを最適化中...")

        # 統計情報を更新
        self.conn.execute("ANALYZE")

        # VACUUMでデータベースを圧縮
        self.conn.execute("VACUUM")

        logger.info("データベース最適化完了")

    def test_search(self) -> None:
        """検索機能のテスト"""
        logger.info("検索機能をテスト中...")

        # BM25スコア付きでのテスト検索
        test_queries = ["revoke token", "create client", "authorization endpoint", "service configuration"]

        for query in test_queries:
            logger.info(f"検索クエリ: '{query}'")

            # DuckDBのFTSクエリ実行
            try:
                # まずFTSクエリを試行
                result = self.conn.execute(
                    """
                    SELECT path, method, summary, description, score
                    FROM (
                        SELECT a.*, fts.score
                        FROM api_endpoints a
                        JOIN (SELECT rowid, score FROM fts_main_api_endpoints(?)) fts
                        ON a.id = fts.rowid
                        ORDER BY fts.score DESC
                        LIMIT 3
                    )
                """,
                    [query],
                ).fetchall()

                # FTSが使えない場合は通常の検索にフォールバック
                if not result:
                    # クエリを個別の単語に分割してOR検索
                    words = query.lower().split()
                    where_conditions = []
                    params = []

                    for word in words:
                        where_conditions.append("LOWER(search_content) LIKE ?")
                        params.append(f"%{word}%")

                    where_clause = " OR ".join(where_conditions)

                    result = self.conn.execute(
                        f"""
                        SELECT path, method, summary, description, 0 as score
                        FROM api_endpoints
                        WHERE {where_clause}
                        LIMIT 3
                    """,
                        params,
                    ).fetchall()

            except Exception as e:
                logger.warning(f"FTS検索失敗、フォールバック検索実行: {str(e)}")
                # フォールバック: 単純な部分一致検索
                words = query.lower().split()
                where_conditions = []
                params = []

                for word in words:
                    where_conditions.append("LOWER(search_content) LIKE ?")
                    params.append(f"%{word}%")

                where_clause = " OR ".join(where_conditions)

                try:
                    result = self.conn.execute(
                        f"""
                        SELECT path, method, summary, description, 0 as score
                        FROM api_endpoints
                        WHERE {where_clause}
                        LIMIT 3
                    """,
                        params,
                    ).fetchall()
                except Exception as e2:
                    logger.error(f"フォールバック検索も失敗: {str(e2)}")
                    result = []

            if result:
                for row in result:
                    if len(row) == 5:  # スコア付き
                        path, method, summary, desc, score = row
                        logger.info(f"  - {method} {path}: {summary} (score: {score})")
                    else:  # スコアなし
                        path, method, summary, desc = row
                        logger.info(f"  - {method} {path}: {summary}")
            else:
                logger.info("  検索結果なし")
            logger.info("")

    def extract_schema_data(self, openapi_spec_path: str) -> list[dict[str, Any]]:
        """OpenAPI仕様書からスキーマ情報を抽出

        Args:
            openapi_spec_path: OpenAPI仕様書のパス

        Returns:
            スキーマ情報のリスト
        """
        with open(openapi_spec_path, encoding="utf-8") as f:
            spec = json.load(f)

        # $refを解決
        spec = jsonref.loads(json.dumps(spec))

        schemas_data = []

        # components.schemasを抽出
        components = spec.get("components", {})
        schemas = components.get("schemas", {})

        for schema_name, schema_def in schemas.items():
            if not isinstance(schema_def, dict):
                continue

            schema_type = schema_def.get("type", "object")
            title = schema_def.get("title", "")
            description = schema_def.get("description", "")

            # プロパティを文字列として保存
            try:
                properties_data = schema_def.get("properties", {})
                # 循環参照や複雑なオブジェクトを処理するため、defaultオプションを使用
                properties = json.dumps(properties_data, ensure_ascii=False, default=str)
            except (TypeError, ValueError) as e:
                logger.warning(f"スキーマ {schema_name} のプロパティをJSONシリアライズできません: {e}")
                properties = "{}"

            # 必須フィールドの抽出（JSON文字列として保存）
            required_fields = schema_def.get("required", [])

            # サンプル値の抽出
            example_value = ""
            if "example" in schema_def:
                try:
                    example_value = json.dumps(schema_def["example"], ensure_ascii=False, default=str)
                except (TypeError, ValueError) as e:
                    logger.warning(f"スキーマ {schema_name} のexample値をJSONシリアライズできません: {e}")
                    example_value = str(schema_def["example"])

            # 検索用コンテンツの作成
            search_parts = [
                schema_name,
                title,
                description,
                schema_type,
            ]

            # プロパティ名も検索対象に追加
            if "properties" in schema_def:
                for prop_name, prop_def in schema_def["properties"].items():
                    search_parts.append(prop_name)
                    if isinstance(prop_def, dict) and "description" in prop_def:
                        search_parts.append(prop_def["description"])

            search_content = " ".join(filter(None, search_parts))

            schema_data = {
                "schema_name": schema_name,
                "schema_type": schema_type,
                "title": title,
                "description": description,
                "properties": properties,
                "required_fields": required_fields,
                "example_value": example_value,
                "search_content": search_content,
            }

            schemas_data.append(schema_data)

        logger.info(f"抽出されたスキーマ数: {len(schemas_data)}")
        return schemas_data

    def insert_schema_data(self, schemas_data: list[dict[str, Any]]) -> None:
        """スキーマデータをデータベースに挿入

        Args:
            schemas_data: スキーマデータのリスト
        """
        logger.info(f"スキーマデータを挿入中... ({len(schemas_data)}件)")

        for i, schema in enumerate(schemas_data, 1):
            try:
                self.conn.execute(
                    """
                    INSERT INTO api_schemas (
                        schema_name, schema_type, title, description,
                        properties, required_fields, example_value, search_content
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        schema["schema_name"],
                        schema["schema_type"],
                        schema["title"],
                        schema["description"],
                        schema["properties"],
                        schema["required_fields"],  # Python list -> DuckDB VARCHAR[]
                        schema["example_value"],
                        schema["search_content"],
                    ),
                )

                if i % 100 == 0:
                    logger.info(f"  挿入済み: {i}/{len(schemas_data)}")

            except Exception as e:
                logger.error(f"スキーマデータ挿入エラー ({schema['schema_name']}): {str(e)}")

        logger.info("スキーマデータ挿入完了")

    def get_database_stats(self) -> dict[str, Any]:
        """データベースの統計情報を取得"""
        stats = {}

        # テーブルの行数
        result = self.conn.execute("SELECT COUNT(*) FROM api_endpoints").fetchone()
        stats["total_apis"] = result[0] if result else 0

        # スキーマテーブルの行数
        try:
            result = self.conn.execute("SELECT COUNT(*) FROM api_schemas").fetchone()
            stats["total_schemas"] = result[0] if result else 0
        except Exception:
            stats["total_schemas"] = 0

        # メソッド別統計
        result = self.conn.execute("""
            SELECT method, COUNT(*)
            FROM api_endpoints
            GROUP BY method
            ORDER BY COUNT(*) DESC
        """).fetchall()
        stats["methods"] = dict(result) if result else {}

        # タグ別統計（上位5つ）
        result = self.conn.execute("""
            SELECT json_extract_string(tags, '$[0]') as primary_tag, COUNT(*)
            FROM api_endpoints
            WHERE json_extract_string(tags, '$[0]') IS NOT NULL
            GROUP BY primary_tag
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """).fetchall()
        stats["top_tags"] = dict(result) if result else {}

        # データベースサイズ
        stats["database_size_mb"] = self.db_path.stat().st_size / 1024 / 1024

        return stats

    def close(self) -> None:
        """データベース接続を閉じる"""
        if self.conn:
            self.conn.close()


def main():
    """メイン処理"""
    # パス設定
    openapi_spec_path = "resources/openapi-spec.json"
    db_path = "resources/authlete_apis.duckdb"

    # OpenAPI仕様書の存在確認
    if not Path(openapi_spec_path).exists():
        logger.error(f"OpenAPI仕様書が見つかりません: {openapi_spec_path}")
        return 1

    try:
        # データベース作成
        db = OpenAPISearchDatabase(db_path)

        # スキーマ作成
        db.setup_database_schema()

        # データ抽出と挿入
        api_data = db.extract_api_data(openapi_spec_path)
        if not api_data:
            logger.error("APIデータが抽出できませんでした")
            return 1

        db.insert_api_data(api_data)

        # スキーマデータの抽出と挿入
        schema_data = db.extract_schema_data(openapi_spec_path)
        if not schema_data:
            logger.warning("スキーマデータが抽出できませんでした")
        else:
            db.insert_schema_data(schema_data)

        # 最適化
        db.optimize_database()

        # 統計情報表示
        stats = db.get_database_stats()
        logger.info("データベース統計:")
        logger.info(f"  総API数: {stats['total_apis']}")
        logger.info(f"  総スキーマ数: {stats['total_schemas']}")
        logger.info(f"  HTTPメソッド別: {stats['methods']}")
        logger.info(f"  主要タグ: {stats['top_tags']}")
        logger.info(f"  DBサイズ: {stats['database_size_mb']:.2f} MB")

        # 検索テスト
        db.test_search()

        # クリーンアップ
        db.close()

        logger.info(f"検索データベース作成完了: {db_path}")
        return 0

    except Exception as e:
        logger.error(f"データベース作成中にエラー: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
