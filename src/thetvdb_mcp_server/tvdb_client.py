"""TVDB API client with transparent authentication and rate limiting."""

import base64
import json
import time

import httpx

from thetvdb_mcp_server.rate_limiter import AsyncRateLimiter

_BASE_URL = "https://api4.thetvdb.com/v4"


class TvdbClient:
    """HTTP client for the TVDB v4 API.

    Handles JWT authentication transparently, including token caching,
    proactive refresh before expiry, and automatic 401 retry. All outbound
    requests (authentication and data) pass through the provided rate limiter.

    Args:
        api_key: TVDB API key obtained from the TVDB developer portal.
        pin: Optional subscriber PIN for extended access. Pass ``None``
            if not applicable.
        rate_limiter: Shared rate limiter instance used to throttle all
            outbound calls.
    """

    def __init__(self, api_key: str, pin: str | None, rate_limiter: AsyncRateLimiter) -> None:
        self._api_key = api_key
        self._pin = pin
        self._rate_limiter = rate_limiter
        self._token: str | None = None

    async def _authenticate(self) -> None:
        payload: dict[str, str] = {"apikey": self._api_key}
        if self._pin is not None:
            payload["pin"] = self._pin
        async with self._rate_limiter:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{_BASE_URL}/login", json=payload)
                response.raise_for_status()
                body = response.json()
        self._token = body["data"]["token"]

    def _decode_exp(self, token: str) -> int:
        payload_b64 = token.split(".")[1]
        padding = (4 - len(payload_b64) % 4) % 4
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + "=" * padding)
        payload = json.loads(payload_bytes)
        return int(payload["exp"])

    def _token_is_fresh(self) -> bool:
        if self._token is None:
            return False
        return self._decode_exp(self._token) - time.time() > 600

    async def _ensure_token(self) -> None:
        if not self._token_is_fresh():
            await self._authenticate()

    async def get(self, path: str, params: dict | None = None) -> dict:  # type: ignore[type-arg]
        """Fetch a TVDB API resource.

        Ensures a valid bearer token is available before making the request.
        On a 401 response, re-authenticates once and retries. Every outbound
        call (authentication and data) passes through the rate limiter.

        Args:
            path: API path relative to ``https://api4.thetvdb.com/v4``,
                e.g. ``/series/78804``.
            params: Optional query parameters to include in the request.

        Returns:
            The parsed JSON response body as a dictionary.

        Raises:
            httpx.HTTPStatusError: If the response status is non-2xx (other
                than a handled 401 that is successfully retried).
        """
        await self._ensure_token()

        async with self._rate_limiter:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{_BASE_URL}{path}",
                    headers={"Authorization": f"Bearer {self._token}"},
                    params=params,
                )

        if response.status_code == 401:
            await self._authenticate()
            async with self._rate_limiter:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{_BASE_URL}{path}",
                        headers={"Authorization": f"Bearer {self._token}"},
                        params=params,
                    )

        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]
