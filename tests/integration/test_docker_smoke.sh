#!/bin/bash
# Docker smoke tests for T-005
# Tests: API healthcheck via Docker, DB connection via Docker
# Run from repo root: bash tests/integration/test_docker_smoke.sh
set -euo pipefail

COMPOSE="docker-compose"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PASS=0
FAIL=0
SKIP=0

cd "$PROJECT_ROOT"

_pass() { echo "  [PASS] $1"; PASS=$((PASS + 1)); }
_fail() { echo "  [FAIL] $1"; FAIL=$((FAIL + 1)); }
_skip() { echo "  [SKIP] $1"; SKIP=$((SKIP + 1)); }

_port_in_use() { ss -tlnp 2>/dev/null | grep -q ":$1 " || nc -z 127.0.0.1 "$1" 2>/dev/null; }

_wait_for_url() {
  local url="$1" label="$2" retries=30
  for i in $(seq 1 $retries); do
    if curl -sf "$url" > /dev/null 2>&1; then
      _pass "$label"
      return 0
    fi
    sleep 2
  done
  _fail "$label (timeout after ${retries}x2s)"
}

_wait_for_service_healthy() {
  local service="$1" retries=30
  for i in $(seq 1 $retries); do
    if $COMPOSE ps "$service" 2>/dev/null | grep -q "healthy"; then
      return 0
    fi
    sleep 2
  done
  return 1
}

echo "=== T-005 Docker Smoke Tests ==="
echo ""

# ── Infrastructure checks ──────────────────────────────────────────────────────
echo "── Infrastructure checks ──"
if [ -f "$PROJECT_ROOT/docker-compose.yaml" ]; then
  _pass "docker-compose.yaml exists"
else
  _fail "docker-compose.yaml missing"
fi

if $COMPOSE config --quiet 2>/dev/null; then
  _pass "docker-compose.yaml is valid"
else
  _fail "docker-compose.yaml is invalid"
fi

[ -f "$PROJECT_ROOT/backend/Dockerfile" ]  && _pass "backend/Dockerfile exists"  || _fail "backend/Dockerfile missing"
[ -f "$PROJECT_ROOT/frontend/Dockerfile.dev" ] && _pass "frontend/Dockerfile.dev exists" || _fail "frontend/Dockerfile.dev missing"

# ── Build checks ───────────────────────────────────────────────────────────────
echo ""
echo "── Build checks ──"
if $COMPOSE build --quiet backend 2>&1 | grep -v "^$" | grep -v "^Step" | tail -3; then
  _pass "backend image builds"
else
  _fail "backend image build failed"
fi

if $COMPOSE build --quiet frontend 2>&1 | grep -v "^$" | grep -v "^Step" | tail -3; then
  _pass "frontend image builds"
else
  _fail "frontend image build failed"
fi

# ── Runtime checks ─────────────────────────────────────────────────────────────
echo ""
echo "── Runtime checks ──"
PORTS_BLOCKED=false
if _port_in_use 5432; then
  _skip "postgres start (port 5432 already in use by another service — stop it first to run this check)"
  PORTS_BLOCKED=true
fi
if _port_in_use 8000; then
  _skip "backend start (port 8000 already in use)"
  PORTS_BLOCKED=true
fi

if [ "$PORTS_BLOCKED" = "false" ]; then
  if $COMPOSE up -d postgres backend 2>&1; then
    echo "  Waiting for postgres to be healthy..."
    if _wait_for_service_healthy postgres; then
      _pass "postgres is healthy"
    else
      _fail "postgres healthcheck timed out"
    fi

    echo "  Waiting for API healthcheck..."
    _wait_for_url "http://localhost:8000/health" "GET /health returns 200"

    db_log=$($COMPOSE logs backend 2>&1 | grep -iE "error|connection refused" | head -5 || true)
    if [ -z "$db_log" ]; then
      _pass "backend logs show no DB connection errors"
    else
      _fail "backend logs contain errors: $db_log"
    fi
  else
    _fail "docker-compose up failed"
  fi

  echo ""
  echo "── Teardown ──"
  $COMPOSE down --volumes --remove-orphans 2>&1 || true
  echo "  Services stopped."
fi

echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed, ${SKIP} skipped ==="
[ "$FAIL" -eq 0 ]
