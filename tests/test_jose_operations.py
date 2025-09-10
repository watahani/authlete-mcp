"""Test JOSE operations for Authlete MCP Server."""

import json
import os

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.integration
async def test_generate_jose_success():
    """Test successfully generating JOSE with mkjose.org API."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    # Valid JWT payload
    payload = json.dumps({"sub": "test_subject", "iss": "test_issuer", "exp": 1841536000, "iat": 1737936000})

    # Valid JWK for ES256
    jwk = json.dumps(
        {
            "kty": "EC",
            "d": "F4YYW_Z3GPwMUvcjLQeuU2bc8kbATJnbZbR_ubFs_8I",
            "use": "sig",
            "crv": "P-256",
            "kid": "test-key-id",
            "x": "uKRLFdBK7LCaUYnLhKYyF53vtmHBSQlKOUETjnZsKNQ",
            "y": "8X-mjomuPghfqMNY0wKKzMuEqQFKeGsj_aevIBjT4Pk",
            "alg": "ES256",
        }
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("generate_jose", {"payload": payload, "algorithm": "ES256", "jwk": jwk})

            assert result.content
            response_text = result.content[0].text

            # Should return a JWT token
            response_json = json.loads(response_text)
            assert "jwt" in response_json
            jwt_token = response_json["jwt"]
            assert isinstance(jwt_token, str)
            assert len(jwt_token.split(".")) == 3  # JWT should have 3 parts separated by dots


@pytest.mark.integration
async def test_generate_jose_without_jwk():
    """Test generating JOSE without JWK (should work for algorithms that don't need JWK)."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    payload = json.dumps({"sub": "test_subject", "exp": 1841536000, "iat": 1737936000})

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("generate_jose", {"payload": payload, "algorithm": "ES256"})

            assert result.content
            response_text = result.content[0].text

            # Should return a result (might be an error about missing JWK, but not about token)
            assert "ORGANIZATION_ACCESS_TOKEN" not in response_text


@pytest.mark.unit
async def test_generate_jose_invalid_payload_json():
    """Test generating JOSE with invalid payload JSON."""
    server_params = StdioServerParameters(
        command="uv", args=["run", "coverage", "run", "--parallel-mode", "main.py"], env={}
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("generate_jose", {"payload": "invalid json", "algorithm": "ES256"})

            assert result.content
            response_text = result.content[0].text
            assert "Error parsing payload JSON" in response_text


@pytest.mark.unit
async def test_generate_jose_invalid_jwk_json():
    """Test generating JOSE with invalid JWK JSON."""
    server_params = StdioServerParameters(
        command="uv", args=["run", "coverage", "run", "--parallel-mode", "main.py"], env={}
    )

    payload = json.dumps({"sub": "test_subject", "exp": 1841536000})

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool(
                "generate_jose", {"payload": payload, "algorithm": "ES256", "jwk": "invalid jwk json"}
            )

            assert result.content
            response_text = result.content[0].text
            assert "Error parsing JWK JSON" in response_text


@pytest.mark.integration
async def test_verify_jose():
    """Test verifying JOSE without service_api_key."""
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    if not token or token == "dummy_token_for_ci":
        pytest.skip("ORGANIZATION_ACCESS_TOKEN not set - skipping integration test")

    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": token, "ORGANIZATION_ID": os.getenv("ORGANIZATION_ID", "")},
    )

    # Sample JWT token for testing
    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("verify_jose", {"jose_token": test_token})

            assert result.content
            response_text = result.content[0].text
            assert "service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_verify_jose_without_token():
    """Test verifying JOSE without valid token."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={},  # No token
    )

    test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("verify_jose", {"service_api_key": "", "jose_token": test_token})

            assert result.content
            response_text = result.content[0].text
            assert "Error: service_api_key parameter is required" in response_text


@pytest.mark.unit
async def test_verify_jose_missing_token():
    """Test verifying JOSE without jose_token parameter."""
    server_params = StdioServerParameters(
        command="uv", args=["run", "coverage", "run", "--parallel-mode", "main.py"], env={}
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("verify_jose", {"service_api_key": "test_service_key"})

            assert result.content
            response_text = result.content[0].text
            assert "jose_token parameter is required" in response_text
