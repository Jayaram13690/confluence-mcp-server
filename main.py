"""Start point for the Confluence MCP server: ``uv run python main.py``.

Thin launcher only (FR-8). The app lives in ``src/servers/confluence_server.py``.
Listens on ``CONFLUENCE_HOST`` (default localhost) and ``CONFLUENCE_PORT``; the
server must not be internet-facing (SEC-1).
"""

import uvicorn

from src.config.config import CONFLUENCE_HOST, CONFLUENCE_PORT

APP = "src.servers.confluence_server:mcp_app"


def main() -> None:

    uvicorn.run(
        APP,
        host=CONFLUENCE_HOST,
        port=CONFLUENCE_PORT,
        timeout_graceful_shutdown=10,
        timeout_keep_alive=5,
    )


if __name__ == "__main__":
    main()
