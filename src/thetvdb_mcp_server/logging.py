"""Structured logging for the Transmission MCP server.

Every log entry is written to stdout as a JSON object with three fields:
``severity``, ``message``, and ``metadata``. Entries whose severity is below
the configured minimum level are silently suppressed.
"""

import json
import sys
from typing import Any

# Ordered from lowest to highest severity.
_LEVELS: list[str] = ["trace", "debug", "info", "warning", "error", "critical"]


def _level_index(level: str) -> int:
    try:
        return _LEVELS.index(level.lower())
    except ValueError:
        raise ValueError(f"Unknown log level: {level!r}. Must be one of {_LEVELS}.") from None


class Logger:
    """Structured logger that writes JSON entries to stdout.

    Each emitted entry is a JSON object on a single line with the keys
    ``severity``, ``message``, and ``metadata``.  Entries whose severity
    falls below the configured minimum are dropped before any I/O occurs.
    """

    def __init__(self, level: str) -> None:
        """Initialise the logger.

        Args:
            level: Minimum severity level to emit. Case-insensitive. Must be
                one of ``trace``, ``debug``, ``info``, ``warning``, ``error``,
                ``critical``.

        Raises:
            ValueError: If *level* is not a recognised severity name.
        """
        self._min_index: int = _level_index(level)

    def _emit(self, severity: str, message: str, metadata: dict[str, Any]) -> None:
        severity = severity.lower()
        if _level_index(severity) < self._min_index:
            return
        entry: dict[str, Any] = {
            "severity": severity,
            "message": message,
            "metadata": metadata,
        }
        print(json.dumps(entry, default=str), file=sys.stdout, flush=True)

    def trace(self, message: str, **metadata: Any) -> None:
        """Emit a trace-level log entry.

        Args:
            message: Human-readable description of the event.
            **metadata: Arbitrary key/value pairs attached to the entry.
        """
        self._emit("trace", message, metadata)

    def debug(self, message: str, **metadata: Any) -> None:
        """Emit a debug-level log entry.

        Args:
            message: Human-readable description of the event.
            **metadata: Arbitrary key/value pairs attached to the entry.
        """
        self._emit("debug", message, metadata)

    def info(self, message: str, **metadata: Any) -> None:
        """Emit an info-level log entry.

        Args:
            message: Human-readable description of the event.
            **metadata: Arbitrary key/value pairs attached to the entry.
        """
        self._emit("info", message, metadata)

    def warning(self, message: str, **metadata: Any) -> None:
        """Emit a warning-level log entry.

        Args:
            message: Human-readable description of the event.
            **metadata: Arbitrary key/value pairs attached to the entry.
        """
        self._emit("warning", message, metadata)

    def error(self, message: str, **metadata: Any) -> None:
        """Emit an error-level log entry.

        Args:
            message: Human-readable description of the event.
            **metadata: Arbitrary key/value pairs attached to the entry.
        """
        self._emit("error", message, metadata)

    def critical(self, message: str, **metadata: Any) -> None:
        """Emit a critical-level log entry.

        Args:
            message: Human-readable description of the event.
            **metadata: Arbitrary key/value pairs attached to the entry.
        """
        self._emit("critical", message, metadata)


def make_logger(level: str) -> Logger:
    """Create a Logger configured to emit at *level* and above.

    Args:
        level: Minimum severity level to emit. Case-insensitive. Must be one
            of ``trace``, ``debug``, ``info``, ``warning``, ``error``,
            ``critical``.

    Returns:
        A :class:`Logger` instance ready for use.

    Raises:
        ValueError: If *level* is not a recognised severity name.
    """
    return Logger(level)
