# /review

## Usage

```
/review
```

## What It Does

Reviews the current branch/state for merge readiness.

Checks:
- ✅ Tests pass (pytest, ng test)
- ✅ Lint passes (ruff, eslint)
- ✅ Typing passes (mypy, tsc)
- ✅ `./scripts/check.sh` returns 0
- ✅ No MVP scope creep
- ✅ Documentation updated
- ✅ All Definition of Done criteria met

## How It Works

This command runs the Backend Reviewer + Frontend Reviewer + Product Guardian agents.

Returns:
- Go/No-go for merge
- List of blockers if any
- Suggestions for improvement

---

## Example

```
/review

Response:
✅ Tests: PASS (42 tests, 100% coverage on domain)
✅ Lint: PASS (ruff, mypy --strict)
✅ Frontend: PASS (ng test, eslint)
✅ Scope: PASS (no P1 features added)
✅ Docs: PASS (README updated)

🟢 GO for merge
```

---

**Use before committing any code.**
