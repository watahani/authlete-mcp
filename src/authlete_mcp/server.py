"""Authlete MCP Server

A Model Context Protocol server that provides tools for managing Authlete services and clients.
"""

from mcp.server.fastmcp import FastMCP

from .tools import client_tools, jose_tools, service_tools, token_tools

# Create MCP server
mcp = FastMCP("Authlete Management Server")

# Register service management tools
mcp.tool()(service_tools.create_service)
mcp.tool()(service_tools.create_service_detailed)
mcp.tool()(service_tools.get_service_schema_example)
mcp.tool()(service_tools.get_service)
mcp.tool()(service_tools.list_services)
mcp.tool()(service_tools.update_service)
mcp.tool()(service_tools.delete_service)

# Register client management tools
mcp.tool()(client_tools.create_client)
mcp.tool()(client_tools.get_client)
mcp.tool()(client_tools.list_clients)
mcp.tool()(client_tools.update_client)
mcp.tool()(client_tools.delete_client)
mcp.tool()(client_tools.rotate_client_secret)
mcp.tool()(client_tools.update_client_secret)
mcp.tool()(client_tools.update_client_lock)
mcp.tool()(client_tools.get_authorized_applications)
mcp.tool()(client_tools.update_client_tokens)
mcp.tool()(client_tools.delete_client_tokens)
mcp.tool()(client_tools.get_granted_scopes)
mcp.tool()(client_tools.delete_granted_scopes)
mcp.tool()(client_tools.get_requestable_scopes)
mcp.tool()(client_tools.update_requestable_scopes)
mcp.tool()(client_tools.delete_requestable_scopes)

# Register token management tools
mcp.tool()(token_tools.list_issued_tokens)
mcp.tool()(token_tools.create_access_token)
mcp.tool()(token_tools.update_access_token)
mcp.tool()(token_tools.revoke_access_token)
mcp.tool()(token_tools.delete_access_token)

# Register JOSE tools
mcp.tool()(jose_tools.generate_jose)
mcp.tool()(jose_tools.verify_jose)


if __name__ == "__main__":
    mcp.run()
