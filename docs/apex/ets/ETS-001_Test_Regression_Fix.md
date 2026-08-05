# ETS-001 — Restore Test Suite to 509/509 Pass

**Document ID:** ETS-001  
**Status:** Planned  
**Lifecycle stage:** Not started — Assessment required before implementation per [APEX-999 §15.1](../APEX-999_Engineering_Handbook.md#151-mandatory-implementation-lifecycle-ets)  
**Date:** 2026-08-05  
**Owner:** Principal Engineer  
**References:** [APEX-001 §Risk TR-01](./APEX-001_Sprint0_Engineering_Assessment.md)

## Objective

Restore CI test pass rate from 500/509 (3 failures, 6 errors) to 509/509.

## Acceptance Criteria

- [ ] `python3 -m unittest discover -s tests` exits 0 locally
- [ ] GitHub Actions CI green on `main`
- [ ] Root cause documented for each failure
- [ ] Regression test added if bug found

## Scope

Test fixes only. No feature or refactor work.

## Out of Scope

Adding coverage tooling; refactoring failing modules beyond minimum fix.

## Estimated Effort

1–2 days

## Priority

P0 — blocks Sprint 0 exit (APEX-001 AC4)
