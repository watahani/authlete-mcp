# Authlete MCP Server

An AI generated Model Context Protocol (MCP) server that provides tools for managing Authlete services and clients through a standardized interface.

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

## Features

### Service Management
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

## Installation

```bash
# Install dependencies
uv sync

# Run the server
uv run python main.py
```

## Usage

### With Claude Desktop

1. Add the server to your Claude Desktop configuration:

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
    }
  }
}
```

### Direct Usage

```bash
# Using stdio transport (default)
uv run python main.py

# Using custom organization access token
ORGANIZATION_ACCESS_TOKEN=your-token uv run python main.py
```

## Configuration

The server requires the following environment variables:

- `ORGANIZATION_ACCESS_TOKEN`: Your organization access token (required)
- `ORGANIZATION_ID`: Your organization ID (optional, can be overridden by function parameters)
- `AUTHLETE_BASE_URL`: Authlete API base URL (default: `https://jp.authlete.com`)
- `AUTHLETE_IDP_URL`: Authlete IdP URL (default: `https://login.authlete.com`)
- `AUTHLETE_API_SERVER_ID`: API Server ID (default: `53285` for JP)

## API Reference

All tools automatically use the `ORGANIZATION_ACCESS_TOKEN` environment variable for authentication. No sensitive tokens are passed as parameters.

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
```

## License

MIT License