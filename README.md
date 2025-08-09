# Authlete MCP Server

AI generated Model Context Protocol (MCP) servers that provide comprehensive tools for:
1. **Authlete Service Management**: Managing Authlete services and clients through a standardized interface
2. **API Documentation Search**: Advanced search capabilities for Authlete OpenAPI specifications

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

## Servers Overview

### 1. Authlete MCP Server (`authlete_mcp_server.py`)
Service and client management server for Authlete platform operations.

### 2. Authlete API Search Server (`authlete_api_search_server.py`) 🆕
Advanced OpenAPI documentation search server with natural language and fuzzy search capabilities.

## Features

### Authlete MCP Server - Service Management
- `create_service`: Create a new Authlete service with basic configuration
- `create_service_detailed`: Create a new Authlete service with comprehensive configuration
- `get_service_schema_example`: Get an example service configuration schema
- `get_service`: Retrieve a service by API key
- `list_services`: List all services
- `update_service`: Update service configuration
- `delete_service`: Delete a service via IdP

### Client Management
- `create_client`: Create a new OAuth client
- `get_client`: Retrieve a client by ID
- `list_clients`: List all clients for a service
- `update_client`: Update client configuration
- `delete_client`: Delete a client
- `rotate_client_secret`: Generate new client secret
- `update_client_secret`: Update client secret manually
- `update_client_lock`: Lock or unlock a client

### Authlete API Search Server - Advanced Search Features
- `search_apis`: Multi-mode API search (exact, partial, fuzzy, natural language)
- `get_api_detail`: Detailed API information with parameters, request/response schemas
- `get_sample_code`: Language-specific code samples for API endpoints
- `suggest_apis`: Natural language API recommendations based on user questions

#### Search Modes
- **Exact**: Perfect string matching for precise searches
- **Partial**: Substring matching for flexible searches  
- **Fuzzy**: Typo-tolerant search using similarity algorithms
- **Natural**: Semantic search for natural language queries

#### Search Filters
- Path-based filtering (`path_query`)
- Description/summary filtering (`description_query`)
- HTTP method filtering (`method_filter`)
- API tag filtering (`tag_filter`)
- Result limit control (`limit`)

## Installation

```bash
# Install dependencies
uv sync

# Run the Authlete MCP Server
uv run python main.py

# Run the API Search Server
uv run python authlete_api_search_server.py
```

## Usage

### With Claude Desktop

#### Both Servers Configuration
Add both servers to your Claude Desktop configuration for comprehensive Authlete support:

```json
{
  "mcpServers": {
    "authlete": {
      "command": "uv",
      "args": ["run", "python", "/path/to/authlete-mcp/main.py"],
      "env": {
        "ORGANIZATION_ACCESS_TOKEN": "your-organization-access-token",
        "ORGANIZATION_ID": "your-organization-id", 
        "AUTHLETE_BASE_URL": "https://jp.authlete.com",
        "AUTHLETE_API_SERVER_ID": "53285"
      }
    },
    "authlete-api-search": {
      "command": "uv",
      "args": ["run", "python", "/path/to/authlete-mcp/authlete_api_search_server.py"]
    }
  }
}
```

#### API Search Server Only
For documentation search only (no service management):

```json
{
  "mcpServers": {
    "authlete-search": {
      "command": "uv", 
      "args": ["run", "python", "/path/to/authlete-mcp/authlete_api_search_server.py"]
    }
  }
}
```

### Direct Usage

```bash
# Run Authlete MCP Server (service management)
uv run python main.py

# Run API Search Server (documentation search)
uv run python authlete_api_search_server.py

# Using custom organization access token for MCP server
ORGANIZATION_ACCESS_TOKEN=your-token uv run python main.py
```

## Configuration

### Authlete MCP Server Configuration
The service management server requires the following environment variables:

- `ORGANIZATION_ACCESS_TOKEN`: Your organization access token (required)
- `ORGANIZATION_ID`: Your organization ID (optional, can be overridden by function parameters)
- `AUTHLETE_BASE_URL`: Authlete API base URL (default: `https://jp.authlete.com`)
- `AUTHLETE_IDP_URL`: Authlete IdP URL (default: `https://login.authlete.com`)
- `AUTHLETE_API_SERVER_ID`: API Server ID (default: `53285` for JP)

### API Search Server Configuration
The documentation search server requires no environment variables and uses:
- `resources/openapi-spec.json`: OpenAPI specification file (automatically located)

## API Reference

### Authlete MCP Server
All tools automatically use the `ORGANIZATION_ACCESS_TOKEN` environment variable for authentication. No sensitive tokens are passed as parameters.

### API Search Server 
The search server provides read-only access to OpenAPI documentation with advanced search capabilities.

### Service Operations

#### create_service
Creates a new Authlete service.

**Parameters:**
- `name` (string, required): Service name
- `organization_id` (string, optional): Organization ID (if empty, uses ORGANIZATION_ID env var)
- `description` (string, optional): Service description

#### create_service_detailed
Creates a new Authlete service with comprehensive configuration using individual parameters.

**Parameters:**
- `name` (string, required): Service name
- `organization_id` (string, optional): Organization ID (if empty, uses ORGANIZATION_ID env var)
- `description` (string, optional): Service description
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
Updates service configuration.

**Parameters:**
- `service_data` (string, required): JSON string containing service data
- `service_api_key` (string, optional): Service API key

#### delete_service
Deletes a service via IdP.

**Parameters:**
- `service_id` (string, required): Service ID to delete
- `organization_id` (string, optional): Organization ID (if empty, uses ORGANIZATION_ID env var)

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

## API Search Server Reference

### search_apis
Multi-mode search for Authlete APIs with flexible filtering options.

**Parameters:**
- `query` (string, optional): General search query across all fields
- `path_query` (string, optional): Specific API path search (e.g., "/api/auth/token")
- `description_query` (string, optional): Search in API descriptions and summaries
- `tag_filter` (string, optional): Filter by API tag (e.g., "Authorization", "Token")
- `method_filter` (string, optional): Filter by HTTP method ("GET", "POST", "PUT", "DELETE")
- `mode` (string, optional): Search mode - "exact", "partial", "fuzzy", "natural" (default: "partial")
- `limit` (integer, optional): Maximum number of results (default: 20, max: 100)

**Returns:** JSON array of search results with path, method, summary, description, tags, and relevance score.

### get_api_detail
Get comprehensive details for a specific API endpoint.

**Parameters:**
- `path` (string, required): Exact API path from search results
- `method` (string, required): HTTP method from search results  
- `language` (string, optional): Programming language for sample code

**Returns:** Detailed API information including parameters, request body, responses, and sample code.

### get_sample_code
Retrieve sample code for a specific API endpoint in the requested language.

**Parameters:**
- `path` (string, required): API path
- `method` (string, required): HTTP method
- `language` (string, required): Programming language ("curl", "javascript", "python", "java", etc.)

**Returns:** Sample code string for the specified endpoint and language.

### suggest_apis
Get API recommendations based on natural language questions.

**Parameters:**
- `question` (string, required): Natural language question about desired functionality
- `limit` (integer, optional): Maximum number of suggestions (default: 5)

**Returns:** JSON object with question and array of recommended APIs with relevance scores.

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
        "AUTHLETE_BASE_URL": "https://jp.authlete.com",
        "AUTHLETE_API_SERVER_ID": "53285"
      }
    }
  }
}
```

With this configuration, you can create services without specifying `organization_id` parameter:

```bash
# Creates a service using ORGANIZATION_ID from environment variables
create_service(name="My Test Service", description="Test service")

# Still works with explicit organization_id (overrides env var)
create_service(name="Another Service", organization_id="123456789", description="Different org service")
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
        "AUTHLETE_BASE_URL": "https://eu.authlete.com",
        "AUTHLETE_IDP_URL": "https://login.authlete.com",
        "AUTHLETE_API_SERVER_ID": "your-eu-api-server-id"
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
export AUTHLETE_BASE_URL="https://jp.authlete.com"
export AUTHLETE_API_SERVER_ID="53285"

# Run the server
uv run python main.py

## API Search Server Usage Examples

### Basic Search
```bash
# Search for token-related APIs
search_apis(query="token")

# Search by specific path
search_apis(path_query="/api/auth/authorization")

# Search with filters
search_apis(query="service", method_filter="POST", limit=5)
```

### Advanced Search Modes
```bash
# Fuzzy search (typo tolerant)
search_apis(query="authorizeation", mode="fuzzy")  # Will find "authorization"

# Natural language search
search_apis(query="I want to revoke a token", mode="natural")
```

### Get API Details
```bash
# Get detailed information for a specific API
get_api_detail(path="/api/auth/token", method="POST")

# Get details with sample code
get_api_detail(path="/api/auth/token", method="POST", language="curl")
```

### Get Sample Code
```bash
# Get sample code in different languages
get_sample_code(path="/api/auth/token", method="POST", language="javascript")
get_sample_code(path="/api/auth/token", method="POST", language="python")
```

### API Suggestions
```bash
# Get API recommendations based on questions
suggest_apis(question="How do I create a new OAuth client?")
suggest_apis(question="トークンを無効化したい")  # Japanese also supported
```

## License

MIT License