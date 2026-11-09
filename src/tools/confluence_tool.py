"""
Confluence tool registry. Exposes register_tools(mcp), which registers MCP tools.

Each tool lives in its own module (read_tools, write_tools, health_tool).
"""
import logging

from fastmcp import FastMCP

from src.config import config
from src.tools.health_tool import _register_health_check
from src.tools.models import CreatePageData, MCPResponse, PageData
from src.tools.read_tools import (
    _register_read_page_by_id,
    _register_read_page_by_title,
    _register_read_page_by_url,
)
from src.tools.write_tools import _register_create_page

logger = logging.getLogger(__name__)

__all__ = ["CreatePageData", "MCPResponse", "PageData", "register_tools"]


def register_tools(mcp: FastMCP) -> None:
    """Register Confluence tools based on configuration."""
    enabled_tools = getattr(config, 'ENABLED_CONFLUENCE_TOOLS', [
        "confluence-readPageById",
        "confluence-readPageByTitle",
        "confluence-readPageByUrl",
        "confluence-searchPages",
        "confluence-createPage",
        "confluence-uploadAttachment"
    ])

    # Define all available tools
    available_tools = {
        "confluence-readPageById": _register_read_page_by_id,
        "confluence-readPageByTitle": _register_read_page_by_title,
        "confluence-readPageByUrl": _register_read_page_by_url,
        "confluence-createPage": _register_create_page,
        "confluence-health": _register_health_check
    }

    # If no tools are specifically enabled, register all available tools
    if not enabled_tools:
        enabled_tools = list(available_tools.keys())
        logger.info("No specific tools configured, registering all available Confluence tools")

    logger.info(f"Registering Confluence tools: {enabled_tools}")

    registered_count = 0
    for tool_name in enabled_tools:
        if tool_name in available_tools:
            available_tools[tool_name](mcp)
            logger.debug(f"Registered tool: {tool_name}")
            registered_count += 1
        else:
            logger.warning(f"Unknown tool requested: {tool_name}. Available tools: {list(available_tools.keys())}")

    logger.info(f"Successfully registered {registered_count} Confluence tools")
