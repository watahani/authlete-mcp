#!/usr/bin/env python3
"""Main entry point for Authlete MCP Server."""

import logging

from src.authlete_mcp.server import run

# Setup logging configuration for debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="/tmp/authlete_mcp.log",  # Log to file instead of stderr
    filemode="w",  # Overwrite log file each time
)

# Enable debug logging for our modules
logging.getLogger("authlete_mcp").setLevel(logging.DEBUG)
logging.getLogger("src.authlete_mcp").setLevel(logging.DEBUG)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("Starting Authlete MCP Server with debug logging...")
    run()
