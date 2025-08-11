#!/usr/bin/env python3
"""
Script to create 30 numbered pytest services for cleanup testing.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from authlete_mcp.api.client import make_authlete_idp_request
from authlete_mcp.config import AuthleteConfig


async def create_test_service(config: AuthleteConfig, service_number: int) -> bool:
    """Create a single test service."""
    try:
        org_id = os.getenv("ORGANIZATION_ID", "")

        service_data = {
            "serviceName": f"pytest-test-service-{service_number:03d}",
            "description": f"Test service #{service_number} created for cleanup testing",
            "issuer": "https://test.example.com",
            "supportedScopes": [
                {"name": "openid", "defaultEntry": True},
                {"name": "profile", "defaultEntry": False},
                {"name": "email", "defaultEntry": False},
            ],
            "supportedResponseTypes": ["CODE"],
            "supportedGrantTypes": ["AUTHORIZATION_CODE"],
            "supportedTokenAuthMethods": ["CLIENT_SECRET_BASIC"],
            "accessTokenDuration": 3600,
            "refreshTokenDuration": 86400,
            "idTokenDuration": 3600,
            "pkceRequired": True,
        }

        # Create IdP API request payload matching MCP implementation
        data = {"apiServerId": int(config.api_server_id), "organizationId": int(org_id), "service": service_data}

        response = await make_authlete_idp_request("POST", "service", config, data)
        service_id = response.get("apiKey", "unknown")
        print(f"✅ Created service: pytest-test-service-{service_number:03d} (ID: {service_id})")
        return True

    except Exception as e:
        print(f"❌ Error creating service #{service_number}: {type(e).__name__}: {str(e)}")
        return False


async def create_test_services():
    """Create 30 numbered test services."""
    print("🚀 Creating 30 pytest test services for cleanup testing...")

    # Check environment
    org_token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not org_token:
        print("❌ ORGANIZATION_ACCESS_TOKEN environment variable not set")
        return False

    organization_id = os.getenv("ORGANIZATION_ID", "")
    if not organization_id:
        print("❌ ORGANIZATION_ID environment variable not set")
        return False

    # Create config
    config = AuthleteConfig(api_key=org_token)

    # Create services
    created_count = 0
    failed_count = 0
    batch_size = 10  # Create in batches to avoid overwhelming the API

    for batch_start in range(1, 31, batch_size):
        batch_end = min(batch_start + batch_size - 1, 30)
        print(f"\n📦 Creating batch {batch_start}-{batch_end}...")

        # Create batch concurrently
        tasks = []
        for i in range(batch_start, batch_end + 1):
            tasks.append(create_test_service(config, i))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count results
        for result in results:
            if isinstance(result, Exception):
                failed_count += 1
            elif result:
                created_count += 1
            else:
                failed_count += 1

        # Small delay between batches
        if batch_end < 30:
            await asyncio.sleep(2)

    # Summary
    print("\n📊 Creation Summary:")
    print(f"   ✅ Successfully created: {created_count} services")
    print(f"   ❌ Failed to create: {failed_count} services")
    print(f"   📈 Total processed: {created_count + failed_count} services")

    return failed_count == 0


if __name__ == "__main__":
    success = asyncio.run(create_test_services())
    sys.exit(0 if success else 1)
