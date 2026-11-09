"""
Unit tests for confluence_service.py - Corrected Version
"""
import os
import tempfile
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Setup logging for tests
from src.utils.log_helper import setup_logging

setup_logging()

# Add project root to Python path for imports
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.exceptions.confluence_exception import (
    AttachmentError,
    AuthenticationError,
    ConfigurationError,
    ContentError,
    NotFoundError,
    ValidationError,
)
from src.exceptions.confluence_exception import (
    ConnectionError as ConfConnectionError,
)
from src.services import connection
from src.services.confluence_service import ConfluenceClient


class TestConfluenceClientValidation:
    """Test cases for validation methods"""
    
    def test_validate_page_id_valid(self):
        """Test validate_page_id with valid page ID"""
        assert ConfluenceClient.validate_page_id("12345") == True
        assert ConfluenceClient.validate_page_id("999999") == True
    
    def test_validate_page_id_invalid(self):
        """Test validate_page_id with invalid page ID"""
        assert ConfluenceClient.validate_page_id("") == False
        assert ConfluenceClient.validate_page_id("abc123") == False
        assert ConfluenceClient.validate_page_id("123abc") == False
        assert ConfluenceClient.validate_page_id(None) == False
        assert ConfluenceClient.validate_page_id(12345) == False
    
    def test_validate_page_title_valid(self):
        """Test validate_page_title with valid titles"""
        assert ConfluenceClient.validate_page_title("Valid Title") == True
        assert ConfluenceClient.validate_page_title("Title-123") == True
        assert ConfluenceClient.validate_page_title("Title_123") == True
        assert ConfluenceClient.validate_page_title("Title123") == True

    def test_validate_page_title_invalid(self):
        """Test validate_page_title with invalid titles"""
        assert ConfluenceClient.validate_page_title("") == False
        assert ConfluenceClient.validate_page_title("Title@123") == False
        assert ConfluenceClient.validate_page_title("Title#123") == False
        assert ConfluenceClient.validate_page_title(None) == False
        assert ConfluenceClient.validate_page_title(12345) == False

    def test_validate_space_key_valid(self):
        """Test validate_space_key with valid space keys"""
        assert ConfluenceClient.validate_space_key("MYSPACE") == True
        assert ConfluenceClient.validate_space_key("SPACE123") == True
        assert ConfluenceClient.validate_space_key("Space_key") == True
    
    def test_validate_space_key_invalid(self):
        """Test validate_space_key with invalid space keys"""
        assert ConfluenceClient.validate_space_key("") == False
        assert ConfluenceClient.validate_space_key("Space@123") == False
        assert ConfluenceClient.validate_space_key("Space#key") == False
        assert ConfluenceClient.validate_space_key(None) == False
        assert ConfluenceClient.validate_space_key(12345) == False
        assert ConfluenceClient.validate_space_key("   ") == False  # whitespace only
    
    def test_validate_url_valid(self):
        """Test validate_url with valid URLs"""
        assert ConfluenceClient.validate_url("https://example.atlassian.net") == True
        assert ConfluenceClient.validate_url("http://localhost:8080") == True
    
    def test_validate_url_invalid(self):
        """Test validate_url with invalid URLs"""
        assert ConfluenceClient.validate_url("") == False
        assert ConfluenceClient.validate_url("not_a_url") == False
        assert ConfluenceClient.validate_url(None) == False
        assert ConfluenceClient.validate_url(12345) == False


class TestConfluenceClientConnection:
    """Test cases for connection management"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = ConfluenceClient()

    @pytest.mark.asyncio
    async def test_get_confluence_success_api_token_email(self, monkeypatch):
        """Test successful connection with API token and email"""
        # Setup config
        monkeypatch.setattr(connection.config, "CONFLUENCE_URL", "https://example.atlassian.net")
        monkeypatch.setattr(connection.config, "CONFLUENCE_API_TOKEN", "token123")
        monkeypatch.setattr(connection.config, "CONFLUENCE_EMAIL", "user@example.com")
        monkeypatch.setattr(connection.config, "CONFLUENCE_USERNAME", None)

        mock_confluence_instance = MagicMock()
        with patch.object(connection, "Confluence", return_value=mock_confluence_instance) as mock_confluence_class:
            # Test the connection
            await self.client.get_confluence()

        # Verify Confluence was instantiated with correct parameters
        mock_confluence_class.assert_called_once_with(
            url="https://example.atlassian.net",
            username="user@example.com",
            password="token123",
            cloud=True
        )

    @pytest.mark.asyncio
    async def test_get_confluence_no_url(self, monkeypatch):
        """Test connection failure when URL is not configured"""
        monkeypatch.setattr(connection.config, "CONFLUENCE_URL", None)

        with pytest.raises(ConfigurationError, match="CONFLUENCE_URL is required"):
            await self.client.get_confluence()

    @pytest.mark.asyncio
    async def test_get_confluence_invalid_url(self, monkeypatch):
        """Test connection failure when URL is invalid"""
        monkeypatch.setattr(connection.config, "CONFLUENCE_URL", "not_a_url")

        with pytest.raises(ConfigurationError, match="CONFLUENCE_URL must be a valid URL"):
            await self.client.get_confluence()

    @pytest.mark.asyncio
    async def test_get_confluence_no_auth(self, monkeypatch):
        """Test connection failure when no authentication is configured"""
        monkeypatch.setattr(connection.config, "CONFLUENCE_URL", "https://example.atlassian.net")
        monkeypatch.setattr(connection.config, "CONFLUENCE_API_TOKEN", None)
        monkeypatch.setattr(connection.config, "CONFLUENCE_EMAIL", None)
        monkeypatch.setattr(connection.config, "CONFLUENCE_USERNAME", None)

        with pytest.raises(AuthenticationError, match="No valid Confluence authentication method configured"):
            await self.client.get_confluence()
    
    def test_reset(self):
        """Test reset method clears the connection"""
        self.client._confluence = MagicMock()
        self.client.reset()
        assert self.client._confluence is None


class TestConfluenceClientContentHelpers:
    """Test cases for content processing helpers"""
    
    def test_html_to_plain_text_valid_html(self):
        """Test HTML to plain text conversion with valid HTML"""
        html = "<h1>Title</h1><p>This is a paragraph with <strong>bold</strong> text.</p>"
        result = ConfluenceClient.html_to_plain_text(html)
        assert "Title" in result
        assert "paragraph" in result
        assert "bold" in result
        assert "<h1>" not in result
        assert "<p>" not in result
    
    def test_html_to_plain_text_with_scripts(self):
        """Test HTML to plain text conversion removes scripts and styles"""
        html = "<html><head><style>body{color:red;}</style></head><body><script>alert('test');</script><p>Content</p></body></html>"
        result = ConfluenceClient.html_to_plain_text(html)
        assert "Content" in result
        assert "alert" not in result
        assert "color:red" not in result
    
    def test_html_to_plain_text_empty(self):
        """Test HTML to plain text conversion with empty content"""
        result = ConfluenceClient.html_to_plain_text("")
        assert result == "No content available"
        
        result = ConfluenceClient.html_to_plain_text(None)
        assert result == "No content available"
    
    def test_html_to_plain_text_invalid_type(self):
        """Test HTML to plain text conversion with invalid input type"""
        result = ConfluenceClient.html_to_plain_text(12345)
        assert result == "No content available"
    
    def test_extract_file_content_txt(self):
        """Test text file content extraction"""
        content = "This is test content"
        content_bytes = content.encode('utf-8')
        
        result = ConfluenceClient.extract_file_content(content_bytes, "test.txt")
        assert result == content
    
    def test_extract_file_content_unsupported(self):
        """Test unsupported file type returns proper message"""
        content_bytes = b"some content"
        
        result = ConfluenceClient.extract_file_content(content_bytes, "test.xyz")
        assert result == " Unsupported file type: test.xyz"
    
    def test_extract_file_content_empty(self):
        """Test empty file returns proper message"""
        content_bytes = b""
        
        result = ConfluenceClient.extract_file_content(content_bytes, "test.txt")
        assert result == "No file content or filename provided"


class TestConfluenceClientContentExtraction:
    """Test cases for file content extraction"""
    
    @patch("fitz.open")
    def test_extract_file_content_pdf(self, mock_fitz):
        """Test PDF content extraction"""
        # Mock PDF document
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "PDF content"
        mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))
        mock_doc.__enter__ = MagicMock(return_value=mock_doc)
        mock_doc.__exit__ = MagicMock(return_value=None)
        mock_fitz.return_value = mock_doc
        
        content_bytes = b"mock pdf content"
        result = ConfluenceClient.extract_file_content(content_bytes, "test.pdf")
        assert result == "PDF content"
    
    @patch("docx.Document")
    @patch("io.BytesIO")
    def test_extract_file_content_docx(self, mock_bytesio, mock_docx):
        """Test DOCX content extraction"""
        # Mock DOCX document
        mock_doc = MagicMock()
        mock_paragraph = MagicMock()
        mock_paragraph.text = "DOCX content"
        mock_doc.paragraphs = [mock_paragraph]
        mock_docx.return_value = mock_doc
        
        content_bytes = b"mock docx content"
        result = ConfluenceClient.extract_file_content(content_bytes, "test.docx")
        assert result == "DOCX content"
    
    def test_extract_file_content_txt_unicode_error(self):
        """Test text file with unicode decode error"""
        content_bytes = b'\xff\xfe'  # Invalid UTF-8
        result = ConfluenceClient.extract_file_content(content_bytes, "test.txt")
        assert result == " Could not decode TXT file."
    
    def test_extract_file_content_exception_handling(self):
        """Test file content extraction with general exception"""
        with patch('fitz.open', side_effect=Exception("Processing error")):
            content_bytes = b"mock pdf content"
            with pytest.raises(ContentError, match="Error processing file test.pdf"):
                ConfluenceClient.extract_file_content(content_bytes, "test.pdf")


class TestConfluenceClientAdvancedConnection:
    """Test cases for advanced connection scenarios"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = ConfluenceClient()

    @pytest.mark.asyncio
    async def test_get_confluence_username_token_auth(self, monkeypatch):
        """Test connection with username and token authentication"""
        monkeypatch.setattr(connection.config, "CONFLUENCE_URL", "https://example.atlassian.net")
        monkeypatch.setattr(connection.config, "CONFLUENCE_API_TOKEN", "token123")
        monkeypatch.setattr(connection.config, "CONFLUENCE_EMAIL", None)
        monkeypatch.setattr(connection.config, "CONFLUENCE_USERNAME", "testuser")

        mock_confluence_instance = MagicMock()
        with patch.object(connection, "Confluence", return_value=mock_confluence_instance) as mock_confluence_class:
            await self.client.get_confluence()

        # Verify Confluence was instantiated with correct parameters
        mock_confluence_class.assert_called_once_with(
            url="https://example.atlassian.net",
            username="testuser",
            password="token123",
            cloud=False
        )

    @pytest.mark.asyncio
    async def test_get_confluence_oauth_auth(self, monkeypatch):
        """Test connection with OAuth authentication"""
        monkeypatch.setattr(connection.config, "CONFLUENCE_URL", "https://example.atlassian.net")
        monkeypatch.setattr(connection.config, "CONFLUENCE_API_TOKEN", None)
        monkeypatch.setattr(connection.config, "CONFLUENCE_EMAIL", None)
        monkeypatch.setattr(connection.config, "CONFLUENCE_USERNAME", None)
        monkeypatch.setattr(connection.config, "oauth_consumer_key", "consumer_key", raising=False)
        monkeypatch.setattr(connection.config, "oauth_private_key_path", "/path/to/key", raising=False)

        mock_confluence_instance = MagicMock()
        with patch.object(connection, "Confluence", return_value=mock_confluence_instance) as mock_confluence_class, \
             patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="private_key_content")):
            await self.client.get_confluence()

        # Verify Confluence was instantiated with OAuth parameters - check for partial match
        _args, kwargs = mock_confluence_class.call_args
        assert kwargs['url'] == "https://example.atlassian.net"
        assert 'oauth' in kwargs
        assert kwargs['oauth']['consumer_key'] == "consumer_key"
        assert kwargs['oauth']['key_cert'] == "private_key_content"

    @pytest.mark.asyncio
    async def test_get_confluence_oauth_key_not_found(self, monkeypatch):
        """Test OAuth connection failure when private key file not found"""
        monkeypatch.setattr(connection.config, "CONFLUENCE_URL", "https://example.atlassian.net")
        monkeypatch.setattr(connection.config, "CONFLUENCE_API_TOKEN", None)
        monkeypatch.setattr(connection.config, "CONFLUENCE_EMAIL", None)
        monkeypatch.setattr(connection.config, "CONFLUENCE_USERNAME", None)
        monkeypatch.setattr(connection.config, "oauth_consumer_key", "consumer_key", raising=False)
        monkeypatch.setattr(connection.config, "oauth_private_key_path", "/nonexistent/path", raising=False)

        with patch("os.path.exists", return_value=False), \
             pytest.raises(ConfigurationError, match="OAuth private key file not found"):
            await self.client.get_confluence()

    @pytest.mark.asyncio
    async def test_get_confluence_connection_test_failure(self, monkeypatch):
        """Test connection failure during connection test"""
        monkeypatch.setattr(connection.config, "CONFLUENCE_URL", "https://example.atlassian.net")
        monkeypatch.setattr(connection.config, "CONFLUENCE_API_TOKEN", "token123")
        monkeypatch.setattr(connection.config, "CONFLUENCE_EMAIL", "user@example.com")
        monkeypatch.setattr(connection.config, "CONFLUENCE_USERNAME", None)

        mock_confluence_instance = MagicMock()
        mock_confluence_instance.get_all_spaces.side_effect = Exception("Connection failed")
        with patch.object(connection, "Confluence", return_value=mock_confluence_instance), \
             pytest.raises(ConfConnectionError, match="Failed to connect to Confluence"):
            await self.client.get_confluence()


class TestConfluenceClientPageOperations:
    """Test cases for page operations"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = ConfluenceClient()

    @pytest.mark.asyncio
    @patch("src.services.connection.Confluence")
    async def test_get_page_content_by_id_success(self, mock_confluence_class):
        """Test successful page content retrieval by ID"""
        # Setup mocks
        mock_confluence_instance = MagicMock()
        mock_confluence_instance.get_page_by_id.return_value = {
            "title": "Test Page",
            "body": {
                "storage": {
                    "value": "<p>This is test content</p>"
                }
            },
            "_links": {"webui": "/spaces/TEST/pages/123"},
            "id": "123"
        }
        mock_confluence_class.return_value = mock_confluence_instance
        self.client._confluence = mock_confluence_instance
        
        # Test the method - note the correct signature: get_page_content_by_id(space_key, page_id)
        result = await self.client.get_page_content_by_id("TEST", "123")
        
        # Verify results
        assert result["title"] == "Test Page"
        assert "This is test content" in result["body"]
        # The URL format is: {client.url}/pages/{page_id}
        assert "/pages/123" in result["url"]
        assert result["id"] == "123"

    @pytest.mark.asyncio
    @patch("src.services.connection.Confluence")
    async def test_get_page_content_by_id_not_found(self, mock_confluence_class):
        """Test page content retrieval by ID when page not found"""
        mock_confluence_instance = MagicMock()
        # Mock returns None, which triggers NotFoundError in the service
        mock_confluence_instance.get_page_by_id.return_value = None
        mock_confluence_class.return_value = mock_confluence_instance
        self.client._confluence = mock_confluence_instance
        
        with pytest.raises(NotFoundError, match="Page id 999 not found"):
            await self.client.get_page_content_by_id("TEST", "999")

    @pytest.mark.asyncio
    @patch("src.services.connection.Confluence") 
    async def test_get_page_content_by_title_success(self, mock_confluence_class):
        """Test successful page content retrieval by title"""
        mock_confluence_instance = MagicMock()
        mock_confluence_instance.get_page_by_title.return_value = {
            "title": "Test Page",
            "body": {
                "storage": {
                    "value": "<p>This is test content</p>"
                }
            },
            "_links": {"webui": "/spaces/TEST/pages/123"},
            "id": "123"
        }
        mock_confluence_instance.url = "https://example.atlassian.net"
        mock_confluence_class.return_value = mock_confluence_instance
        self.client._confluence = mock_confluence_instance
        
        result = await self.client.get_page_content_by_title("TEST", "Test Page")
        
        assert result["title"] == "Test Page"
        assert "This is test content" in result["body"]
        # The URL format is: {client.url}/pages/{page_id}
        assert result["url"] == "https://example.atlassian.net/pages/123"
        assert result["id"] == "123"

    @pytest.mark.asyncio
    @patch("src.services.connection.Confluence")
    async def test_get_page_content_by_title_not_found(self, mock_confluence_class):
        """Test page content retrieval by title when page not found"""
        mock_confluence_instance = MagicMock()
        # Mock returns None, which triggers NotFoundError in the service
        mock_confluence_instance.get_page_by_title.return_value = None
        mock_confluence_class.return_value = mock_confluence_instance
        self.client._confluence = mock_confluence_instance
        
        with pytest.raises(NotFoundError, match="Page title 'Nonexistent Page' not found in space TEST"):
            await self.client.get_page_content_by_title("TEST", "Nonexistent Page")


class TestConfluenceClientPageCreation:
    """Test cases for page creation"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = ConfluenceClient()

    @pytest.mark.asyncio
    async def test_create_page_with_content_success(self, monkeypatch):
        """Test successful page creation with content"""
        monkeypatch.setattr(connection.config, "CONFLUENCE_URL", "https://example.atlassian.net")
        mock_confluence_instance = MagicMock()
        mock_confluence_instance.create_page.return_value = {
            "id": "456",
            "title": "New Test Page",
            "_links": {"webui": "/spaces/TEST/pages/456"}
        }
        self.client._confluence = mock_confluence_instance
        
        # Note the correct signature: create_page_with_content(space_key, title, body, attachment, representation)
        result = await self.client.create_page_with_content("TEST", "New Test Page", "<p>New content</p>", None, "storage")
        
        assert result["id"] == "456"
        assert result["title"] == "New Test Page"
        assert result["url"] == "https://example.atlassian.net/pages/456"

    @pytest.mark.asyncio
    @patch("src.services.connection.Confluence")
    async def test_create_page_validation_errors(self, mock_confluence_class):
        """Test page creation with validation errors"""
        mock_confluence_instance = MagicMock()
        mock_confluence_class.return_value = mock_confluence_instance
        self.client._confluence = mock_confluence_instance
        
        # Test invalid space key
        with pytest.raises(ValidationError, match="Invalid space key"):
            await self.client.create_page_with_content("", "Test Page", "Content", None, "storage")
            
        # Test invalid page title  
        with pytest.raises(ValidationError, match="Title is required and must be a non-empty string"):
            await self.client.create_page_with_content("TEST", "", "Content", None, "storage")


class TestConfluenceClientAttachments:
    """Test cases for attachment operations"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = ConfluenceClient()
    
    def test_list_attachments_success(self, monkeypatch):
        """Test successful attachment listing"""
        monkeypatch.setattr(connection.config, "CONFLUENCE_URL", "https://example.atlassian.net")
        self.client._confluence = MagicMock()
        self.client._confluence.get_attachments_from_content.return_value = {
            "results": [
                {
                    "title": "test.pdf",
                    "id": "att-123",
                    "_links": {"download": "/download/attachments/123/test.pdf"}
                }
            ]
        }
        
        result = self.client.list_attachments("123")
        
        assert len(result) == 1
        assert result[0]["title"] == "test.pdf"
        assert "downloadLink" in result[0]
    
    def test_list_attachments_exception(self):
        """Test attachment listing with exception"""
        self.client._confluence = MagicMock()
        self.client._confluence.get_attachments_from_content.side_effect = Exception("API Error")
        
        result = self.client.list_attachments("123")
        assert result == []

    @pytest.mark.asyncio
    @patch("src.services.connection.Confluence")
    async def test_attach_file_to_page_success(self, mock_confluence_class):
        """Test successful file attachment"""
        mock_confluence_instance = MagicMock()
        mock_confluence_instance.attach_file.return_value = {
            "id": "789",
            "title": "test.txt"
        }
        mock_confluence_class.return_value = mock_confluence_instance
        self.client._confluence = mock_confluence_instance
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content")
            temp_path = f.name
        
        try:
            result = await self.client.attach_file_to_page("123", temp_path)
            assert result["id"] == "789"
            assert result["title"] == "test.txt"
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_attach_file_to_page_validation_error(self):
        """Test file attachment with validation error"""
        with pytest.raises(ValidationError, match="Invalid page id"):
            await self.client.attach_file_to_page("", "test.txt")

    @pytest.mark.asyncio
    async def test_attach_file_to_page_missing_file(self):
        """Test file attachment with missing file"""
        with pytest.raises(AttachmentError, match="Attachment file path invalid or missing"):
            await self.client.attach_file_to_page("123", "/nonexistent/file.txt")


class TestConfluenceClientEdgeCases:
    """Test cases for edge cases and error scenarios"""
    
    def test_html_to_plain_text_complex_html(self):
        """Test HTML to plain text conversion with complex HTML"""
        html = """
        <div class="content">
            <h1>Main Title</h1>
            <div class="section">
                <h2>Subtitle</h2>
                <p>Paragraph with <a href="#">link</a> and <em>emphasis</em>.</p>
                <ul>
                    <li>Item 1</li>
                    <li>Item 2</li>
                </ul>
            </div>
        </div>
        """
        
        result = ConfluenceClient.html_to_plain_text(html)
        assert "Main Title" in result
        assert "Subtitle" in result
        assert "Paragraph" in result
        assert "link" in result
        assert "emphasis" in result
        assert "Item 1" in result
        assert "Item 2" in result
        # Verify HTML tags are removed
        assert "<div>" not in result
        assert "<h1>" not in result
        assert "<ul>" not in result

    def test_html_to_plain_text_with_exception(self):
        """Test html_to_plain_text falls back to an error string on processing errors"""
        with patch('src.services.content.BeautifulSoup') as mock_bs:
            mock_bs.side_effect = Exception("Parsing error")

            result = ConfluenceClient.html_to_plain_text("<p>Test</p>")

        assert result == "Error parsing content"

    def test_validate_methods_edge_cases(self):
        """Test validation methods with edge cases"""
        # Note: Based on actual implementation, whitespace-only strings are valid for page titles
        # The regex allows spaces, so "   " would pass validation
        # This test should match the actual behavior
        assert ConfluenceClient.validate_page_title("   ") == True  # whitespace passes regex
        assert ConfluenceClient.validate_space_key("   ") == False  # stripped to empty, fails
        assert ConfluenceClient.validate_page_id("   ") == False  # whitespace doesn't match digit regex
