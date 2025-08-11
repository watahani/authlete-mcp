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
    """List all services in the organization with pagination."""
    all_services = []
    start = 0
    page_size = 8  # Small page size for testing pagination

    try:
        while True:
            end = start + page_size
            endpoint = f"service/get/list?limited=true&start={start}&end={end}"
            response = await make_authlete_request("GET", endpoint, config)

            services = response.get("services", [])
            total_count = response.get("totalCount", 0)

            all_services.extend(services)

            # Check if we've reached the end - when start >= total_count or no services returned
            if start >= total_count or len(services) == 0:
                break

            start = end  # Next start is end (inclusive range)

        print(f"Found {len(all_services)} total services (totalCount: {total_count})")
        return all_services

    except Exception as e:
        print(f"Error listing services: {e}")
        return []


async def delete_service_by_api_key(config: AuthleteConfig, service_api_key: str, service_name: str) -> bool:
    """Delete a service using IdP API by its API key."""
    try:
        # Delete using IdP API with organization token
        delete_data = {
            "organizationId": os.getenv("ORGANIZATION_ID", ""),
            "serviceId": service_api_key,  # Use the API key directly as service ID
            "apiServerId": config.api_server_id,
        }

        await make_authlete_idp_request("POST", "service/remove", config, delete_data)
        print(f"✅ Deleted service: {service_name} (ID: {service_api_key})")
        return True

    except Exception as e:
        print(f"❌ Error deleting service {service_name}: {type(e).__name__}: {str(e)}")
        import traceback

        print(f"   Full traceback: {traceback.format_exc()}")
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
    config = AuthleteConfig(api_key=org_token)

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

        success = await delete_service_by_api_key(config, str(service_api_key), service_name)
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
