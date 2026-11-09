"""Custom exception types for the Confluence MCP application."""

class ConfluenceError(Exception):
    """Base exception for Confluence-related errors."""


class ConfigurationError(ConfluenceError):
    """Raised when application configuration is missing or invalid."""


class AuthenticationError(ConfluenceError):
    """Raised when no valid authentication method is configured."""


class ConnectionError(ConfluenceError):
    """Raised when unable to connect or perform a connectivity check."""


class ValidationError(ConfluenceError):
    """Raised when input validation fails."""


class NotFoundError(ConfluenceError):
    """Raised when a requested resource cannot be found."""


class ContentError(ConfluenceError):
    """Raised when content processing fails."""


class CreatePageError(ConfluenceError):
    """Raised when a page cannot be created."""


class AttachmentError(ConfluenceError):
    """Raised when attaching a file to a page fails."""


class HealthCheckError(ConfluenceError):
    """Raised when the health check fails."""
