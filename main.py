#!/usr/bin/env python3
"""Main entry point for Authlete MCP Server."""

from src.authlete_mcp.server import mcp

if __name__ == "__main__":
    mcp.run()