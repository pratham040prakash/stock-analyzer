# APS-001 — Today's Brief

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Status** | Draft |
| **Owner** | Product |
| **Last Updated** | 2026-08-06 |

**Purpose:** Today's Brief — the daily decision surface. One screen, one primary question: *Should I act on my capital today, and why?*

## Related documents

- Journey: [UX-002 Morning Brief](../journeys/UX-002-Morning-Brief.md)
- Wireframe: [WF-001 Today's Brief](../../design/wireframes/WF-001-Todays-Brief.md)
- Component: [CMP-001 Recommendation](../../design/components/CMP-001-Recommendation.md)
- API: [API-001 Today's Brief](../../engineering/api/API-001-Todays-Brief.yaml)
- ADR: [ADR-001 Today's Brief](../../engineering/architecture/ADR-001-Todays-Brief.md)
- Object: [OBJ-003 Decision](../../engineering/data-model/OBJ-003-Decision.md)
- Legacy: [ETS-003 Today Surface](../../docs/apex/ets/ETS-003_Today_Surface_Product_Spec.md) · [ETS-003a](../../docs/apex/ets/ETS-003a_Morning_Brief_Experience_Spec.md) · [ETS-003b](../../docs/apex/ets/ETS-003b_Morning_Brief_Data_Wiring.md) · [ETS-003c](../../docs/apex/ets/ETS-003c_Verdict_Canvas_Trust_Bind.md)

---

## Problem

Indian retail investors with limited morning time face decision overload. They open trading apps and leave more anxious than when they arrived. APEX must answer one question in under 30 seconds — including permission to wait.

## Goals

- User states verdict + reason aloud within 30 seconds (WAIT days included)
- Single authoritative verdict from `DecisionEngine` → `MorningBriefViewModel`
- Broker sync state visible; personalized when connected
- Recommendation contract fully explorable without leaving Today

## Non-Goals

- Market screener, news feed, social features, copy trading ([DECISION_LOG](../../.cursor/DECISION_LOG.md))
- Separate Morning Brief tab — Brief **is** Today ([APEX-004 §17.1](../../docs/apex/APEX-004_Experience_Operating_System.md))

## User Journey

→ [UX-002 Morning Brief](../journeys/UX-002-Morning-Brief.md)

## Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Hero shows verdict word + mentor (max ~18 words) + primary CTA | P0 |
| FR-2 | L0.5 session ribbon from context restrictions / risk mode | P0 |
| FR-3 | Recommendation contract in fixed order via "Why I'm saying this" popover | P0 |
| FR-4 | Help Me Understand with Simple / Business / Professional levels | P0 |
| FR-5 | States: Loading, Prepare (first visit), Success, Stale, Error, Offline (connect) | P0 |
| FR-6 | Stale-while-revalidate: show last brief + "Updating…" during refresh | P1 |
| FR-7 | Proof CTA when proof canvas active; no pressure connect path | P0 |
| FR-8 | Data path: `load_today_core` → `DecisionContextBundle` → `assemble_view_model` | P0 |

## States

| State | Verdict / UX | CTA |
|-------|--------------|-----|
| **Loading** | Reviewing + dots | None (rerun) |
| **Prepare** | Prepare + welcome copy | None |
| **Success** | Trade / Wait / Rest | Contextual |
| **Stale** | Last verdict + stale badge | Unchanged |
| **Error** | Pause + failure message | Try again / done |
| **Offline** | Connect + sync off | Connect Zerodha (no pressure) |

## Edge Cases

| Case | Expected behaviour |
|------|-------------------|
| Missing broker | Connect path; hero intel suppressed; no pressure CTA |
| ACT without evidence | Downgrade to Wait ([ETS-003b](../../docs/apex/ets/ETS-003b_Morning_Brief_Data_Wiring.md)) |
| Refresh while cached | Show last bundle + updating banner |
| Loss streak ≥ 2 | Pause verdict; discipline copy |

## Accessibility

→ [AccessibilityChecklist](../../qa/accessibility/AccessibilityChecklist.md) · [CMP-001](../../design/components/CMP-001-Recommendation.md)

- Session ribbon uses `role="status"`
- Verdict word is plain text (not color-only)
- Popover sections use headings + lists for screen readers

## Performance

→ [PerformanceBudget](../../qa/performance/PerformanceBudget.md)

- Cold: thinking/prepare canvas ≤ 1 rerun cycle
- Warm: cached bundle TTL 45s (`load_today_core`)
- No live broker recompute on rehydration (E0.6)

## Analytics

Meaningful events only — verdict shown, CTA tapped, proof opened. No vanity metrics. See [MASTER_PROMPT](../../.cursor/MASTER_PROMPT.md).

## Acceptance Criteria

→ [QA-001 Today's Brief](../../qa/acceptance/QA-001-Todays-Brief.md)

## Future Scope

- Progressive L1/L2/L3 loading stages ([BACKLOG](../roadmap/BACKLOG.md))
- Dedicated Portfolio Intelligence / CDQS cards below fold
- React/Next target UI (architecture frozen for Sprint 1 planning)
