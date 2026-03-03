# Claude Code Instructions

## Docstrings

Write docstrings for users, not implementers:
- Describe **what** the function does, its inputs, outputs, and guarantees
- Do not expose internal logic, private helpers, or implementation details
- Preserve encapsulation — explain behaviour and usage clearly, not how it works internally

Required on all public functions, classes, and methods (anything not prefixed with `_`).
Format: Google style.

## Type Annotations

Annotate all public functions and methods (parameters and return types).
Private/internal helpers (`_` prefix) are exempt but annotations are encouraged.

## Code Standards

All code must pass before committing:
- `ruff format` — formatting
- `ruff check` — linting (unused imports and variables are errors)
- `mypy` — type checking (standard mode)

See `aidlc-docs/inception/standards.md` for the full standards reference.
