# /ticket

## Usage

```
/ticket T-008
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
7. **NO auto-review** (you run /review manually after 2-3 tickets)

## How It Works

This command triggers the TDD-Mentor agent to guide implementation of any T-XXX ticket.

**Important** : Each ticket is independent. You batch 2-3 tickets, then run `/review` once.

---

## Workflow (Optimized for Cost)

```
/ticket T-008              # No auto-review
/ticket T-009              # No auto-review
/ticket T-010              # No auto-review

/review                    # Check all 3 at once

git add .
git commit -m "feat: T-008,009,010 - batch"
```

This saves ~50% on API costs vs auto-review per ticket.

---

## Example

```
/ticket T-008

TDD-Mentor (Haiku model) will:
1. Read T-008 from CLAUDE.md
2. Break into atomic tasks
3. Write test file first
4. Implement to pass tests
5. Verify ./scripts/check.sh
6. Report: "T-008 Complete ✅ (no auto-review)"
```

---

**Batch 2-3 tickets, then /review once. Much cheaper!**
