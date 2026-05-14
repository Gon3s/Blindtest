# /ticket

## Usage

```
/ticket T-011
/ticket T-024
```

## What It Does

Implements a ticket from the Blindtest MVP backlog (see Notion).

1. **Reads the ticket** from Notion or CLAUDE.md context
2. **Creates a plan** (test-first approach)
3. **Writes tests** before implementation (TDD strict)
4. **Implements** to make tests pass
5. **Verifies** with `./scripts/check.sh`
6. **Reports** changes and status — no auto-review

## Workflow (Cost-Optimized)

Batch 2-3 tickets, then run `/review` once:

```
/ticket T-011
/ticket T-012
/ticket T-013

/review                    # one review for the batch

git add .
git commit -m "feat: T-011,012,013 - description"
git push origin main
```

## TDD Cycle (per ticket)

```
1. RED    — Write failing tests
2. GREEN  — Implement to pass tests
3. REFACTOR — Clean up, check ./scripts/check.sh
```

---

**Batch 2-3 tickets, then /review once. See CLAUDE.md for cost strategy.**
