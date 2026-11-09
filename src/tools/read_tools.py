"""confluence-readPageById / ByTitle / ByUrl tools."""
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from pydantic import Field

from src.exceptions.confluence_exception import ConfluenceError
from src.tools import shared
from src.tools.context import _resolve_context_params
from src.tools.errors import READ_ERRORS, error_envelope


def _register_read_page_by_id(mcp: FastMCP) -> None:
    """Register the read page by ID tool."""
    @mcp.tool(
        name="confluence-readPageById",
        description="Read Confluence page content by ID with structured response format.",
        tags={"confluence", "read"}
    )
    async def read_page_content_by_id(
        ctx: Context,
        space_key: Annotated[str, Field(description="Confluence space key")],
        page_id: Annotated[str, Field(description="Confluence page ID")],
    ) -> dict[str, Any]:
        try:
            page_data = await shared.confluence_client.get_page_content_by_id(space_key, page_id)

            return {
                "id": page_data["id"],
                "title": page_data["title"],
                "attachments": page_data.get("attachments", page_data.get("attachment_data", [])),
                "body": page_data["body"],
                "url": page_data.get("url")
            }

        except ConfluenceError as e:
            return error_envelope(e, READ_ERRORS, {"page_id": page_id, "space_key": space_key})


def _register_read_page_by_title(mcp: FastMCP) -> None:
    """Register the read page by title tool."""
    @mcp.tool(
        name="confluence-readPageByTitle",
        description="Read Confluence page content by title within a space with structured response format.",
        tags={"confluence", "read"}
    )
    async def read_page_content_by_title(
        ctx: Context,
        space_key: Annotated[str, Field(description="Confluence space key")],
        page_title: Annotated[str, Field(description="Confluence page title")],
    ) -> dict[str, Any]:
        try:
            space_key, page_title = _resolve_context_params(ctx, space_key, page_title)

            page_data = await shared.confluence_client.get_page_content_by_title(space_key, page_title)

            return {
                "id": page_data["id"],
                "title": page_data["title"],
                "attachments": page_data.get("attachments", []),
                "body": page_data["body"],
                "url": page_data.get("url")
            }

        except ConfluenceError as e:
            return error_envelope(e, READ_ERRORS, {"page_title": page_title, "space_key": space_key})


def _register_read_page_by_url(mcp: FastMCP) -> None:
    """Register the read page by URL tool."""
    @mcp.tool(
        name="confluence-readPageByUrl",
        description="Read Confluence page content from a page URL with structured response format. Supports various Confluence URL formats.",
        tags={"confluence", "read"}
    )
    async def read_page_content_by_url(
        ctx: Context,
        page_url: Annotated[str, Field(description="Full Confluence page URL (e.g., https://your-domain.atlassian.net/wiki/spaces/SPACE/pages/123456/Page+Title)")],
    ) -> dict[str, Any]:
        try:
            page_data = await shared.confluence_client.get_page_content_by_url(page_url)

            return {
                "id": page_data["id"],
                "title": page_data["title"],
                "attachments": page_data.get("attachments", []),
                "body": page_data["body"],
                "url": page_data.get("url"),
                "space_key": page_data.get("space_key")
            }

        except ConfluenceError as e:
            return error_envelope(e, READ_ERRORS, {"page_url": page_url})
