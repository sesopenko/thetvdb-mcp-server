#!/bin/bash
set -e
uv run ruff format .
uv run ruff check . --fix