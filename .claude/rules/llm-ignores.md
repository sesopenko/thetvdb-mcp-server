# LLM ignores (Claude Code)

This rule lists files/folders that Claude Code should **not** pull into context by default.
Only include these files if the user explicitly asks for them (or asks a question that
requires their contents).

## Ignored paths

- LICENSE.txt
- dockerhub/repository-overview-copy.md — Docker Hub copy-paste artifact; not developer documentation
