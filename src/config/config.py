"""
Configuration for Atlassian MCP application.
"""

import os

from dotenv import load_dotenv

from src.config.config_reader import AppConfigReader

# Load environment variables from .env file
load_dotenv()

azure_config = AppConfigReader().load()


def get_config(name: str, default: str | None = None) -> str | None:
    """
    Get configuration from Azure App Configuration first.
    Fall back to environment variables when Azure configuration
    is not available.
    """
    return azure_config.get(name, os.getenv(name, default))


# Server host and port remain environment-based. Host defaults to localhost (SEC-1);
# the container image sets 0.0.0.0.
CONFLUENCE_HOST = os.getenv("CONFLUENCE_HOST", "127.0.0.1")
CONFLUENCE_PORT = int(os.getenv("CONFLUENCE_PORT", "9001"))

# Configuration comes from Azure App Configuration first.
# Falls back to .env for local development.
CONFLUENCE_URL = get_config("CONFLUENCE_URL")
CONFLUENCE_EMAIL = get_config("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = get_config("CONFLUENCE_API_TOKEN")
CONFLUENCE_USERNAME = get_config("CONFLUENCE_USERNAME")

LOG_LEVEL = get_config("LOG_LEVEL", "INFO")