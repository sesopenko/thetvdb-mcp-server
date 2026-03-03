FROM python:3.13-slim

# Copy uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Pre-compile bytecode for faster container startup
ENV UV_COMPILE_BYTECODE=1

# Install production dependencies first (separate layer for cache efficiency)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source and install the project
COPY src/ ./src/
RUN uv sync --frozen --no-dev

EXPOSE 8080

CMD ["uv", "run", "transmission-mcp", "--config", "/config/config.toml"]
