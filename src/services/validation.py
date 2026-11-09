"""Input validation and URL parsing helpers for Confluence identifiers."""
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ValidationMixin:
    """Static validators exposed on ConfluenceClient."""

    @staticmethod
    def validate_page_id(page_id: str) -> bool:
        if not page_id or not isinstance(page_id, str):
            return False
        return page_id.strip().isdigit()

    @staticmethod
    def validate_page_title(page_title: str) -> bool:
        if not page_title or not isinstance(page_title, str):
            return False
        return bool(re.match(r'^[a-zA-Z0-9\s\-_]+$', page_title))

    @staticmethod
    def validate_space_key(space_key: str) -> bool:
        if not space_key or not isinstance(space_key, str):
            return False
        space_key = space_key.strip()
        if not space_key:
            return False
        return bool(re.match(r'^[a-zA-Z0-9\s\-_]+$', space_key))

    @staticmethod
    def validate_url(url: str) -> bool:
        if not url or not isinstance(url, str):
            return False
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def extract_page_id_from_url(page_url: str) -> tuple[str | None, str | None]:
        """
        Extract page ID and space key from a Confluence page URL.
        Supports formats:
        - /wiki/spaces/{space}/pages/{pageId}/{title}
        - /pages/viewpage.action?pageId={pageId}
        - /display/{space}/{title}

        Returns: (page_id, space_key) tuple, or (None, None) if extraction fails
        """
        if not page_url or not isinstance(page_url, str):
            return None, None

        try:
            # Pattern 1: Modern URL format /wiki/spaces/{space}/pages/{pageId}/{title}
            match = re.search(r'/spaces/([^/]+)/pages/(\d+)', page_url)
            if match:
                return match.group(2), match.group(1)

            # Pattern 2: Classic URL format /pages/viewpage.action?pageId={pageId}
            match = re.search(r'[?&]pageId=(\d+)', page_url)
            if match:
                space_match = re.search(r'[?&]spaceKey=([^&]+)', page_url)
                return match.group(1), (space_match.group(1) if space_match else None)

            # Pattern 3: Display URL format /display/{space}/{title}
            # Needs a lookup by title, so there is no page_id here.
            match = re.search(r'/display/([^/]+)/([^/?]+)', page_url)
            if match:
                return None, match.group(1)

            return None, None

        except Exception as e:
            logger.error(f"Error extracting page ID from URL: {e}")
            return None, None
