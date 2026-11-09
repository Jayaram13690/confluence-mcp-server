"""
ConfluenceClient: core logic for interacting with Atlassian Confluence.

Composed from focused mixins; each lives in its own module:
validation, connection, content, attachments, page_read, page_write.
"""
from src.services.attachments import AttachmentMixin
from src.services.connection import ConnectionMixin
from src.services.content import ContentMixin
from src.services.page_read import PageReadMixin
from src.services.page_write import PageWriteMixin
from src.services.validation import ValidationMixin


class ConfluenceClient(
    ValidationMixin,
    ConnectionMixin,
    ContentMixin,
    AttachmentMixin,
    PageReadMixin,
    PageWriteMixin,
):
    def __init__(self) -> None:
        self._confluence = None
