#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cp -f "$REPO_ROOT/scripts/commit-msg.hook" "$REPO_ROOT/.git/hooks/commit-msg"
chmod +x "$REPO_ROOT/.git/hooks/commit-msg"
echo "Git hooks installed."
