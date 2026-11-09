"""confluence-health tool."""
from datetime import UTC, datetime
from typing import Any

from fastmcp import Context, FastMCP

from src.exceptions.confluence_exception import ConfluenceError
from src.tools import shared


def _register_health_check(mcp: FastMCP) -> None:
    """Register the health check tool."""
    @mcp.tool(
        name="confluence-health",
        description="Health check for Confluence MCP service with structured response format.",
        tags={"confluence", "read"}
    )
    async def health_check(ctx: Context) -> dict[str, Any]:
        try:
            client = await shared.confluence_client.get_confluence()
            spaces = client.get_all_spaces(start=0, limit=1)

            return {
                "status": "healthy",
                "service": "confluence-mcp",
                "confluence_url": client.url if hasattr(client, 'url') else "unknown",
                "spaces_accessible": len(spaces.get("results", [])) > 0,
                "timestamp": datetime.now(UTC).isoformat().replace('+00:00', 'Z')
            }

        except ConfluenceError as e:
            return {
                "error_code": "HEALTH_CHECK_ERROR",
                "error_message": f"Health check failed: {e!s}",
                "error_details": {"service": "confluence-mcp"}
            }
        except Exception as e:
            return {
                "error_code": "UNKNOWN_ERROR",
                "error_message": f"Health check failed: {e!s}",
                "error_details": {"service": "confluence-mcp", "error_type": type(e).__name__}
            }
