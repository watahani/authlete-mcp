#!/usr/bin/env python3
"""Main entry point for Authlete MCP Server."""

from src.authlete_mcp.logging import get_logger
from src.authlete_mcp.server import run

if __name__ == "__main__":
    # Use our PII masking logger instead of standard logging
    logger = get_logger(__name__)
    logger.info("Starting Authlete MCP Server...")
    run()
