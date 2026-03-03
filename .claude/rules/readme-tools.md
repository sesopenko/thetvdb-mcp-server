# Claude Code Instructions

## README Tools Table

The `README.md` contains an "Available Tools" table that must be kept current.

**When implementing a new MCP tool, you MUST update the tools table in `README.md` before the construction phase is considered complete.**

The table lives under the `## Available Tools` heading:

```markdown
| Tool | Description |
|---|---|
| `tool_name` | One-sentence description of what the tool does |
```

### Rules

- Add one row per tool, in the order tools are implemented
- The description must be user-facing: what the tool does, not how it works
- Do not add a row until the tool is implemented and its tests pass
- Do not remove rows for tools that have been implemented
