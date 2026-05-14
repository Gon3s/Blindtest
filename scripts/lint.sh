#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

echo "Blindtest — Lint"
echo "================"

echo ""
echo "[Backend]"
(cd "$ROOT/backend" && uv run ruff check .)
(cd "$ROOT/backend" && uv run mypy --strict src/)

echo ""
echo "[Frontend]"
(cd "$ROOT/frontend" && npx ng lint)
(cd "$ROOT/frontend" && npx tsc --noEmit -p tsconfig.app.json)

echo ""
echo "Lint passed."
