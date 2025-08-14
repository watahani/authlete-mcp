# Authlete MCP Server

A unified Model Context Protocol (MCP) server that provides comprehensive tools for:
1. **Authlete Service Management**: Managing Authlete services and clients through a standardized interface
2. **Advanced API Search**: Natural language search capabilities for Authlete OpenAPI specifications with fuzzy matching and semantic search

**⚠️ Compatibility Note**: This server supports **Authlete 3.0 only**. It is not compatible with Authlete 2.3.

## Architecture

The server follows a modular architecture with clear separation of concerns:

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
    ├── service_tools.py  # Service management (8 tools)
    ├── client_tools.py   # Client management (17 tools)
    ├── token_tools.py    # Token operations (5 tools)
    ├── jose_tools.py     # JOSE operations (2 tools)
    ├── search_tools.py   # API/schema search (5 tools)
    └── utility_tools.py  # Utilities like JWKS generation (1 tool)
```

### Reference Resources

When implementing new Authlete API tools, please refer to these resource files:
- `resources/postman_collection.json`: Postman collection for Authlete service and client management APIs including service operations, client operations, and tool-related endpoints
- `resources/openapi-spec.json`: OpenAPI specification for Authlete API with detailed schema definitions and parameter descriptions
- `resources/idp-openapi-spec.json`: Authlete IdP API specification for service creation and deletion operations (service create and service remove endpoints only)

These resources provide authoritative examples of:
- Correct API endpoint URLs and HTTP methods
- Required and optional request parameters
- Request body structures and data types
- Expected response formats and status codes
- Authentication requirements for each endpoint

## Features

### Service Management Tools
- `create_service`: Create a new Authlete service with basic configuration
- `create_service_detailed`: Create a new Authlete service with comprehensive configuration
- `get_service_schema_example`: Get an example service configuration schema
- `get_service`: Retrieve a service by API key
- `list_services`: List all services
- `update_service`: Update service configuration (full overwrite)
- `patch_service`: Partially update service configuration (merges with current data)
- `delete_service`: Delete a service via IdP

### Client Management
- `create_client`: Create a new OAuth client
- `get_client`: Retrieve a client by ID
- `list_clients`: List all clients for a service
- `update_client`: Update client configuration (full overwrite)
- `patch_client`: Partially update client configuration (merges with current data)
- `delete_client`: Delete a client
- `rotate_client_secret`: Generate new client secret
- `update_client_secret`: Update client secret manually
- `update_client_lock`: Lock or unlock a client

### Extended Client Operations
- `get_authorized_applications`: Get authorized applications for a subject
- `update_client_tokens`: Update client tokens for a subject
- `delete_client_tokens`: Delete client tokens for a subject
- `get_granted_scopes`: Get granted scopes for a client and subject
- `delete_granted_scopes`: Delete granted scopes for a client and subject
- `get_requestable_scopes`: Get requestable scopes for a client
- `update_requestable_scopes`: Update requestable scopes for a client
- `delete_requestable_scopes`: Delete requestable scopes for a client

### Token Operations
- `list_issued_tokens`: List issued tokens for a service
- `create_access_token`: Create an access token
- `update_access_token`: Update an access token
- `revoke_access_token`: Revoke an access token
- `delete_access_token`: Delete an access token

### JOSE Operations
- `generate_jose`: Generate JOSE (JSON Web Signature/Encryption) object
- `verify_jose`: Verify JOSE (JSON Web Signature/Encryption) object

### Advanced API Search Tools 🆕
- `search_apis`: Natural language API search with semantic matching and relevance scoring
- `get_api_detail`: Detailed API information with parameters, request/response schemas, and sample code
  - **Context Optimization**: Advanced filtering options for description and body content (up to 96% size reduction)
  - **Smart Defaults**: Optimized for LLM context efficiency while maintaining useful information
- `get_sample_code`: Language-specific code samples for API endpoints
- `list_schemas`: List or search OpenAPI schemas
- `get_schema_detail`: Get detailed information for a specific schema

### Utility Tools
- `generate_jwks`: Generate JSON Web Key Set (JWKS) using mkjwk.org API

#### Search Features
- **Natural Language Search**: Ask questions like "revoke token" or "create client" and get relevant APIs
- **Relevance Scoring**: Results are ranked by relevance with intelligent scoring algorithm
- **DuckDB-Powered**: Fast, full-text search with optimized performance

#### Search Filters
- Path-based filtering (`path_query`)
- Description/summary filtering (`description_query`)
- HTTP method filtering (`method_filter`)
- API tag filtering (`tag_filter`)
- Result limit control (`limit`)

## Installation

### Local Development

```bash
# Install dependencies
uv sync

# Create the search database (required for API search functionality)
uv run python scripts/create_search_database.py

# Run the unified Authlete MCP Server
uv run python main.py
```

### Docker

The server is also available as a Docker image published to GitHub Container Registry.

#### Pull from GitHub Container Registry

```bash
# Pull the latest image
docker pull ghcr.io/watahani/authlete-mcp:latest

# Run with environment variables
docker run -it --rm \
  -e ORGANIZATION_ACCESS_TOKEN=$YOUR_TOKEN \
  -e ORGANIZATION_ID=$YOUR_ORG_ID \
  ghcr.io/watahani/authlete-mcp:latest
```

#### Build Locally

```bash
# Build the Docker image
docker build -t authlete-mcp .

# Run the container
docker run -it --rm \
  -e ORGANIZATION_ACCESS_TOKEN=$YOUR_TOKEN \
  -e ORGANIZATION_ID=$YOUR_ORG_ID \
  authlete-mcp
```

#### Using Docker Compose

```bash
# Create .env file with your credentials
cat > .env << EOF
ORGANIZATION_ACCESS_TOKEN=your-organization-token
ORGANIZATION_ID=your-organization-id
AUTHLETE_API_URL=https://jp.authlete.com
AUTHLETE_API_SERVER_ID=53285
EOF

# Run with Docker Compose
docker compose up authlete-mcp

# For development with live code reloading
docker compose --profile dev up authlete-mcp-dev
```

## Usage

### With Claude Desktop

#### Local Installation

Add the unified server to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "authlete": {
      "command": "uv",
      "args": ["run", "python", "/path/to/authlete-mcp/main.py"],
      "env": {
        "ORGANIZATION_ACCESS_TOKEN": "your-organization-access-token",
        "ORGANIZATION_ID": "your-organization-id", 
        "AUTHLETE_API_URL": "https://jp.authlete.com",
        "AUTHLETE_API_SERVER_ID": "53285",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

#### Docker Installation

You can also run the server using Docker:

```json
{
  "mcpServers": {
    "authlete": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "ORGANIZATION_ACCESS_TOKEN=your-organization-access-token",
        "-e", "ORGANIZATION_ID=your-organization-id",
        "-e", "AUTHLETE_API_URL=https://jp.authlete.com",
        "-e", "AUTHLETE_API_SERVER_ID=53285",
        "-e", "LOG_LEVEL=INFO",
        "ghcr.io/watahani/authlete-mcp:latest"
      ]
    }
  }
}
```

### Direct Usage

```bash
# Run unified Authlete MCP Server (all tools: service, client, token, JOSE, search, utility)
uv run python main.py

# Using custom organization access token
ORGANIZATION_ACCESS_TOKEN=your-token uv run python main.py

# Run with specific authlete server (EU region)
AUTHLETE_API_URL=https://eu.authlete.com AUTHLETE_API_SERVER_ID=63294 uv run python main.py
```

## Configuration

The unified server supports the following environment variables:

### Required Environment Variables
- `ORGANIZATION_ACCESS_TOKEN`: Your organization access token (required for all Authlete API operations)
- `ORGANIZATION_ID`: Your organization ID (required for service creation and deletion operations)

### Optional Configuration
- `AUTHLETE_API_URL`: Authlete API URL (default: `https://jp.authlete.com`)
- `AUTHLETE_API_SERVER_ID`: API Server ID (default: `53285` for JP)
- `AUTHLETE_IDP_URL`: Authlete IdP URL (default: `https://login.authlete.com`)
- `LOG_LEVEL`: Logging level (default: `INFO`) - Set to `DEBUG` for detailed HTTP request/response logging with PII masking

**⚠️ Important**: `AUTHLETE_API_URL` and `AUTHLETE_API_SERVER_ID` must be configured as a pair:
- **JP region**: `AUTHLETE_API_URL=https://jp.authlete.com` + `AUTHLETE_API_SERVER_ID=53285`
- **EU region**: `AUTHLETE_API_URL=https://eu.authlete.com` + `AUTHLETE_API_SERVER_ID=63294`

### API Search Requirements
- `resources/authlete_apis.duckdb`: Search database file (created by `scripts/create_search_database.py`)

**Note**: API search functionality is automatically disabled if the search database is not found, but service management will still work.

## Security Features

### 🔐 PII Masking and Secure Logging

The server includes comprehensive PII (Personally Identifiable Information) masking to protect sensitive data in logs:

#### Automatic PII Protection
- **Authlete Credentials**: `service_api_key`, `service_api_secret`, `ORGANIZATION_ACCESS_TOKEN`
- **OAuth/OIDC Tokens**: `client_secret`, `access_token`, `refresh_token`, `id_token`, `authorization_code`
- **Device Flow**: `user_code`, `client_notification_token`
- **JWT/Crypto Data**: `jwks`, `signature_key_id`, JWK values (`n`, `d`, `p`, `q`, etc.)
- **Authentication Data**: `password`, `authorization` headers, Bearer tokens

#### Multi-Format Support
- **JSON**: `{"client_secret": "value"}` → `{"client_secret": "***** REDACTED *****"}`
- **URL-encoded**: `client_secret=value&param=normal` → `client_secret=***** REDACTED *****&param=normal`
- **Environment Variables**: `ORGANIZATION_ACCESS_TOKEN=token123` → `ORGANIZATION_ACCESS_TOKEN=***** REDACTED *****`
- **Authorization Headers**: `Bearer token123456789` → `Bearer ***** REDACTED *****`

#### Logging Configuration
```bash
# Default INFO level - basic operational logs only
LOG_LEVEL=INFO

# DEBUG level - includes detailed HTTP request/response with PII masked
LOG_LEVEL=DEBUG

# Other levels: WARNING, ERROR, CRITICAL
```

#### Sample Secure Log Output
```
2025-08-12 18:45:23 - authlete_mcp.tools.service_tools - DEBUG - HTTP POST IdP API /service - Request: {
  "service": {
    "client_secret": "***** REDACTED *****",
    "serviceName": "MyService"
  }
}
2025-08-12 18:45:23 - authlete_mcp.tools.service_tools - DEBUG - HTTP POST IdP API /service - Response (200): {
  "resultMessage": "Service created successfully"
}
```

**Security Benefits:**
- ✅ Complete protection of sensitive tokens and secrets in all log outputs
- ✅ Safe for production environments and log aggregation systems
- ✅ Maintains debugging capability without exposing credentials
- ✅ Automatic detection across multiple data formats

## API Reference

All service management tools automatically use the `ORGANIZATION_ACCESS_TOKEN` environment variable for authentication. No sensitive tokens are passed as parameters.

API search tools provide read-only access to OpenAPI documentation with advanced search capabilities.

### Service Operations

#### create_service
Creates a new Authlete service.

**Parameters:**
- `name` (string, required): Service name
- `description` (string, optional): Service description

#### create_service_detailed
Creates a new Authlete service with comprehensive configuration using individual parameters.

**Parameters:**
- `service_config` (string, required): JSON string containing service configuration following Authlete API service schema
- `issuer` (string, optional): Issuer identifier URL (https:// format)
- `authorization_endpoint` (string, optional): Authorization endpoint URL
- `token_endpoint` (string, optional): Token endpoint URL
- `userinfo_endpoint` (string, optional): UserInfo endpoint URL
- `revocation_endpoint` (string, optional): Token revocation endpoint URL
- `jwks_uri` (string, optional): JWK Set endpoint URL
- `supported_scopes` (string, optional): Comma-separated scopes (default: "openid,profile,email")
- `supported_response_types` (string, optional): Comma-separated response types (default: "CODE")
- `supported_grant_types` (string, optional): Comma-separated grant types (default: "AUTHORIZATION_CODE")
- `supported_token_auth_methods` (string, optional): Comma-separated auth methods (default: "CLIENT_SECRET_BASIC")
- `pkce_required` (boolean, optional): Whether PKCE is required
- `pkce_s256_required` (boolean, optional): Whether S256 is required for PKCE
- `access_token_duration` (integer, optional): Access token duration in seconds (default: 86400)
- `refresh_token_duration` (integer, optional): Refresh token duration in seconds (default: 864000)
- `id_token_duration` (integer, optional): ID token duration in seconds (default: 86400)
- `direct_authorization_endpoint_enabled` (boolean, optional): Enable direct authorization endpoint
- `direct_token_endpoint_enabled` (boolean, optional): Enable direct token endpoint
- `direct_userinfo_endpoint_enabled` (boolean, optional): Enable direct userinfo endpoint
- `jwks` (string, optional): JWK Set document content (JSON string)

#### get_service_schema_example
Returns a comprehensive JSON example that can be used as a template for service configuration.

**Parameters:**
- None required

#### get_service
Retrieves service information.

**Parameters:**
- `service_api_key` (string, optional): Specific service API key to retrieve

#### update_service
Updates service configuration with complete data (full overwrite).

**Parameters:**
- `service_data` (string, required): JSON string containing complete service data
- `service_api_key` (string, optional): Service API key

#### patch_service
Partially updates service configuration by merging with existing data.

**Parameters:**
- `service_patch_data` (string, required): JSON string containing fields to update (partial data)
- `service_api_key` (string, optional): Service API key

#### delete_service
Deletes a service via IdP.

**Parameters:**
- `service_id` (string, required): Service ID to delete

### Client Operations

#### create_client
Creates a new OAuth client.

**Parameters:**
- `client_data` (string, required): JSON string containing client configuration
- `service_api_key` (string, optional): Service API key

#### get_client
Retrieves client information.

**Parameters:**
- `client_id` (string, required): Client ID
- `service_api_key` (string, optional): Service API key

#### update_client
Updates client configuration with complete data (full overwrite).

**Parameters:**
- `client_id` (string, required): Client ID to update
- `client_data` (string, required): JSON string containing complete client data
- `service_api_key` (string, optional): Service API key

#### patch_client
Partially updates client configuration by merging with existing data.

**Parameters:**
- `client_id` (string, required): Client ID to patch
- `client_patch_data` (string, required): JSON string containing fields to update (partial data)
- `service_api_key` (string, optional): Service API key

### API Search Operations

#### search_apis
Natural language search for Authlete APIs with intelligent relevance scoring.

**Parameters:**
- `query` (string, optional): Natural language search query (e.g., "revoke token", "create client")
- `path_query` (string, optional): Specific API path search (e.g., "/api/auth/token")
- `description_query` (string, optional): Search in API descriptions and summaries
- `tag_filter` (string, optional): Filter by API tag (e.g., "Authorization", "Token")
- `method_filter` (string, optional): Filter by HTTP method ("GET", "POST", "PUT", "DELETE")
- `mode` (string, optional): Search mode (maintained for compatibility, uses natural language search)
- `limit` (integer, optional): Maximum number of results (default: 20, max: 100)

**Returns:** JSON array of search results with path, method, summary, description, tags, and relevance score.

#### get_api_detail
Get comprehensive details for a specific API endpoint with advanced filtering options for context optimization.

**Parameters:**
- `path` (string, optional): Exact API path (required if operation_id not provided)
- `method` (string, optional): HTTP method (required if operation_id not provided)
- `operation_id` (string, optional): Operation ID (alternative to path+method)
- `language` (string, optional): Programming language for sample code
- `description_style` (string, optional): Description filtering style (default: "summary_and_headers")
  - `"full"`: Complete description text
  - `"none"`: No description
  - `"summary_and_headers"`: Summary + header list (default, optimal for context efficiency)
  - `"line_range"`: Specific line range (use with line_start/line_end)
- `line_start` (integer, optional): Start line for line_range style (1-indexed, default: 1)
- `line_end` (integer, optional): End line for line_range style (1-indexed, default: 100)
- `request_body_style` (string, optional): Request body filtering style (default: "none")
  - `"full"`: Complete request body details
  - `"none"`: No request body (default)
  - `"schema_only"`: Schema references only (significant size reduction)
- `response_body_style` (string, optional): Response body filtering style (default: "none")
  - `"full"`: Complete response body details
  - `"none"`: No response body (default)
  - `"schema_only"`: Schema references only (significant size reduction)

**Returns:** Detailed API information including parameters, request body, responses, and sample code. Size optimized based on filtering options (up to 96% reduction with schema_only).

#### get_sample_code
Retrieve sample code for a specific API endpoint in the requested language.

**Parameters:**
- `language` (string, required): Programming language ("curl", "javascript", "python", "java", etc.)
- `path` (string, optional): API path (required if operation_id not provided)
- `method` (string, optional): HTTP method (required if operation_id not provided)
- `operation_id` (string, optional): Operation ID (alternative to path+method)

**Returns:** Sample code string for the specified endpoint and language.

## Working Configuration Examples

### Example 1: Basic Configuration with Environment Variables

```json
{
  "mcpServers": {
    "authlete": {
      "command": "uv",
      "args": ["run", "python", "/path/to/authlete-mcp/main.py"],
      "env": {
        "ORGANIZATION_ACCESS_TOKEN": "06uqWx-1R9pH8z07Ex3OxvBOdrwJeps-hPxxUm35uTc",
        "ORGANIZATION_ID": "143361107080408",
        "AUTHLETE_API_URL": "https://jp.authlete.com",
        "AUTHLETE_API_SERVER_ID": "53285"
      }
    }
  }
}
```

With this configuration, you can create services using the ORGANIZATION_ID from environment variables:

```bash
# Creates a service using ORGANIZATION_ID from environment variables
create_service(name="My Test Service", description="Test service")
```

### Example 2: Configuration for Different Regions

For EU region (eu.authlete.com):
```json
{
  "mcpServers": {
    "authlete-eu": {
      "command": "uv", 
      "args": ["run", "python", "/path/to/authlete-mcp/main.py"],
      "env": {
        "ORGANIZATION_ACCESS_TOKEN": "your-eu-org-token",
        "ORGANIZATION_ID": "your-eu-org-id",
        "AUTHLETE_API_URL": "https://eu.authlete.com",
        "AUTHLETE_IDP_URL": "https://login.authlete.com",
        "AUTHLETE_API_SERVER_ID": "63294"
      }
    }
  }
}
```

### Example 3: Testing Configuration

For testing and development:
```bash
# Set environment variables
export ORGANIZATION_ACCESS_TOKEN="your-test-token"
export ORGANIZATION_ID="your-test-org-id"
export AUTHLETE_API_URL="https://jp.authlete.com"
export AUTHLETE_API_SERVER_ID="53285"

# Run the server
uv run python main.py

## Usage Examples

### Basic Search
```bash
# Search for token-related APIs
search_apis(query="token")

# Search by specific path
search_apis(path_query="/api/auth/authorization")

# Search with filters
search_apis(query="service", method_filter="POST", limit=5)
```

### Natural Language Search
```bash
# Ask questions in natural language
search_apis(query="how to revoke access token")
search_apis(query="create new oauth client")
search_apis(query="get user information")
```

### Get API Details
```bash
# Get detailed information for a specific API
get_api_detail(path="/api/auth/token", method="POST")

# Get details with sample code
get_api_detail(path="/api/auth/token", method="POST", language="curl")

# Use operation ID instead of path+method
get_api_detail(operation_id="revokeToken", language="javascript")

# Context-optimized API details (recommended for large APIs)
get_api_detail(operation_id="client_create_api", description_style="summary_and_headers", 
               request_body_style="schema_only", response_body_style="schema_only")

# Get only schema structure without verbose content (96% size reduction)
get_api_detail(path="/api/auth/authorization", method="POST", description_style="none",
               request_body_style="schema_only", response_body_style="schema_only")

# Get specific line range of description
get_api_detail(operation_id="auth_authorization_api", description_style="line_range",
               line_start=1, line_end=50)
```

### Get Sample Code
```bash
# Get sample code in different languages
get_sample_code(language="javascript", path="/api/auth/token", method="POST")
get_sample_code(language="python", operation_id="revokeToken")
get_sample_code(language="curl", path="/api/auth/authorization", method="POST")
```

### Combined Service Management and Search
```bash
# Create a service then search for related APIs
create_service(name="My OAuth Service", description="Test OAuth service")

# Search for APIs to use with the new service
search_apis(query="oauth client registration")
search_apis(query="token endpoint")
```

## License

MIT License