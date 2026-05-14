#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

echo "Blindtest — Format"
echo "=================="

echo ""
echo "[Backend]"
(cd "$ROOT/backend" && uv run ruff format .)

echo ""
echo "[Frontend]"
(cd "$ROOT/frontend" && npx prettier --write "src/**/*.{ts,html,scss}")

echo ""
echo "Format done."
