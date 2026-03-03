# Claude Code Instructions

## apply-project-config.sh

`scripts/apply-project-config.sh` is the template customisation script. It reads identity values
from `project.env` and substitutes them in-place into every file that embeds those values.

### Files the script modifies

| File | What is substituted |
|---|---|
| `pyproject.toml` | Project `name`, `description`, script entry-point name, and wheel package path |
| `.claude/rules/repository-overview.md` | Docker image name (`sesopenko/mcp-base`) |
| `.claude/rules/readme-docker-compose.md` | Docker image name (`sesopenko/mcp-base`) |
| `README.md` | Docker image name, MCP server name, and package name (`mcp_base`) in code examples and file-path references |
| `MAINTAINERS.md` | Package name (`mcp_base`) in run commands |
| `tests/unit/*.py` | Package name in import statements |
| `dockerhub/repository-overview-copy.md` | Docker image name |
| `src/mcp_base/*.py` | Package name in module docstrings and imports |
| `src/mcp_base/` (directory) | Renamed to `src/${PACKAGE_NAME}/` |

### Rules

- When you add a new file that embeds any value from `project.env` (image name, project name,
  package name, MCP server name, or description), you MUST add a corresponding `substitute` call
  to `scripts/apply-project-config.sh` and a row to the table above before the task is considered complete.
- The script must remain idempotent — substitutions must be safe to run multiple times.
- Do not hard-code the template identity values (`sesopenko/mcp-base`, `mcp_base`, etc.) in any
  new file without also wiring up a substitution in the script.
