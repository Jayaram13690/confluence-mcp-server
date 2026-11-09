"""Page creation, with an optional attachment."""
import logging
import os
from datetime import UTC, datetime
from typing import Any

from src.config import config
from src.exceptions.confluence_exception import CreatePageError, ValidationError

logger = logging.getLogger(__name__)


class PageWriteMixin:
    """Write operations exposed on ConfluenceClient."""

    async def _attach_on_create(self, page_id: str, file_path: str) -> dict[str, Any]:
        """Attach a file to a freshly created page; always returns a status record."""
        custom_filename = 'file1.pdf'
        try:
            if not os.path.exists(file_path):
                return self._attach_error(file_path, custom_filename, f"File not found: {file_path}")
            if not os.path.isfile(file_path):
                return self._attach_error(file_path, custom_filename, f"Path is not a file: {file_path}")
            filename = custom_filename or os.path.basename(file_path)
            try:
                result = await self.attach_file_to_page(page_id, file_path, filename)
                return {
                    "file_path": file_path,
                    "filename": filename,
                    "status": "success",
                    "attachment_id": result.get("id") if result else None,
                }
            except Exception as attach_error:
                return self._attach_error(file_path, filename, str(attach_error))
        except Exception as e:
            return self._attach_error(file_path, custom_filename or os.path.basename(file_path), str(e))

    @staticmethod
    def _attach_error(file_path: str, filename: str, error: str) -> dict[str, Any]:
        return {"file_path": file_path, "filename": filename, "status": "error", "error": error}

    async def create_page_with_content(self, space_key: str, title: str, body: str, attachment: str | None, representation: str) -> dict[str, Any] | None:
        if not self.validate_space_key(space_key):
            raise ValidationError(f"Invalid space key format: {space_key}")
        if not title or not isinstance(title, str) or not title.strip():
            raise ValidationError("Title is required and must be a non-empty string")
        if not body or not isinstance(body, str):
            raise ValidationError("Body content is required")
        if representation not in ['storage', 'wiki', 'view']:
            raise ValidationError(f"Invalid representation format: {representation}")
        client = await self.get_confluence()
        page = client.create_page(space=space_key, title=title.strip(), body=body, representation=representation)
        if not page or 'id' not in page:
            raise CreatePageError("Failed to create page - no page ID returned")

        attached_files: list[dict[str, Any]] = []
        if attachment and isinstance(attachment, str) and attachment.strip():
            attached_files.append(await self._attach_on_create(page["id"], attachment.strip()))

        return {
            "id": page.get('id'),
            "title": title.strip(),
            "url": f"{config.CONFLUENCE_URL}/pages/{page.get('id')}",
            "space_key": space_key,
            "representation": representation,
            "attached_files": attached_files,
            "created": datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
        }
