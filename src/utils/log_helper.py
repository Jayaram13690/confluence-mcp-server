"""Logging configuration and helper utilities.

This module provides a centralized logging configuration that:
- Uses UTC timestamps with 'Z' suffix
- Respects LOG_LEVEL environment variable (default: INFO)
- Is idempotent (safe to call setup_logging() multiple times)
- Provides consistent formatting across all modules

Usage:
    from src.utils.log_helper import setup_logging
    import logging
    
    # Setup logging (usually done once at application startup)
    setup_logging()
    
    # Get logger for your module
    logger = logging.getLogger(__name__)
    
    # Use the logger
    logger.info("This will be logged with UTC timestamp")
    logger.debug("This will only appear if LOG_LEVEL=DEBUG")

Environment Variables:
    LOG_LEVEL: Controls logging verbosity (DEBUG, INFO, WARNING, ERROR)
               Defaults to INFO if not set
"""

import logging
import os
import time

_DEFAULT_FMT = "%(levelname)s %(asctime)sZ [%(name)s] %(message)s"


class _UTCFormatter(logging.Formatter):
    """Force UTC timestamps with trailing 'Z'."""

    converter = time.gmtime


def setup_logging():
    """Idempotent root logger setup.

    Respects LOG_LEVEL environment variable (default: INFO).

    Returns:
        Configured root logger.
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()

    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_UTCFormatter(_DEFAULT_FMT))
        root.addHandler(handler)

    root.setLevel(level)
    return root
