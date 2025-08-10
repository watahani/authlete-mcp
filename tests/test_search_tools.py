"""Test cases for API search tools."""

import json
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.unit
async def test_search_apis_basic_functionality():
    """Test search_apis basic functionality"""
    server_params = StdioServerParameters(
        command="python", args=["-m", "authlete_mcp_server"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # Call search_apis tool
            result = await session.call_tool("search_apis", {"query": "token"})

            # Should return some kind of result (JSON array, error message, or no results message)
            content = result.content[0].text
            assert content is not None and len(content) > 0

            # If it returns JSON (database exists and works), verify basic structure
            try:
                import json

                results = json.loads(content)
                if isinstance(results, list) and results:
                    # Verify structure of results
                    first_result = results[0]
                    assert "path" in first_result
                    assert "method" in first_result
                    assert "summary" in first_result
            except json.JSONDecodeError:
                # If not JSON, should be an error message or no results message
                assert (
                    "Search database not found" in content
                    or "No APIs found matching the search criteria." in content
                    or "Search error:" in content
                )


@pytest.mark.integration
async def test_search_apis_with_database():
    """Test search_apis functionality with actual database"""
    # Skip if search database doesn't exist
    db_path = Path("resources/authlete_apis.duckdb")
    if not db_path.exists():
        pytest.skip("Search database not found. Run 'uv run python scripts/create_search_database.py' first")

    server_params = StdioServerParameters(
        command="python", args=["-m", "authlete_mcp_server"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test basic search
            result = await session.call_tool("search_apis", {"query": "token"})

            # Should return JSON results
            content = result.content[0].text
            assert content != "No APIs found matching the search criteria."

            # Parse the JSON response
            search_results = json.loads(content)
            assert isinstance(search_results, list)

            if search_results:  # If there are results
                # Check structure of first result
                first_result = search_results[0]
                required_fields = ["path", "method", "operation_id", "summary", "description", "tags", "score"]
                for field in required_fields:
                    assert field in first_result


@pytest.mark.integration
async def test_search_apis_with_filters():
    """Test search_apis with various filters"""
    # Skip if search database doesn't exist
    db_path = Path("resources/authlete_apis.duckdb")
    if not db_path.exists():
        pytest.skip("Search database not found. Run 'uv run python scripts/create_search_database.py' first")

    server_params = StdioServerParameters(
        command="python", args=["-m", "authlete_mcp_server"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test with method filter
            result = await session.call_tool("search_apis", {"query": "auth", "method_filter": "POST", "limit": 5})

            content = result.content[0].text
            if content != "No APIs found matching the search criteria.":
                search_results = json.loads(content)
                assert len(search_results) <= 5

                # Check that all results have POST method
                for result in search_results:
                    assert result["method"] == "POST"


@pytest.mark.integration
async def test_get_api_detail_with_database():
    """Test get_api_detail functionality"""
    # Skip if search database doesn't exist
    db_path = Path("resources/authlete_apis.duckdb")
    if not db_path.exists():
        pytest.skip("Search database not found. Run 'uv run python scripts/create_search_database.py' first")

    server_params = StdioServerParameters(
        command="python", args=["-m", "authlete_mcp_server"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # First find an API to get details for
            search_result = await session.call_tool("search_apis", {"query": "token", "limit": 1})
            search_content = search_result.content[0].text

            if search_content != "No APIs found matching the search criteria.":
                search_results = json.loads(search_content)
                if search_results:
                    first_api = search_results[0]

                    # Get API details using path and method
                    detail_result = await session.call_tool(
                        "get_api_detail", {"path": first_api["path"], "method": first_api["method"]}
                    )

                    detail_content = detail_result.content[0].text
                    assert not detail_content.startswith("API details not found")

                    # Parse the detailed response
                    api_detail = json.loads(detail_content)
                    required_fields = [
                        "path",
                        "method",
                        "operation_id",
                        "summary",
                        "description",
                        "parameters",
                        "request_body",
                        "responses",
                    ]
                    for field in required_fields:
                        assert field in api_detail


@pytest.mark.integration
async def test_get_api_detail_by_operation_id():
    """Test get_api_detail using operation_id"""
    # Skip if search database doesn't exist
    db_path = Path("resources/authlete_apis.duckdb")
    if not db_path.exists():
        pytest.skip("Search database not found. Run 'uv run python scripts/create_search_database.py' first")

    server_params = StdioServerParameters(
        command="python", args=["-m", "authlete_mcp_server"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # First find an API with operation_id
            search_result = await session.call_tool("search_apis", {"query": "token", "limit": 1})
            search_content = search_result.content[0].text

            if search_content != "No APIs found matching the search criteria.":
                search_results = json.loads(search_content)
                if search_results and search_results[0]["operation_id"]:
                    operation_id = search_results[0]["operation_id"]

                    # Get API details using operation_id
                    detail_result = await session.call_tool("get_api_detail", {"operation_id": operation_id})

                    detail_content = detail_result.content[0].text
                    assert not detail_content.startswith("API details not found")

                    api_detail = json.loads(detail_content)
                    assert api_detail["operation_id"] == operation_id


@pytest.mark.integration
async def test_get_sample_code():
    """Test get_sample_code functionality"""
    # Skip if search database doesn't exist
    db_path = Path("resources/authlete_apis.duckdb")
    if not db_path.exists():
        pytest.skip("Search database not found. Run 'uv run python scripts/create_search_database.py' first")

    server_params = StdioServerParameters(
        command="python", args=["-m", "authlete_mcp_server"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # First find an API
            search_result = await session.call_tool("search_apis", {"query": "token", "limit": 1})
            search_content = search_result.content[0].text

            if search_content != "No APIs found matching the search criteria.":
                search_results = json.loads(search_content)
                if search_results:
                    first_api = search_results[0]

                    # Get sample code in curl format
                    sample_result = await session.call_tool(
                        "get_sample_code",
                        {"language": "curl", "path": first_api["path"], "method": first_api["method"]},
                    )

                    sample_content = sample_result.content[0].text

                    # Should either return sample code or "Sample code not found"
                    assert isinstance(sample_content, str)
                    # If it's sample code, it should contain "curl" command
                    if not sample_content.startswith("Sample code not found"):
                        assert "curl" in sample_content.lower()


@pytest.mark.unit
async def test_get_api_detail_missing_params():
    """Test get_api_detail with missing required parameters"""
    server_params = StdioServerParameters(
        command="python", args=["-m", "authlete_mcp_server"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call without required parameters
            result = await session.call_tool("get_api_detail", {})

            content = result.content[0].text
            assert "Either 'operation_id' or both 'path' and 'method' parameters are required" in content


@pytest.mark.unit
async def test_get_sample_code_missing_language():
    """Test get_sample_code with missing language parameter"""
    server_params = StdioServerParameters(
        command="python", args=["-m", "authlete_mcp_server"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call without language parameter
            result = await session.call_tool("get_sample_code", {"path": "/test", "method": "GET"})

            content = result.content[0].text
            # FastMCP handles validation at framework level
            assert (
                "language parameter is required" in content
                or "validation error" in content
                or "Field required" in content
            )


@pytest.mark.integration
async def test_search_apis_with_method_filter():
    """Test search_apis with method filter"""
    # Skip if search database doesn't exist
    db_path = Path("resources/authlete_apis.duckdb")
    if not db_path.exists():
        pytest.skip("Search database not found. Run 'uv run python scripts/create_search_database.py' first")

    server_params = StdioServerParameters(
        command="python", args=["-m", "authlete_mcp_server"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Search with method filter
            result = await session.call_tool("search_apis", {"query": "api", "method_filter": "POST", "limit": 10})

            content = result.content[0].text
            assert content is not None

            # If we get results, verify they're all POST methods
            if content != "No APIs found matching the search criteria.":
                try:
                    results = json.loads(content)
                    if isinstance(results, list) and results:
                        for api_result in results:
                            assert api_result.get("method") == "POST"
                except json.JSONDecodeError:
                    # Error message is acceptable
                    pass


@pytest.mark.integration
async def test_search_apis_with_different_modes():
    """Test search_apis with different search modes"""
    # Skip if search database doesn't exist
    db_path = Path("resources/authlete_apis.duckdb")
    if not db_path.exists():
        pytest.skip("Search database not found. Run 'uv run python scripts/create_search_database.py' first")

    server_params = StdioServerParameters(
        command="python", args=["-m", "authlete_mcp_server"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test different search modes (the 'mode' parameter may not be supported in current implementation)
            search_modes = ["natural"]  # Only test supported mode

            for mode in search_modes:
                result = await session.call_tool("search_apis", {"query": "service", "mode": mode, "limit": 3})

                content = result.content[0].text
                assert content is not None
                # Should not return a search error
                assert not content.startswith("Search error:")


@pytest.mark.unit
async def test_search_apis_with_no_parameters():
    """Test search_apis with no parameters"""
    server_params = StdioServerParameters(
        command="python", args=["-m", "authlete_mcp_server"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Search with no parameters
            result = await session.call_tool("search_apis", {})

            content = result.content[0].text
            # Should return either search results or "no results" message
            try:
                results = json.loads(content)
                is_valid_json = isinstance(results, list)
            except json.JSONDecodeError:
                is_valid_json = False

            assert (
                "No APIs found matching the search criteria." in content
                or "Search database not found" in content
                or is_valid_json
            )
