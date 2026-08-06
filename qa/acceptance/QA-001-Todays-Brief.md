# QA-001 — Today's Brief

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Status** | Draft |
| **Owner** | QA |
| **Last Updated** | 2026-08-06 |

**Purpose:** Acceptance criteria and test scenarios for APS-001 Today's Brief

**Spec:** [APS-001 Today's Brief](../../product/specifications/APS-001-Todays-Brief.md)

## Scenarios

| ID | Given | When | Then |
|----|-------|------|------|
| QA-001-01 | Broker connected, NORMAL scenario | Today renders | Verdict word + mentor + sync row visible |
| QA-001-02 | NO_BROKER scenario | Today renders | Verdict Connect; hero intel hidden; CTA Connect Zerodha |
| QA-001-03 | Decision with explainability + evidence | User opens Why popover | Sections appear in contract order: Why → Evidence → Trade-offs → Risks → What could change → Suggested next step → Help me understand |
| QA-001-04 | Help me understand expander | User selects Simple / Business / Professional | Matching bullet depth shown |
| QA-001-05 | Risk session ribbon populated | Today renders | Ribbon chips visible in L0.5 |
| QA-001-06 | Stale brief | Today renders | Stale badge visible; verdict not hidden |
| QA-001-07 | DATA_UNAVAILABLE | Today renders | failure_message shown; hero intel suppressed |
| QA-001-08 | First visit (no last bundle) | load_dashboard_data returns None | Prepare canvas shown |
| QA-001-09 | Returning visit refreshing | load_dashboard_data returns cached + _refreshing | Last verdict shown with updating banner |
| QA-001-10 | E0.6 rehydration | assemble_view_model(record_snapshot=False) | Uses frozen broker from cache, not live snapshot |

## Automated coverage

- `tests/test_aps_001_today_brief.py`
- `tests/test_ets_003c.py`
- `tests/test_p0_readiness.py`
- `tests/test_apex_013_e0_6_context_determinism.py`
