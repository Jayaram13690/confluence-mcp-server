"""Page read operations (by ID, title and URL)."""
import logging
from typing import Any

from src.exceptions.confluence_exception import NotFoundError, ValidationError
from src.services.content import select_body

logger = logging.getLogger(__name__)

_EXPAND = 'body.storage,body.view,body.export_view'


def _page_meta(page: dict) -> dict[str, Any]:
    """Fields common to every page read result."""
    version = page.get('version', {})
    return {
        "created": page.get('created'),
        "modified": version.get('when'),
        "author": version.get('by', {}).get('displayName', 'Unknown'),
    }


class PageReadMixin:
    """Read operations exposed on ConfluenceClient."""

    async def get_page_content_by_id(self, space_key: str, page_id: str) -> dict[str, Any] | None:
        if not self.validate_page_id(page_id):
            raise ValidationError("Invalid page id")
        if not self.validate_space_key(space_key):
            raise ValidationError("Invalid space key")
        client = await self.get_confluence()
        page = client.get_page_by_id(page_id, expand=_EXPAND)
        if not page:
            raise NotFoundError(f"Page id {page_id} not found")

        attachments = self.read_attachments(client, page_id)
        page_content, content_type = select_body(page)

        return {
            "id": page_id,
            "title": page.get('title', 'Unknown Title'),
            "body": self.html_to_plain_text(page_content),
            "body_type": content_type,
            "attachments": attachments,
            "url": f"{client.url}/pages/{page.get('id', page_id)}" if hasattr(client, 'url') else None,
            **_page_meta(page),
        }

    async def get_page_content_by_title(self, space_key: str, page_title: str) -> dict[str, Any] | None:
        if not self.validate_page_title(page_title):
            raise ValidationError("Invalid page title")
        if not self.validate_space_key(space_key):
            raise ValidationError("Invalid space key")
        client = await self.get_confluence()
        page = client.get_page_by_title(space_key, page_title, expand=_EXPAND)
        if not page:
            raise NotFoundError(f"Page title '{page_title}' not found in space {space_key}")

        attachments = self.read_attachments(client, page["id"])
        content, _ = select_body(page)

        return {
            "id": page.get('id'),
            "title": page.get('title', 'Unknown Title'),
            "body": self.html_to_plain_text(content),
            "attachments": attachments,
            "url": f"{client.url}/pages/{page.get('id')}" if hasattr(client, 'url') else None,
            **_page_meta(page),
        }

    async def get_page_content_by_url(self, page_url: str) -> dict[str, Any] | None:
        """
        Get page content from a Confluence page URL.
        Extracts page ID and space key from URL and retrieves content.
        """
        if not page_url or not isinstance(page_url, str):
            raise ValidationError("Invalid page URL")

        if not self.validate_url(page_url):
            raise ValidationError("URL format is invalid")

        page_id, space_key = self.extract_page_id_from_url(page_url)

        if not page_id:
            raise ValidationError(
                "Could not extract page ID from URL. Supported formats: "
                "/spaces/{space}/pages/{pageId}/{title} or "
                "/pages/viewpage.action?pageId={pageId}"
            )

        if not space_key:
            # If space key not in URL, try to get it from the page metadata
            client = await self.get_confluence()
            try:
                page = client.get_page_by_id(page_id, expand='space')
                if page and 'space' in page:
                    space_key = page['space'].get('key', '')
            except Exception as e:
                raise NotFoundError(f"Could not retrieve space key for page {page_id}: {e}")

        return await self.get_page_content_by_id(space_key, page_id)
