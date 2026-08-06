# APEX Refactoring Prompt

Refactor for clarity and single source of truth — not for fashion.

## Goal

What maintainability or trust problem does this solve?

## Invariants (must not break)

- Public API contracts
- DecisionContextBundle / ledger determinism (if touched)
- Recommendation structure and copy order
- Test suite green

## Plan

1. Extract / consolidate (no behaviour change)
2. Tests first or parallel
3. Remove dead paths only with approval

## Rollback

Git revert path or feature flag:

## Out of scope

Drive-by features · Architecture rewrites without approval
