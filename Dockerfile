# Build stage with Python slim (same Debian version as Distroless)
FROM python:3.11-slim-bookworm AS builder

# Set working directory
WORKDIR /build

# Install uv for faster dependency management
RUN pip install uv

# Copy dependency files and README for hatchling
COPY pyproject.toml uv.lock README.md ./

# Install dependencies
RUN uv sync --no-dev --frozen

# Production stage with Distroless (Debian 12 = bookworm)
FROM gcr.io/distroless/python3-debian12:latest AS production

# Set working directory
WORKDIR /app

# Copy only the site-packages from virtual environment (avoid symlink issues)
COPY --from=builder /build/.venv/lib/python3.11/site-packages /app/site-packages

# Copy the application source code
COPY src/ ./src/
COPY main.py ./

# Only copy the necessary DuckDB file from resources
COPY resources/authlete_apis.duckdb ./resources/

# Set environment variables to use copied packages
ENV PYTHONPATH=/app:/app/site-packages
ENV PYTHONUNBUFFERED=1

# Expose port for health checks (optional)
EXPOSE 8000

# Run the MCP server using Distroless Python directly
CMD ["/usr/bin/python3.11", "main.py"]