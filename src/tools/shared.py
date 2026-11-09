"""Process-wide ConfluenceClient shared by every tool module."""
from src.services.confluence_service import ConfluenceClient

confluence_client = ConfluenceClient()
