# Architecture Documentation

## Project Structure

```
authlete-mcp/
├── src/authlete_mcp/           # Main package
│   ├── __init__.py            # Package initialization
│   ├── server.py              # MCP server setup
│   ├── config.py              # Configuration management
│   ├── api/                   # API client modules
│   │   ├── __init__.py
│   │   └── client.py          # HTTP client for Authlete APIs
│   ├── models/                # Pydantic models
│   │   ├── __init__.py
│   │   ├── service.py         # Service-related models
│   │   └── client.py          # Client-related models
│   └── tools/                 # MCP tool implementations
│       ├── __init__.py
│       ├── service_tools.py   # Service management tools
│       └── client_tools.py    # Client management tools
├── tests/                     # Test suite
│   ├── test_service_*.py      # Service-related tests
│   ├── test_client_*.py       # Client-related tests
│   └── test_*.py              # Other tests
├── examples/                  # Usage examples
│   └── create_service_example.py
├── docs/                      # Documentation
│   ├── API.md                 # API reference
│   └── ARCHITECTURE.md        # This file
├── main.py                    # Entry point
├── pyproject.toml            # Project configuration
└── README.md                 # Project overview
```

## Components

### Server (`src/authlete_mcp/server.py`)
- FastMCP server instance
- Tool registration
- Main entry point for the MCP server

### Configuration (`src/authlete_mcp/config.py`)
- Environment variable management
- Authlete API configuration
- Default values and validation

### API Client (`src/authlete_mcp/api/client.py`)
- HTTP client for Authlete API endpoints
- Standard API and IdP API support
- Error handling and response processing
- Special handling for 204 No Content responses

### Models (`src/authlete_mcp/models/`)
- Pydantic models for request/response validation
- Service configuration models
- Client configuration models
- Type safety and documentation

### Tools (`src/authlete_mcp/tools/`)
- MCP tool implementations
- Service management operations
- Client management operations
- Error handling and validation

## Design Principles

### Modularity
Each component has a single responsibility and clear interfaces.

### Extensibility
New tools and models can be easily added without modifying existing code.

### Type Safety
Pydantic models ensure type safety and runtime validation.

### Error Handling
Consistent error handling across all components with descriptive error messages.

### Testing
Comprehensive test coverage with unit and integration tests.

## Extension Points

### Adding New Tools
1. Create tool functions in appropriate `tools/` module
2. Register tools in `server.py`
3. Add tests in `tests/`
4. Update documentation in `docs/API.md`

### Adding New Models
1. Define Pydantic models in `models/`
2. Export from `models/__init__.py`
3. Use in tool implementations
4. Add validation tests

### Adding New API Endpoints
1. Extend `api/client.py` with new request methods
2. Handle specific response formats
3. Add error handling
4. Create corresponding tools

## Dependencies

### Runtime
- `fastmcp`: MCP server framework
- `httpx`: HTTP client
- `pydantic`: Data validation and settings management

### Development
- `pytest`: Testing framework
- `pytest-asyncio`: Async test support
- `python-dotenv`: Environment variable management
- `ruff`: Code formatting and linting