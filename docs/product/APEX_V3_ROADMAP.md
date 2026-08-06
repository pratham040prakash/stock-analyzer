# APEX V3 — Roadmap

**Document ID:** APEX-V3-ROADMAP  
**Version:** 0.3  
**Status:** ACTIVE — V3-102 shipped  
**Date:** 2026-08-06  
**Owner:** Product  
**Parent:** [APEX_V3_PRODUCT_STRATEGY.md](./APEX_V3_PRODUCT_STRATEGY.md)  
**Baseline:** v2.0.0 GA

---

## Program Overview

APEX V3 extends the **Daily Decision Experience** (V2 GA) into a full **Investment Operating System** — portfolio intelligence, decision memory, and review cadences — without violating frozen architecture or product constitution.

**Program duration:** ~18 months (Q4 2026 → Q4 2027)  
**Release model:** Milestone tags (`v3.0.0-alpha`, `v3.0.0-beta`, `v3.0.0`)  
**Quality bar:** Regression gate + full suite 100%; no undocumented failures

---

## Phase Map

```text
2026 Q4          2027 Q1          2027 Q2          2027 Q3          2027 Q4
    │                │                │                │                │
    ▼                ▼                ▼                ▼                ▼
 Phase 0          Phase 1          Phase 2          Phase 3          Phase 4–5
 Strategy         Portfolio        Decision         Review           Capital +
 (NOW)            Intelligence     Memory           Cadences         OS Nav
```

---

## Phase 0 — Product Vision & Strategy ✅

| ID | Deliverable | Status |
|----|-------------|--------|
| V3-P0-001 | Product Strategy | ✅ Approved |
| V3-P0-002 | Roadmap | ✅ Approved |
| V3-P0-003 | Information Architecture | ✅ Approved |
| V3-P0-004 | Feature Backlog | ✅ Approved |
| V3-P0-005 | Product Review sign-off | ✅ Approved |

**Exit criteria:** Product Review approved; no production code ✅

---

## Phase 1 — Portfolio Intelligence (Q4 2026) — IN PROGRESS

**Theme:** Answer *"What do I own and is it healthy?"*

| ID | Milestone | Outcome | Status |
|----|-----------|---------|--------|
| **V3-101** | **Portfolio Command Center** | Overview screen, contracts, assembly, Understand SSOT | **✅ Shipped** |
| **V3-102** | **Holdings Experience** | Inventory ledger, search/filter/sort, row Understand, watchlist | **✅ Shipped** |
| V3-103 | Allocation indicators | Policy drift vs bucket tags per row | Planned |
| V3-104 | Health scoring surface | Reuse APS-005 patterns at portfolio level | Planned |
| V3-105 | Integration tests | Render-level; 100% gate | ✅ 25-test gate |

**Dependencies:** Zerodha connected; existing portfolio use cases  
**Non-goals:** Rebalance execution; tax optimization

**Target tag:** `v3.0.0-alpha1`

---

## Phase 2 — Decision Memory (Q1 2027)

**Theme:** *"What did I decide and what happened?"*

| ID | Milestone | Outcome |
|----|-----------|---------|
| V3-201 | Decision Receipt | Immutable receipt on ACT/WAIT with proof link |
| V3-202 | Weekly Review | Sunday ritual; broker reconcile |
| V3-203 | Journal page shell | Journal tab; trade log integration |
| V3-204 | Discipline metrics | Process score (not P&L leaderboard) |

**Target tag:** `v3.0.0-alpha2`

---

## Phase 3 — Review Cadences (Q2 2027)

**Theme:** *"Am I on track this month/quarter?"*

| ID | Milestone | Outcome |
|----|-----------|---------|
| V3-301 | Monthly Portfolio Doctor | Drift, concentration, sacred core check |
| V3-302 | Quarterly review | Thesis + goal progress |
| V3-303 | Review contracts | Shared compositor for cadence surfaces |
| V3-304 | Notification hooks | Optional Telegram/email digest (existing infra) |

**Target tag:** `v3.0.0-beta1`

---

## Phase 4 — Capital & Thesis (Q3 2027)

**Theme:** *"Where does new money go?"*

| ID | Milestone | Outcome |
|----|-----------|---------|
| V3-401 | New Capital workflow | UX-004 implemented |
| V3-402 | Thesis Tracker | Per-symbol thesis + invalidation |
| V3-403 | Investment Book | Long-form thesis storage (read-only export) |
| V3-404 | Explore integration | Screener → Research → Today handoff |

**Target tag:** `v3.0.0-beta2`

---

## Phase 5 — OS Consolidation (Q4 2027)

**Theme:** One Investment OS; retire legacy tabs

| ID | Milestone | Outcome |
|----|-----------|---------|
| V3-501 | 5-page nav GA | Home · Portfolio · Research · Journal · You |
| V3-502 | Legacy tab redirects | All bookmarks preserved |
| V3-503 | Investor DNA v1 | Profile + behavior summary |
| V3-504 | Contextual Learning | Lessons tied to user verdicts |
| V3-505 | V3 GA hardening | RC pattern; docs freeze |

**Target tag:** `v3.0.0`

---

## Cross-cutting tracks (all phases)

| Track | Owner | Notes |
|-------|-------|-------|
| **Quality** | Engineering | Extend 54-test gate; integration tests per milestone |
| **Accessibility** | UX + Eng | WCAG baseline maintained |
| **Documentation** | Product | ETS per milestone; APEX-015+ series |
| **Design system** | UX | Extend V2 tokens; no duplicate CSS |
| **Trust / Proof** | Product | Expand proof overlay to portfolio |

---

## V2 maintenance window

During V3 program, V2 GA receives:

- P0 bug fixes only on frozen surfaces
- No hierarchy changes to Home Command Center
- Dependency / CI hygiene (V2.1 pattern)

---

## Milestone dependency graph

```mermaid
flowchart TD
    P0[Phase 0 Strategy] --> P1[Phase 1 Portfolio]
    P1 --> P2[Phase 2 Decision Memory]
    P2 --> P3[Phase 3 Review Cadences]
    P1 --> P4[Phase 4 Capital Thesis]
    P3 --> P5[Phase 5 OS Consolidation]
    P4 --> P5
    P5 --> GA[v3.0.0 GA]
```

---

## Release train

| Tag | Phase | Expected |
|-----|-------|----------|
| — | Phase 0 docs | 2026-08-06 ✅ |
| **V3-101** | **Portfolio Command Center** | **2026-08-06 ✅** |
| `v3.0.0-alpha1` | Portfolio Intelligence (remaining) | 2026-12 |
| `v3.0.0-alpha2` | Decision Memory | 2027-03 |
| `v3.0.0-beta1` | Review Cadences | 2027-06 |
| `v3.0.0-beta2` | Capital & Thesis | 2027-09 |
| **`v3.0.0`** | OS Consolidation GA | 2027-12 |

---

## Open decisions (Product Review)

1. Trades dock → Journal vs Home sub-route?
2. Session ribbon — wire or remove in V3.1 maintenance?
3. Alpha AI — Research-only or also Portfolio drill-down?
4. Investor DNA — Phase 5 or separate V3.1 program?
