#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

echo "Blindtest — Tests"
echo "================="

echo ""
echo "[Backend]"
(cd "$ROOT/backend" && uv run pytest)

echo ""
echo "[Frontend]"
(cd "$ROOT/frontend" && npx ng test --watch=false)

echo ""
echo "All tests passed."
