"""
Unit tests for confluence_server.py
"""
import asyncio
import json
import signal
from unittest.mock import patch

import pytest
from fastmcp import FastMCP

from src.servers import confluence_server


class TestHealthCheckRoute:
    """Test cases for the /mcp/confluence/health route handler"""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy_status(self):
        response = await confluence_server.health_check(request=None)

        assert response.status_code == 200
        assert json.loads(response.body) == {
            "status": "healthy",
            "service": "confluence-mcp-server",
        }


class TestModuleSetup:
    """Test cases for module-level server setup"""

    def test_mcp_instance_created(self):
        assert isinstance(confluence_server.mcp, FastMCP)

    def test_mcp_app_is_asgi_callable(self):
        assert callable(confluence_server.mcp_app)

    def test_logger_configured(self):
        assert confluence_server.logger.name == "confluence-mcp-server"


class TestToolMetadata:
    """Tool listings must not leak FastMCP-internal `_fastmcp` metadata."""

    @pytest.mark.asyncio
    async def test_listed_tools_have_no_fastmcp_meta(self):
        from fastmcp import Client

        async with Client(confluence_server.mcp) as client:
            tools = await client.list_tools()

        assert tools
        assert not [t.name for t in tools if t.meta and "_fastmcp" in t.meta]


class TestShutdownHandler:
    """Test cases for shutdown_handler"""

    @pytest.mark.asyncio
    async def test_shutdown_handler_cancels_other_tasks(self):
        async def sleeper():
            await asyncio.sleep(10)

        task = asyncio.create_task(sleeper())
        await asyncio.sleep(0)

        await confluence_server.shutdown_handler()

        assert task.cancelled()

    @pytest.mark.asyncio
    async def test_shutdown_handler_with_no_other_tasks(self):
        await confluence_server.shutdown_handler()


class TestSetupSignalHandlers:
    """Test cases for setup_signal_handlers"""

    @patch("src.servers.confluence_server.signal.signal")
    def test_registers_sigint_handler(self, mock_signal):
        confluence_server.setup_signal_handlers()

        registered_signals = [call.args[0] for call in mock_signal.call_args_list]
        assert signal.SIGINT in registered_signals
        if hasattr(signal, "SIGBREAK"):
            assert signal.SIGBREAK in registered_signals

    @patch("src.servers.confluence_server.asyncio.create_task")
    @patch("src.servers.confluence_server.signal.signal")
    def test_signal_handler_schedules_shutdown(self, mock_signal, mock_create_task):
        confluence_server.setup_signal_handlers()

        handler = next(
            call.args[1] for call in mock_signal.call_args_list if call.args[0] == signal.SIGINT
        )
        handler(signal.SIGINT, None)

        mock_create_task.assert_called_once()
        mock_create_task.call_args.args[0].close()


class TestStatelessHttp:
    """The server is stateless (D-stateless); the flag must not use the deprecated form."""

    def test_no_stateless_http_deprecation_warning(self):
        import importlib
        import warnings

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            importlib.reload(confluence_server)

        assert not [w for w in caught if "stateless_http" in str(w.message)]

    def test_requests_need_no_session(self):
        from starlette.testclient import TestClient

        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        body = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        with TestClient(confluence_server.mcp_app) as client:
            response = client.post("/mcp/confluence", json=body, headers=headers)

        assert response.status_code == 200
