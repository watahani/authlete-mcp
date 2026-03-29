#!/usr/bin/env python3
"""
Script to update OpenAPI spec from Authlete documentation.

Downloads the latest OpenAPI specification from Authlete docs and updates
the local resources/openapi-spec.json file.
"""

import asyncio
import sys
from pathlib import Path

import httpx
import yaml

AUTHLETE_SPEC_URL = "https://raw.githubusercontent.com/authlete/openapi/refs/heads/main/spec_next.yaml"
RESOURCES_DIR = Path(__file__).parent.parent / "resources"
OPENAPI_SPEC_FILE = RESOURCES_DIR / "openapi-spec.json"


async def download_openapi_spec(max_retries: int = 3, retry_delay: float = 5.0) -> dict:
    """Download the OpenAPI spec (YAML format) from Authlete docs."""
    print(f"Downloading OpenAPI spec from {AUTHLETE_SPEC_URL}...")

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(AUTHLETE_SPEC_URL)
                response.raise_for_status()

                print(f"Downloaded {len(response.content)} bytes")
                content_type = response.headers.get("content-type", "").lower()
                print(f"Content-Type: {content_type}")

                spec_data = yaml.safe_load(response.text)
                print("Parsed as YAML format")
                return spec_data
        except (httpx.HTTPStatusError, httpx.RequestError, yaml.YAMLError) as exc:
            last_error = exc
            print(f"Attempt {attempt}/{max_retries} failed: {type(exc).__name__}: {exc}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)

    raise RuntimeError(
        f"Failed to download OpenAPI spec after {max_retries} attempts: {type(last_error).__name__}: {last_error}"
    )


def save_openapi_spec(spec_data: dict) -> None:
    """Save the OpenAPI spec to resources/openapi-spec.json."""
    # Ensure resources directory exists
    RESOURCES_DIR.mkdir(exist_ok=True)

    # Save with pretty formatting
    import json

    with open(OPENAPI_SPEC_FILE, "w", encoding="utf-8") as f:
        json.dump(spec_data, f, indent=2, ensure_ascii=False)

    print(f"OpenAPI spec saved to {OPENAPI_SPEC_FILE}")


def check_for_changes(new_spec: dict) -> bool:
    """Check if the downloaded spec is different from the existing one."""
    if not OPENAPI_SPEC_FILE.exists():
        print("No existing OpenAPI spec found - will create new file")
        return True

    try:
        import json

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

    except (Exception, FileNotFoundError):
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
            print("WARNING: Downloaded data doesn't appear to be an OpenAPI spec")
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
        print(f"ERROR: Failed to update OpenAPI spec: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
