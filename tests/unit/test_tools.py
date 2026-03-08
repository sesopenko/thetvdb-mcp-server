"""Unit tests for MCP tool implementations."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import thetvdb_mcp_server.tools as tools_module
from thetvdb_mcp_server.tools import (
    convert_datetime_timezone,
    get_current_datetime,
    health_check,
    tvdb_get_series,
    tvdb_get_series_naming_bundle,
    tvdb_search_series,
)


def test_get_current_datetime_returns_iso_string() -> None:
    """get_current_datetime returns a string parseable by datetime.fromisoformat."""
    result = get_current_datetime("UTC")
    parsed = datetime.fromisoformat(result)
    assert parsed is not None


def test_get_current_datetime_offset_matches_timezone() -> None:
    """get_current_datetime returns +00:00 offset for UTC."""
    result = get_current_datetime("UTC")
    parsed = datetime.fromisoformat(result)
    assert parsed.utcoffset() == UTC.utcoffset(None)


def test_get_current_datetime_invalid_timezone_raises_value_error() -> None:
    """get_current_datetime raises ValueError for an unknown timezone name."""
    with pytest.raises(ValueError, match="Unknown timezone"):
        get_current_datetime("Not/ATimezone")


def test_convert_datetime_timezone_tokyo_to_edmonton() -> None:
    """convert_datetime_timezone converts Tokyo time to Edmonton time."""
    result = convert_datetime_timezone(
        input_datetime="2026-01-15T23:00:00",
        input_timezone="Asia/Tokyo",
        output_timezone="America/Edmonton",
    )

    assert result == {
        "input_datetime": "2026-01-15T23:00:00+09:00",
        "input_timezone": "Asia/Tokyo",
        "input_timezone_abbreviation": "JST",
        "output_datetime": "2026-01-15T07:00:00-07:00",
        "output_timezone": "America/Edmonton",
        "output_timezone_abbreviation": "MST",
    }


def test_convert_datetime_timezone_invalid_input_timezone_raises_value_error() -> None:
    """convert_datetime_timezone raises ValueError for an unknown input timezone."""
    with pytest.raises(ValueError, match="Unknown timezone"):
        convert_datetime_timezone(
            input_datetime="2026-01-15T23:00:00",
            input_timezone="Not/ARealTimezone",
            output_timezone="America/Edmonton",
        )


def test_convert_datetime_timezone_rejects_offset_aware_input() -> None:
    """convert_datetime_timezone rejects input datetimes that already include an offset."""
    with pytest.raises(ValueError, match="must not include a UTC offset"):
        convert_datetime_timezone(
            input_datetime="2026-01-15T23:00:00+09:00",
            input_timezone="Asia/Tokyo",
            output_timezone="America/Edmonton",
        )


def test_health_check_returns_ok() -> None:
    """health_check returns {"status": "ok"}."""
    result = health_check()
    assert result == {"status": "ok"}


def _make_mock_client(response_data: Any) -> MagicMock:
    """Return a mock TvdbClient whose get() returns response_data."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=response_data)
    return mock_client


@pytest.mark.asyncio
async def test_tvdb_get_series_returns_data_dict() -> None:
    """tvdb_get_series returns the data dict from the TVDB response."""
    series_data = {"id": 78804, "name": "Doctor Who", "slug": "doctor-who"}
    mock_client = _make_mock_client({"data": series_data, "status": "success"})

    with patch.object(tools_module, "_client", mock_client):
        result = await tvdb_get_series(series_id=78804)

    assert result == series_data


@pytest.mark.asyncio
async def test_tvdb_get_series_passes_correct_id_in_path() -> None:
    """tvdb_get_series includes the series ID in the request path."""
    mock_client = _make_mock_client({"data": {"id": 12345}, "status": "success"})

    with patch.object(tools_module, "_client", mock_client):
        await tvdb_get_series(series_id=12345)

    mock_client.get.assert_awaited_once_with("/series/12345")


@pytest.mark.asyncio
async def test_tvdb_get_series_naming_bundle_mode1_returns_series_dict() -> None:
    """Mode 1: returns the series dict when season_type is omitted."""
    series_data = {"id": 78804, "name": "Doctor Who"}
    mock_client = _make_mock_client({"data": series_data, "status": "success"})

    with patch.object(tools_module, "_client", mock_client):
        result = await tvdb_get_series_naming_bundle(series_id=78804)

    assert result == series_data
    mock_client.get.assert_awaited_once_with("/series/78804")


@pytest.mark.asyncio
async def test_tvdb_get_series_naming_bundle_mode1_ignores_lang() -> None:
    """Mode 1: lang is ignored when season_type is omitted."""
    series_data = {"id": 78804, "name": "Doctor Who"}
    mock_client = _make_mock_client({"data": series_data, "status": "success"})

    with patch.object(tools_module, "_client", mock_client):
        result = await tvdb_get_series_naming_bundle(series_id=78804, lang="eng")

    assert result == series_data
    mock_client.get.assert_awaited_once_with("/series/78804")


@pytest.mark.asyncio
async def test_tvdb_get_series_naming_bundle_mode2_single_page() -> None:
    """Mode 2: returns combined episode list from a single-page response."""
    ep1 = {
        "id": 1,
        "name": "Pilot",
        "aired": "2020-01-01",
        "number": 1,
        "seasonNumber": 1,
        "image": "image_url",
        "overview": "An overview",
    }
    ep2 = {
        "id": 2,
        "name": "Episode 2",
        "aired": "2020-01-08",
        "number": 2,
        "seasonNumber": 1,
        "image": "image_url_2",
        "overview": "Another overview",
    }
    # First call returns episodes, second call returns empty to stop pagination.
    mock_client = MagicMock()
    mock_client.get = AsyncMock(
        side_effect=[
            {"data": {"episodes": [ep1, ep2]}},
            {"data": {"episodes": []}},
        ]
    )

    with patch.object(tools_module, "_client", mock_client):
        result = await tvdb_get_series_naming_bundle(series_id=100, season_type="official")

    expected = [
        {"aired": "2020-01-01", "number": 1, "seasonNumber": 1},
        {"aired": "2020-01-08", "number": 2, "seasonNumber": 1},
    ]
    assert result == expected


@pytest.mark.asyncio
async def test_tvdb_get_series_naming_bundle_mode2_multi_page() -> None:
    """Mode 2: returns combined episode list across multiple pages."""
    ep1 = {
        "id": 1,
        "name": "Pilot",
        "aired": "2020-01-01",
        "number": 1,
        "seasonNumber": 1,
        "image": "image_url",
        "overview": "An overview",
    }
    ep2 = {
        "id": 2,
        "name": "Episode 2",
        "aired": "2020-01-08",
        "number": 2,
        "seasonNumber": 1,
        "image": "image_url_2",
        "overview": "Another overview",
    }
    ep3 = {
        "id": 3,
        "name": "Episode 3",
        "aired": "2020-01-15",
        "number": 3,
        "seasonNumber": 1,
        "image": "image_url_3",
        "overview": "Yet another overview",
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(
        side_effect=[
            {"data": {"episodes": [ep1, ep2]}},
            {"data": {"episodes": [ep3]}},
            {"data": {"episodes": []}},
        ]
    )

    with patch.object(tools_module, "_client", mock_client):
        result = await tvdb_get_series_naming_bundle(series_id=100, season_type="official")

    expected = [
        {"aired": "2020-01-01", "number": 1, "seasonNumber": 1},
        {"aired": "2020-01-08", "number": 2, "seasonNumber": 1},
        {"aired": "2020-01-15", "number": 3, "seasonNumber": 1},
    ]
    assert result == expected
    assert mock_client.get.await_count == 3


@pytest.mark.asyncio
async def test_tvdb_get_series_naming_bundle_mode3_includes_lang_in_path() -> None:
    """Mode 3: language code is included in the request path."""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(
        side_effect=[
            {"data": {"episodes": [{"id": 1}]}},
            {"data": {"episodes": []}},
        ]
    )

    with patch.object(tools_module, "_client", mock_client):
        await tvdb_get_series_naming_bundle(series_id=200, season_type="official", lang="eng")

    first_call_path = mock_client.get.call_args_list[0][0][0]
    assert first_call_path == "/series/200/episodes/official/eng"


@pytest.mark.asyncio
async def test_tvdb_get_series_naming_bundle_strips_extra_fields() -> None:
    """Returns only aired, number, and seasonNumber for each episode."""
    episode_with_many_fields = {
        "id": 999,
        "tvdb_id": "999",
        "name": "Test Episode",
        "aired": "2020-05-15",
        "number": 5,
        "seasonNumber": 2,
        "image": "https://example.com/image.jpg",
        "overview": "A detailed episode overview",
        "runtime": 45,
        "type": "standard",
        "status": "aired",
    }
    mock_client = MagicMock()
    mock_client.get = AsyncMock(
        side_effect=[
            {"data": {"episodes": [episode_with_many_fields]}},
            {"data": {"episodes": []}},
        ]
    )

    with patch.object(tools_module, "_client", mock_client):
        result = await tvdb_get_series_naming_bundle(series_id=100, season_type="official")

    assert result == [{"aired": "2020-05-15", "number": 5, "seasonNumber": 2}]
    # Verify no extra fields are present.
    assert len(result[0]) == 3


@pytest.mark.asyncio
async def test_tvdb_search_series_returns_results() -> None:
    """tvdb_search_series returns the list from the data field."""
    series_list = [{"tvdb_id": "1", "name": "Breaking Bad"}]
    mock_client = _make_mock_client({"data": series_list, "status": "success"})

    with patch.object(tools_module, "_client", mock_client):
        result = await tvdb_search_series(query="Breaking Bad")

    assert result == series_list


@pytest.mark.asyncio
async def test_tvdb_search_series_returns_empty_list_when_data_empty() -> None:
    """tvdb_search_series returns an empty list when data is empty."""
    mock_client = _make_mock_client({"data": [], "status": "success"})

    with patch.object(tools_module, "_client", mock_client):
        result = await tvdb_search_series(query="Nonexistent Series")

    assert result == []


@pytest.mark.asyncio
async def test_tvdb_search_series_omits_year_when_not_provided() -> None:
    """tvdb_search_series does not include year param when year is None."""
    mock_client = _make_mock_client({"data": []})

    with patch.object(tools_module, "_client", mock_client):
        await tvdb_search_series(query="Firefly")

    call_kwargs = mock_client.get.call_args
    params = call_kwargs[1]["params"] if call_kwargs[1] else call_kwargs[0][1]
    assert "year" not in params


@pytest.mark.asyncio
async def test_tvdb_search_series_includes_year_when_provided() -> None:
    """tvdb_search_series includes year param when year is given."""
    mock_client = _make_mock_client({"data": []})

    with patch.object(tools_module, "_client", mock_client):
        await tvdb_search_series(query="Firefly", year=2002)

    call_kwargs = mock_client.get.call_args
    params = call_kwargs[1]["params"] if call_kwargs[1] else call_kwargs[0][1]
    assert params["year"] == 2002


@pytest.mark.asyncio
async def test_tvdb_search_series_offset_and_limit_passed_to_api() -> None:
    """tvdb_search_series passes offset and limit directly to the API."""
    mock_client = _make_mock_client({"data": []})

    with patch.object(tools_module, "_client", mock_client):
        await tvdb_search_series(query="Lost", offset=20, limit=5)

    call_kwargs = mock_client.get.call_args
    params = call_kwargs[1]["params"] if call_kwargs[1] else call_kwargs[0][1]
    assert params["offset"] == 20
    assert params["limit"] == 5
