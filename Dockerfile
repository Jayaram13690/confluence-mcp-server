# Use Python 3.13 slim image for consistency with local development
FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy uv project files
COPY pyproject.toml uv.lock ./

# Install production dependencies
RUN uv sync --no-dev --no-install-project

# Copy the entire src directory
COPY src/ ./src/
COPY main.py ./

# Set environment variables for production
ENV PYTHONPATH=/app
ENV CONFLUENCE_HOST=0.0.0.0
ENV CONFLUENCE_PORT=9001
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 9001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import socket,os; port=int(os.getenv('CONFLUENCE_PORT',9001)); sock=socket.socket(); sock.settimeout(5); sock.connect(('localhost', port)); sock.close()" || exit 1

# Start Confluence MCP server
CMD ["uv", "run", "python", "main.py"]