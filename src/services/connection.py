"""Confluence connection management."""
import logging
import os

from atlassian import Confluence

from src.config import config
from src.exceptions.confluence_exception import (
    AuthenticationError,
    ConfigurationError,
    ConfluenceError,
)
from src.exceptions.confluence_exception import (
    ConnectionError as ConfConnectionError,
)

logger = logging.getLogger(__name__)


class ConnectionMixin:
    """Lazily builds and caches the Confluence client."""

    _confluence: Confluence | None = None

    def _build_client(self) -> Confluence:
        """Pick an auth method from config and construct the client."""
        if config.CONFLUENCE_API_TOKEN and config.CONFLUENCE_EMAIL:
            logger.debug("Using email and API token authentication")
            return Confluence(
                url=config.CONFLUENCE_URL,
                username=config.CONFLUENCE_EMAIL,
                password=config.CONFLUENCE_API_TOKEN,
                cloud=True,
            )
        if config.CONFLUENCE_USERNAME and config.CONFLUENCE_API_TOKEN:
            logger.debug("Using username and API token authentication")
            return Confluence(
                url=config.CONFLUENCE_URL,
                username=config.CONFLUENCE_USERNAME,
                password=config.CONFLUENCE_API_TOKEN,
                cloud=False,
            )
        if getattr(config, 'oauth_consumer_key', None) and getattr(config, 'oauth_private_key_path', None):
            logger.debug("Using OAuth authentication")
            if not os.path.exists(config.oauth_private_key_path):
                logger.error(f"OAuth private key file not found: {config.oauth_private_key_path}")
                raise ConfigurationError(f"OAuth private key file not found: {config.oauth_private_key_path}")
            with open(config.oauth_private_key_path) as key_file:
                private_key = key_file.read()
            return Confluence(
                url=config.CONFLUENCE_URL,
                oauth={
                    'consumer_key': config.oauth_consumer_key,
                    'key_cert': private_key,
                    'access_token': '',
                    'access_token_secret': '',
                },
            )
        logger.error("No valid Confluence authentication method configured")
        raise AuthenticationError("No valid Confluence authentication method configured")

    async def get_confluence(self) -> Confluence | None:
        logger.info("Getting Confluence connection")
        if self._confluence is not None:
            logger.debug("Returning existing Confluence connection")
            return self._confluence

        logger.debug(f"Connecting to Confluence at {config.CONFLUENCE_URL}")

        if not config.CONFLUENCE_URL:
            logger.error("Confluence URL not configured")
            raise ConfigurationError("CONFLUENCE_URL is required")
        if not self.validate_url(config.CONFLUENCE_URL):
            logger.error("Invalid Confluence URL format")
            raise ConfigurationError("CONFLUENCE_URL must be a valid URL")

        try:
            self._confluence = self._build_client()

            # smoke test
            try:
                self._confluence.get_all_spaces(start=0, limit=1)
            except Exception as conn_error:
                logger.error(f"Failed to test Confluence connection: {conn_error}")
                self._confluence = None
                raise ConfConnectionError(f"Failed to connect to Confluence: {conn_error}")

            logger.info("Successfully established Confluence connection")
            return self._confluence
        except ConfluenceError:
            # let custom exceptions propagate
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Confluence: {e}")
            self._confluence = None
            raise ConfConnectionError(str(e))

    def reset(self) -> None:
        self._confluence = None
