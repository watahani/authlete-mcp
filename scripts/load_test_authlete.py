#!/usr/bin/env python3
"""Simple load test runner for Authlete API."""

import asyncio
import json
import os
import sys
import time
from collections import Counter
from typing import Any

import httpx
from dotenv import load_dotenv

REQUESTS_PER_SECOND = int(os.getenv("LOAD_TEST_RPS", "100"))
TEST_DURATION_SECONDS = float(os.getenv("LOAD_TEST_DURATION_SECONDS", "5"))
ENDPOINT_PATH = os.getenv(
    "LOAD_TEST_ENDPOINT",
    "/api/service/get/list?limited=true&start=0&end=1",
)
TIMEOUT_SECONDS = float(os.getenv("LOAD_TEST_TIMEOUT_SECONDS", "10"))


def ensure_env() -> tuple[str, str]:
    """Ensure required environment variables are present."""
    load_dotenv()

    access_token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    base_url = os.getenv("AUTHLETE_API_URL") or os.getenv("AUTHLETE_BASE_URL")

    if not access_token or not base_url:
        print("Missing required environment variables.", file=sys.stderr)
        print("Ensure ORGANIZATION_ACCESS_TOKEN and AUTHLETE_API_URL are set in .env.", file=sys.stderr)
        sys.exit(1)

    return access_token, base_url.rstrip("/")


async def perform_request(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    results: list[dict[str, Any]],
    idx: int,
) -> None:
    """Execute a single HTTP request and capture the outcome."""
    start = time.perf_counter()
    entry: dict[str, Any] = {"id": idx}
    try:
        response = await client.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        entry["status"] = response.status_code
        entry["elapsed_ms"] = round((time.perf_counter() - start) * 1000, 2)
        if response.status_code >= 400:
            payload = response.text
            entry["error_excerpt"] = payload[:200]
    except Exception as exc:  # noqa: BLE001 - want raw exception details
        entry["status"] = "exception"
        entry["error"] = repr(exc)
        entry["elapsed_ms"] = round((time.perf_counter() - start) * 1000, 2)

    results.append(entry)


async def run_load_test(total_requests: int) -> list[dict[str, Any]]:
    """Run the load test and return collected request metadata."""
    access_token, base_url = ensure_env()
    url = f"{base_url}{ENDPOINT_PATH}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    results: list[dict[str, Any]] = []
    interval = 1.0 / REQUESTS_PER_SECOND

    async with httpx.AsyncClient() as client:
        tasks = []
        for idx in range(total_requests):
            tasks.append(asyncio.create_task(perform_request(client, url, headers, results, idx)))
            await asyncio.sleep(interval)

        await asyncio.gather(*tasks)

    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate a summary of the load test run."""
    status_counts = Counter(str(result.get("status")) for result in results)
    durations = [result.get("elapsed_ms", 0) for result in results if isinstance(result.get("elapsed_ms"), int | float)]
    summary = {
        "total_requests": len(results),
        "status_counts": dict(status_counts),
        "min_latency_ms": min(durations) if durations else None,
        "max_latency_ms": max(durations) if durations else None,
        "avg_latency_ms": round(sum(durations) / len(durations), 2) if durations else None,
    }

    errors = [result for result in results if str(result.get("status")) not in {"200", "204"}]
    if errors:
        summary["error_samples"] = errors[:5]

    return summary


async def main() -> None:
    total_requests = int(REQUESTS_PER_SECOND * TEST_DURATION_SECONDS)
    print(
        json.dumps(
            {
                "rps": REQUESTS_PER_SECOND,
                "duration_seconds": TEST_DURATION_SECONDS,
                "total_requests": total_requests,
                "endpoint": ENDPOINT_PATH,
            },
            indent=2,
        )
    )

    results = await run_load_test(total_requests)
    report = summarize(results)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
