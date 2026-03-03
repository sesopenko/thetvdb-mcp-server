"""Unit tests for MCP tool implementations."""

from mcp_base.tools import health_check


def test_health_check_returns_ok() -> None:
    """health_check returns {"status": "ok"}."""
    result = health_check()
    assert result == {"status": "ok"}
