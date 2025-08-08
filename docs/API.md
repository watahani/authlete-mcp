# Authlete MCP Server API Documentation

This document describes the available tools in the Authlete MCP Server.

## Service Management Tools

### create_service
Creates a new Authlete service with basic configuration.

**Parameters:**
- `name` (required): Service name
- `organization_id` (optional): Organization ID (defaults to ORGANIZATION_ID env var)
- `description` (optional): Service description

**Example:**
```python
result = await session.call_tool("create_service", {
    "name": "my-service",
    "description": "My OpenID Connect service"
})
```

### create_service_detailed
Creates a new Authlete service with detailed configuration.

**Parameters:**
- `name` (required): Service name
- `organization_id` (optional): Organization ID
- `description` (optional): Service description
- `issuer` (optional): Issuer identifier URL
- `authorization_endpoint` (optional): Authorization endpoint URL
- `token_endpoint` (optional): Token endpoint URL
- `userinfo_endpoint` (optional): UserInfo endpoint URL
- `revocation_endpoint` (optional): Token revocation endpoint URL
- `jwks_uri` (optional): JWK Set endpoint URL
- `supported_scopes` (optional): Comma-separated list of supported scopes
- `supported_response_types` (optional): Comma-separated response types
- `supported_grant_types` (optional): Comma-separated grant types
- `supported_token_auth_methods` (optional): Comma-separated auth methods
- `pkce_required` (optional): Whether PKCE is required
- `pkce_s256_required` (optional): Whether S256 is required for PKCE
- `access_token_duration` (optional): Access token duration in seconds
- `refresh_token_duration` (optional): Refresh token duration in seconds
- `id_token_duration` (optional): ID token duration in seconds
- `direct_authorization_endpoint_enabled` (optional): Enable direct authorization endpoint
- `direct_token_endpoint_enabled` (optional): Enable direct token endpoint
- `direct_userinfo_endpoint_enabled` (optional): Enable direct userinfo endpoint
- `jwks` (optional): JWK Set document content

### list_services
Lists all Authlete services.

**Parameters:** None

### get_service
Gets an Authlete service by API key.

**Parameters:**
- `service_api_key` (optional): Service API key (defaults to main token)

### update_service
Updates an Authlete service.

**Parameters:**
- `service_data` (required): JSON string containing service data to update
- `service_api_key` (optional): Service API key

### delete_service
Deletes an Authlete service via IdP.

**Parameters:**
- `service_id` (required): Service ID (apiKey) to delete
- `organization_id` (optional): Organization ID

### get_service_schema_example
Gets an example of service configuration schema.

**Parameters:** None

## Client Management Tools

### create_client
Creates a new Authlete client.

**Parameters:**
- `client_data` (required): JSON string containing client data
- `service_api_key` (optional): Service API key

### get_client
Gets an Authlete client by ID.

**Parameters:**
- `client_id` (required): Client ID to retrieve
- `service_api_key` (optional): Service API key

### list_clients
Lists all Authlete clients.

**Parameters:**
- `service_api_key` (optional): Service API key

### update_client
Updates an Authlete client.

**Parameters:**
- `client_id` (required): Client ID to update
- `client_data` (required): JSON string containing client data to update
- `service_api_key` (optional): Service API key

### delete_client
Deletes an Authlete client.

**Parameters:**
- `client_id` (required): Client ID to delete
- `service_api_key` (optional): Service API key

### rotate_client_secret
Rotates an Authlete client secret.

**Parameters:**
- `client_id` (required): Client ID
- `service_api_key` (optional): Service API key

### update_client_secret
Updates an Authlete client secret.

**Parameters:**
- `client_id` (required): Client ID
- `secret_data` (required): JSON string containing new secret data
- `service_api_key` (optional): Service API key

### update_client_lock
Updates an Authlete client lock status.

**Parameters:**
- `client_id` (required): Client ID
- `lock_flag` (required): True to lock, False to unlock
- `service_api_key` (optional): Service API key

## Environment Variables

The following environment variables are required:

- `ORGANIZATION_ACCESS_TOKEN`: Authlete organization access token
- `ORGANIZATION_ID`: Authlete organization ID
- `AUTHLETE_BASE_URL` (optional): Authlete base URL (defaults to https://jp.authlete.com)
- `AUTHLETE_IDP_URL` (optional): Authlete IdP URL (defaults to https://login.authlete.com)
- `AUTHLETE_API_SERVER_ID` (optional): API Server ID (defaults to 53285)

## Error Handling

All tools return JSON responses. In case of errors, the response will include an error message starting with "Error:". Successful operations return the JSON response from the Authlete API.

For service deletion, a successful response includes:
```json
{
  "success": true,
  "message": "Service deleted successfully"
}
```