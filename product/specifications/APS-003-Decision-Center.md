# APS 003 Decision Center

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Status** | Draft |
| **Owner** | Product |
| **Last Updated** | 2026-08-06 |

**Purpose:** Decision Workspace — options and trade-offs




## Related documents

- Journey: [../journeys/UX-004-New-Capital.md](../journeys/UX-004-New-Capital.md)
- Wireframe: [../../design/wireframes/WF-004-Decision.md](../../design/wireframes/WF-004-Decision.md)
- Component: [../../design/components/CMP-001-Recommendation.md](../../design/components/CMP-001-Recommendation.md)
- API: [../../engineering/api/API-004-Decision.yaml](../../engineering/api/API-004-Decision.yaml)
- ADR: [../../engineering/architecture/ADR-002-Recommendation-Engine.md](../../engineering/architecture/ADR-002-Recommendation-Engine.md)
- Object: [../../engineering/data-model/OBJ-003-Decision.md](../../engineering/data-model/OBJ-003-Decision.md)
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

→ See [UX-004-New-Capital](../journeys/UX-004-New-Capital.md)

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

→ [QA spec](../../qa/acceptance/QA-003-Recommendation.md)

## Future Scope

Deferred items documented in [BACKLOG](../roadmap/BACKLOG.md).
