#!/usr/bin/env python3
"""
Cleanup script to delete services created during pytest runs.
This script identifies services with names starting with "pytest-" and deletes them.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from authlete_mcp.api.client import make_authlete_idp_request, make_authlete_request
from authlete_mcp.config import AuthleteConfig


async def list_all_services(config: AuthleteConfig) -> list[dict]:
    """List all services in the organization."""
    try:
        response = await make_authlete_request("GET", "service/get/list", config)
        services = response.get("services", [])
        print(f"Found {len(services)} total services")
        return services
    except Exception as e:
        print(f"Error listing services: {e}")
        return []


async def delete_service_by_api_key(config: AuthleteConfig, service_api_key: str, service_name: str) -> bool:
    """Delete a service using IdP API by its API key."""
    try:
        # First get service details to find the service ID
        service_config = AuthleteConfig(
            api_key=service_api_key,
            base_url=config.base_url,
            idp_url=config.idp_url,
            api_server_id=config.api_server_id,
        )

        service_details = await make_authlete_request("GET", "service", service_config)
        service_id = service_details.get("apiKey")  # API key is used as service ID for deletion

        if not service_id:
            print(f"❌ Could not find service ID for {service_name}")
            return False

        # Delete using IdP API
        delete_data = {
            "organizationId": config.organization_id or os.getenv("ORGANIZATION_ID", ""),
            "serviceId": service_id,
        }

        org_config = AuthleteConfig(
            api_key=config.api_key,  # Use organization token for IdP operations
            base_url=config.base_url,
            idp_url=config.idp_url,
            api_server_id=config.api_server_id,
        )

        await make_authlete_idp_request("POST", "service/remove", org_config, delete_data)
        print(f"✅ Deleted service: {service_name} (ID: {service_id})")
        return True

    except Exception as e:
        print(f"❌ Error deleting service {service_name}: {e}")
        return False


async def cleanup_test_services():
    """Main cleanup function."""
    print("🧹 Starting cleanup of pytest services...")

    # Check environment
    org_token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not org_token:
        print("❌ ORGANIZATION_ACCESS_TOKEN environment variable not set")
        return False

    organization_id = os.getenv("ORGANIZATION_ID", "")
    if not organization_id:
        print("⚠️ ORGANIZATION_ID not set, using empty string")

    # Create config
    config = AuthleteConfig(api_key=org_token, organization_id=organization_id)

    # List all services
    services = await list_all_services(config)

    # Filter services that start with "pytest-"
    test_services = [service for service in services if service.get("serviceName", "").startswith("pytest-")]

    if not test_services:
        print("✅ No pytest services found to clean up")
        return True

    print(f"🔍 Found {len(test_services)} pytest services to clean up:")
    for service in test_services:
        print(f"  - {service.get('serviceName')} (API Key: {service.get('apiKey')})")

    # Delete each test service
    deleted_count = 0
    failed_count = 0

    for service in test_services:
        service_name = service.get("serviceName")
        service_api_key = service.get("apiKey")

        if not service_api_key:
            print(f"❌ No API key found for service: {service_name}")
            failed_count += 1
            continue

        success = await delete_service_by_api_key(config, service_api_key, service_name)
        if success:
            deleted_count += 1
        else:
            failed_count += 1

    # Summary
    print("\n📊 Cleanup Summary:")
    print(f"   ✅ Successfully deleted: {deleted_count} services")
    print(f"   ❌ Failed to delete: {failed_count} services")
    print(f"   📈 Total processed: {deleted_count + failed_count} services")

    return failed_count == 0


if __name__ == "__main__":
    success = asyncio.run(cleanup_test_services())
    sys.exit(0 if success else 1)
