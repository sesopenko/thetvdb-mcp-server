"""Unit tests for TvdbClient."""

import base64
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from thetvdb_mcp_server.rate_limiter import AsyncRateLimiter
from thetvdb_mcp_server.tvdb_client import TvdbClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_jwt(exp: int) -> str:
    """Return a minimal JWT-like string with the given exp claim."""
    payload_bytes = json.dumps({"exp": exp}).encode()
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=").decode()
    return f"fakeheader.{payload_b64}.fakesig"


def fresh_jwt() -> str:
    return make_jwt(int(time.time()) + 7200)


def stale_jwt() -> str:
    return make_jwt(int(time.time()) + 300)


class SpyRateLimiter(AsyncRateLimiter):
    """Rate limiter subclass that counts how many times a slot is acquired."""

    def __init__(self) -> None:
        super().__init__(calls_per_second=1000.0)
        self.acquire_count = 0

    async def __aenter__(self) -> "SpyRateLimiter":
        self.acquire_count += 1
        await super().__aenter__()
        return self


def make_mock_http(
    post_token: str | None = None,
    get_side_effects: list | None = None,
) -> AsyncMock:
    """Return a mock httpx.AsyncClient instance.

    Args:
        post_token: JWT string the mock /login POST should return. Defaults
            to a fresh JWT.
        get_side_effects: List of mock responses for sequential GET calls.
            If ``None``, a single 200 success response is used.
    """
    if post_token is None:
        post_token = fresh_jwt()

    post_response = MagicMock()
    post_response.status_code = 200
    post_response.json.return_value = {"data": {"token": post_token}}
    post_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=post_response)

    if get_side_effects is None:
        ok_response = MagicMock()
        ok_response.status_code = 200
        ok_response.json.return_value = {"data": {"id": 1}}
        ok_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=ok_response)
    else:
        mock_client.get = AsyncMock(side_effect=get_side_effects)

    return mock_client


# ---------------------------------------------------------------------------
# _decode_exp
# ---------------------------------------------------------------------------


def test_decode_exp_parses_known_payload() -> None:
    """_decode_exp returns the exp value encoded in the JWT payload."""
    expected_exp = 1_700_000_000
    token = make_jwt(expected_exp)
    client = TvdbClient("key", None, AsyncRateLimiter())
    assert client._decode_exp(token) == expected_exp


# ---------------------------------------------------------------------------
# _token_is_fresh
# ---------------------------------------------------------------------------


def test_token_is_fresh_returns_false_when_no_token() -> None:
    """_token_is_fresh returns False when no token has been cached."""
    client = TvdbClient("key", None, AsyncRateLimiter())
    assert client._token_is_fresh() is False


def test_token_is_fresh_returns_false_when_expiring_soon() -> None:
    """_token_is_fresh returns False when the token expires in < 600 seconds."""
    client = TvdbClient("key", None, AsyncRateLimiter())
    client._token = stale_jwt()
    assert client._token_is_fresh() is False


def test_token_is_fresh_returns_true_when_well_within_validity() -> None:
    """_token_is_fresh returns True when the token expires in > 600 seconds."""
    client = TvdbClient("key", None, AsyncRateLimiter())
    client._token = fresh_jwt()
    assert client._token_is_fresh() is True


# ---------------------------------------------------------------------------
# get — authentication behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_authenticates_on_first_use() -> None:
    """get calls _authenticate when no token is cached."""
    spy = SpyRateLimiter()
    client = TvdbClient("key", None, spy)

    mock_http = make_mock_http()
    with patch("thetvdb_mcp_server.tvdb_client.httpx.AsyncClient", return_value=mock_http):
        await client.get("/series/1")

    mock_http.post.assert_called_once()


@pytest.mark.asyncio
async def test_get_does_not_reauthenticate_when_token_is_fresh() -> None:
    """get skips authentication when a fresh token is already cached."""
    spy = SpyRateLimiter()
    client = TvdbClient("key", None, spy)
    client._token = fresh_jwt()

    mock_http = make_mock_http()
    with patch("thetvdb_mcp_server.tvdb_client.httpx.AsyncClient", return_value=mock_http):
        await client.get("/series/1")

    mock_http.post.assert_not_called()


@pytest.mark.asyncio
async def test_get_reauthenticates_and_retries_on_401() -> None:
    """get re-authenticates once and retries the request on a 401 response."""
    spy = SpyRateLimiter()
    client = TvdbClient("key", None, spy)
    client._token = fresh_jwt()

    unauthorized = MagicMock()
    unauthorized.status_code = 401

    success = MagicMock()
    success.status_code = 200
    success.json.return_value = {"data": {"id": 42}}
    success.raise_for_status = MagicMock()

    mock_http = make_mock_http(get_side_effects=[unauthorized, success])
    with patch("thetvdb_mcp_server.tvdb_client.httpx.AsyncClient", return_value=mock_http):
        result = await client.get("/series/1")

    assert mock_http.post.call_count == 1
    assert mock_http.get.call_count == 2
    assert result == {"data": {"id": 42}}


# ---------------------------------------------------------------------------
# rate limiter acquisition
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rate_limiter_acquired_for_every_outbound_call() -> None:
    """Rate limiter is acquired for authentication and each data GET."""
    spy = SpyRateLimiter()
    client = TvdbClient("key", None, spy)
    # No cached token — first get will authenticate (1 limiter slot) then
    # make the data request (1 limiter slot), totalling 2 acquisitions.
    mock_http = make_mock_http()
    with patch("thetvdb_mcp_server.tvdb_client.httpx.AsyncClient", return_value=mock_http):
        await client.get("/series/1")

    assert spy.acquire_count == 2
