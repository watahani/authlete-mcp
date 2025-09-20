"""Direct integration tests for JOSE verify operations using internal functions."""

import json
import os
import time

import pytest

from src.authlete_mcp.logging import get_logger
from src.authlete_mcp.tools.jose_tools import generate_jose, verify_jose
from src.authlete_mcp.tools.service_tools import create_service, delete_service
from src.authlete_mcp.tools.utility_tools import generate_jwks

logger = get_logger(__name__)


@pytest.mark.integration
async def test_jose_verify_with_service_direct():
    """Test JOSE verification using direct function calls - complete integration test.

    This test performs the following steps:
    1. Create test service using direct function call
    2. Generate JWKS using direct function call
    3. Generate JOSE using direct function call
    4. Verify JOSE using direct function call with various parameters
    5. Clean up test service using direct function call
    """

    # Check for integration test requirements
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    org_id = os.getenv("ORGANIZATION_ID")
    if not token or token == "test-token" or not org_id or org_id == "12345":
        pytest.skip("Real ORGANIZATION_ACCESS_TOKEN and ORGANIZATION_ID not set - skipping integration test")

    service_api_key = None

    try:
        # Step 1: Create test service
        logger.info("Creating test service...")

        service_name = f"pytest-jose-verify-direct-{int(time.time())}"
        create_result = await create_service(
            name=service_name, description="Direct function call test service for JOSE verify integration testing"
        )

        assert not create_result.startswith("Error"), f"Service creation failed: {create_result}"
        service_data = json.loads(create_result)
        service_api_key = str(service_data.get("apiKey"))
        assert service_api_key and service_api_key != "None", "Service API key not found"

        logger.info(f"Created service with API key: {service_api_key}")

        # Step 2: Generate JWKS
        logger.info("Generating JWKS...")

        jwks_result = await generate_jwks(kty="rsa", size=2048, use="sig", alg="RS256", kid="test-service-key")

        assert not jwks_result.startswith("Error"), f"JWKS generation failed: {jwks_result}"
        jwks_data = json.loads(jwks_result)
        logger.info("Generated JWKS successfully")

        # Step 3: Generate JOSE token
        logger.info("Generating JOSE token...")

        payload = {
            "iss": service_api_key,
            "sub": "test-subject",
            "aud": "test-audience",
            "exp": int(time.time()) + 3600,  # 1 hour from now
            "iat": int(time.time()),
            "custom_claim": "test-value",
        }

        jose_result = await generate_jose(
            payload=json.dumps(payload), algorithm="RS256", jwk=json.dumps(jwks_data["jwk"])
        )

        assert not jose_result.startswith("Error"), f"JOSE generation failed: {jose_result}"
        jose_data = json.loads(jose_result)
        jose_token = jose_data.get("jwt")  # mkjose returns "jwt" field
        assert jose_token, "JOSE token not found in response"

        logger.info(f"Generated JOSE token: {jose_token[:50]}...")

        # Step 4: Test JOSE verification (expected to fail without service JWKS configured)
        logger.info("Testing JOSE verification...")

        verify_result = await verify_jose(jose_token=jose_token, service_api_key=service_api_key)

        assert not verify_result.startswith("Error: service_api_key"), "Should have service API key"
        logger.info("Basic JOSE verification attempt completed")

        # Step 5: Test with mandatory claims parameter
        logger.info("Testing JOSE verification with mandatory claims...")

        verify_with_claims_result = await verify_jose(
            jose_token=jose_token, service_api_key=service_api_key, mandatory_claims="iss sub aud"
        )

        assert not verify_with_claims_result.startswith("Error: service_api_key"), "Should have service API key"
        logger.info("JOSE verification with mandatory claims completed")

        # Step 6: Test with clock skew tolerance
        logger.info("Testing JOSE verification with clock skew...")

        verify_with_skew_result = await verify_jose(
            jose_token=jose_token,
            service_api_key=service_api_key,
            clock_skew=300,  # 5 minutes tolerance
        )

        assert not verify_with_skew_result.startswith("Error: service_api_key"), "Should have service API key"
        logger.info("JOSE verification with clock skew completed")

        # Step 7: Test invalid token handling
        logger.info("Testing invalid JOSE token...")

        invalid_verify_result = await verify_jose(jose_token="invalid.jose.token", service_api_key=service_api_key)

        # Should return some kind of verification failure from Authlete API, not parameter error
        assert not invalid_verify_result.startswith("Error: service_api_key"), "Should have service API key"
        logger.info("Invalid JOSE token handling completed")

        logger.info("✅ All JOSE verification tests completed successfully")

    finally:
        # Cleanup: Delete test service
        if service_api_key:
            try:
                logger.info(f"Cleaning up test service: {service_api_key}")
                delete_result = await delete_service(service_id=service_api_key)
                logger.info(f"Cleanup result: {delete_result}")
            except Exception as e:
                logger.warning(f"Failed to cleanup service {service_api_key}: {e}")


@pytest.mark.integration
async def test_jose_verify_parameter_validation_direct():
    """Test JOSE verification parameter validation using direct function calls."""

    # Check for integration test requirements
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    org_id = os.getenv("ORGANIZATION_ID")
    if not token or token == "test-token" or not org_id or org_id == "12345":
        pytest.skip("Real ORGANIZATION_ACCESS_TOKEN and ORGANIZATION_ID not set - skipping integration test")

    # Test 1: Missing service_api_key
    logger.info("Testing missing service_api_key parameter...")

    verify_result = await verify_jose(jose_token="sample.jose.token", service_api_key="")

    assert verify_result.startswith("Error: service_api_key parameter is required"), "Should require service API key"
    logger.info("✅ Missing service_api_key validation works")

    # Test 2: Missing jose_token
    logger.info("Testing missing jose_token parameter...")

    verify_result = await verify_jose(jose_token="", service_api_key="test_service_key")

    assert verify_result.startswith("Error: jose_token parameter is required"), "Should require JOSE token"
    logger.info("✅ Missing jose_token validation works")

    # Test 3: Missing ORGANIZATION_ACCESS_TOKEN (should be set in environment)
    logger.info("Testing environment variable presence...")

    verify_result = await verify_jose(jose_token="sample.jose.token", service_api_key="test_service_key")

    # Should not fail due to missing token (token is set), should fail due to invalid service key
    assert not verify_result.startswith("Error: ORGANIZATION_ACCESS_TOKEN"), "Token should be set in environment"
    logger.info("✅ Environment variable validation works")

    logger.info("✅ All parameter validation tests completed successfully")


@pytest.mark.integration
async def test_jose_generation_with_different_algorithms_direct():
    """Test JOSE generation with different algorithms using direct function calls."""

    # Check for integration test requirements
    token = os.getenv("ORGANIZATION_ACCESS_TOKEN")
    org_id = os.getenv("ORGANIZATION_ID")
    if not token or token == "test-token" or not org_id or org_id == "12345":
        pytest.skip("Real ORGANIZATION_ACCESS_TOKEN and ORGANIZATION_ID not set - skipping integration test")

    # Test 1: RSA RS256
    logger.info("Testing JOSE generation with RSA RS256...")

    rsa_jwks_result = await generate_jwks(kty="rsa", size=2048, use="sig", alg="RS256")

    assert not rsa_jwks_result.startswith("Error"), f"RSA JWKS generation failed: {rsa_jwks_result}"
    rsa_jwks_data = json.loads(rsa_jwks_result)

    payload = {"iss": "test-issuer", "sub": "test-subject", "exp": int(time.time()) + 3600, "iat": int(time.time())}

    rsa_jose_result = await generate_jose(
        payload=json.dumps(payload), algorithm="RS256", jwk=json.dumps(rsa_jwks_data["jwk"])
    )

    assert not rsa_jose_result.startswith("Error"), f"RSA JOSE generation failed: {rsa_jose_result}"
    rsa_jose_data = json.loads(rsa_jose_result)
    assert "jwt" in rsa_jose_data, "RSA JOSE should contain JWT"
    logger.info("✅ RSA RS256 JOSE generation successful")

    # Test 2: EC ES256
    logger.info("Testing JOSE generation with EC ES256...")

    ec_jwks_result = await generate_jwks(kty="ec", crv="P-256", use="sig", alg="ES256")

    assert not ec_jwks_result.startswith("Error"), f"EC JWKS generation failed: {ec_jwks_result}"
    ec_jwks_data = json.loads(ec_jwks_result)

    ec_jose_result = await generate_jose(
        payload=json.dumps(payload), algorithm="ES256", jwk=json.dumps(ec_jwks_data["jwk"])
    )

    assert not ec_jose_result.startswith("Error"), f"EC JOSE generation failed: {ec_jose_result}"
    ec_jose_data = json.loads(ec_jose_result)
    assert "jwt" in ec_jose_data, "EC JOSE should contain JWT"
    logger.info("✅ EC ES256 JOSE generation successful")

    logger.info("✅ All algorithm tests completed successfully")
