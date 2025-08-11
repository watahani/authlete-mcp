"""Tests for JWKS generation functionality."""

import json

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.unit
async def test_jwks_generation_tool_exists():
    """Test that generate_jwks tool is available."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            tool_names = [tool.name for tool in tools.tools]
            assert "generate_jwks" in tool_names

            # Check tool schema
            jwks_tool = next(tool for tool in tools.tools if tool.name == "generate_jwks")
            assert jwks_tool.description
            assert "JSON Web Key Set" in jwks_tool.description
            assert "mkjwk.org" in jwks_tool.description


@pytest.mark.integration
async def test_generate_jwks_default_rsa():
    """Test RSA key generation with default parameters."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Call generate_jwks tool with default parameters
            result = await session.call_tool("generate_jwks", {})
            assert result.content

            response_text = result.content[0].text
            data = json.loads(response_text)

            # Verify structure
            assert "jwk" in data
            assert "jwks" in data
            assert "pub" in data
            assert data["jwk"]["kty"] == "RSA"

            # Verify RSA key components exist
            jwk = data["jwk"]
            assert "n" in jwk  # RSA modulus
            assert "e" in jwk  # RSA exponent


@pytest.mark.integration
async def test_generate_jwks_ec_with_curve():
    """Test EC key generation with curve parameter."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Call generate_jwks tool with EC parameters
            result = await session.call_tool(
                "generate_jwks", {"kty": "ec", "crv": "P-256", "use": "sig", "alg": "ES256"}
            )
            assert result.content

            response_text = result.content[0].text
            data = json.loads(response_text)

            assert data["jwk"]["kty"] == "EC"
            assert data["jwk"]["crv"] == "P-256"
            assert data["jwk"]["use"] == "sig"
            assert data["jwk"]["alg"] == "ES256"

            # Verify EC key components exist
            jwk = data["jwk"]
            assert "x" in jwk  # EC x coordinate
            assert "y" in jwk  # EC y coordinate


@pytest.mark.unit
async def test_generate_jwks_ec_missing_curve():
    """Test EC key generation fails without curve parameter."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Call generate_jwks tool with EC but no curve
            result = await session.call_tool("generate_jwks", {"kty": "ec", "use": "sig"})
            assert result.content

            response_text = result.content[0].text
            assert "Error: curve (crv) parameter is required" in response_text


@pytest.mark.integration
async def test_generate_jwks_with_x509():
    """Test key generation with X.509 certificate."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Call generate_jwks tool with X.509
            result = await session.call_tool("generate_jwks", {"kty": "rsa", "x509": True, "size": 2048, "use": "sig"})
            assert result.content

            response_text = result.content[0].text
            data = json.loads(response_text)

            assert "cert" in data
            assert "x509pub" in data
            assert "x509priv" in data

            # Verify X.509 certificate format
            assert data["cert"].startswith("-----BEGIN CERTIFICATE-----")
            assert data["x509pub"].startswith("-----BEGIN PUBLIC KEY-----")
            assert data["x509priv"].startswith("-----BEGIN PRIVATE KEY-----")


@pytest.mark.integration
async def test_generate_jwks_okp_with_curve():
    """Test OKP key generation with Ed25519 curve."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Call generate_jwks tool with OKP parameters
            result = await session.call_tool(
                "generate_jwks", {"kty": "okp", "crv": "Ed25519", "use": "sig", "alg": "EdDSA"}
            )
            assert result.content

            response_text = result.content[0].text
            data = json.loads(response_text)

            assert data["jwk"]["kty"] == "OKP"
            assert data["jwk"]["crv"] == "Ed25519"
            assert data["jwk"]["use"] == "sig"
            assert data["jwk"]["alg"] == "EdDSA"

            # Verify OKP key components exist
            jwk = data["jwk"]
            assert "x" in jwk  # OKP x coordinate


@pytest.mark.integration
async def test_generate_jwks_oct_with_size():
    """Test oct (symmetric) key generation with custom size."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Call generate_jwks tool with oct parameters
            result = await session.call_tool("generate_jwks", {"kty": "oct", "size": 256, "use": "sig", "alg": "HS256"})
            assert result.content

            response_text = result.content[0].text
            data = json.loads(response_text)

            assert data["jwk"]["kty"] == "oct"
            assert data["jwk"]["use"] == "sig"
            assert data["jwk"]["alg"] == "HS256"

            # Verify oct key components exist
            jwk = data["jwk"]
            assert "k" in jwk  # Symmetric key value


@pytest.mark.integration
async def test_generate_jwks_with_kid_generation():
    """Test key generation with automatic key ID generation."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Call generate_jwks tool with date generation
            result = await session.call_tool("generate_jwks", {"kty": "rsa", "gen": "date"})
            assert result.content

            response_text = result.content[0].text
            data = json.loads(response_text)

            assert "kid" in data["jwk"]

            # The key ID should be generated automatically
            kid = data["jwk"]["kid"]
            assert kid is not None
            assert len(kid) > 0


@pytest.mark.integration
async def test_generate_jwks_real_api():
    """Integration test with actual mkjwk.org API."""
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "coverage", "run", "--parallel-mode", "main.py"],
        env={"ORGANIZATION_ACCESS_TOKEN": "test-token"},
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # Call generate_jwks tool with real API
            result = await session.call_tool(
                "generate_jwks", {"kty": "rsa", "size": 2048, "use": "sig", "alg": "RS256"}
            )
            assert result.content

            response_text = result.content[0].text
            data = json.loads(response_text)

            # Verify structure
            assert "jwk" in data
            assert "jwks" in data
            assert "pub" in data

            # Verify RSA key components
            jwk = data["jwk"]
            assert jwk["kty"] == "RSA"
            assert jwk["use"] == "sig"
            assert jwk["alg"] == "RS256"
            assert "n" in jwk  # RSA modulus
            assert "e" in jwk  # RSA exponent
            assert "d" in jwk  # Private exponent (private key)

            # Verify JWKS structure
            jwks = data["jwks"]
            assert "keys" in jwks
            assert len(jwks["keys"]) == 1
            assert jwks["keys"][0]["kty"] == "RSA"

            # Verify public key doesn't have private components
            pub = data["pub"]
            assert pub["kty"] == "RSA"
            assert "n" in pub
            assert "e" in pub
            assert "d" not in pub  # Should not have private exponent
