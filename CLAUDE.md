# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Multiplayer music blindtest app for private friend sessions. Core game loop that must never regress:

```
Create room → Join by code + pseudo → Play round (10 songs × 30s) → Answer (free text) → Validate → Reveal → Score → Relaunch
```

No user accounts, no payments, no voice input. Pseudos only. Music via Deezer 30s previews + fixture fallback.

## Commands

```bash
# Full quality gate — run before every commit
./scripts/check.sh        # ruff, mypy, pytest, eslint, tsc, ng test

# Start all services (Docker Compose)
./scripts/dev.sh           # Equivalent to docker-compose up -d

# Backend (from backend/)
uv run pytest              # All tests
uv run pytest tests/path/test_file.py::test_name  # Single test
uv run ruff check .        # Lint
uv run ruff format .       # Format
uv run mypy --strict src/  # Type check

# Frontend (from frontend/)
ng test --watch=false      # Unit tests (CI mode)
ng lint                    # ESLint
tsc --noEmit               # Type check
ng serve                   # Dev server (also runs in Docker on :4200)
```

**Service URLs (after `./scripts/dev.sh`)**:
- Frontend: http://localhost:4200
- API + Swagger: http://localhost:8000 / http://localhost:8000/docs
- DB Admin (Adminer): http://localhost:8081

## Architecture

### Monorepo Layout

```
backend/src/
├── domain/          # Pure business logic — zero infrastructure imports
│   ├── models.py    # Entities, value objects
│   ├── errors.py    # Domain exceptions (mapped to HTTP in routes)
│   └── rules/       # State machines (Room states, etc.)
├── application/     # Use cases — orchestrates domain + infrastructure
│   ├── services/
│   └── dto.py
├── infrastructure/  # SQLAlchemy, connections, Deezer adapter
│   ├── db.py
│   ├── repositories/
│   └── adapters/
└── api/             # FastAPI routes — thin, validation + serialization only

frontend/src/app/
├── core/            # Singleton services, guards (API client, WebSocket service)
├── shared/          # Reusable dumb components, pipes, directives
└── pages/           # Smart components, one per route (home, room, game, leaderboard)
```

### Key Architectural Rules

**Backend — domain purity**: `domain/` must have zero imports from `fastapi`, `sqlalchemy`, `requests`, or any other infrastructure library. Business logic tested without a running DB or server.

**Backend — routes are thin**: No business logic in route handlers. Routes call service methods, map domain errors to HTTP status codes.

**Backend — WebSocket**: Manager pattern for connection lifecycle. Broadcast typed messages. Graceful cleanup on disconnect.

**Frontend — standalone components**: All Angular components use `standalone: true`. No NgModule declarations for new code.

**Frontend — change detection**: Default to `OnPush`. Dumb components only receive `@Input`/emit `@Output`. Smart components (pages) wire services.

**Frontend — reactivity**: Services expose `BehaviorSubject`/`ReplaySubject`. Templates use `async` pipe. No unsubscribed observables.

**Frontend — WebSocket**: Single WS service with reconnection logic (exponential backoff, not infinite retry). Cleanup subscriptions in `ngOnDestroy`.

## Definition of Done

A ticket is complete only when:

1. Tests written before implementation (TDD — no exceptions)
2. `pytest` passes (backend) + `ng test:ci` passes (frontend)
3. `ruff check` + `mypy --strict` pass (backend)
4. `eslint` + `tsc --noEmit` pass (frontend)
5. `./scripts/check.sh` returns 0
6. DB migrations included if schema changed (Alembic)

## Typing

- Python: `mypy --strict` must pass. Use `Optional[T]`, explicit return types on all functions.
- TypeScript: `strict: true` in tsconfig. No `any` without a comment explaining why.

## Slash Commands

- `/ticket T-XXX` — implement a ticket (TDD-first, verify with check.sh)
- `/review` — pre-merge readiness check (runs backend + frontend + product guardian agents)
- `/tdd-cycle [description]` — plan a Red-Green-Refactor cycle for complex features

## Agents

Specialized agents in `.claude/agents/`:
- `tdd-mentor` — enforces test-first; invoke when starting any business logic
- `backend-reviewer` — validates hexagonal architecture, mypy, domain purity
- `frontend-reviewer` — validates Angular standalone, TypeScript strict, RxJS patterns
- `product-guardian` — blocks scope creep; anything not in T-001 to T-041 is out of MVP

## Notion (Source of Truth)

- Tickets: https://www.notion.so/35db6460-0100-8108-b0b9-ec19b6238ac5
- Update ticket status after each completed ticket.
