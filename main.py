#!/usr/bin/env python3
"""Main entry point for Authlete MCP Server."""

import os

from src.authlete_mcp.logging import get_logger
from src.authlete_mcp.server import run

if __name__ == "__main__":
    # Use our PII masking logger instead of standard logging
    logger = get_logger(__name__)

    # Log environment variable status for debugging
    org_token = os.getenv("ORGANIZATION_ACCESS_TOKEN", "")
    org_id = os.getenv("ORGANIZATION_ID", "")

    logger.info("Starting Authlete MCP Server...")
    logger.debug(f"ORGANIZATION_ACCESS_TOKEN: {'SET' if org_token else 'NOT SET'}")
    logger.debug(f"ORGANIZATION_ID: {'SET' if org_id else 'NOT SET'}")

    if not org_token:
        logger.warning(
            "ORGANIZATION_ACCESS_TOKEN not set - API operations will be disabled, search functionality will be available"
        )

    run()
