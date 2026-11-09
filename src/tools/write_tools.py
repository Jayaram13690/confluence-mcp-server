"""confluence-createPage tool."""
from typing import Annotated, Any

from fastmcp import Context, FastMCP
from pydantic import Field

from src.exceptions.confluence_exception import AttachmentError, ConfluenceError
from src.tools import shared
from src.tools.errors import CREATE_ERRORS, error_envelope


def _register_create_page(mcp: FastMCP) -> None:
    """Register the create page tool."""
    @mcp.tool(
        name="confluence-createPage",
        description="Create a new Confluence page with optional file attachment and structured response format.",
        tags={"confluence", "write"}
    )
    async def create_page(
        ctx: Context,
        space_key: Annotated[str, Field(description="Confluence space key")],
        title: Annotated[str, Field(description="Title for the new page")],
        body: Annotated[str, Field(description="Page content (HTML, wiki, or view)")],
        attachment: Annotated[str | None, Field(description="Optional file path to attach")]=None,
        representation: Annotated[str, Field(description="Content representation: storage|wiki|view")]="storage",
    ) -> dict[str, Any]:
        try:
            result = await shared.confluence_client.create_page_with_content(
                space_key, title, body, attachment, representation
            )

            return {
                "id": result["id"],
                "title": title,
                "url": result["url"],
                "space_key": space_key,
                "attached_files": result["attached_files"]
            }
        except ConfluenceError as e:
            details = {"space_key": space_key, "title": title}
            if isinstance(e, AttachmentError):
                details["attachment"] = attachment
            return error_envelope(e, CREATE_ERRORS, details)
