#!/bin/bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

echo "Blindtest — Quality Gate"
echo "========================"

TMPDIR_CHECKS="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_CHECKS"' EXIT

run_group() {
    local group="$1"
    local outfile="$TMPDIR_CHECKS/${group}.out"
    local exitfile="$TMPDIR_CHECKS/${group}.exit"
    shift
    {
        failures=0
        echo ""
        echo "[$group]"
        while [[ $# -ge 2 ]]; do
            label="$1"; shift
            cmd="$1"; shift
            echo ""
            echo "→ $label"
            if ! bash -c "$cmd"; then
                echo "  FAILED: $label"
                failures=$((failures + 1))
            fi
        done
        echo "$failures" > "$exitfile"
    } > "$outfile" 2>&1 &
}

run_group "Backend" \
    "ruff check"          "cd '$ROOT/backend' && uv run ruff check ." \
    "mypy --strict"       "cd '$ROOT/backend' && uv run mypy --strict src/" \
    "pytest"              "cd '$ROOT/backend' && uv run pytest" \
    "pytest integration"  "cd '$ROOT/backend' && uv run pytest tests/integration -n 0"

run_group "Frontend" \
    "eslint"       "cd '$ROOT/frontend' && npx ng lint" \
    "tsc --noEmit" "cd '$ROOT/frontend' && npx tsc --noEmit -p tsconfig.app.json" \
    "ng test"      "cd '$ROOT/frontend' && npx ng test --watch=false"

wait

FAILURES=0
for group in Backend Frontend; do
    cat "$TMPDIR_CHECKS/${group}.out"
    group_failures="$(cat "$TMPDIR_CHECKS/${group}.exit")"
    FAILURES=$((FAILURES + group_failures))
done

echo ""
echo "========================"
if [ "$FAILURES" -eq 0 ]; then
    echo "All checks passed."
    exit 0
else
    echo "$FAILURES check(s) failed."
    exit 1
fi
