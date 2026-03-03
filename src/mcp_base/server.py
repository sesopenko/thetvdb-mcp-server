"""FastMCP server entrypoint for the mcp-base server.

Run with::

    uv run python -m mcp_base

or via the installed script::

    mcp-base
"""

import argparse
from pathlib import Path

import fastmcp

from mcp_base.config import load_config
from mcp_base.logging import Logger, make_logger
from mcp_base.tools import health_check as _health_check

mcp = fastmcp.FastMCP("mcp-base")

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
    parser = argparse.ArgumentParser(description="mcp-base MCP server")
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
