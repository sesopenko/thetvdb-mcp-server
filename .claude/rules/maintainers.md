# Claude Code Instructions

## MAINTAINERS.md

`MAINTAINERS.md` is the developer reference for working on this project. It must stay accurate as the project grows.

**When a construction phase introduces a new developer command — running tests, starting the server, managing dependencies, or any other workflow step — you MUST add it to `MAINTAINERS.md` before the phase is considered complete.**

### Rules

- Add commands in the section that best describes their purpose (e.g. "Running Tests", "Running the Server")
- Create a new section if no existing section fits
- Include the exact command to run, with a brief description if it is not self-evident
- Remove or update entries when commands change (e.g. a test path is renamed)
- Do not add commands up front for functionality that does not exist yet

### Example entry format

```markdown
## Running Tests

### Unit tests

```bash
uv run pytest tests/unit/
```

### Integration tests

Requires a running Transmission instance (see docker-compose.test.yml).

```bash
uv run pytest tests/integration/
```
```
