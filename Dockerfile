# Build stage with full Python environment
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /build

# Install uv for faster dependency management
RUN pip install uv

# Copy dependency files and README for hatchling
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --no-dev --frozen

# Production stage with Distroless
FROM gcr.io/distroless/python3-debian12:latest AS production

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /build/.venv /app/.venv

# Copy the application source code
COPY src/ ./src/
COPY main.py ./

# Only copy the necessary DuckDB file from resources
COPY resources/authlete_apis.duckdb ./resources/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port for health checks (optional)
EXPOSE 8000

# Run the MCP server using the installed virtual environment
CMD ["/app/.venv/bin/python", "main.py"]