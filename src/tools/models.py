"""Structured response models for Confluence tools."""
from typing import Any

from pydantic import BaseModel


class MCPResponse(BaseModel):
    """Industry standard MCP response format."""
    content: list[dict[str, str]]
    data: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    is_error: bool = False
    error: dict[str, Any] | None = None


class PageData(BaseModel):
    """Structured page data model."""
    id: str
    title: str
    body: str
    attachments: list[dict[str, str]]
    space_key: str
    url: str | None = None


class CreatePageData(BaseModel):
    """Structured create page response model."""
    id: str
    title: str
    url: str
    space_key: str
    attached_files: list[dict[str, Any]]
