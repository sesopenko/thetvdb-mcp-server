"""FastMCP server entrypoint for the thetvdb-mcp-server server.

Run with::

    uv run python -m thetvdb_mcp_server

or via the installed script::

    thetvdb-mcp-server
"""

import argparse
from pathlib import Path

import fastmcp

from thetvdb_mcp_server.config import load_config
from thetvdb_mcp_server.logging import Logger, make_logger
from thetvdb_mcp_server.tools import health_check as _health_check

mcp = fastmcp.FastMCP("thetvdb-mcp-server")

_logger: Logger | None = None


@mcp.tool()
def health_check() -> dict[str, str]:
    """Return a simple health status indicating the server is running.

    Returns:
        A dict with a single ``status`` key set to ``"ok"``.
    """
    return _health_check()


def main() -> None:
    """Parse CLI arguments, load configuration, and start the MCP server."""
    parser = argparse.ArgumentParser(description="thetvdb-mcp-server MCP server")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.toml"),
        help="Path to config.toml (default: config.toml)",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    global _logger
    _logger = make_logger(config.logging.level)

    mcp.run(
        transport="streamable-http",
        host=config.server.host,
        port=config.server.port,
    )
