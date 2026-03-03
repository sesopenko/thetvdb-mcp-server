# Commit Message Rules

## Convention

Use **Conventional Commits**: `type(scope): subject`

Examples:
- `feat(tools): add list_torrents`
- `fix(client): handle connection timeout`
- `docs(readme): update installation steps`

## Subject Line

- Maximum **50 characters** (including type and scope)
- **Imperative mood** — "Add config loader", not "Added config loader"
- **No trailing period**

## Scope

Scope is **required** on every commit. Choose a scope that identifies the component or area changed (e.g. `tools`, `client`, `config`, `tests`).

## Body

A commit body is **always required**. After a blank line following the subject, explain **why** the change was made — not just what was changed.

```
feat(tools): add list_torrents tool

Expose torrent listing via MCP so clients can query active downloads
without polling the Transmission RPC directly.
```

## WIP Commits

WIP commits are **not allowed on main**. Every commit on main must be complete and pass all quality gates (`ruff format`, `ruff check`, `mypy`).

## Breaking Changes

Not applicable — this project has no external API consumers.

## Enforcement

Commit message format is enforced by **commitlint via pre-commit hook**. Non-conforming commits are blocked.
