"""Launcher tests (FR-8). No network, no server started."""

import main


def _run_main(monkeypatch, host, port):
    calls = []
    monkeypatch.setattr(main.uvicorn, "run", lambda *a, **kw: calls.append((a, kw)))
    monkeypatch.setattr(main, "CONFLUENCE_HOST", host)
    monkeypatch.setattr(main, "CONFLUENCE_PORT", port)
    main.main()
    return calls


def test_main_runs_app_on_configured_host_and_port(monkeypatch):
    # FR-8 / CFG-7 / SEC-1
    calls = _run_main(monkeypatch, "0.0.0.0", 9123)

    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args == ("src.servers.confluence_server:mcp_app",)
    assert kwargs["host"] == "0.0.0.0"
    assert kwargs["port"] == 9123
    assert kwargs["timeout_graceful_shutdown"] == 10


def test_default_host_is_localhost():
    # SEC-1: not internet-facing unless explicitly configured
    from src.config import config

    assert config.CONFLUENCE_HOST == "127.0.0.1"
