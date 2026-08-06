# APS 002 Investment Workspace

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Status** | Draft |
| **Owner** | Product |
| **Last Updated** | 2026-08-06 |

**Purpose:** Investment Workspace — continue owning?




## Related documents

- Journey: [../journeys/UX-003-Investment-Review.md](../journeys/UX-003-Investment-Review.md)
- Wireframe: [../../design/wireframes/WF-002-Investment.md](../../design/wireframes/WF-002-Investment.md)
- Component: [../../design/components/CMP-002-PortfolioHealth.md](../../design/components/CMP-002-PortfolioHealth.md)
- API: [../../engineering/api/API-002-Investment.yaml](../../engineering/api/API-002-Investment.yaml)
- ADR: [../../engineering/architecture/ADR-003-Single-Source-Of-Truth.md](../../engineering/architecture/ADR-003-Single-Source-Of-Truth.md)
- Object: [../../engineering/data-model/OBJ-001-Investment.md](../../engineering/data-model/OBJ-001-Investment.md)
- Legacy: [docs/apex/](../../docs/apex/README.md) (implementation reference)

---

## Problem

_TBD — who is affected and why it matters now._

## Goals

- _Primary measurable outcome_
- _Trust / clarity outcome_

## Non-Goals

- _Explicit exclusion — see [DECISION_LOG](../../.cursor/DECISION_LOG.md)_

## User Journey

→ See [UX-003-Investment-Review](../journeys/UX-003-Investment-Review.md)

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | _Core behaviour_ | P0 |

## States

Loading · Empty · Error · Offline · Success · Stale

## Edge Cases

| Case | Expected behaviour |
|------|-------------------|
| Missing broker | Connect path; no pressure CTA |

## Accessibility

→ [AccessibilityChecklist](../../qa/accessibility/AccessibilityChecklist.md) · [CMP-001](../../design/components/CMP-001-Recommendation.md)

## Performance

→ [PerformanceBudget](../../qa/performance/PerformanceBudget.md)

## Analytics

Meaningful events only — no vanity metrics. See [MASTER_PROMPT](../../.cursor/MASTER_PROMPT.md#analytics).

## Acceptance Criteria

→ [QA spec](../../qa/acceptance/QA-002-Investment.md)

## Future Scope

Deferred items documented in [BACKLOG](../roadmap/BACKLOG.md).
