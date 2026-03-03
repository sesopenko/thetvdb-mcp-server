# Claude Code Instructions

## README Docker Compose Example

The `README.md` contains a Docker Compose example block under `### Option A — Docker Compose`.
This example must stay accurate as the project evolves.

**When any of the following change, you MUST update the example before the task is considered complete:**

- The published Docker Hub image name or tag strategy
- The container port or the host port mapping
- The config file path inside the container (`/config/config.toml`)
- Any new required volumes or environment variables

### Rules

- The example must always use the published Docker Hub image (`sesopenko/mcp-base:latest`),
  not a local `build: .` reference
- Keep the example minimal — only include what a user needs to get started
- Do not add optional or advanced configuration to the example; document those separately
