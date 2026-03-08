"""MCP tool implementations for the thetvdb-mcp-server server."""

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from thetvdb_mcp_server.config import AppConfig
from thetvdb_mcp_server.rate_limiter import tvdb_rate_limiter
from thetvdb_mcp_server.tvdb_client import TvdbClient

_client: TvdbClient | None = None
_EPISODE_FIELDS = {"aired", "number", "seasonNumber"}


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


def get_current_datetime(timezone: str) -> str:
    """Return the current date and time in the given IANA timezone.

    Use this tool when you need to know the current date or time, for example
    to determine whether a series is currently airing or to calculate how long
    ago an episode aired.

    Args:
        timezone: IANA timezone name, e.g. ``"America/Edmonton"``,
            ``"Europe/London"``, or ``"UTC"``.

    Returns:
        ISO 8601 datetime string with UTC offset, e.g.
        ``"2026-03-06T07:30:00-07:00"``.

    Raises:
        ValueError: If ``timezone`` is not a valid IANA timezone name.
    """
    try:
        tz = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        raise ValueError(f"Unknown timezone: {timezone!r}") from None
    return datetime.now(tz).isoformat()


def convert_datetime_timezone(
    input_datetime: str,
    input_timezone: str,
    output_timezone: str,
) -> dict[str, str]:
    """Convert a local datetime from one IANA timezone to another.

    Use this tool when you know an airtime in one timezone and need the
    equivalent local time elsewhere.

    Args:
        input_datetime: Local datetime in ISO 8601 format *without* a UTC offset,
            e.g. ``"2026-01-15T23:00:00"`` or ``"2026-01-15 23:00"``.
        input_timezone: IANA timezone for the input datetime, e.g. ``"Asia/Tokyo"``.
        output_timezone: IANA timezone to convert into, e.g. ``"America/Edmonton"``.

    Returns:
        A dict containing both the source and converted datetimes as ISO 8601
        strings with UTC offsets, plus timezone abbreviations.

    Raises:
        ValueError: If either timezone is invalid, if ``input_datetime`` is not
            parseable as ISO 8601, or if ``input_datetime`` already includes a
            UTC offset.
    """
    try:
        parsed_input = datetime.fromisoformat(input_datetime)
    except ValueError as exc:
        raise ValueError(
            "input_datetime must be a valid ISO 8601 date/time string, for example '2026-01-15T23:00:00'"
        ) from exc

    if parsed_input.tzinfo is not None:
        raise ValueError("input_datetime must not include a UTC offset; pass input_timezone separately")

    source_tz = _get_timezone(input_timezone)
    target_tz = _get_timezone(output_timezone)

    source_datetime = parsed_input.replace(tzinfo=source_tz)
    converted_datetime = source_datetime.astimezone(target_tz)

    return {
        "input_datetime": source_datetime.isoformat(),
        "input_timezone": input_timezone,
        "input_timezone_abbreviation": source_datetime.tzname() or input_timezone,
        "output_datetime": converted_datetime.isoformat(),
        "output_timezone": output_timezone,
        "output_timezone_abbreviation": converted_datetime.tzname() or output_timezone,
    }


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


async def tvdb_get_series_naming_bundle(
    series_id: int,
    season_type: str | None = None,
    lang: str | None = None,
) -> dict[str, Any] | list[dict[str, Any]]:
    """Fetch naming and episode data for a TV series from TVDB.

    This tool operates in two modes depending on whether ``season_type`` is
    provided.

    **Mode 1 — Series record** (``season_type`` omitted):
    Returns the series base record dict (identical to ``tvdb_get_series``).
    Use this when you need series-level metadata such as name, network, status,
    and genre without episode detail.

    **Mode 2 — Episode list** (``season_type`` provided, ``lang`` omitted):
    Returns a combined list of every episode dict across all pages for the
    requested season ordering. Pagination is handled automatically.

    **Mode 3 — Translated episode list** (``season_type`` and ``lang`` both
    provided):
    Same as Mode 2 but requests episode data translated into the specified
    language. Pagination is handled automatically.

    Args:
        series_id: Numeric TVDB series ID, e.g. ``78804`` for Doctor Who.
        season_type: Season ordering to use when fetching episodes. Omit for
            Mode 1 (series record). Valid values:

            - ``"official"`` — broadcast/streaming order (most common).
            - ``"dvd"`` — DVD release order; may differ from air order.
            - ``"absolute"`` — single sequential number across all seasons;
              common for anime.
            - ``"alternate"`` — an alternative ordering defined by the
              community.
            - ``"regional"`` — ordering used in a specific region.
            - ``"default"`` — the series default ordering as set on TVDB.
        lang: Two or three character language code (e.g. ``"eng"``, ``"deu"``)
            for translated episode data. Only used in Mode 3; ignored when
            ``season_type`` is omitted.

    Returns:
        - **Mode 1**: Series base record dict (see ``tvdb_get_series`` for
          field details).
        - **Mode 2 / Mode 3**: A flat list of episode dicts. Common fields
          include ``id``, ``name``, ``seasonNumber``, ``number``,
          ``aired``, and ``overview``.
    """
    assert _client is not None, "init_tools() must be called before using tools"

    if season_type is None:
        response = await _client.get(f"/series/{series_id}")
        return response["data"]  # type: ignore[return-value]

    episodes: list[dict[str, Any]] = []
    page = 0
    while True:
        if lang is not None:
            path = f"/series/{series_id}/episodes/{season_type}/{lang}"
        else:
            path = f"/series/{series_id}/episodes/{season_type}"
        response = await _client.get(path, params={"page": page})
        data = response.get("data", {})
        page_episodes: list[dict[str, Any]] = data.get("episodes", [])
        if not page_episodes:
            break
        episodes.extend(page_episodes)
        page += 1
    return [{k: v for k, v in ep.items() if k in _EPISODE_FIELDS} for ep in episodes]


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


def _get_timezone(timezone: str) -> ZoneInfo:
    """Return a ZoneInfo object for a valid IANA timezone name."""
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        raise ValueError(f"Unknown timezone: {timezone!r}") from None
