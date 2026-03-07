<!-- This file is copy-pasted into Docker Hub as the repository overview.
     It is NOT developer documentation. Do not read this for project context.
     Edit it only when tools, config, Docker Compose examples, or endpoints change. -->
# thetvdb-mcp-server

A [FastMCP](https://github.com/jlowin/fastmcp) server that exposes [TVDB](https://thetvdb.com/) TV series data to AI assistants via the Model Context Protocol.

[MCP (Model Context Protocol)](https://modelcontextprotocol.io/) is an open standard that lets AI assistants call external tools and services. This server implements MCP over HTTP so any MCP-compatible AI application can query TV series information from TVDB.

GitHub: [sesopenko/thetvdb-mcp-server](https://github.com/sesopenko/thetvdb-mcp-server)

---

## Quick Start

### Docker Compose

1. Create a `docker-compose.yml`:

   ```yaml
   services:
     thetvdb-mcp-server:
       image: sesopenko/thetvdb-mcp-server:latest
       ports:
         - "8080:8080"
       volumes:
         - ./config.toml:/config/config.toml:ro
       restart: unless-stopped
   ```

2. Copy the example config and edit it:

   ```bash
   cp config.toml.example config.toml
   ```

3. Start the server:

   ```bash
   docker compose up -d
   ```

---

## Configuration

Create a `config.toml` in the working directory (or pass `--config <path>`):

```toml
[server]
host = "0.0.0.0"  # address the MCP server listens on (0.0.0.0 = all interfaces)
port = 8080        # port the MCP server listens on

[logging]
level = "info"     # log verbosity: debug, info, warning, error

[tvdb]
api_key = "your-api-key-here"  # TVDB API key from https://thetvdb.com/dashboard/account/apikey (required)
pin = ""                        # subscriber PIN for extended access; omit or leave blank if not applicable
```

---

## Connecting an AI Application

Point your MCP-compatible AI application at the server's MCP endpoint:

```
http://<host>:<port>/mcp
```

For example, if the server is running on `192.168.1.10` with the default port:

```
http://192.168.1.10:8080/mcp
```

Consult your AI application's documentation for how to register an MCP server.

---

## Available Tools

| Tool | Description |
|---|---|
| `health_check` | Returns `{"status": "ok"}` to confirm the server is running. |
| `tvdb_search_series` | Search TVDB for TV series by title, with optional year filter and pagination. |
| `tvdb_get_series` | Fetch the full base record for a TV series by its TVDB ID. |
| `tvdb_get_series_naming_bundle` | Fetch series metadata or a complete paginated episode list for a given season ordering. |
| `get_current_datetime` | Returns the current date and time for a given IANA timezone as an ISO 8601 string. |
| `convert_datetime_timezone` | Converts a time from one IANA timezone to IANA another.|

---

## Example System Prompt

Copy and adapt this prompt to give your AI assistant clear guidance on using the tools.

```xml
<system>
  <role>
    You are a helpful assistant with access to a TVDB MCP server. Use the available
    tools to look up TV series information accurately and efficiently.
  </role>
  <tools>
    <tool name="health_check">Check that the MCP server is running and reachable.</tool>
    <tool name="tvdb_search_series">Search TVDB for TV series by title. Returns a list of matching series records including TVDB IDs. Supports optional year filtering and pagination.</tool>
    <tool name="tvdb_get_series">Fetch the full base record for a TV series by its TVDB ID, including network, status, genres, and image information.</tool>
    <tool name="tvdb_get_series_naming_bundle">Fetch series metadata (when season_type is omitted) or a complete paginated episode list for a given season ordering and optional language.</tool>
    <tool name="get_current_datetime">Return the current date and time for a given IANA timezone (e.g. "UTC", "America/Edmonton") as an ISO 8601 string. Use this to anchor time-sensitive queries such as whether a series is still airing.</tool>
  </tools>
  <guidelines>
    <item>Call health_check if the user asks whether the server is available.</item>
    <item>Use tvdb_search_series to find a series TVDB ID before calling tvdb_get_series or tvdb_get_series_naming_bundle.</item>
    <item>Use tvdb_get_series when the user needs series-level details such as network, status, or genre.</item>
    <item>Use tvdb_get_series_naming_bundle to retrieve episode lists; specify season_type (e.g. "official") and lang as needed.</item>
    <item>Use get_current_datetime (with the user's local timezone if known, otherwise "UTC") when you need the current date or time to answer questions about airing schedules or episode recency.</item>
  </guidelines>
</system>
```

---

## License

Copyright (c) Sean Esopenko 2026

Licensed under the [GNU General Public License v3.0](https://github.com/sesopenko/thetvdb-mcp-server/blob/main/LICENSE.txt).

---

## Acknowledgement: Riding on the Backs of Giants

This project was built with the assistance of [Claude Code](https://claude.ai/code), an AI coding assistant developed by Anthropic.

AI assistants like Claude are trained on enormous amounts of data — much of it written by the open-source community: the libraries, tools, documentation, and decades of shared knowledge that developers have contributed freely. Without that foundation, tools like this would not be possible.

In recognition of that debt, this project is released under the [GNU General Public License v3.0](https://github.com/sesopenko/thetvdb-mcp-server/blob/main/LICENSE.txt). The GPL ensures that this code — and any derivative work — remains open source. It is a small act of reciprocity: giving back to the commons that made it possible.

To every developer who ever pushed a commit to a public repo, wrote a Stack Overflow answer, or published a package under an open license — thank you.
