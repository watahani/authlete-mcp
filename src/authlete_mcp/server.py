"""Authlete MCP Server using modular structure."""

import logging

from mcp.server.fastmcp import FastMCP

from .tools import (
    client_tools,
    jose_tools,
    search_tools,
    service_tools,
    token_tools,
    utility_tools,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Authlete Management and API Search Server")

# Service Management Tools
mcp.tool()(service_tools.create_service)
mcp.tool()(service_tools.create_service_detailed)
mcp.tool()(service_tools.get_service_schema_example)
mcp.tool()(service_tools.get_service)
mcp.tool()(service_tools.list_services)
mcp.tool()(service_tools.update_service)
mcp.tool()(service_tools.delete_service)

# Client Management Tools
mcp.tool()(client_tools.create_client)
mcp.tool()(client_tools.get_client)
mcp.tool()(client_tools.list_clients)
mcp.tool()(client_tools.update_client)
mcp.tool()(client_tools.delete_client)
mcp.tool()(client_tools.rotate_client_secret)
mcp.tool()(client_tools.update_client_secret)
mcp.tool()(client_tools.update_client_lock)

# Extended Client Operations
mcp.tool()(client_tools.get_authorized_applications)
mcp.tool()(client_tools.update_client_tokens)
mcp.tool()(client_tools.delete_client_tokens)
mcp.tool()(client_tools.get_granted_scopes)
mcp.tool()(client_tools.delete_granted_scopes)
mcp.tool()(client_tools.get_requestable_scopes)
mcp.tool()(client_tools.update_requestable_scopes)
mcp.tool()(client_tools.delete_requestable_scopes)

# Token Operations
mcp.tool()(token_tools.list_issued_tokens)
mcp.tool()(token_tools.create_access_token)
mcp.tool()(token_tools.update_access_token)
mcp.tool()(token_tools.revoke_access_token)
mcp.tool()(token_tools.delete_access_token)

# JOSE Operations
mcp.tool()(jose_tools.generate_jose)
mcp.tool()(jose_tools.verify_jose)

# Search Tools
mcp.tool()(search_tools.search_apis)
mcp.tool()(search_tools.get_api_detail)
mcp.tool()(search_tools.get_sample_code)
mcp.tool()(search_tools.list_schemas)
mcp.tool()(search_tools.get_schema_detail)

# Utility Tools
mcp.tool()(utility_tools.generate_jwks)


def run():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    run()
