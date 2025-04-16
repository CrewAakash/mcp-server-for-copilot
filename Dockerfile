# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy dependency files first to leverage Docker caching
COPY pyproject.toml uv.lock ./

# Install dependencies only (faster builds when code changes)
RUN uv sync --frozen --no-dev

# Copy the MCP server files
COPY src ./src
COPY agent_definition.json ./agent_definition.json

# Expose the port the MCP server runs on
EXPOSE 8000

# Command to run the MCP server
CMD ["uv", "run", "src/main.py"]