"""Error envelopes: map typed exceptions to {error_code, error_message, error_details}."""
from typing import Any

from src.exceptions.confluence_exception import (
    AttachmentError,
    ConfluenceError,
    CreatePageError,
    NotFoundError,
    ValidationError,
)

# Ordered most-specific first; the first isinstance match wins.
READ_ERRORS: list[tuple[type[ConfluenceError], str]] = [
    (NotFoundError, "PAGE_NOT_FOUND"),
    (ValidationError, "VALIDATION_ERROR"),
    (ConfluenceError, "CONFLUENCE_ERROR"),
]

CREATE_ERRORS: list[tuple[type[ConfluenceError], str]] = [
    (ValidationError, "VALIDATION_ERROR"),
    (CreatePageError, "CREATE_PAGE_ERROR"),
    (AttachmentError, "ATTACHMENT_ERROR"),
    (ConfluenceError, "CONFLUENCE_ERROR"),
]


def error_envelope(
    exc: ConfluenceError,
    mapping: list[tuple[type[ConfluenceError], str]],
    details: dict[str, Any],
) -> dict[str, Any]:
    """Build the error result for exc using the first matching code in mapping."""
    code = next(c for t, c in mapping if isinstance(exc, t))
    return {"error_code": code, "error_message": str(exc), "error_details": details}
