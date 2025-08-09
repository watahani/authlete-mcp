#!/usr/bin/env python3
"""
Test operationId search functionality for the Authlete API search server
"""

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from authlete_api_search_server import AuthleteApiSearcher


class TestOperationIdSearch:
    """Test cases for operation_id search functionality"""

    @pytest.fixture
    async def searcher(self):
        """Create AuthleteApiSearcher instance"""
        return AuthleteApiSearcher()

    @pytest.mark.asyncio
    async def test_search_by_operation_id_auth_token_revoke(self, searcher):
        """Test searching for auth_token_revoke_api by operationId"""
        # Test the specific operation_id mentioned by user
        operation_id = "auth_token_revoke_api"

        # Search by operation_id
        detail = await searcher.get_api_detail(operation_id=operation_id)

        # Verify the result
        assert detail is not None, f"API with operationId '{operation_id}' should be found"
        assert detail["operation_id"] == operation_id
        assert detail["path"] == "/api/{serviceId}/auth/token/revoke"
        assert detail["method"] == "POST"
        assert "revoke" in detail["summary"].lower() or "revoke" in detail["description"].lower()

    @pytest.mark.asyncio
    async def test_search_apis_finds_token_revoke(self, searcher):
        """Test that search_apis can find the token revoke API"""
        # Search for token revoke APIs
        results = await searcher.search_apis(query="revoke token", limit=10)

        # Find the auth_token_revoke_api in results
        revoke_api = None
        for result in results:
            if result.get("operation_id") == "auth_token_revoke_api":
                revoke_api = result
                break

        assert revoke_api is not None, "auth_token_revoke_api should be found in search results"
        assert revoke_api["path"] == "/api/{serviceId}/auth/token/revoke"
        assert revoke_api["method"] == "POST"

    @pytest.mark.asyncio
    async def test_get_api_detail_by_path_method(self, searcher):
        """Test getting API detail by path and method (traditional way)"""
        path = "/api/{serviceId}/auth/token/revoke"
        method = "POST"

        detail = await searcher.get_api_detail(path=path, method=method)

        assert detail is not None, f"API {method} {path} should be found"
        assert detail["path"] == path
        assert detail["method"] == method
        assert detail["operation_id"] == "auth_token_revoke_api"

    @pytest.mark.asyncio
    async def test_get_api_detail_by_operation_id_vs_path_method(self, searcher):
        """Test that operation_id search returns same result as path+method search"""
        operation_id = "auth_token_revoke_api"
        path = "/api/{serviceId}/auth/token/revoke"
        method = "POST"

        # Get detail by operation_id
        detail_by_operation_id = await searcher.get_api_detail(operation_id=operation_id)

        # Get detail by path+method
        detail_by_path_method = await searcher.get_api_detail(path=path, method=method)

        # Both should return the same API
        assert detail_by_operation_id is not None
        assert detail_by_path_method is not None
        assert detail_by_operation_id["path"] == detail_by_path_method["path"]
        assert detail_by_operation_id["method"] == detail_by_path_method["method"]
        assert detail_by_operation_id["operation_id"] == detail_by_path_method["operation_id"]

    @pytest.mark.asyncio
    async def test_operation_id_not_found(self, searcher):
        """Test behavior when operation_id doesn't exist"""
        non_existent_operation_id = "non_existent_operation_id_12345"

        detail = await searcher.get_api_detail(operation_id=non_existent_operation_id)

        assert detail is None, "Non-existent operation_id should return None"

    @pytest.mark.asyncio
    async def test_operation_id_parameter_validation(self, searcher):
        """Test parameter validation for get_api_detail"""
        # Test with no parameters - should return None
        detail = await searcher.get_api_detail()
        assert detail is None, "get_api_detail with no parameters should return None"

        # Test with only path but no method - should return None
        detail = await searcher.get_api_detail(path="/api/{serviceId}/auth/token/revoke")
        assert detail is None, "get_api_detail with only path should return None"

        # Test with only method but no path - should return None
        detail = await searcher.get_api_detail(method="POST")
        assert detail is None, "get_api_detail with only method should return None"

    @pytest.mark.asyncio
    async def test_multiple_token_operations(self, searcher):
        """Test that we can find multiple token-related operations by their operation_ids"""
        token_operation_ids = [
            "auth_token_api",
            "auth_token_create_api",
            "auth_token_delete_api",
            "auth_token_revoke_api",
        ]

        found_operations = []
        for operation_id in token_operation_ids:
            detail = await searcher.get_api_detail(operation_id=operation_id)
            if detail:
                found_operations.append(
                    {"operation_id": detail["operation_id"], "path": detail["path"], "method": detail["method"]}
                )

        # Should find at least 3 token operations (including the revoke one)
        assert len(found_operations) >= 3, f"Should find at least 3 token operations, found: {found_operations}"

        # Verify auth_token_revoke_api is in the results
        revoke_found = any(op["operation_id"] == "auth_token_revoke_api" for op in found_operations)
        assert revoke_found, "auth_token_revoke_api should be found in token operations"

    @pytest.mark.asyncio
    async def test_natural_language_search_for_revoke(self, searcher):
        """Test that natural language search can find the revoke API"""
        # Test natural language queries that should realistically find the revoke API
        # (based on actual words in the API summary and description)
        queries = ["revoke token", "revoke access token", "revoke"]

        for query in queries:
            results = await searcher.search_apis(query=query, limit=10)

            # Check if auth_token_revoke_api is in the results (should be in top results)
            revoke_found = any(
                result.get("operation_id") == "auth_token_revoke_api"
                for result in results[:5]  # Check top 5 results
            )

            assert revoke_found, (
                f"Query '{query}' should find auth_token_revoke_api in top 5 results, but found: {[r.get('operation_id') for r in results[:5]]}"
            )

        # Test that "revoke" gives auth_token_revoke_api as the top result
        results = await searcher.search_apis(query="revoke", limit=5)
        assert len(results) > 0, "Query 'revoke' should return results"
        assert results[0].get("operation_id") == "auth_token_revoke_api", (
            f"Query 'revoke' should return auth_token_revoke_api as top result, got: {results[0].get('operation_id')}"
        )

    @pytest.mark.asyncio
    async def test_revoke_token_includes_both_revoke_apis(self, searcher):
        """Test that 'revoke token' search includes both revoke-related APIs"""
        results = await searcher.search_apis(query="revoke token", limit=10)

        # Extract operation_ids from results
        operation_ids = [result.get("operation_id") for result in results]

        # Both revoke-related APIs should be in the results
        assert "auth_token_revoke_api" in operation_ids, (
            f"auth_token_revoke_api should be in revoke token search results. Found: {operation_ids[:5]}"
        )
        assert "auth_revocation_api" in operation_ids, (
            f"auth_revocation_api should be in revoke token search results. Found: {operation_ids[:5]}"
        )

        # Find the positions of both APIs
        revoke_api_position = operation_ids.index("auth_token_revoke_api") + 1
        revocation_api_position = operation_ids.index("auth_revocation_api") + 1

        print("Search results positions:")
        print(f"  auth_token_revoke_api: #{revoke_api_position}")
        print(f"  auth_revocation_api: #{revocation_api_position}")

        # Both should be in top results (within first 10)
        assert revoke_api_position <= 10, (
            f"auth_token_revoke_api should be in top 10 results, found at position {revoke_api_position}"
        )
        assert revocation_api_position <= 10, (
            f"auth_revocation_api should be in top 10 results, found at position {revocation_api_position}"
        )

        # Verify the details of both APIs
        revoke_api = next(r for r in results if r.get("operation_id") == "auth_token_revoke_api")
        revocation_api = next(r for r in results if r.get("operation_id") == "auth_revocation_api")

        # Verify paths and methods
        assert revoke_api["path"] == "/api/{serviceId}/auth/token/revoke"
        assert revoke_api["method"] == "POST"
        assert revocation_api["path"] == "/api/{serviceId}/auth/revocation"
        assert revocation_api["method"] == "POST"


if __name__ == "__main__":
    # Run specific test for quick verification
    async def quick_test():
        searcher = AuthleteApiSearcher()

        print("🧪 Testing auth_token_revoke_api...")
        detail = await searcher.get_api_detail(operation_id="auth_token_revoke_api")

        if detail:
            print(f"✅ Found: {detail['method']} {detail['path']}")
            print(f"   Summary: {detail['summary']}")
        else:
            print("❌ auth_token_revoke_api not found")

    asyncio.run(quick_test())
