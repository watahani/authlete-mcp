"""MCP tools for Authlete API operations."""

# Import specific functions instead of using star imports
from .client_tools import (
    create_client,
    delete_client,
    get_client,
    list_clients,
    rotate_client_secret,
    update_client,
    update_client_lock,
    update_client_secret,
)
from .service_tools import (
    create_service,
    create_service_detailed,
    delete_service,
    get_service,
    get_service_schema_example,
    list_services,
    update_service,
)

__all__ = [
    # Service tools
    "create_service",
    "create_service_detailed",
    "get_service_schema_example",
    "get_service",
    "list_services",
    "update_service",
    "delete_service",
    # Client tools
    "create_client",
    "get_client",
    "list_clients",
    "update_client",
    "delete_client",
    "rotate_client_secret",
    "update_client_secret",
    "update_client_lock",
]
