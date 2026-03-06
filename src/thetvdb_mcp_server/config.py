"""Configuration loading for the thetvdb-mcp-server server.

Reads a TOML config file and returns typed dataclass instances for each
section. The default config path is ``config.toml`` in the working directory;
pass ``--config <path>`` at the CLI to override.
"""

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ServerConfig:
    """Network binding settings for the MCP server."""

    host: str
    port: int


@dataclass
class LoggingConfig:
    """Logging behaviour settings."""

    level: str


@dataclass
class TvdbConfig:
    """TVDB API credentials."""

    api_key: str
    pin: str | None = None


@dataclass
class AppConfig:
    """Top-level application configuration, parsed from a TOML file."""

    server: ServerConfig
    logging: LoggingConfig
    tvdb: TvdbConfig


def load_config(path: Path = Path("config.toml")) -> AppConfig:
    """Load and validate application configuration from a TOML file.

    Args:
        path: Path to the TOML configuration file.
            Defaults to ``config.toml`` in the working directory.

    Returns:
        A fully populated :class:`AppConfig` instance.

    Raises:
        FileNotFoundError: If the config file does not exist at *path*.
        KeyError: If a required section or key is missing from the file.
        tomllib.TOMLDecodeError: If the file is not valid TOML.
    """
    with open(path, "rb") as f:
        raw = tomllib.load(f)

    server = ServerConfig(
        host=raw["server"]["host"],
        port=int(raw["server"]["port"]),
    )
    logging = LoggingConfig(
        level=raw["logging"]["level"],
    )
    tvdb_raw = raw["tvdb"]
    tvdb = TvdbConfig(
        api_key=tvdb_raw["api_key"],
        pin=tvdb_raw.get("pin"),
    )
    return AppConfig(server=server, logging=logging, tvdb=tvdb)
