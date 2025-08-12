"""Logging configuration for Authlete MCP server.

This module provides structured logging with PII masking capabilities.
"""

import json
import logging
import os
import re
from typing import Any

# Logging configuration - using standard Python logging levels


class PIIMaskingFormatter(logging.Formatter):
    """Custom formatter that masks PII information in log messages."""

    # Sensitive fields that should be masked based on Authlete requirements
    SENSITIVE_FIELDS = [
        # OAuth/OIDC related
        "client_secret",
        "access_token",
        "refresh_token",
        "authorization_code",
        "id_token",
        "code",
        # Device flow
        "user_code",
        "client_notification_token",
        # Authlete Credentials
        "service_api_key",
        "service_api_secret",
        "service_owner_api_key",
        "service_owner_api_secret",
        "sns_credentials",
        "developer_sns_credentials",
        "ticket",
        "subject",
        # Authentication & Authorization
        "password",
        "token",
        "authorization",
        "client_certificate",
        "client_certificate_path",
        # JWT/Crypto/Certificate related
        "jwks",
        "federation_jwks",
        "client_secret_expires_at",
        "trusted_root_certificates",
        "encryption_key_id",
        "signature_key_id",
        "access_token_signature_key_id",
        "refresh_token_signature_key_id",
        "id_token_signature_key_id",
        # Additional patterns for environment variables and headers
        "ORGANIZATION_ACCESS_TOKEN",
        "bearer",
    ]

    REDACTION_MARK = "***** REDACTED *****"

    @classmethod
    def _build_patterns(cls):
        """Build regex patterns for sensitive field masking."""
        patterns = []

        for field in cls.SENSITIVE_FIELDS:
            # JSON format: "field": "value" or "field":"value"
            patterns.append(re.compile(rf'("{re.escape(field)}"\s*:\s*)"([^"]*)"', re.IGNORECASE))

            # URL-encoded format: field=value (stop at & or whitespace)
            patterns.append(re.compile(rf"\b{re.escape(field)}=([^&\s]+)", re.IGNORECASE))

            # Environment variable format: FIELD=value or FIELD: value
            patterns.append(re.compile(rf"\b{re.escape(field)}\s*[:=]\s*([^\s,}}\]]+)", re.IGNORECASE))

        # Additional patterns for common formats
        # Bearer token format: Bearer <token>
        patterns.append(re.compile(r"Bearer\s+([A-Za-z0-9+/=._-]+)", re.IGNORECASE))

        # Authorization header: Authorization: <scheme> <token>
        patterns.append(re.compile(r"Authorization:\s*[A-Za-z]+\s+([A-Za-z0-9+/=._-]+)", re.IGNORECASE))

        # JWK cryptographic values (common JWK fields with long base64 values)
        jwk_fields = ["n", "e", "d", "p", "q", "dp", "dq", "qi", "k", "x", "y"]
        for jwk_field in jwk_fields:
            patterns.append(re.compile(rf'"{re.escape(jwk_field)}"\s*:\s*"([A-Za-z0-9+/=_-]{{20,}})"', re.IGNORECASE))

        return patterns

    @classmethod
    def get_patterns(cls):
        """Get compiled regex patterns, building them lazily."""
        if not hasattr(cls, "_compiled_patterns"):
            cls._compiled_patterns = cls._build_patterns()
        return cls._compiled_patterns

    @classmethod
    def mask_pii(cls, message: str) -> str:
        """Mask PII information in a message string."""
        masked_message = message
        patterns = cls.get_patterns()

        for pattern in patterns:

            def replace_func(match):
                # Handle different pattern types
                if len(match.groups()) == 2:
                    # Pattern with field name and value capture groups (JSON format)
                    return f'{match.group(1)}"{cls.REDACTION_MARK}"'
                elif len(match.groups()) == 1:
                    # Pattern with single capture group (the sensitive value)
                    full_match = match.group(0)
                    sensitive_value = match.group(1)
                    return full_match.replace(sensitive_value, cls.REDACTION_MARK)
                else:
                    # Fallback - replace entire match
                    return cls.REDACTION_MARK

            masked_message = pattern.sub(replace_func, masked_message)

        return masked_message

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with PII masking."""
        # Apply PII masking to the message
        if hasattr(record, "msg") and record.msg:
            record.msg = self.__class__.mask_pii(str(record.msg))

        # Format the record using parent formatter
        formatted = super().format(record)

        # Apply PII masking to the final formatted message as well
        return self.__class__.mask_pii(formatted)


# No custom log levels - using standard Python logging levels only


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with PII masking configured."""
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        # Get log level from environment variable, default to INFO
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()

        # Map string levels to logging constants
        level_mapping = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        log_level = level_mapping.get(log_level_str, logging.INFO)

        # Create console handler
        handler = logging.StreamHandler()
        handler.setLevel(log_level)

        # Create formatter with PII masking
        formatter = PIIMaskingFormatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

        # Configure logger
        logger.addHandler(handler)
        logger.setLevel(log_level)
        logger.propagate = False

    return logger


def log_request_response(
    logger: logging.Logger,
    method: str,
    url: str,
    request_data: dict[str, Any] | None = None,
    response_data: dict[str, Any] | None = None,
    status_code: int | None = None,
    error: Exception | None = None,
) -> None:
    """Log HTTP request and response details at appropriate levels."""

    # Log request at DEBUG level
    if request_data:
        logger.debug(f"HTTP {method} {url} - Request: {json.dumps(request_data, indent=2)}")
    else:
        logger.debug(f"HTTP {method} {url}")

    # Log response based on result
    if error:
        logger.error(f"HTTP {method} {url} - Error: {type(error).__name__}: {str(error)}")
        if hasattr(error, "response") and hasattr(error.response, "status_code"):
            logger.debug(f"HTTP {method} {url} - Response status: {error.response.status_code}")
            if hasattr(error.response, "text"):
                logger.debug(f"HTTP {method} {url} - Response text: {error.response.text}")
    elif response_data:
        if status_code:
            logger.debug(f"HTTP {method} {url} - Response ({status_code}): {json.dumps(response_data, indent=2)}")
        else:
            logger.debug(f"HTTP {method} {url} - Response: {json.dumps(response_data, indent=2)}")
    elif status_code:
        logger.debug(f"HTTP {method} {url} - Response status: {status_code}")
