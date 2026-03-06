"""MCP tool implementations for the thetvdb-mcp-server server."""

from typing import Any

from thetvdb_mcp_server.config import AppConfig
from thetvdb_mcp_server.rate_limiter import tvdb_rate_limiter
from thetvdb_mcp_server.tvdb_client import TvdbClient

_client: TvdbClient | None = None


def init_tools(config: AppConfig) -> None:
    """Initialise the shared TVDB client from application configuration.

    Must be called once at startup before any TVDB tool is invoked.

    Args:
        config: Fully loaded application configuration.
    """
    global _client
    _client = TvdbClient(
        api_key=config.tvdb.api_key,
        pin=config.tvdb.pin,
        rate_limiter=tvdb_rate_limiter,
    )


def health_check() -> dict[str, str]:
    """Return a simple health status indicating the server is running.

    Returns:
        A dict with a single ``status`` key set to ``"ok"``.
    """
    return {"status": "ok"}


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
    assert _client is not None, "init_tools() must be called before using tools"
    response = await _client.get(f"/series/{series_id}")
    return response["data"]  # type: ignore[return-value]


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
    assert _client is not None, "init_tools() must be called before using tools"
    params: dict[str, Any] = {
        "q": query,
        "type": "series",
        "offset": offset,
        "limit": limit,
    }
    if year is not None:
        params["year"] = year
    response = await _client.get("/search", params=params)
    return response.get("data", [])  # type: ignore[return-value]
