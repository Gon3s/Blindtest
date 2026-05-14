# /tdd-cycle

## Usage

```
/tdd-cycle [feature description]
/tdd-cycle Implement Room state machine with transitions
/tdd-cycle Add validation for participant names
```

## What It Does

Plans a complete TDD cycle for a complex feature.

Returns:
1. **Test Plan** - What tests to write
2. **Test Code** - Test file (red phase)
3. **Implementation Plan** - How to implement
4. **Code** - Implementation (green phase)
5. **Refactor Suggestions** - Optional improvements (refactor phase)

## How It Works

This command uses TDD-Mentor to guide the full Red-Green-Refactor cycle.

---

## Example

```
/tdd-cycle Implement email validation for answers

TDD-Mentor will:

1. RED PHASE
   - Write tests for valid email
   - Write tests for invalid email
   - Write tests for normalized email

2. GREEN PHASE
   - Implement EmailValidator class
   - Make tests pass

3. REFACTOR
   - Suggest optimizations
   - Check for code duplication

4. VERIFY
   - Run ./scripts/check.sh
   - Report coverage
```

---

**Use for complex domain logic or business rules.**
