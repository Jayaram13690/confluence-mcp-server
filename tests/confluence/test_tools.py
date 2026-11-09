"""
Unit tests for confluence_tool.py
"""
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastmcp import Context, FastMCP

from src.exceptions.confluence_exception import (
    AttachmentError,
    ConfluenceError,
    CreatePageError,
    NotFoundError,
    ValidationError,
)
from src.tools import confluence_tool, context
from src.tools.confluence_tool import (
    CreatePageData,
    MCPResponse,
    PageData,
    register_tools,
)

DEFAULT_REGISTERED_TOOLS = [
    "confluence-readPageById",
    "confluence-readPageByTitle",
    "confluence-readPageByUrl",
    "confluence-createPage",
]


def _capture_tool(mock_mcp, target_name):
    """Wire mock_mcp.tool so the decorated function for target_name is captured."""
    captured = {}

    def tool_decorator(*, name, description, tags):
        def wrapper(func):
            if name == target_name:
                captured["func"] = func
            return func

        return wrapper

    mock_mcp.tool = tool_decorator
    return captured


class TestDataModels:
    """Test cases for Pydantic models"""

    def test_mcp_response_model(self):
        response = MCPResponse(
            content=[{"type": "text", "text": "test"}],
            data={"key": "value"},
            is_error=False,
        )

        assert len(response.content) == 1
        assert response.content[0]["text"] == "test"
        assert response.data["key"] == "value"
        assert response.is_error is False

    def test_page_data_model(self):
        page_data = PageData(
            id="123",
            title="Test Page",
            body="Content",
            attachments=[],
            space_key="SPACE",
        )

        assert page_data.id == "123"
        assert page_data.title == "Test Page"
        assert page_data.body == "Content"
        assert page_data.space_key == "SPACE"

    def test_create_page_data_model(self):
        create_data = CreatePageData(
            id="123",
            title="New Page",
            url="https://example.com/123",
            space_key="SPACE",
            attached_files=[],
        )

        assert create_data.id == "123"
        assert create_data.title == "New Page"
        assert create_data.url == "https://example.com/123"


class TestRegisterTools:
    """Test cases for register_tools function"""

    def test_register_tools_default_set(self):
        """Without ENABLED_CONFLUENCE_TOOLS configured, only the tools present in
        both the default fallback list and available_tools get registered."""
        mock_mcp = Mock(spec=FastMCP)

        register_tools(mock_mcp)

        assert mock_mcp.tool.call_count == len(DEFAULT_REGISTERED_TOOLS)
        tool_names = [call.kwargs.get("name") for call in mock_mcp.tool.call_args_list]
        assert set(tool_names) == set(DEFAULT_REGISTERED_TOOLS)

    def test_register_tools_respects_configured_list(self, monkeypatch):
        monkeypatch.setattr(
            confluence_tool.config,
            "ENABLED_CONFLUENCE_TOOLS",
            ["confluence-health", "confluence-unknownTool"],
            raising=False,
        )
        mock_mcp = Mock(spec=FastMCP)

        register_tools(mock_mcp)

        assert mock_mcp.tool.call_count == 1
        assert mock_mcp.tool.call_args_list[0].kwargs.get("name") == "confluence-health"

    def test_register_tools_tool_descriptions(self):
        mock_mcp = Mock(spec=FastMCP)

        register_tools(mock_mcp)

        for call in mock_mcp.tool.call_args_list:
            assert call.kwargs.get("description")

    def test_register_tools_tool_tags(self):
        mock_mcp = Mock(spec=FastMCP)

        register_tools(mock_mcp)

        for call in mock_mcp.tool.call_args_list:
            assert "confluence" in call.kwargs.get("tags")

    def test_register_tools_with_real_mcp(self):
        mcp = FastMCP(name="test-mcp")
        register_tools(mcp)


class TestReadPageByIdTool:
    """Test cases for the confluence-readPageById tool"""

    def setup_method(self):
        self.mock_ctx = Mock(spec=Context)

    def _get_tool_func(self):
        mock_mcp = Mock(spec=FastMCP)
        captured = _capture_tool(mock_mcp, "confluence-readPageById")
        register_tools(mock_mcp)
        return captured["func"]

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_read_page_by_id_success(self, mock_confluence_instance):
        expected_result = {
            "id": "12345",
            "title": "Test Page",
            "body": "Page content",
            "attachments": [{"fileName": "test.pdf", "content": "PDF content"}],
            "url": "https://example.com/pages/12345",
        }
        mock_confluence_instance.get_page_content_by_id = AsyncMock(return_value=expected_result)

        tool_func = self._get_tool_func()
        result = await tool_func(self.mock_ctx, "SPACE", "12345")

        assert result["id"] == "12345"
        assert result["title"] == "Test Page"
        assert result["attachments"][0]["fileName"] == "test.pdf"
        mock_confluence_instance.get_page_content_by_id.assert_called_once_with("SPACE", "12345")

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_read_page_by_id_not_found_error(self, mock_confluence_instance):
        mock_confluence_instance.get_page_content_by_id = AsyncMock(
            side_effect=NotFoundError("Page not found")
        )

        tool_func = self._get_tool_func()
        result = await tool_func(self.mock_ctx, "SPACE", "12345")

        assert result["error_code"] == "PAGE_NOT_FOUND"
        assert result["error_message"] == "Page not found"
        assert result["error_details"]["page_id"] == "12345"

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_read_page_by_id_validation_error(self, mock_confluence_instance):
        mock_confluence_instance.get_page_content_by_id = AsyncMock(
            side_effect=ValidationError("Invalid page id")
        )

        tool_func = self._get_tool_func()
        result = await tool_func(self.mock_ctx, "SPACE", "bad-id")

        assert result["error_code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_read_page_by_id_confluence_error(self, mock_confluence_instance):
        mock_confluence_instance.get_page_content_by_id = AsyncMock(
            side_effect=ConfluenceError("Something went wrong")
        )

        tool_func = self._get_tool_func()
        result = await tool_func(self.mock_ctx, "SPACE", "12345")

        assert result["error_code"] == "CONFLUENCE_ERROR"


class TestReadPageByTitleTool:
    """Test cases for the confluence-readPageByTitle tool"""

    def setup_method(self):
        self.mock_ctx = Mock(spec=Context)

    def _get_tool_func(self):
        mock_mcp = Mock(spec=FastMCP)
        captured = _capture_tool(mock_mcp, "confluence-readPageByTitle")
        register_tools(mock_mcp)
        return captured["func"]

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_read_page_by_title_success(self, mock_confluence_instance):
        expected_result = {
            "id": "12345",
            "title": "Test Page",
            "body": "Page content",
            "attachments": [],
            "url": "https://example.com/pages/12345",
        }
        mock_confluence_instance.get_page_content_by_title = AsyncMock(return_value=expected_result)

        tool_func = self._get_tool_func()
        result = await tool_func(self.mock_ctx, "SPACE", "Test Page")

        assert result["id"] == "12345"
        mock_confluence_instance.get_page_content_by_title.assert_called_once_with("SPACE", "Test Page")

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_read_page_by_title_not_found_error(self, mock_confluence_instance):
        mock_confluence_instance.get_page_content_by_title = AsyncMock(
            side_effect=NotFoundError("Page not found")
        )

        tool_func = self._get_tool_func()
        result = await tool_func(self.mock_ctx, "SPACE", "Missing Page")

        assert result["error_code"] == "PAGE_NOT_FOUND"
        assert result["error_details"]["page_title"] == "Missing Page"


class TestReadPageByUrlTool:
    """Test cases for the confluence-readPageByUrl tool"""

    def setup_method(self):
        self.mock_ctx = Mock(spec=Context)

    def _get_tool_func(self):
        mock_mcp = Mock(spec=FastMCP)
        captured = _capture_tool(mock_mcp, "confluence-readPageByUrl")
        register_tools(mock_mcp)
        return captured["func"]

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_read_page_by_url_success(self, mock_confluence_instance):
        expected_result = {
            "id": "12345",
            "title": "Test Page",
            "body": "Page content",
            "attachments": [],
            "url": "https://example.com/pages/12345",
            "space_key": "SPACE",
        }
        mock_confluence_instance.get_page_content_by_url = AsyncMock(return_value=expected_result)

        tool_func = self._get_tool_func()
        result = await tool_func(self.mock_ctx, "https://example.com/wiki/spaces/SPACE/pages/12345/Test+Page")

        assert result["id"] == "12345"
        assert result["space_key"] == "SPACE"

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_read_page_by_url_validation_error(self, mock_confluence_instance):
        mock_confluence_instance.get_page_content_by_url = AsyncMock(
            side_effect=ValidationError("Invalid page URL")
        )

        tool_func = self._get_tool_func()
        result = await tool_func(self.mock_ctx, "not-a-url")

        assert result["error_code"] == "VALIDATION_ERROR"
        assert result["error_details"]["page_url"] == "not-a-url"


class TestCreatePageTool:
    """Test cases for the confluence-createPage tool"""

    def setup_method(self):
        self.mock_ctx = Mock(spec=Context)

    def _get_tool_func(self):
        mock_mcp = Mock(spec=FastMCP)
        captured = _capture_tool(mock_mcp, "confluence-createPage")
        register_tools(mock_mcp)
        return captured["func"]

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_create_page_success(self, mock_confluence_instance):
        expected_result = {
            "id": "12345",
            "url": "https://example.com/pages/12345",
            "attached_files": [],
        }
        mock_confluence_instance.create_page_with_content = AsyncMock(return_value=expected_result)

        tool_func = self._get_tool_func()
        result = await tool_func(self.mock_ctx, "SPACE", "New Page", "<p>Content</p>", None, "storage")

        assert result["id"] == "12345"
        assert result["title"] == "New Page"
        assert result["space_key"] == "SPACE"
        mock_confluence_instance.create_page_with_content.assert_called_once_with(
            "SPACE", "New Page", "<p>Content</p>", None, "storage"
        )

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_create_page_validation_error(self, mock_confluence_instance):
        mock_confluence_instance.create_page_with_content = AsyncMock(
            side_effect=ValidationError("Title is required")
        )

        tool_func = self._get_tool_func()
        result = await tool_func(self.mock_ctx, "SPACE", "", "<p>Content</p>", None, "storage")

        assert result["error_code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_create_page_create_page_error(self, mock_confluence_instance):
        mock_confluence_instance.create_page_with_content = AsyncMock(
            side_effect=CreatePageError("Failed to create page")
        )

        tool_func = self._get_tool_func()
        result = await tool_func(self.mock_ctx, "SPACE", "New Page", "<p>Content</p>", None, "storage")

        assert result["error_code"] == "CREATE_PAGE_ERROR"

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_create_page_attachment_error(self, mock_confluence_instance):
        mock_confluence_instance.create_page_with_content = AsyncMock(
            side_effect=AttachmentError("Attachment failed")
        )

        tool_func = self._get_tool_func()
        result = await tool_func(self.mock_ctx, "SPACE", "New Page", "<p>Content</p>", "/tmp/file.txt", "storage")

        assert result["error_code"] == "ATTACHMENT_ERROR"
        assert result["error_details"]["attachment"] == "/tmp/file.txt"


class TestHealthCheckTool:
    """Test cases for the confluence-health tool"""

    def setup_method(self):
        self.mock_ctx = Mock(spec=Context)

    def _get_tool_func(self, monkeypatch):
        monkeypatch.setattr(
            confluence_tool.config, "ENABLED_CONFLUENCE_TOOLS", ["confluence-health"], raising=False
        )
        mock_mcp = Mock(spec=FastMCP)
        captured = _capture_tool(mock_mcp, "confluence-health")
        register_tools(mock_mcp)
        return captured["func"]

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_health_check_success(self, mock_confluence_instance, monkeypatch):
        mock_confluence = Mock()
        mock_confluence.get_all_spaces.return_value = {"results": [{"key": "SPACE"}]}
        mock_confluence.url = "https://example.atlassian.net"
        mock_confluence_instance.get_confluence = AsyncMock(return_value=mock_confluence)

        tool_func = self._get_tool_func(monkeypatch)
        result = await tool_func(self.mock_ctx)

        assert result["status"] == "healthy"
        assert result["confluence_url"] == "https://example.atlassian.net"
        assert result["spaces_accessible"] is True

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_health_check_no_spaces(self, mock_confluence_instance, monkeypatch):
        mock_confluence = Mock()
        mock_confluence.get_all_spaces.return_value = {"results": []}
        mock_confluence.url = "https://example.atlassian.net"
        mock_confluence_instance.get_confluence = AsyncMock(return_value=mock_confluence)

        tool_func = self._get_tool_func(monkeypatch)
        result = await tool_func(self.mock_ctx)

        assert result["spaces_accessible"] is False

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_health_check_confluence_error(self, mock_confluence_instance, monkeypatch):
        mock_confluence_instance.get_confluence = AsyncMock(
            side_effect=ConfluenceError("Configuration error")
        )

        tool_func = self._get_tool_func(monkeypatch)
        result = await tool_func(self.mock_ctx)

        assert result["error_code"] == "HEALTH_CHECK_ERROR"
        assert "Configuration error" in result["error_message"]

    @pytest.mark.asyncio
    @patch("src.tools.shared.confluence_client")
    async def test_health_check_unknown_error(self, mock_confluence_instance, monkeypatch):
        mock_confluence_instance.get_confluence = AsyncMock(side_effect=RuntimeError("boom"))

        tool_func = self._get_tool_func(monkeypatch)
        result = await tool_func(self.mock_ctx)

        assert result["error_code"] == "UNKNOWN_ERROR"
        assert result["error_details"]["error_type"] == "RuntimeError"


class TestResolveContextParams:
    """Test cases for _resolve_context_params"""

    class _CtxStub:
        pass

    def test_passthrough_when_no_overrides(self):
        ctx = self._CtxStub()

        space_key, page_title = context._resolve_context_params(ctx, "SPACE", "Title")

        assert (space_key, page_title) == ("SPACE", "Title")

    def test_direct_attribute_overrides_space_key(self):
        ctx = self._CtxStub()
        ctx.confluence_space_key = "OVERRIDDEN_SPACE"

        space_key, _ = context._resolve_context_params(ctx, "SPACE", "Title")

        assert space_key == "OVERRIDDEN_SPACE"

    def test_meta_dict_overrides_page_title(self):
        ctx = self._CtxStub()
        ctx.meta = {"confluence_page_title": "META_TITLE"}

        _, page_title = context._resolve_context_params(ctx, "SPACE", "Title")

        assert page_title == "META_TITLE"

    def test_none_page_title_is_not_overridden(self):
        ctx = self._CtxStub()
        ctx.confluence_page_title = "SHOULD_NOT_APPEAR"

        _, page_title = context._resolve_context_params(ctx, "SPACE", None)

        assert page_title is None


class TestToolConfiguration:
    """Test cases for tool naming/description conventions"""

    def test_tool_names_are_consistent(self):
        mock_mcp = Mock(spec=FastMCP)
        register_tools(mock_mcp)

        tool_names = [call.kwargs.get("name") for call in mock_mcp.tool.call_args_list]

        for name in tool_names:
            assert name.startswith("confluence-")

    def test_tool_descriptions_are_meaningful(self):
        mock_mcp = Mock(spec=FastMCP)
        register_tools(mock_mcp)

        for call in mock_mcp.tool.call_args_list:
            description = call.kwargs.get("description")
            assert len(description) > 20
            assert "confluence" in description.lower()
