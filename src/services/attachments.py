"""Attachment listing, reading and uploading."""
import logging
import os
from typing import Any

from src.config import config
from src.exceptions.confluence_exception import AttachmentError, ValidationError

logger = logging.getLogger(__name__)


class AttachmentMixin:
    """Attachment operations exposed on ConfluenceClient."""

    def list_attachments(self, page_id: str) -> list[dict[str, str]]:
        if not self._confluence:
            return []
        try:
            attachments = self._confluence.get_attachments_from_content(page_id, expand="body", start=0, limit=50)
            return [
                {
                    "id": att["id"],
                    "title": att["title"],
                    "downloadLink": config.CONFLUENCE_URL + att["_links"]["download"],
                }
                for att in attachments.get("results", [])
            ]
        except Exception as e:
            logger.error(f"Failed to list attachments for page {page_id}: {e}")
            return []

    def read_attachments(self, client: Any, page_id: str) -> list[dict[str, str]]:
        """Download each attachment of a page and extract its text."""
        attachments: list[dict[str, str]] = []
        try:
            for att in self.list_attachments(page_id):
                try:
                    resp = client.session.get(att["downloadLink"])
                    resp.raise_for_status()
                    content = self.extract_file_content(resp.content, att["title"])
                    attachments.append({
                        "fileName": att["title"],
                        "content": content,
                        "downloadLink": att["downloadLink"],
                        "id": att["id"],
                    })
                except Exception as att_error:
                    attachments.append({
                        "fileName": att.get("title", "unknown"),
                        "content": f"Error processing attachment: {att_error}",
                        "downloadLink": att.get("downloadLink", ""),
                        "id": att.get("id", ""),
                        "error": str(att_error),
                    })
        except Exception:
            pass
        return attachments

    async def attach_file_to_page(self, page_id: str, file_path: str, filename: str | None = None) -> dict[str, Any] | None:
        if not self.validate_page_id(page_id):
            raise ValidationError("Invalid page id")
        if not file_path or not os.path.exists(file_path):
            raise AttachmentError("Attachment file path invalid or missing")
        client = await self.get_confluence()
        if not filename:
            filename = os.path.basename(file_path)
        try:
            return client.attach_file(
                filename=file_path,
                name=filename,
                content_type=None,
                page_id=page_id,
                comment="Attached via MCP API",
            )
        except Exception as e:
            raise AttachmentError(str(e))
