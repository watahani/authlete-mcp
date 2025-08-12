#!/usr/bin/env python3
"""
Script to update Authlete IdP OpenAPI spec.

Downloads the latest OpenAPI specification from Authlete IdP API and updates
the local resources/idp-openapi-spec.yaml file.
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx
import yaml

AUTHLETE_IDP_SPEC_URL = "https://dev-idp.authlete.net/v3/api-docs.yaml"
RESOURCES_DIR = Path(__file__).parent.parent / "resources"
IDP_OPENAPI_SPEC_FILE = RESOURCES_DIR / "idp-openapi-spec.yaml"
IDP_OPENAPI_SPEC_JSON_FILE = RESOURCES_DIR / "idp-openapi-spec.json"


async def download_idp_openapi_spec() -> dict:
    """Download the IdP OpenAPI spec YAML from Authlete IdP API."""
    print(f"Downloading IdP OpenAPI spec from {AUTHLETE_IDP_SPEC_URL}...")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(AUTHLETE_IDP_SPEC_URL)
        response.raise_for_status()

        print(f"Downloaded {len(response.content)} bytes")

        # Parse YAML directly
        try:
            spec_data = yaml.safe_load(response.text)
            return spec_data
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML response: {e}")


def save_idp_openapi_spec(spec_data: dict) -> None:
    """Save the IdP OpenAPI spec to resources/."""
    # Ensure resources directory exists
    RESOURCES_DIR.mkdir(exist_ok=True)

    # Save as YAML
    with open(IDP_OPENAPI_SPEC_FILE, "w", encoding="utf-8") as f:
        yaml.dump(spec_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Save as JSON for compatibility
    with open(IDP_OPENAPI_SPEC_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(spec_data, f, indent=2, ensure_ascii=False)

    print(f"IdP OpenAPI spec saved to {IDP_OPENAPI_SPEC_FILE} and {IDP_OPENAPI_SPEC_JSON_FILE}")


def check_for_changes(new_spec: dict) -> bool:
    """Check if the downloaded IdP spec is different from the existing one."""
    if not IDP_OPENAPI_SPEC_JSON_FILE.exists():
        print("No existing IdP OpenAPI spec found - will create new file")
        return True

    try:
        with open(IDP_OPENAPI_SPEC_JSON_FILE, encoding="utf-8") as f:
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
    """Main function to update the IdP OpenAPI spec."""
    try:
        print("Starting IdP OpenAPI spec update...")

        # Download the YAML file directly
        spec_data = await download_idp_openapi_spec()

        # Validate it's a proper OpenAPI spec
        if "openapi" not in spec_data and "swagger" not in spec_data:
            print("WARNING: Downloaded YAML doesn't appear to be an OpenAPI spec")
            print(f"Keys found: {list(spec_data.keys())}")

        # Check for changes
        has_changes = check_for_changes(spec_data)

        if not has_changes:
            print("No changes detected - IdP OpenAPI spec is up to date")
            return

        # Save the spec
        save_idp_openapi_spec(spec_data)

        # Print some info about the spec
        info = spec_data.get("info", {})
        print("Updated IdP OpenAPI spec:")
        print(f"  Title: {info.get('title', 'Unknown')}")
        print(f"  Version: {info.get('version', 'Unknown')}")
        print(f"  Paths: {len(spec_data.get('paths', {}))}")

        print("IdP OpenAPI spec update completed successfully!")

    except Exception as e:
        print(f"ERROR: Failed to update IdP OpenAPI spec: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
