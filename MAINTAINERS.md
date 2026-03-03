# Maintainers Guide

Developer reference for setting up and working on this project.

Commands are added to this file as the corresponding functionality is built. Check back as construction phases complete.

---

## Setup

### 1. Install uv

Follow the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### 2. Install dependencies

```bash
uv sync
```

### 3. Install pre-commit hooks

```bash
uv run pre-commit install
```

---

## Customising the Template

After forking, edit `project.env` with your own project identity values, then run:

```bash
bash scripts/apply-project-config.sh
```

This substitutes the template name, package name, Docker image name, and description throughout the repository. The script is idempotent — safe to run multiple times.

---

## Code Quality

Run all quality checks manually:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy src/
```

These checks also run automatically on every commit via pre-commit hooks.

---

## Running the Server

### Locally

```bash
uv run python -m mcp_base
```

Pass `--config <path>` to use a non-default config file location.

### Via Docker

Build the image:

```bash
docker build -t mcp-base .
```

Start the server (requires `config.toml` in the current directory):

```bash
docker compose up
```

---

## Running Tests

### Unit tests

```bash
uv run pytest tests/unit/
```

---

## Publishing Docker Images

Docker image publishing is disabled by default. The publish workflow checks for a GitHub Actions
repository variable before attempting to push to Docker Hub. This prevents forks and copies of the
repository from pushing images unintentionally.

### Enabling Docker publish

1. Go to **Settings → Secrets and variables → Actions → Variables** in your GitHub repository.
2. Create a repository variable named `ENABLE_DOCKER_PUBLISH` with the value `true`.
3. Also add the following **secrets** (under the Secrets tab):
   - `DOCKERHUB_ACCESS_TOKEN` — a Docker Hub access token with write permission
4. And the following **variable**:
   - `DOCKERHUB_USERNAME` — your Docker Hub username

Once `ENABLE_DOCKER_PUBLISH` is set to `true`, the workflow will push:
- `:latest` on every merge to `main`
- `:<version>`, `:<major>.<minor>`, and `:<major>` tags when a `v*` tag is pushed

### Disabling Docker publish

Delete the `ENABLE_DOCKER_PUBLISH` variable (or set it to any value other than `true`).
The publish jobs will be skipped on the next CI run.

---

## AI Agent Rails

The `.claude/rules/` directory contains a set of standing instructions that are automatically loaded whenever Claude Code is used in this repository. They act as guardrails — keeping the agent's behaviour consistent and predictable as you extend the project.

**Commit discipline**
- The agent never creates a commit unless you explicitly ask it to
- Commit messages are enforced to follow Conventional Commits (`type(scope): subject`, 50-character limit, body required, no WIP commits on main)

**Code quality**
- All public functions and methods must have Google-style docstrings describing behaviour, not implementation
- Full type annotations are required on all public interfaces
- Code must pass `ruff format`, `ruff check`, and `mypy` before committing

**Documentation accuracy**
- The Available Tools table in `README.md` must be updated whenever a new tool is implemented
- The Docker Compose example in `README.md` must stay accurate if the image name, port, or config path changes
- `dockerhub/repository-overview-copy.md` (the Docker Hub overview) must be updated to match any changes to tools, configuration, or endpoints
- `MAINTAINERS.md` must be updated with any new developer commands introduced during development

**Template integrity**
- Any new file that embeds a value from `project.env` (image name, package name, etc.) must have a corresponding substitution wired up in `scripts/apply-project-config.sh`
- The Acknowledgement section at the bottom of `README.md` is permanent and must never be removed

**Structured development workflow**
- The agent follows the AIDLC (AI-Driven Development Lifecycle) workflow for non-trivial changes: inception (requirements and design), construction (code generation), and operations (placeholder)
- Each phase requires explicit user approval before proceeding

### Using these rules in Cursor

The rules are written for Claude Code but the same constraints apply in Cursor. Run the following script to copy them into `.cursor/rules/` with the `.mdc` extension and the frontmatter Cursor requires for always-on rules:

```bash
bash scripts/copy-rules-to-cursor.sh
```

Re-run it any time the rules change to keep the two sets in sync.

---

## Managing Dependencies

### Add a runtime dependency

```bash
uv add <package>
```

### Add a dev dependency

```bash
uv add --dev <package>
```

### Upgrade all dependencies

```bash
uv lock --upgrade
```
