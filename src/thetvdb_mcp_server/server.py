"""FastMCP server entrypoint for the thetvdb-mcp-server server.

Run with::

    uv run python -m thetvdb_mcp_server

or via the installed script::

    thetvdb-mcp-server
"""

import argparse
from pathlib import Path
from typing import Any

import fastmcp

from thetvdb_mcp_server.config import load_config
from thetvdb_mcp_server.logging import Logger, make_logger
from thetvdb_mcp_server.tools import health_check as _health_check
from thetvdb_mcp_server.tools import init_tools
from thetvdb_mcp_server.tools import tvdb_get_series as _tvdb_get_series
from thetvdb_mcp_server.tools import tvdb_search_series as _tvdb_search_series

mcp = fastmcp.FastMCP("thetvdb-mcp-server")

_logger: Logger | None = None


@mcp.tool()
def health_check() -> dict[str, str]:
    """Return a simple health status indicating the server is running.

    Returns:
        A dict with a single ``status`` key set to ``"ok"``.
    """
    return _health_check()


@mcp.tool()
async def tvdb_search_series(
    query: str,
    year: int | None = None,
    offset: int = 0,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search TVDB for TV series matching a query string.

    Use this tool to find a series by title, alias, or translation. It is the
    first step when you need a TVDB series ID before fetching full series
    details or episode lists.

    Args:
        query: Search string. Matched against series titles, aliases, and
            translations across all languages. Required.
        year: Optional four-digit year to restrict results to series that
            first aired in that year. Omit to search all years.
        offset: Number of results to skip, for pagination. Defaults to ``0``.
        limit: Maximum number of results to return. Defaults to ``10``.
            The TVDB search index supports up to 5 000 results total.

    Returns:
        A list of series result dicts from the TVDB ``data`` field. Common
        fields in each dict include ``objectID``, ``name``, ``first_air_time``,
        ``image_url``, ``overview``, ``status``, and ``tvdb_id``.
    """
    return await _tvdb_search_series(query=query, year=year, offset=offset, limit=limit)


@mcp.tool()
async def tvdb_get_series(series_id: int) -> dict[str, Any]:
    """Fetch the base record for a single TV series by its TVDB ID.

    Use this tool when you already know the TVDB series ID and need the full
    series record, including network, status, genres, and image information.
    To find a series ID first, use ``tvdb_search_series``.

    Args:
        series_id: Numeric TVDB series ID, e.g. ``78804`` for Doctor Who.

    Returns:
        The series base record dict from the TVDB ``data`` field. Common fields
        include ``id``, ``name``, ``slug``, ``image``, ``firstAired``,
        ``lastAired``, ``status``, ``originalNetwork``, and ``genres``.
    """
    return await _tvdb_get_series(series_id=series_id)


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

    init_tools(config)

    mcp.run(
        transport="streamable-http",
        host=config.server.host,
        port=config.server.port,
    )
