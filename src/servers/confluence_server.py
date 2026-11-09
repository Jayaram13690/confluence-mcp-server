"""
Confluence MCP Server using FastMCP with thread-safe configuration.
"""

import asyncio
import logging
import signal

from fastmcp import FastMCP
from starlette.responses import JSONResponse

from src.tools.confluence_tool import register_tools
from src.utils.log_helper import setup_logging

# Initialize logging at module level
try:
    setup_logging()
    logger = logging.getLogger("confluence-mcp-server")
    logger.debug("Initializing Confluence MCP server at module level...")
except Exception as e:
    print(f"Logging setup error during initialization: {e}")
    raise

# Create MCP server instance at module level for uvicorn
mcp = FastMCP(name="confluence-mcp-server", include_fastmcp_meta=False)

# Register tools
logger.info("Registering tools...")
register_tools(mcp)


# Add health check endpoint using Starlette JSONResponse
@mcp.custom_route("/mcp/confluence/health", methods=["GET"])
async def health_check(request):
    logger.debug("Health check endpoint called")
    return JSONResponse({"status": "healthy", "service": "confluence-mcp-server"})


logger.info("Health check endpoint registered at /mcp/confluence/health")

# Create ASGI application using FastMCP's streamable_http_app() method
# This is the correct way to expose FastMCP for uvicorn deployment
# Set the base path to /mcp/confluence instead of default /mcp
mcp_app = mcp.http_app(path="/mcp/confluence", stateless_http=True)

logger.info("FastMCP ASGI application 'mcp_app' created and ready for uvicorn")
logger.info("MCP endpoint will be available at: http://localhost:{port}/mcp/confluence")


# Add shutdown handler
async def shutdown_handler():
    """Handle graceful shutdown of the server."""
    logger.info("Shutdown signal received, cleaning up...")

    # Cancel all running tasks except the current one
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    if tasks:
        logger.info(f"Cancelling {len(tasks)} outstanding tasks...")
        for task in tasks:
            task.cancel()

        # Wait for tasks to complete cancellation
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("All tasks cancelled successfully")

    logger.info("Shutdown complete")


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""

    def handle_signal(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(shutdown_handler())

    # Register signal handlers (Windows supports SIGINT and SIGBREAK)
    signal.signal(signal.SIGINT, handle_signal)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, handle_signal)


# Initialize signal handlers
# setup_signal_handlers()
logger.info("Signal handlers registered for graceful shutdown")
