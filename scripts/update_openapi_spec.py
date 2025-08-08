#!/usr/bin/env python3
"""
Script to update OpenAPI spec from Authlete documentation.

Downloads the latest OpenAPI specification from Authlete docs and updates
the local resources/openapi-spec.json file.
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx

AUTHLETE_SPEC_URL = "https://docs.authlete.com/en/shared/3.0.0/spec"
RESOURCES_DIR = Path(__file__).parent.parent / "resources"
OPENAPI_SPEC_FILE = RESOURCES_DIR / "openapi-spec.json"


async def download_openapi_spec() -> dict:
    """Download the OpenAPI spec JSON directly from Authlete docs."""
    print(f"Downloading OpenAPI spec from {AUTHLETE_SPEC_URL}...")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(AUTHLETE_SPEC_URL)
        response.raise_for_status()

        print(f"Downloaded {len(response.content)} bytes")

        # Parse JSON directly
        try:
            spec_data = response.json()
            return spec_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")


def save_openapi_spec(spec_data: dict) -> None:
    """Save the OpenAPI spec to resources/openapi-spec.json."""
    # Ensure resources directory exists
    RESOURCES_DIR.mkdir(exist_ok=True)

    # Save with pretty formatting
    with open(OPENAPI_SPEC_FILE, "w", encoding="utf-8") as f:
        json.dump(spec_data, f, indent=2, ensure_ascii=False)

    print(f"OpenAPI spec saved to {OPENAPI_SPEC_FILE}")


def check_for_changes(new_spec: dict) -> bool:
    """Check if the downloaded spec is different from the existing one."""
    if not OPENAPI_SPEC_FILE.exists():
        print("No existing OpenAPI spec found - will create new file")
        return True

    try:
        with open(OPENAPI_SPEC_FILE, encoding="utf-8") as f:
            existing_spec = json.load(f)

        # Compare versions if available
        existing_version = existing_spec.get("info", {}).get("version")
        new_version = new_spec.get("info", {}).get("version")

        if existing_version and new_version:
            if existing_version != new_version:
                print(f"Version change detected: {existing_version} -> {new_version}")
                return True

        # Compare paths count as a simple check
        existing_paths = len(existing_spec.get("paths", {}))
        new_paths = len(new_spec.get("paths", {}))

        if existing_paths != new_paths:
            print(f"Path count changed: {existing_paths} -> {new_paths}")
            return True

        print("No significant changes detected")
        return False

    except (json.JSONDecodeError, FileNotFoundError):
        print("Error reading existing spec - will update")
        return True


async def main():
    """Main function to update the OpenAPI spec."""
    try:
        print("Starting OpenAPI spec update...")

        # Download the JSON file directly
        spec_data = await download_openapi_spec()

        # Validate it's a proper OpenAPI spec
        if "openapi" not in spec_data and "swagger" not in spec_data:
            print("WARNING: Downloaded JSON doesn't appear to be an OpenAPI spec")
            print(f"Keys found: {list(spec_data.keys())}")

        # Check for changes
        has_changes = check_for_changes(spec_data)

        if not has_changes:
            print("No changes detected - OpenAPI spec is up to date")
            return

        # Save the spec
        save_openapi_spec(spec_data)

        # Print some info about the spec
        info = spec_data.get("info", {})
        print("Updated OpenAPI spec:")
        print(f"  Title: {info.get('title', 'Unknown')}")
        print(f"  Version: {info.get('version', 'Unknown')}")
        print(f"  Paths: {len(spec_data.get('paths', {}))}")

        print("OpenAPI spec update completed successfully!")

    except Exception as e:
        print(f"ERROR: Failed to update OpenAPI spec: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
