"""Unit tests for the structured logging module."""

import json
from datetime import UTC, datetime
from typing import Any

import pytest

from mcp_base.logging import Logger, make_logger

# All severity levels in ascending order.
ALL_LEVELS = ["trace", "debug", "info", "warning", "error", "critical"]


# ── Helpers ────────────────────────────────────────────────────────────────────


def emit_at(logger: Logger, level: str, message: str, **metadata: object) -> None:
    """Call the logger method that matches *level*."""
    getattr(logger, level)(message, **metadata)


def captured_entries(capsys: pytest.CaptureFixture[str]) -> list[dict[str, Any]]:
    """Return all JSON entries written to stdout since the last capture."""
    out = capsys.readouterr().out
    return [json.loads(line) for line in out.splitlines() if line.strip()]


# ── Required fields ────────────────────────────────────────────────────────────


def test_entry_has_severity_field(capsys: pytest.CaptureFixture[str]) -> None:
    """Every emitted entry contains a 'severity' field."""
    logger = make_logger("trace")
    logger.info("hello")
    entries = captured_entries(capsys)
    assert len(entries) == 1
    assert "severity" in entries[0]


def test_entry_has_message_field(capsys: pytest.CaptureFixture[str]) -> None:
    """Every emitted entry contains a 'message' field."""
    logger = make_logger("trace")
    logger.info("hello")
    entries = captured_entries(capsys)
    assert entries[0]["message"] == "hello"


def test_entry_has_metadata_field(capsys: pytest.CaptureFixture[str]) -> None:
    """Every emitted entry contains a 'metadata' field, even when empty."""
    logger = make_logger("trace")
    logger.info("hello")
    entries = captured_entries(capsys)
    assert "metadata" in entries[0]


# ── Metadata content ───────────────────────────────────────────────────────────


def test_metadata_included_when_provided(capsys: pytest.CaptureFixture[str]) -> None:
    """Metadata key/value pairs passed as kwargs appear in the emitted entry."""
    logger = make_logger("trace")
    logger.info("event", tool="list_torrents", count=3)
    entries = captured_entries(capsys)
    assert entries[0]["metadata"] == {"tool": "list_torrents", "count": 3}


def test_metadata_empty_when_not_provided(capsys: pytest.CaptureFixture[str]) -> None:
    """Metadata is an empty dict when no kwargs are passed."""
    logger = make_logger("trace")
    logger.info("event")
    entries = captured_entries(capsys)
    assert entries[0]["metadata"] == {}


# ── Severity field value ───────────────────────────────────────────────────────


@pytest.mark.parametrize("level", ALL_LEVELS)
def test_severity_field_matches_level(level: str, capsys: pytest.CaptureFixture[str]) -> None:
    """The 'severity' field in the emitted entry matches the method called."""
    logger = make_logger("trace")
    emit_at(logger, level, "msg")
    entries = captured_entries(capsys)
    assert entries[0]["severity"] == level


# ── Level filtering ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("level", ALL_LEVELS)
def test_entry_at_configured_level_is_emitted(level: str, capsys: pytest.CaptureFixture[str]) -> None:
    """An entry at exactly the configured minimum level is emitted."""
    logger = make_logger(level)
    emit_at(logger, level, "msg")
    assert len(captured_entries(capsys)) == 1


@pytest.mark.parametrize(
    "configured, emitted",
    [
        ("debug", "trace"),
        ("info", "trace"),
        ("info", "debug"),
        ("warning", "info"),
        ("error", "warning"),
        ("critical", "error"),
    ],
)
def test_entry_below_configured_level_is_suppressed(
    configured: str,
    emitted: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An entry whose severity is below the configured minimum is not written."""
    logger = make_logger(configured)
    emit_at(logger, emitted, "msg")
    assert captured_entries(capsys) == []


@pytest.mark.parametrize(
    "configured, emitted",
    [
        ("debug", "info"),
        ("info", "warning"),
        ("warning", "error"),
        ("error", "critical"),
    ],
)
def test_entry_above_configured_level_is_emitted(
    configured: str,
    emitted: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An entry whose severity is above the configured minimum is emitted."""
    logger = make_logger(configured)
    emit_at(logger, emitted, "msg")
    assert len(captured_entries(capsys)) == 1


# ── make_logger factory ────────────────────────────────────────────────────────


def test_make_logger_returns_logger_instance() -> None:
    """make_logger returns a Logger instance."""
    assert isinstance(make_logger("info"), Logger)


def test_make_logger_invalid_level_raises() -> None:
    """make_logger raises ValueError for an unrecognised level string."""
    with pytest.raises(ValueError):
        make_logger("verbose")


def test_logger_invalid_level_raises() -> None:
    """Logger.__init__ raises ValueError for an unrecognised level string."""
    with pytest.raises(ValueError):
        Logger("loud")


# ── Non-serializable metadata ──────────────────────────────────────────────────


def test_metadata_datetime_does_not_raise(capsys: pytest.CaptureFixture[str]) -> None:
    """datetime values in metadata are serialized without raising TypeError."""
    logger = make_logger("trace")
    logger.info("event", ts=datetime(2026, 1, 1, tzinfo=UTC))
    entries = captured_entries(capsys)
    assert len(entries) == 1


def test_metadata_exception_does_not_raise(capsys: pytest.CaptureFixture[str]) -> None:
    """Exception objects in metadata are serialized without raising TypeError."""
    logger = make_logger("trace")
    logger.error("boom", exc=ValueError("something went wrong"))
    entries = captured_entries(capsys)
    assert len(entries) == 1


def test_metadata_bytes_does_not_raise(capsys: pytest.CaptureFixture[str]) -> None:
    """bytes values in metadata are serialized without raising TypeError."""
    logger = make_logger("trace")
    logger.debug("raw", data=b"\xff\xfe")
    entries = captured_entries(capsys)
    assert len(entries) == 1


def test_metadata_non_serializable_value_is_stringified(capsys: pytest.CaptureFixture[str]) -> None:
    """Non-JSON-serializable metadata values are converted to their str() representation."""
    logger = make_logger("trace")
    exc = ValueError("oops")
    logger.error("event", exc=exc)
    entries = captured_entries(capsys)
    assert entries[0]["metadata"]["exc"] == str(exc)


# ── Output format ──────────────────────────────────────────────────────────────


def test_output_is_valid_json(capsys: pytest.CaptureFixture[str]) -> None:
    """Each line of stdout output is valid JSON."""
    logger = make_logger("trace")
    for level in ALL_LEVELS:
        emit_at(logger, level, "msg")
    out = capsys.readouterr().out
    for line in out.splitlines():
        json.loads(line)  # raises if invalid


def test_each_entry_on_separate_line(capsys: pytest.CaptureFixture[str]) -> None:
    """Multiple entries are written one per line."""
    logger = make_logger("trace")
    logger.info("first")
    logger.info("second")
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if line.strip()]
    assert len(lines) == 2
