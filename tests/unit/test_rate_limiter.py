"""Unit tests for AsyncRateLimiter."""

import time

import pytest

from thetvdb_mcp_server.rate_limiter import AsyncRateLimiter


@pytest.mark.asyncio
async def test_single_acquire_completes_without_delay() -> None:
    """First acquire on a fresh limiter completes immediately."""
    limiter = AsyncRateLimiter(calls_per_second=10.0)
    start = time.monotonic()
    async with limiter:
        pass
    elapsed = time.monotonic() - start
    # Should complete well under one interval (0.1 s)
    assert elapsed < 0.05


@pytest.mark.asyncio
async def test_two_sequential_acquires_are_separated_by_interval() -> None:
    """Two sequential acquires are separated by at least 1/calls_per_second seconds."""
    calls_per_second = 10.0
    min_interval = 1.0 / calls_per_second
    limiter = AsyncRateLimiter(calls_per_second=calls_per_second)

    async with limiter:
        pass

    start = time.monotonic()
    async with limiter:
        pass
    elapsed = time.monotonic() - start

    assert elapsed >= min_interval * 0.9  # allow 10% tolerance


@pytest.mark.asyncio
async def test_limiter_is_reusable() -> None:
    """Limiter can be acquired multiple times without error."""
    limiter = AsyncRateLimiter(calls_per_second=100.0)
    for _ in range(3):
        async with limiter:
            pass
