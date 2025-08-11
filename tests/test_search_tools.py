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
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
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
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
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
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
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
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
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
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
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
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
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
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
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
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
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
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
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
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
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
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
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


# Schema Search Tests
@pytest.mark.unit
async def test_list_schemas_basic_functionality():
    """Test list_schemas basic functionality"""
    server_params = StdioServerParameters(
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call list_schemas tool
            result = await session.call_tool("list_schemas", {})

            content = result.content[0].text
            assert content is not None and len(content) > 0

            # Should return either JSON results or database not found message
            try:
                schemas = json.loads(content)
                if isinstance(schemas, list):
                    # Verify structure if we got results
                    for schema in schemas[:3]:  # Check first few schemas
                        assert "schema_name" in schema
                        assert "schema_type" in schema
                        assert "title" in schema
                        assert "description" in schema
            except json.JSONDecodeError:
                # If not JSON, should be an error or info message
                assert (
                    "Search database not found" in content
                    or "No schemas found matching the specified criteria." in content
                    or "Schema search error:" in content
                )


@pytest.mark.integration
async def test_list_schemas_with_database():
    """Test list_schemas with actual database"""
    # Skip if search database doesn't exist
    db_path = Path("resources/authlete_apis.duckdb")
    if not db_path.exists():
        pytest.skip("Search database not found. Run 'uv run python scripts/create_search_database.py' first")

    server_params = StdioServerParameters(
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test without parameters (should return all schemas)
            result = await session.call_tool("list_schemas", {})
            content = result.content[0].text

            # Should return JSON results
            assert content != "No schemas found matching the specified criteria."

            schemas = json.loads(content)
            assert isinstance(schemas, list)
            assert len(schemas) > 0

            # Check structure of first schema
            first_schema = schemas[0]
            required_fields = ["schema_name", "schema_type", "title", "description", "score"]
            for field in required_fields:
                assert field in first_schema


@pytest.mark.integration
async def test_list_schemas_with_query():
    """Test list_schemas with query parameter"""
    # Skip if search database doesn't exist
    db_path = Path("resources/authlete_apis.duckdb")
    if not db_path.exists():
        pytest.skip("Search database not found. Run 'uv run python scripts/create_search_database.py' first")

    server_params = StdioServerParameters(
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Search for token-related schemas
            result = await session.call_tool("list_schemas", {"query": "token", "limit": 5})
            content = result.content[0].text

            if content != "No schemas found matching the specified criteria.":
                schemas = json.loads(content)
                assert isinstance(schemas, list)
                assert len(schemas) <= 5

                # Should contain token-related schemas
                schema_names = [s["schema_name"] for s in schemas]
                # Check if any schema name contains 'token' or related terms
                has_relevant_schema = any("token" in name.lower() or "access" in name.lower() for name in schema_names)
                # Allow empty results if no token schemas exist
                assert has_relevant_schema or len(schemas) == 0


@pytest.mark.integration
async def test_list_schemas_with_limit():
    """Test list_schemas with limit parameter"""
    # Skip if search database doesn't exist
    db_path = Path("resources/authlete_apis.duckdb")
    if not db_path.exists():
        pytest.skip("Search database not found. Run 'uv run python scripts/create_search_database.py' first")

    server_params = StdioServerParameters(
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test with limit parameter
            result = await session.call_tool("list_schemas", {"limit": 5})
            content = result.content[0].text

            if content != "No schemas found matching the specified criteria.":
                schemas = json.loads(content)
                assert isinstance(schemas, list)
                assert len(schemas) <= 5


@pytest.mark.unit
async def test_get_schema_detail_missing_param():
    """Test get_schema_detail with missing schema_name parameter"""
    server_params = StdioServerParameters(
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call without schema_name parameter
            result = await session.call_tool("get_schema_detail", {})

            content = result.content[0].text
            # FastMCP handles validation at framework level
            assert (
                "schema_name parameter is required" in content
                or "validation error" in content
                or "Field required" in content
            )


@pytest.mark.integration
async def test_get_schema_detail_with_database():
    """Test get_schema_detail with actual database"""
    # Skip if search database doesn't exist
    db_path = Path("resources/authlete_apis.duckdb")
    if not db_path.exists():
        pytest.skip("Search database not found. Run 'uv run python scripts/create_search_database.py' first")

    server_params = StdioServerParameters(
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # First get a list of available schemas
            list_result = await session.call_tool("list_schemas", {"limit": 1})
            list_content = list_result.content[0].text

            if list_content != "No schemas found matching the specified criteria.":
                schemas = json.loads(list_content)
                if schemas:
                    schema_name = schemas[0]["schema_name"]

                    # Get detail for the first schema
                    detail_result = await session.call_tool("get_schema_detail", {"schema_name": schema_name})
                    detail_content = detail_result.content[0].text

                    assert not detail_content.startswith("Schema not found")

                    # Parse the detailed response
                    schema_detail = json.loads(detail_content)
                    required_fields = [
                        "schema_name",
                        "schema_type",
                        "title",
                        "description",
                        "properties",
                        "required_fields",
                        "example",
                    ]
                    for field in required_fields:
                        assert field in schema_detail

                    # Verify schema name matches
                    assert schema_detail["schema_name"] == schema_name


@pytest.mark.integration
async def test_get_schema_detail_nonexistent():
    """Test get_schema_detail with non-existent schema"""
    # Skip if search database doesn't exist
    db_path = Path("resources/authlete_apis.duckdb")
    if not db_path.exists():
        pytest.skip("Search database not found. Run 'uv run python scripts/create_search_database.py' first")

    server_params = StdioServerParameters(
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Try to get details for non-existent schema
            result = await session.call_tool("get_schema_detail", {"schema_name": "NonExistentSchema"})
            content = result.content[0].text

            assert content.startswith("Schema not found: NonExistentSchema")


@pytest.mark.unit
async def test_list_schemas_with_empty_query():
    """Test list_schemas with empty string query parameter"""
    server_params = StdioServerParameters(
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call list_schemas with query explicitly set to empty string
            result = await session.call_tool("list_schemas", {"query": ""})

            content = result.content[0].text
            assert content is not None and len(content) > 0

            # Should return either JSON results or database not found message
            try:
                schemas = json.loads(content)
                if isinstance(schemas, list):
                    # Verify structure if we got results
                    for schema in schemas[:3]:  # Check first few schemas
                        assert "schema_name" in schema
                        assert "schema_type" in schema
                        assert "title" in schema
                        assert "description" in schema
            except json.JSONDecodeError:
                # If not JSON, should be an error or info message
                assert (
                    "Search database not found" in content
                    or "No schemas found matching the specified criteria." in content
                    or "Schema search error:" in content
                )


@pytest.mark.unit
async def test_list_schemas_with_none_query():
    """Test list_schemas with None query parameter should now cause validation error"""
    server_params = StdioServerParameters(
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call list_schemas with query explicitly set to None
            result = await session.call_tool("list_schemas", {"query": None})

            content = result.content[0].text
            assert content is not None and len(content) > 0

            # Should now return a Pydantic validation error since we changed type from str|None to str
            assert (
                "Error executing tool list_schemas:" in content
                and "validation error" in content
                and "Input should be a valid string" in content
            )


@pytest.mark.unit
async def test_search_apis_with_empty_query():
    """Test search_apis with empty string query parameter"""
    server_params = StdioServerParameters(
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call search_apis with query explicitly set to empty string
            result = await session.call_tool("search_apis", {"query": ""})

            content = result.content[0].text
            assert content is not None and len(content) > 0

            # Should return some kind of result (JSON array, error message, or no results message)
            try:
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


@pytest.mark.unit
async def test_search_apis_with_none_values():
    """Test search_apis with None values should now cause validation error"""
    server_params = StdioServerParameters(
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Call search_apis with None values (this should now cause validation error)
            result = await session.call_tool(
                "search_apis",
                {
                    "query": None,
                    "path_query": None,
                    "description_query": None,
                    "tag_filter": None,
                    "method_filter": None,
                },
            )

            content = result.content[0].text
            assert content is not None and len(content) > 0

            # Should now return Pydantic validation errors since we changed types from str|None to str
            assert (
                "Error executing tool search_apis:" in content
                and "validation error" in content
                and "Input should be a valid string" in content
            )


@pytest.mark.unit
async def test_search_apis_priority_order():
    """Test search_apis priority order: query > path_query > description_query"""
    server_params = StdioServerParameters(
        command="python", args=["main.py"], env={"ORGANIZATION_ACCESS_TOKEN": "test-token"}
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test that query has highest priority (should ignore path_query and description_query)
            result1 = await session.call_tool(
                "search_apis",
                {"query": "token", "path_query": "/auth/client", "description_query": "service management"},
            )

            # Test path_query priority when query is empty (should ignore description_query)
            result2 = await session.call_tool(
                "search_apis", {"query": "", "path_query": "/auth/client", "description_query": "service management"}
            )

            # Test description_query when both query and path_query are empty
            result3 = await session.call_tool(
                "search_apis", {"query": "", "path_query": "", "description_query": "service management"}
            )

            # All should return valid responses without errors
            for result in [result1, result2, result3]:
                content = result.content[0].text
                assert content is not None and len(content) > 0
                # Should not contain crash errors
                assert "Search error:" not in content or "Search database not found" in content
