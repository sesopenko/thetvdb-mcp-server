#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

CONFIG_CREATED=0
COMPOSE_UP=0

cleanup() {
    if [[ $COMPOSE_UP -eq 1 ]]; then
        echo "--- Tearing down compose stack ---"
        docker compose down --timeout 10 2>&1 || true
    fi
    if [[ $CONFIG_CREATED -eq 1 ]]; then
        rm -f config.toml
    fi
}
trap cleanup EXIT

# ── 1. Dockerfile ─────────────────────────────────────────────────────────────
echo "=== Testing Dockerfile ==="
docker build -t transmission-mcp .
echo "PASS: docker build"

# ── 2. docker-compose.yml ─────────────────────────────────────────────────────
echo ""
echo "=== Testing docker-compose.yml ==="

cp config.toml.example config.toml
CONFIG_CREATED=1

docker compose up -d
COMPOSE_UP=1

# Wait up to 15 s for the server to become ready
TIMEOUT=15
ELAPSED=0
while [[ $ELAPSED -lt $TIMEOUT ]]; do
    if docker compose logs 2>&1 | grep -q "Application startup complete"; then
        break
    fi
    sleep 1
    ELAPSED=$((ELAPSED + 1))
done

if [[ $ELAPSED -ge $TIMEOUT ]]; then
    echo "FAIL: server did not report startup within ${TIMEOUT}s"
    docker compose logs 2>&1
    exit 1
fi

# Confirm the container is still running (didn't crash after startup)
STATUS=$(docker compose ps --format json | python3 -c "
import sys, json
rows = [json.loads(l) for l in sys.stdin if l.strip()]
states = [r.get('State','') for r in rows]
print(' '.join(states))
")
if [[ "$STATUS" != *"running"* ]]; then
    echo "FAIL: container is not in running state (got: $STATUS)"
    exit 1
fi

echo "PASS: docker compose up — server running on port 8080"
