# /ticket

## Usage

```
/ticket T-003
/ticket T-024
```

## What It Does

Implements a ticket from Blindtest App MVP backlog.

1. **Reads the ticket** from CLAUDE.md or Notion
2. **Creates a plan** (test-first approach)
3. **Writes tests** before implementation
4. **Implements** to make tests pass
5. **Verifies** with `./scripts/check.sh`
6. **Reports** changes and status

## How It Works

This command triggers the TDD-Mentor agent to guide implementation of any T-XXX ticket from Sprint 0-6.

---

## Example

```
/ticket T-003

TDD-Mentor will:
1. Read T-003 from CLAUDE.md
2. Break it into atomic tasks
3. Write test file first (test_health_check.py)
4. Create implementation (main.py, GET /health)
5. Run pytest
6. Verify ./scripts/check.sh
7. Report: "T-003 Complete ✅"
```

---

**Always use this for any T-XXX ticket implementation.**
