#!/usr/bin/env python3
"""
Script to update Authlete IdP OpenAPI spec.

Downloads the latest OpenAPI specification from Authlete IdP API and updates
the local resources/idp-openapi-spec.{json,yaml} files.
"""

import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx
import yaml

AUTHLETE_IDP_SPEC_URL = "https://login.authlete.com/v3/api-docs"
RESOURCES_DIR = Path(__file__).parent.parent / "resources"
IDP_OPENAPI_SPEC_FILE = RESOURCES_DIR / "idp-openapi-spec.yaml"
IDP_OPENAPI_SPEC_JSON_FILE = RESOURCES_DIR / "idp-openapi-spec.json"


def compute_spec_hash(spec_data: dict) -> str:
    """Compute a stable hash of the specification for change detection."""
    normalized = json.dumps(spec_data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


async def download_idp_openapi_spec(max_retries: int = 3, retry_delay: float = 5.0) -> dict:
    """Download the IdP OpenAPI spec JSON from Authlete IdP API."""
    print(f"Downloading IdP OpenAPI spec from {AUTHLETE_IDP_SPEC_URL}...")

    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
                response = await client.get(AUTHLETE_IDP_SPEC_URL)
                response.raise_for_status()

                print(f"Downloaded {len(response.content)} bytes")

                spec_data = response.json()
                return spec_data
        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
            last_error = exc
            print(f"Attempt {attempt}/{max_retries} failed: {type(exc).__name__}: {exc}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)

    raise RuntimeError(
        f"Failed to download IdP OpenAPI spec after {max_retries} attempts: {type(last_error).__name__}: {last_error}"
    )


def save_idp_openapi_spec(spec_data: dict) -> None:
    """Save the IdP OpenAPI spec to resources/idp-openapi-spec.{json,yaml}."""
    # Ensure resources directory exists
    RESOURCES_DIR.mkdir(exist_ok=True)

    # Save JSON version
    with open(IDP_OPENAPI_SPEC_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(spec_data, f, indent=2, ensure_ascii=False)

    # Save YAML for readability/reference
    with open(IDP_OPENAPI_SPEC_FILE, "w", encoding="utf-8") as f:
        yaml.dump(spec_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"IdP OpenAPI spec saved to {IDP_OPENAPI_SPEC_JSON_FILE} and {IDP_OPENAPI_SPEC_FILE}")


def load_existing_spec() -> dict | None:
    """Load the previously stored IdP spec if it exists."""
    if IDP_OPENAPI_SPEC_JSON_FILE.exists():
        loader = json.load
        source = IDP_OPENAPI_SPEC_JSON_FILE
    elif IDP_OPENAPI_SPEC_FILE.exists():
        loader = yaml.safe_load
        source = IDP_OPENAPI_SPEC_FILE
    else:
        return None

    try:
        with open(source, encoding="utf-8") as handle:
            return loader(handle)
    except (json.JSONDecodeError, yaml.YAMLError, OSError):
        return None


def extract_metadata(spec_data: dict | None) -> tuple[str, int]:
    """Return version and path count metadata."""
    if not isinstance(spec_data, dict):
        return ("unknown", 0)

    info = spec_data.get("info") or {}
    version = info.get("version", "unknown")
    paths_count = len(spec_data.get("paths", {}) or {})
    return (version, paths_count)


def emit_github_outputs(outputs: dict[str, Any]) -> None:
    """Emit outputs for GitHub Actions, if available."""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return

    with open(output_path, "a", encoding="utf-8") as handle:
        for key, value in outputs.items():
            if value is None:
                continue
            handle.write(f"{key}={value}\n")


async def main():
    """Main function to update the IdP OpenAPI spec."""
    try:
        print("Starting IdP OpenAPI spec update...")

        # Download the JSON file directly
        spec_data = await download_idp_openapi_spec()

        # Validate it's a proper OpenAPI spec
        if "openapi" not in spec_data and "swagger" not in spec_data:
            print("WARNING: Downloaded data doesn't appear to be an OpenAPI spec")
            print(f"Keys found: {list(spec_data.keys())}")

        existing_spec = load_existing_spec()
        new_spec_hash = compute_spec_hash(spec_data)
        existing_spec_hash = compute_spec_hash(existing_spec) if existing_spec else ""
        current_version, current_paths = extract_metadata(existing_spec)
        new_version, new_paths = extract_metadata(spec_data)

        has_changes = new_spec_hash != existing_spec_hash

        if not has_changes:
            print("No changes detected - IdP OpenAPI spec is up to date")
            emit_github_outputs(
                {
                    "has-changes": "false",
                    "current-version": current_version,
                    "current-paths": current_paths,
                    "new-version": new_version,
                    "new-paths": new_paths,
                    "spec-sha256": new_spec_hash,
                }
            )
            return

        # Save the spec
        save_idp_openapi_spec(spec_data)

        # Print some info about the spec
        info = spec_data.get("info", {})

        print("Updated IdP OpenAPI spec:")
        print(f"  Title: {info.get('title', 'Unknown')}")
        print(f"  Version: {new_version}")
        print(f"  Paths: {new_paths}")

        print("IdP OpenAPI spec update completed successfully!")

        emit_github_outputs(
            {
                "has-changes": "true",
                "current-version": current_version,
                "current-paths": current_paths,
                "new-version": new_version,
                "new-paths": new_paths,
                "spec-sha256": new_spec_hash,
            }
        )

    except Exception as e:
        print(f"ERROR: Failed to update IdP OpenAPI spec: {type(e).__name__}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
