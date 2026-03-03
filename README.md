# mcp-base

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE.txt)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/downloads/)

A bare-bones [FastMCP](https://github.com/jlowin/fastmcp) server template. Use this as a starting point to build your own MCP server without starting from scratch.

[MCP (Model Context Protocol)](https://modelcontextprotocol.io/) is an open standard that lets AI assistants call external tools and services. This template implements MCP over HTTP so any MCP-compatible AI application can reach your server.

---

## Prerequisites

- **Docker** — for the Docker Compose deployment path
- **uv** — for the source deployment path (see [Installing uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Node.js** — required for the git commit hooks; the hooks use [commitlint](https://commitlint.js.org/) to enforce Conventional Commits, which is the best-in-class Node.js tool for commit message validation

---

## Customising the Template

### 1. Copy the template

**On GitHub** — click **Use this template → Create a new repository**. This creates a clean copy with no fork relationship and no template history.

**Without GitHub** — clone, strip the history, and reinitialise:

```bash
git clone https://github.com/sesopenko/mcp-base.git my-project
cd my-project
rm -rf .git
git init
git add .
git commit -m "chore: bootstrap from mcp-base template"
```

### 2. Customise identity values

Edit `project.env` to set your own values (Docker image name, package name, project name, description), then run the setup script to substitute them throughout the repository:

```bash
bash scripts/apply-project-config.sh
```

The script is idempotent — safe to run multiple times.

---

## Quick Start

### Option A — Docker Compose

1. Create a `docker-compose.yml`:

   ```yaml
   services:
     mcp-base:
       image: sesopenko/mcp-base:latest
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

### Option B — Run from Source

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) if you haven't already.

2. Install dependencies:

   ```bash
   uv sync
   ```

3. Copy the example config and edit it:

   ```bash
   cp config.toml.example config.toml
   ```

4. Start the server:

   ```bash
   uv run python -m mcp_base
   ```

---

## Security

This server has **no authentication** on its MCP endpoint. It is designed for LAN use only.

**Do not expose this server directly to the internet.**

If you need to access it remotely, place it behind a reverse proxy that handles TLS termination and access control. Configuring a reverse proxy is outside the scope of this project.

---

## Configuration

Create a `config.toml` in the working directory (or pass `--config <path>`):

```toml
[server]
host = "0.0.0.0"
port = 8080

[logging]
level = "info"
```

### [server]

| Key | Default | Description |
|---|---|---|
| `host` | `"0.0.0.0"` | Address the MCP server listens on. `0.0.0.0` binds all interfaces. |
| `port` | `8080` | Port the MCP server listens on. |

### [logging]

| Key | Default | Description |
|---|---|---|
| `level` | `"info"` | Log verbosity. One of: `debug`, `info`, `warning`, `error`. |

---

## Connecting an AI Application

This server uses the **Streamable HTTP** MCP transport. Clients communicate via HTTP POST with streaming responses — opening the endpoint in a browser will return a `Not Acceptable` error, which is expected.

Point your MCP-compatible AI application at the server's MCP endpoint:

```
http://<host>:<port>/mcp
```

For example, if the server is running on `192.168.1.10` with the default port:

```
http://192.168.1.10:8080/mcp
```

Consult your AI application's documentation for how to register an MCP server. Ensure it supports the Streamable HTTP transport (most modern MCP clients do).

---

## Example System Prompt

XML is preferred over markdown for system prompts because explicit named tags give unambiguous semantic meaning — the AI always knows exactly what each block contains. Markdown headings require inference and are more likely to be misinterpreted.

Copy and adapt this prompt to give your AI assistant clear guidance on using the tools.

> **Tip — let an LLM write this for you.** XML-structured system prompts are effective but unfamiliar to most developers and tedious to write by hand. A quick conversation with any capable LLM (describe your tools, what they do, and how you want the assistant to behave) will produce a well-structured prompt you can drop straight in. The results are often better than anything written manually as plain text or markdown.
>
> * XML tags act like labeled folders — the model knows exactly where each piece of information starts and stops
> * Training data is full of structured markup, so models already "think" in tags naturally
> * Tags prevent the model from confusing your instructions with the content it's working on
```xml
<system>
  <role>
    You are a helpful assistant with access to an MCP server. Use the available
    tools to fulfil user requests accurately and efficiently.
  </role>
  <tools>
    <tool name="health_check">Check that the MCP server is running and reachable.</tool>
  </tools>
  <guidelines>
    <item>Call health_check if the user asks whether the server is available.</item>
  </guidelines>
</system>
```

---

## Available Tools

| Tool | Description |
|---|---|
| `health_check` | Returns `{"status": "ok"}` to confirm the server is running. |

> Tools are documented here as they are implemented.

---

## Architecture

The template follows a clean three-layer separation:

| File | Purpose |
|---|---|
| `src/mcp_base/tools.py` | Pure Python functions — one function per tool, no framework coupling |
| `src/mcp_base/server.py` | FastMCP wiring — registers tool functions with `@mcp.tool()` and runs the server |
| `src/mcp_base/config.py` | TOML config loading — typed dataclasses for `[server]` and `[logging]` sections |
| `src/mcp_base/logging.py` | Structured logger factory |

### Adding a tool

1. Add a function to `src/mcp_base/tools.py` with a Google-style docstring and full type annotations.
2. Import the function in `src/mcp_base/server.py` and register it with `@mcp.tool()`.
3. Add a unit test in `tests/unit/`.
4. Add a row to the **Available Tools** table in this README.

---

## Running Tests

```bash
uv run pytest tests/unit/
```

---

## Contributing / Maintaining

See [MAINTAINERS.md](MAINTAINERS.md) for setup, development commands, AI agent rails, and how to run tests.

---

## License

Copyright (c) Sean Esopenko 2026

This project is licensed under the [GNU General Public License v3.0](LICENSE.txt).

---

## Acknowledgement: Riding on the Backs of Giants

This project was built with the assistance of [Claude Code](https://claude.ai/code), an AI coding assistant developed by Anthropic.

AI assistants like Claude are trained on enormous amounts of data — much of it written by the open-source community: the libraries, tools, documentation, and decades of shared knowledge that developers have contributed freely. Without that foundation, tools like this would not be possible.

In recognition of that debt, this project is released under the [GNU General Public License v3.0](LICENSE.txt). The GPL ensures that this code — and any derivative work — remains open source. It is a small act of reciprocity: giving back to the commons that made it possible.

To every developer who ever pushed a commit to a public repo, wrote a Stack Overflow answer, or published a package under an open license — thank you.
