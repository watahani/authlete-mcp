# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Authlete MCP (Model Context Protocol) Server that provides tools for managing Authlete services and clients through a standardized interface. The server acts as a bridge between MCP clients (like Claude Desktop) and Authlete's OAuth/OpenID Connect services.

## Architecture

- **Single server file**: `authlete_mcp_server.py` contains all MCP tools and API integration logic
- **FastMCP-based**: Uses FastMCP framework for simplified MCP server development
- **Async/await pattern**: All API operations are asynchronous using `httpx` for HTTP requests
- **Two API endpoints**: 
  - Authlete API (`AUTHLETE_BASE_URL`) for service/client management
  - Authlete IdP API (`AUTHLETE_IDP_URL`) for service creation/deletion operations

## Development Commands

```bash
# Install dependencies
uv sync

# Run the MCP server
uv run authlete_mcp_server.py

# Run tests
uv run pytest                           # Run all tests
uv run pytest -m unit                  # Run only unit tests (no API calls)
uv run pytest -m integration           # Run integration tests (requires AUTHLETE_INTEGRATION_TOKEN)
uv run pytest tests/test_mcp_connection.py  # Run specific test file
uv run pytest -v                       # Verbose output
uv run pytest --tb=long                # Detailed traceback

# Update OpenAPI specification
uv run python scripts/update_openapi_spec.py  # Update resources/openapi-spec.json from latest Authlete docs

# Lint and format code
ruff check authlete_mcp_server.py
ruff format authlete_mcp_server.py
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
- **Service Management**: Create, read, update, delete services via both direct API and IdP API
- **Client Management**: Full CRUD operations for OAuth clients including secret rotation and locking

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

### Reference Resources
When implementing new Authlete API tools, please refer to these resource files:
- `resources/postman_collection.json`: Complete Postman collection with all available Authlete API endpoints, request formats, and expected responses
- `resources/openapi-spec.json`: OpenAPI specification for Authlete API with detailed schema definitions and parameter descriptions

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
4. **Environment Variables**: Check for `DEFAULT_API_KEY` (organization token) existence last

### Error Handling Patterns
- All tools return JSON strings, with errors prefixed as "Error: ..."
- Parameter validation errors: `"Error: [parameter_name] parameter is required"`
- JSON parsing errors: `"Error parsing [data_type] JSON: {error_details}"`
- Environment errors: `"Error: ORGANIZATION_ACCESS_TOKEN environment variable not set"`
- API errors: Extract and return Authlete API `resultMessage` when available

### Authentication Patterns
- **Client Operations**: Always require `service_api_key` parameter (no fallback to organization token)
- **Service Operations**: Use `service_api_key` if provided, otherwise fall back to `DEFAULT_API_KEY`
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

## YOU SHOUD DO

1. Please respond in Japanese.