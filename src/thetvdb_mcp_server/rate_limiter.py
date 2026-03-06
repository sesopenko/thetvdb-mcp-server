"""Async rate limiter for TVDB API calls.

Enforces a maximum call rate across all outbound requests to the TVDB API.
The module exports a single shared ``tvdb_rate_limiter`` instance for use
throughout the application.
"""

import asyncio
import time


class AsyncRateLimiter:
    """Async context manager that enforces a maximum call rate.

    Blocks on entry until enough time has elapsed since the last acquired
    slot. Uses ``asyncio.sleep`` exclusively; no threading primitives are
    used.

    Args:
        calls_per_second: Maximum number of calls allowed per second.
            Defaults to ``1.0``.
    """

    def __init__(self, calls_per_second: float = 1.0) -> None:
        self._min_interval = 1.0 / calls_per_second
        self._last_call_time: float = 0.0

    async def __aenter__(self) -> "AsyncRateLimiter":
        now = time.monotonic()
        elapsed = now - self._last_call_time
        wait = self._min_interval - elapsed
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_call_time = time.monotonic()
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass


tvdb_rate_limiter = AsyncRateLimiter()
