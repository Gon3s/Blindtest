#!/bin/bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

echo "Blindtest — Quality Gate"
echo "========================"

FAILURES=0

run() {
    local label="$1"; shift
    echo ""
    echo "→ $label"
    if ! "$@"; then
        echo "  FAILED: $label"
        FAILURES=$((FAILURES + 1))
    fi
}

# ── Backend ────────────────────────────────────────────────
echo ""
echo "[Backend]"

run "ruff check"    bash -c "cd '$ROOT/backend' && uv run ruff check ."
run "mypy --strict" bash -c "cd '$ROOT/backend' && uv run mypy --strict src/"
run "pytest"        bash -c "cd '$ROOT/backend' && uv run pytest"

# ── Frontend ───────────────────────────────────────────────
echo ""
echo "[Frontend]"

run "eslint"        bash -c "cd '$ROOT/frontend' && npx ng lint"
run "tsc --noEmit"  bash -c "cd '$ROOT/frontend' && npx tsc --noEmit -p tsconfig.app.json"
run "ng test"       bash -c "cd '$ROOT/frontend' && npx ng test --watch=false"

# ── Result ─────────────────────────────────────────────────
echo ""
echo "========================"
if [ "$FAILURES" -eq 0 ]; then
    echo "All checks passed."
    exit 0
else
    echo "$FAILURES check(s) failed."
    exit 1
fi
