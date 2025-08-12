#!/usr/bin/env python3
"""Example of creating a service using the Authlete MCP Server."""

import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

load_dotenv()

async def create_service_example():
    """Example of creating a service."""
    
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "python", "main.py"],
        env={
            "ORGANIZATION_ACCESS_TOKEN": os.getenv("ORGANIZATION_ACCESS_TOKEN", ""),
            "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", ""),
            "AUTHLETE_API_URL": os.getenv("AUTHLETE_API_URL", "https://jp.authlete.com"),
            "AUTHLETE_API_SERVER_ID": os.getenv("AUTHLETE_API_SERVER_ID", "53285")
        }
    )
    
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Create a basic service
            print("Creating a basic service...")
            result = await session.call_tool("create_service", {
                "name": "example-service",
                "description": "An example service created via MCP"
            })
            
            if result.content:
                print(f"Result: {result.content[0].text}")
            
            # Create a detailed service
            print("\nCreating a detailed service...")
            detailed_result = await session.call_tool("create_service_detailed", {
                "name": "detailed-example-service",
                "description": "A detailed example service",
                "issuer": "https://example.com/auth",
                "supported_scopes": "openid,profile,email,custom_scope",
                "pkce_required": True,
                "access_token_duration": 3600
            })
            
            if detailed_result.content:
                print(f"Result: {detailed_result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(create_service_example())