# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a unified Authlete MCP (Model Context Protocol) Server that provides comprehensive tools for:
1. **Managing Authlete services and clients** through a standardized interface
2. **Advanced API search** with natural language query capabilities and DuckDB-powered full-text search

The server acts as a bridge between MCP clients (like Claude Desktop) and Authlete's OAuth/OpenID Connect services, while also providing intelligent search capabilities for Authlete's API documentation.

## Architecture

- **Modular structure**: Code is organized in `src/authlete_mcp/` with clear separation of concerns
- **FastMCP-based**: Uses FastMCP framework for simplified MCP server development
- **Async/await pattern**: All API operations are asynchronous using `httpx` for HTTP requests
- **DuckDB search engine**: `AuthleteApiSearcher` class in `src/authlete_mcp/search.py` provides fast, full-text search capabilities
- **Two API endpoints**: 
  - Authlete API (`AUTHLETE_BASE_URL`) for service/client management
  - Authlete IdP API (`AUTHLETE_IDP_URL`) for service creation/deletion operations
- **Search database**: `resources/authlete_apis.duckdb` contains indexed API documentation for fast search

### Module Structure
```
src/authlete_mcp/
├── server.py              # Main MCP server with tool registration
├── config.py              # Configuration and environment variables
├── search.py              # AuthleteApiSearcher search engine
├── models/
│   └── base.py           # Data models (Scope, ServiceDetail, etc.)
├── api/
│   └── client.py         # HTTP client for Authlete APIs
└── tools/                # MCP tools organized by functionality
    ├── service_tools.py  # Service management (7 tools)
    ├── client_tools.py   # Client management (16 tools)
    ├── token_tools.py    # Token operations (5 tools)
    ├── jose_tools.py     # JOSE operations (2 tools)
    ├── search_tools.py   # API/schema search (5 tools)
    └── utility_tools.py  # Utilities like JWKS generation (1 tool)
```

## Development Commands

```bash
# Install dependencies
uv sync

# Run the MCP server
uv run python main.py

# Run tests
uv run pytest                           # Run all tests
uv run pytest -m unit                  # Run only unit tests (no API calls)
uv run pytest -m integration           # Run integration tests (requires AUTHLETE_INTEGRATION_TOKEN)
uv run pytest tests/test_mcp_connection.py  # Run specific test file
uv run pytest -v                       # Verbose output
uv run pytest --tb=long                # Detailed traceback

# Create/update search database
uv run python scripts/create_search_database.py  # Create resources/authlete_apis.duckdb from OpenAPI spec

# Update OpenAPI specification
uv run python scripts/update_openapi_spec.py  # Update resources/openapi-spec.json from latest Authlete docs

# Clean up test services
uv run python scripts/cleanup_test_services.py  # Delete services with "pytest-" prefix

# Lint and format code
uv run ruff check src/ tests/ scripts/ main.py    # Check for linting errors
uv run ruff format src/ tests/ scripts/ main.py   # Auto-format files
uv run ruff check --fix src/ tests/ scripts/      # Auto-fix fixable errors

# Lint YAML files
uv run yamllint .github/                # Lint YAML files with yamllint

# Set up Git hooks for automated quality checks
./setup-hooks.sh                        # Install pre-commit hooks (run once)
# Pre-commit hooks will automatically run: linting, formatting, tests, and database validation
```

## Environment Configuration

Required environment variables:
- `ORGANIZATION_ACCESS_TOKEN`: Organization access token (required for all operations)
- `ORGANIZATION_ID`: Default organization ID (optional, can be overridden per function)
- `AUTHLETE_BASE_URL`: API base URL (defaults to "https://jp.authlete.com")
- `AUTHLETE_IDP_URL`: IdP URL (defaults to "https://login.authlete.com") 
- `AUTHLETE_API_SERVER_ID`: API Server ID (defaults to "53285")

For integration testing, the same environment variables from .env are used.

## Key Implementation Details

### Tool Categories
- **Service Management** (`service_tools.py`): Create, read, update, delete services via both direct API and IdP API
- **Client Management** (`client_tools.py`): Full CRUD operations for OAuth clients including secret rotation and locking
- **Token Management** (`token_tools.py`): Access token lifecycle management
- **JOSE Operations** (`jose_tools.py`): JWT/JWS/JWE generation and verification
- **API Search Tools** (`search_tools.py`): Natural language search, API details retrieval, and sample code generation
- **Utility Tools** (`utility_tools.py`): JWKS generation and other utilities

### Error Handling Pattern
- All tools return JSON strings, with errors prefixed as "Error: ..."
- HTTP errors extract Authlete API `resultMessage` when available
- JSON parsing errors are caught and returned as formatted error strings

### API Authentication
- Uses Bearer token authentication with the organization access token
- Supports both organization-level tokens and service-specific API keys
- Service API keys can be passed as optional parameters to override default authentication

### Configuration Models
- `AuthleteConfig`: Base configuration with API credentials and endpoints
- `ServiceDetail`: Comprehensive service configuration following Authlete schema
- `Scope`: OAuth scope definition with name and default entry flag
- `AuthleteApiSearcher`: DuckDB-based search engine with natural language processing capabilities

### Reference Resources
When implementing new Authlete API tools, please refer to these resource files:
- `resources/postman_collection.json`: Complete Postman collection with all available Authlete API endpoints, request formats, and expected responses
- `resources/openapi-spec.json`: OpenAPI specification for Authlete API with detailed schema definitions and parameter descriptions
- `resources/authlete_apis.duckdb`: Search database containing indexed API documentation for fast retrieval

These resources provide authoritative examples of:
- Correct API endpoint URLs and HTTP methods
- Required and optional request parameters
- Request body structures and data types
- Expected response formats and status codes
- Authentication requirements for each endpoint

## Testing Structure

Tests are organized using pytest with direct async context management:
- `tests/test_simple_connection.py`: Basic MCP server connection and tool discovery
- `tests/test_service_operations.py`: Service management operations 
- `tests/test_client_operations.py`: Client management operations
- `tests/test_error_handling.py`: Error scenarios and edge cases

Test markers:
- `@pytest.mark.unit`: Unit tests that don't require real API credentials (use mock tokens)
- `@pytest.mark.integration`: Integration tests that require real Authlete API access

Each test creates its own MCP client session using `stdio_client` and `ClientSession` directly, avoiding pytest-asyncio fixture complications.

## Common Patterns

When implementing or modifying MCP tools, follow these established patterns:

### Parameter Validation Order
1. **Service API Key Validation**: Always check `service_api_key` parameter is provided for operations requiring it
2. **Required Parameters**: Validate all required parameters (e.g., `client_id`, `access_token`, etc.)
3. **JSON Parsing**: Parse JSON parameters using `json.loads()` with proper error handling
4. **Environment Variables**: Check for `ORGANIZATION_ACCESS_TOKEN` (organization token) existence last

### Error Handling Patterns
- All tools return JSON strings, with errors prefixed as "Error: ..."
- Parameter validation errors: `"Error: [parameter_name] parameter is required"`
- JSON parsing errors: `"Error parsing [data_type] JSON: {error_details}"`
- Environment errors: `"Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"`
- API errors: Extract and return Authlete API `resultMessage` when available

### Authentication Patterns
- **Client Operations**: Always require `service_api_key` parameter (no fallback to organization token)
- **Service Operations**: Use `service_api_key` if provided, otherwise fall back to `ORGANIZATION_ACCESS_TOKEN`
- **Token/JOSE Operations**: Always require `service_api_key` parameter

### API Response Handling
1. **HTTP 204 No Content**: Handle as successful deletion/update operations
2. **Success Responses**: Return formatted JSON using `json.dumps(result, indent=2)`
3. **Deletion Success Messages**: Return clear success messages like `"Service deleted successfully (ID: {id})"`
4. **API Endpoints**: 
   - Use Authlete API (`AUTHLETE_BASE_URL`) for most operations
   - Use Authlete IdP API (`AUTHLETE_IDP_URL`) for service creation/deletion operations

### Tool Categories and Patterns
- **Service Management**: Support both direct API and IdP API operations
- **Client Management**: Full CRUD operations with mandatory service API key validation
- **Token Management**: Access token lifecycle management with service API key requirement
- **Extended Client Operations**: Authorization, scopes, and token management for clients
- **JOSE Operations**: JWT/JWS/JWE generation and verification utilities

## GitHub Development Workflow

このプロジェクトでは、機能追加やバグ修正において以下のGitHubワークフローを採用します。

**重要**: このプロジェクトではGitHub操作にGitHub MCPを使用します。Claude CodeがGitHub MCP (Model Context Protocol) を通じて、プルリクエストの作成、マージ、ワークフロー管理を自動化します。手動でGitHub CLIコマンドを実行する必要はありません。

### ブランチ戦略
- **main**: 安定版リリースブランチ。常にデプロイ可能な状態を維持
- **feature branches**: 機能追加・修正用のブランチ（命名規則: `feature/issue-description`, `fix/bug-description`）

### 基本的な開発フロー

1. **Issue作成 (Optional)**
   ```bash
   # GitHubでIssueを作成して作業内容を明確化
   # 特に大きな機能追加の場合は必須
   ```

2. **機能ブランチの作成**
   ```bash
   # mainから最新のブランチを作成
   git checkout main
   git pull origin main
   git checkout -b feature/add-new-api-endpoints
   ```

3. **開発・テスト・コミット**
   ```bash
   # 開発
   # 必ずテストを実行してから次のステップへ
   uv run pytest -m unit
   uv run ruff check src/ tests/ scripts/
   uv run ruff format src/ tests/ scripts/
   
   # コミット
   git add .
   git commit -m "feat: add new token management API endpoints
   
   - Add list_issued_tokens, create_access_token, update_access_token
   - Add comprehensive test coverage for token operations  
   - Update OpenAPI spec with new endpoints
   
   🤖 Generated with [Claude Code](https://claude.ai/code)
   
   Co-Authored-By: Claude <noreply@anthropic.com>"
   ```

4. **プルリクエスト作成**
   ```bash
   # ブランチをプッシュ
   git push origin feature/add-new-api-endpoints
   ```
   
   **GitHub MCP使用**: プルリクエストの作成は`mcp__github__create_pull_request`ツールを使用します。Claude Codeが自動的に以下の処理を行います：
   - `mcp__github__create_branch`: 新しいブランチ作成（必要に応じて）
   - `mcp__github__create_pull_request`: 適切なタイトルと説明でPR作成
   - `mcp__github__update_pull_request`: レビューワーの設定やラベル追加

5. **レビュープロセス**
   ```bash
   # レビューリクエスト（自動的にwatahaniがレビューワーに設定されます）
   # GitHub Actionsによる自動チェック
   # - Tests (複数Python版でのテスト実行)
   # - Linting and Formatting
   # - Security Scan (bandit)
   # - YAML Lint
   ```

6. **マージ**
   **GitHub MCP使用**: マージは`mcp__github__merge_pull_request`ツールを使用します：
   ```
   mcp__github__merge_pull_request:
   - merge_method: "squash" (Squash and Merge)
   - commit_title: 適切なコミットタイトル
   - commit_message: 詳細なコミットメッセージ
   ```
   ブランチは自動削除される設定です。

### PR作成時のガイドライン

#### PRタイトル規則
- `feat: 新機能追加の説明`
- `fix: バグ修正の説明`  
- `docs: ドキュメント更新`
- `test: テスト追加・修正`
- `refactor: リファクタリング`
- `chore: 依存関係更新、設定変更等`

#### PR説明テンプレート
```markdown
## Summary
- 変更内容の箇条書きサマリー
- なぜこの変更が必要なのかの背景

## Test plan
- [ ] Unit tests pass (pytest -m unit)  
- [ ] Integration tests pass (pytest -m integration) ※実際のAPI呼び出しが必要な場合
- [ ] Code quality checks pass (ruff check/format)
- [ ] Manual testing completed ※手動テストが必要な場合

## Breaking Changes
- 破壊的変更がある場合のみ記載
- API変更、設定変更等

🤖 Generated with [Claude Code](https://claude.ai/code)
```

### レビュー観点
1. **機能性**: 要求仕様を満たしているか
2. **コード品質**: 既存パターンに従っているか、可読性は十分か
3. **テスト**: 適切なテストカバレッジがあるか
4. **パフォーマンス**: パフォーマンスに影響がないか
5. **セキュリティ**: セキュリティリスクがないか
6. **文書化**: 必要に応じてドキュメントが更新されているか

### GitHub Actions自動チェック
- **Test Workflow**: Python 3.10-3.12での単体・統合テスト
- **CI Workflow**: API互換性チェック、パフォーマンステスト、カバレッジ生成
- **OpenAPI Spec Update**: 毎日自動でAuthlete仕様書をチェック・更新PR作成

### CI/CD失敗時の対応

GitHub Actionsでlintingやテストが失敗した場合の修正方法：

#### Lintingエラーの修正
```bash
# エラーの確認
uv run ruff check authlete_mcp_server.py tests/

# 自動修正可能なエラーを修正
uv run ruff check --fix authlete_mcp_server.py tests/

# フォーマットの修正
uv run ruff format authlete_mcp_server.py tests/

```

## YOU SHOULD DO

1. Please respond in Japanese.