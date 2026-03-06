"""Unit tests for MCP tool implementations."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import thetvdb_mcp_server.tools as tools_module
from thetvdb_mcp_server.tools import health_check, tvdb_get_series, tvdb_search_series


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
