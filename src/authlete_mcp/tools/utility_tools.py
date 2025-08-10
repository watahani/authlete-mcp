"""Utility tools for Authlete MCP Server."""

import json

import httpx
from mcp.server.fastmcp import Context


async def generate_jwks(
    kty: str = "rsa",
    size: int = 2048,
    use: str | None = None,
    alg: str | None = None,
    kid: str | None = None,
    gen: str = "specified",
    crv: str | None = None,
    x509: bool = False,
    ctx: Context = None,
) -> str:
    """Generate JSON Web Key Set (JWKS) using mkjwk.org API.

    This tool generates cryptographic keys in JWK/JWKS format for use in OAuth 2.0/OpenID Connect implementations.

    Args:
        kty: Key type - "rsa", "ec", "oct", or "okp" (default: "rsa")
        size: Key size in bits for RSA/oct keys (default: 2048, minimum 512, step 8)
        use: Key use - "sig" (signature) or "enc" (encryption), affects available algorithms
        alg: Algorithm for the key (e.g., "RS256", "ES256", "HS256", "EdDSA")
             - RSA sig: RS256,RS384,RS512,PS256,PS384,PS512
             - RSA enc: RSA1_5,RSA-OAEP,RSA-OAEP-256
             - EC sig: ES256,ES384,ES512,ES256K
             - EC enc: ECDH-ES,ECDH-ES+A128KW,ECDH-ES+A192KW,ECDH-ES+A256KW
             - oct sig: HS256,HS384,HS512
             - oct enc: A128KW,A192KW,A256KW,A128GCMKW,A192GCMKW,A256GCMKW,dir
             - okp sig: EdDSA
             - okp enc: ECDH-ES,ECDH-ES+A128KW,ECDH-ES+A192KW,ECDH-ES+A256KW
        kid: Key ID (optional) - identifier for the key
        gen: Key ID generation method - "specified" (use kid param), "sha256", "sha1", "date", "timestamp" (default: "specified")
        crv: Curve for EC/OKP keys - EC: "P-256","P-384","P-521","secp256k1", OKP: "Ed25519","Ed448","X25519","X448"
        x509: Generate X.509 certificate wrapper for RSA/EC keys (default: False)

    Returns:
        JSON string containing generated keys with jwk, jwks, and pub (public key) fields
    """
    try:
        # Build the request URL
        url = f"https://mkjwk.org/jwk/{kty}"
        params = {}

        # Add parameters if provided
        if alg:
            params["alg"] = alg
        if use:
            params["use"] = use
        if kid and gen == "specified":
            params["kid"] = kid
        if gen != "specified":
            params["gen"] = gen

        # Key type specific parameters
        if kty in ["rsa", "ec"]:
            params["x509"] = str(x509).lower()

        if kty in ["rsa", "oct"]:
            params["size"] = str(size)

        if kty in ["ec", "okp"]:
            if not crv:
                return "Error: curve (crv) parameter is required for EC and OKP key types"
            params["crv"] = crv

        # Make the request
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

            # Return the JSON response
            result = response.json()
            return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} - {e.response.text}"
    except httpx.RequestError as e:
        return f"Error: Request failed - {str(e)}"
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON response - {str(e)}"
    except Exception as e:
        return f"Error generating JWKS: {str(e)}"
