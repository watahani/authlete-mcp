"""Base data models for Authlete services."""

import re
from enum import Enum

from pydantic import BaseModel, Field


class DescriptionStyle(Enum):
    """Description filtering styles for API documentation."""

    FULL = "full"
    NONE = "none"
    LINE_RANGE = "line_range"
    SUMMARY_AND_HEADERS = "summary_and_headers"  # Default: summary + header list


class BodyStyle(Enum):
    """Body (request/response) filtering styles for API documentation."""

    FULL = "full"
    NONE = "none"
    SCHEMA_ONLY = "schema_only"  # Show only schema references, not full content


def filter_description(
    description: str | None, style: DescriptionStyle | str, line_range: tuple[int, int] | None = None
) -> str | None:
    """Filter description text based on the specified style.

    Args:
        description: The original description text
        style: Filtering style (full, none, headers_only, line_range)
        line_range: Tuple of (start_line, end_line) for line_range style (1-indexed)

    Returns:
        Filtered description text or None
    """
    if not description:
        return description

    # Convert string to enum if needed
    if isinstance(style, str):
        try:
            style = DescriptionStyle(style)
        except ValueError:
            # Invalid style, return full description
            return description

    if style == DescriptionStyle.NONE:
        return None
    elif style == DescriptionStyle.FULL:
        return description
    elif style == DescriptionStyle.LINE_RANGE:
        if line_range is None:
            # If no range specified, return full description
            return description
        return _extract_line_range(description, line_range[0], line_range[1])
    elif style == DescriptionStyle.SUMMARY_AND_HEADERS:
        return _extract_summary_and_headers(description)
    else:
        # Unknown style, return full description
        return description


def _extract_line_range(text: str, start_line: int, end_line: int) -> str:
    """Extract specified line range from text (1-indexed)."""
    if not text:
        return ""

    lines = text.split("\n")
    total_lines = len(lines)

    # Validate range
    start_line = max(1, start_line)
    end_line = min(total_lines, end_line)

    if start_line > total_lines or start_line > end_line:
        return f"Invalid line range: {start_line}-{end_line} (total lines: {total_lines})"

    # Extract lines (convert to 0-indexed for slicing)
    selected_lines = lines[start_line - 1 : end_line]

    # Add line numbers
    result_lines = []
    for i, line in enumerate(selected_lines, start_line):
        result_lines.append(f"{i:4d}: {line}")

    return "\n".join(result_lines)


def _extract_summary_and_headers(text: str) -> str:
    """Extract summary (text before first header) and all headers with line numbers."""
    if not text:
        return ""

    lines = text.split("\n")
    summary_lines = []
    headers = []
    found_first_header = False

    for i, line in enumerate(lines, 1):
        # Check if this line is a markdown header (# ## ### etc.)
        is_markdown_header = re.match(r"^#{1,6}\s+", line.strip())
        # Check if this line is a bold header (**text**)
        is_bold_header = re.match(r"^\*\*(.+?)\*\*$", line.strip())

        if is_markdown_header or is_bold_header:
            headers.append(f"{i:4d}: {line.strip()}")
            found_first_header = True
        elif not found_first_header:
            # Still in summary section
            summary_lines.append(line)

    # Build result
    result_parts = []

    # Add summary if exists
    if summary_lines:
        summary = "\n".join(summary_lines).strip()
        if summary:
            result_parts.append(f"=== Summary ===\n{summary}")

    # Add headers if exists
    if headers:
        result_parts.append("=== Headers ===\n" + "\n".join(headers))
    elif found_first_header:
        result_parts.append("=== Headers ===\n(No headers found)")

    if not result_parts:
        # No headers found, return first 300 chars as summary
        truncated = text[:300]
        if len(text) > 300:
            truncated += "..."
        return f"=== Summary ===\n{truncated}"

    return "\n\n".join(result_parts)


def filter_body_content(body_data: dict | None, style: BodyStyle | str) -> dict | None:
    """Filter request/response body content based on the specified style.

    Args:
        body_data: The original body data (request_body or response data)
        style: Filtering style (full, none, schema_only)

    Returns:
        Filtered body data or None
    """
    if not body_data:
        return body_data

    # Convert string to enum if needed
    if isinstance(style, str):
        try:
            style = BodyStyle(style)
        except ValueError:
            # Invalid style, return full body
            return body_data

    if style == BodyStyle.NONE:
        return None
    elif style == BodyStyle.FULL:
        return body_data
    elif style == BodyStyle.SCHEMA_ONLY:
        return _extract_schema_references(body_data)
    else:
        # Unknown style, return full body
        return body_data


def _extract_schema_references(body_data: dict) -> dict:
    """Extract schema references from body content, removing detailed schemas."""
    if not isinstance(body_data, dict):
        # Handle non-dict data (strings, lists, etc.)
        if isinstance(body_data, str):
            return {"type": "string", "content": "simplified"}
        else:
            return {"type": type(body_data).__name__, "content": "simplified"}

    # Create a copy to avoid modifying the original
    filtered_body = {}

    for key, value in body_data.items():
        if key == "content":
            if isinstance(value, dict):
                # Filter content section to show only media type keys and basic info
                filtered_content = {}
                for media_type, media_content in value.items():
                    if isinstance(media_content, dict):
                        # Keep only schema references, remove detailed schema definitions
                        filtered_media = {}
                        if "schema" in media_content:
                            schema = media_content["schema"]
                            if isinstance(schema, dict):
                                # Extract only reference information
                                if "$ref" in schema:
                                    filtered_media["schema"] = {"$ref": schema["$ref"]}
                                else:
                                    filtered_media["schema"] = _simplify_schema(schema)
                            elif isinstance(schema, str):
                                # Handle string schemas (try to parse as JSON)
                                try:
                                    import json

                                    parsed_schema = json.loads(schema)
                                    if isinstance(parsed_schema, dict):
                                        if "$ref" in parsed_schema:
                                            filtered_media["schema"] = {"$ref": parsed_schema["$ref"]}
                                        else:
                                            filtered_media["schema"] = _simplify_schema(parsed_schema)
                                    else:
                                        filtered_media["schema"] = {"type": "unknown", "original": "string"}
                                except (json.JSONDecodeError, ImportError):
                                    filtered_media["schema"] = {"type": "unknown", "original": "string"}
                            else:
                                filtered_media["schema"] = media_content["schema"]

                        # Keep other non-schema fields, but filter examples if they're too long
                        for k, v in media_content.items():
                            if k != "schema":
                                if k == "example" and isinstance(v, str) and len(v) > 200:
                                    # Truncate long examples
                                    filtered_media[k] = v[:200] + "..."
                                else:
                                    filtered_media[k] = v

                        filtered_content[media_type] = filtered_media
                    else:
                        filtered_content[media_type] = media_content
                filtered_body[key] = filtered_content
            elif isinstance(value, str):
                # Handle string content (simplified representation)
                filtered_body[key] = {"type": "string", "content": "simplified"}
            else:
                filtered_body[key] = value
        else:
            # Keep other fields as-is
            filtered_body[key] = value

    return filtered_body


def _simplify_schema(schema: dict) -> dict:
    """Simplify a JSON Schema by keeping only essential structure information.

    This follows JSON Schema conventions for concise representation:
    - Keep type, required, and property names
    - Remove descriptions, examples, and other verbose fields
    - Simplify nested objects recursively
    """
    if not isinstance(schema, dict):
        return schema

    simplified = {}

    # Keep essential schema fields
    essential_fields = ["type", "required", "enum", "format", "items"]
    for field in essential_fields:
        if field in schema:
            if field == "items" and isinstance(schema[field], dict):
                # Recursively simplify array items schema
                simplified[field] = _simplify_schema(schema[field])
            else:
                simplified[field] = schema[field]

    # Handle properties with simplified structure - only show property names and basic types
    if "properties" in schema and isinstance(schema["properties"], dict):
        simplified_props = {}
        for prop_name, prop_schema in schema["properties"].items():
            if isinstance(prop_schema, dict):
                # Only keep essential type information
                prop_simplified = {"type": prop_schema.get("type", "unknown")}

                # Keep enum values if they're short
                if "enum" in prop_schema:
                    enum_vals = prop_schema["enum"]
                    if isinstance(enum_vals, list) and len(str(enum_vals)) < 100:
                        prop_simplified["enum"] = enum_vals

                # For arrays, show item type if simple
                if prop_schema.get("type") == "array" and "items" in prop_schema:
                    items_schema = prop_schema["items"]
                    if isinstance(items_schema, dict) and "type" in items_schema:
                        prop_simplified["items"] = {"type": items_schema["type"]}

                # For objects, show that it has properties but don't expand them
                if prop_schema.get("type") == "object" and "properties" in prop_schema:
                    prop_count = len(prop_schema["properties"])
                    prop_simplified["properties"] = f"[{prop_count} properties]"

                simplified_props[prop_name] = prop_simplified
            elif isinstance(prop_schema, str):
                # Handle string schemas
                simplified_props[prop_name] = {"type": "string_schema"}
            else:
                simplified_props[prop_name] = {"type": "unknown"}

        simplified["properties"] = simplified_props

    # If no essential info found, at least show type
    if not simplified and "type" not in simplified:
        simplified["type"] = schema.get("type", "object")

    return simplified


class Scope(BaseModel):
    """Scope definition."""

    name: str = Field(..., description="Scope name")
    defaultEntry: bool = Field(False, description="Whether this scope is default")
    description: str | None = Field(None, description="Scope description")


class ServiceDetail(BaseModel):
    """Detailed service configuration based on Authlete Service schema."""

    serviceName: str = Field(..., description="The name of this service")
    description: str | None = Field(None, description="The description about the service")
    issuer: str | None = Field(
        None, description="The issuer identifier of the service. A URL that starts with https://"
    )

    # Supported features
    supportedScopes: list[Scope] | None = Field(None, description="Scopes supported by the service")
    supportedResponseTypes: list[str] | None = Field(
        None, description="Response types supported (e.g., CODE, ID_TOKEN)"
    )
    supportedGrantTypes: list[str] | None = Field(
        None, description="Grant types supported (e.g., AUTHORIZATION_CODE, CLIENT_CREDENTIALS)"
    )
    supportedTokenAuthMethods: list[str] | None = Field(None, description="Token endpoint authentication methods")

    # Endpoints
    authorizationEndpoint: str | None = Field(None, description="Authorization endpoint URL")
    tokenEndpoint: str | None = Field(None, description="Token endpoint URL")
    userInfoEndpoint: str | None = Field(None, description="UserInfo endpoint URL")
    revocationEndpoint: str | None = Field(None, description="Token revocation endpoint URL")
    jwksUri: str | None = Field(None, description="JWK Set endpoint URL")

    # Security settings
    pkceRequired: bool | None = Field(None, description="Whether PKCE is required")
    pkceS256Required: bool | None = Field(None, description="Whether S256 is required for PKCE")

    # Token settings
    accessTokenDuration: int | None = Field(None, description="Access token duration in seconds")
    refreshTokenDuration: int | None = Field(None, description="Refresh token duration in seconds")
    idTokenDuration: int | None = Field(None, description="ID token duration in seconds")

    # Advanced settings
    jwks: str | None = Field(None, description="JWK Set document content")
    directAuthorizationEndpointEnabled: bool | None = Field(None, description="Enable direct authorization endpoint")
    directTokenEndpointEnabled: bool | None = Field(None, description="Enable direct token endpoint")
    directUserInfoEndpointEnabled: bool | None = Field(None, description="Enable direct userinfo endpoint")


class ClientCreateRequest(BaseModel):
    """Request model for creating a client."""

    name: str = Field(..., description="Client name")
    description: str | None = Field(None, description="Client description")
    client_type: str | None = Field(None, description="Client type")
    redirect_uris: list[str] | None = Field(None, description="Redirect URIs")
