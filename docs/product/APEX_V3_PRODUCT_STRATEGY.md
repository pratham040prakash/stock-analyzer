# APEX V3 — Product Strategy

**Document ID:** APEX-V3-STRATEGY  
**Version:** 0.1  
**Status:** DRAFT — Phase 0 (Product Vision & Strategy)  
**Date:** 2026-08-06  
**Owner:** Product  
**Authors:** Product · Staff Engineering · UX · Architecture  
**Baseline:** APEX v2.0.0 GA (`v2.0.0`)  
**References:** [MASTER_PROMPT](../../.cursor/MASTER_PROMPT.md) · [APEX-014](../apex/APEX-014_V2_Architecture_and_Release.md) · [APEX-003](../apex/APEX-003_Product_Strategy_and_PRD.md) · [APEX-000](../apex/APEX-000_Company_Constitution.md)

**Scope:** Product strategy only. No implementation. Frozen V2 architecture is preserved.

---

## Table of Contents

1. [Vision Statement](#1-vision-statement)
2. [Product Mission](#2-product-mission)
3. [Target Users](#3-target-users)
4. [User Personas](#4-user-personas)
5. [Investor Workflows](#5-investor-workflows)
6. [Product Pillars](#6-product-pillars)
7. [Capability Map](#7-capability-map)
8. [Feature Prioritization](#8-feature-prioritization)
9. [Information Architecture](#9-information-architecture)
10. [UX Navigation](#10-ux-navigation)
11. [Screen Map](#11-screen-map)
12. [Roadmap](#12-roadmap)
13. [Technical Architecture Impact](#13-technical-architecture-impact)
14. [Risks](#14-risks)
15. [Success Metrics](#15-success-metrics)
16. [Out-of-Scope Items](#16-out-of-scope-items)

---

## 1. Vision Statement

**APEX V3 becomes the world's most trusted daily-to-decadal investment decision companion** — one system that answers *what to do with your money today*, *why*, and *how it fits your long-term plan*, without turning investing into a game, a feed, or a chatbot.

V2 proved the **Daily Decision Experience** works: verdict-first, explainable, render-only, testable. V3 extends that trust across **portfolio intelligence, decision memory, and review cadences** while preserving the frozen decision pipeline.

> *Better decisions. Not more decisions.*

---

## 2. Product Mission

Help serious retail investors in India make **fewer, higher-quality decisions** with:

- **Clarity** — answer before explanation, every time
- **Trust** — broker-verified truth, explicit uncertainty, no fabricated metrics
- **Discipline** — capital rules, review rituals, decision receipts
- **Learning** — continuous education tied to *their* decisions, not generic tips

V3 does **not** optimize for trading frequency, screen time, or engagement hacks.

---

## 3. Target Users

### Primary (V3 launch cohort)

| Segment | Profile | V2 fit | V3 need |
|---------|---------|--------|---------|
| **Disciplined swing investor** | ₹10L–₹1Cr portfolio, Zerodha, tactical pool + SIP | ✅ Daily Brief + Review | Portfolio health, thesis tracking |
| **Busy professional** | 15 min/day, wants verdict not dashboard | ✅ Home Command Center | Weekly/monthly review automation |
| **Self-directed learner** | Reads fundamentals, hates Telegram tips | ✅ Understand popover | Structured learning tied to holdings |

### Secondary (V3 expansion)

| Segment | V3 value |
|---------|----------|
| ETF-focused allocator | Simpler verdicts, allocation drift alerts |
| Options-aware (not options-first) | Risk framing, expiry awareness — not chain trading |
| Advanced DIY | Decision receipts, calibration, export |

### Explicit non-target

- Day traders seeking speed / L2 data
- Social / copy-trading communities
- Crypto / F&O speculators (excluded by constitution)

---

## 4. User Personas

### Persona A — Arjun (Primary)

**Role:** Software engineer, Bangalore  
**Capital:** ₹15L portfolio · ₹40K tactical pool · ₹25K/mo SIP  
**Behavior:** Opens Kite + 4 apps every morning; decision fatigue by 9:15 AM  
**V2 satisfaction:** Today verdict in 30 seconds; Review Workspace when ACT  
**V3 jobs:** "Is my portfolio healthy?" · "Am I on track for ₹10 Cr?" · "Did I follow my rules this week?"

### Persona B — Meera (Long-term)

**Role:** Product manager, dual-income household  
**Capital:** ₹40L, 80% delivery, sacred core untouched  
**V3 jobs:** Monthly allocation review · Reduce anxiety during drawdowns · Teach spouse the plan

### Persona C — Vikram (Advanced)

**Role:** Ex-banker, reads ARs  
**Capital:** ₹2Cr+, multi-bucket  
**V3 jobs:** Thesis tracker · Decision receipts · Calibration vs system

### Persona D — Priya (Beginner)

**Role:** First job, starting SIP  
**Capital:** ₹3L, learning  
**V3 jobs:** Onboarding · plain-language learning · "wait" as valid outcome

*Detailed persona files remain in `product/personas/` — V3 references, does not replace.*

---

## 5. Investor Workflows

### 5.1 Daily (shipped V2 — extend, do not redesign)

```text
Wake → Today (Verdict Hero) → ACT or WAIT
         ↓ ACT
      Review Workspace → Plan → Kite
         ↓ WAIT
      Understand popover → optional depth → close calm
```

### 5.2 Weekly (V3 — new cadence)

```text
Sunday evening → Weekly Review
  → What happened this week (broker truth)
  → Decisions vs outcomes
  → Discipline score (process, not P&L bragging)
  → One focus for next week
```

### 5.3 Monthly (V3)

```text
Month-end → Portfolio Doctor
  → Allocation vs policy
  → Concentration / drift
  → Sacred core vs tactical separation
  → One rebalance suggestion (optional, user-owned)
```

### 5.4 Quarterly / Annual (V3)

```text
Quarter → Thesis check · goal progress · tax-aware notes (informational)
Year → Investor DNA refresh · annual letter to self
```

### 5.5 Capital events (V3)

```text
Bonus / windfall → New Capital workflow
  → Where does this fit? (core / tactical / wait)
  → Size within rules · no FOMO framing
```

### 5.6 Research (V3 — depth on demand)

```text
Symbol question → Research workbench
  → Thesis · health · risk (reuse APS contracts)
  → Alpha AI report (existing) as deep layer
  → Return to Today with context preserved
```

---

## 6. Product Pillars

| # | Pillar | V2 state | V3 ambition |
|---|--------|----------|-------------|
| 1 | **Daily Decision** | ✅ GA | Harden; session ribbon decision; smarter loading |
| 2 | **Execution Review** | ✅ GA | Plan polish; proof overlay integration |
| 3 | **Portfolio Intelligence** | Partial (backend) | **Primary V3 bet** — unified Portfolio page |
| 4 | **Decision Memory** | Fragmented | Decision Receipts + Journal truth |
| 5 | **Review Cadences** | Spec only | Weekly · Monthly · Quarterly surfaces |
| 6 | **Capital Allocation** | Partial | Policy engine + New Capital flow |
| 7 | **Learning** | Static snippet | Contextual lessons from *their* verdicts |
| 8 | **Trust & Proof** | ETS-003c | Expand proof to portfolio + review |

**Pillar rule:** Each pillar maps to one primary question (principle #5).

---

## 7. Capability Map

```text
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION (V2 frozen)                   │
│  Contracts → Components → Theme → Render-only UI               │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                   V3 NEW PRESENTATION LAYER                    │
│  Portfolio contracts · Review contracts · Receipt contracts    │
│  (projections only — no verdict logic in UI)                   │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│              DOMAIN / USE CASES (existing + extend)            │
│  MorningBrief · Portfolio assembly · Journal · Wealth plan     │
│  Decision receipts · Review assembly · Calibration             │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│         FROZEN PIPELINE (unchanged)                            │
│  DecisionContextBundle → DecisionArtifact → MorningBriefVM     │
└─────────────────────────────────────────────────────────────┘
```

### Capability inventory

| Capability | V2 | V3 target | Domain owner |
|------------|----|-----------|--------------|
| Today verdict | ✅ | Maintain | Decision engine + MBVM |
| Review depth | ✅ | Maintain | APS contracts |
| Portfolio holdings view | Backend | **Ship UI** | Portfolio use cases |
| Weekly review | — | **New** | Review assembly |
| Decision receipt | — | **New** | Journal + decision |
| Thesis tracker | Partial | **Ship** | Investment OS |
| Explore / screener | Legacy tabs | **Integrate** | Existing analyzers |
| Learning | Static | **Contextual** | Content + verdict hook |
| Investor DNA | — | **Phase 2 V3** | Profile + behavior |

---

## 8. Feature Prioritization

### MoSCoW (V3 program)

| Priority | Features |
|----------|----------|
| **Must** | Portfolio page (holdings, health, allocation) · Weekly Review · Decision Receipt on ACT/WAIT |
| **Should** | Monthly Portfolio Doctor · New Capital flow · Contextual Learning |
| **Could** | Thesis Tracker UI · Explore integration · Quarterly review |
| **Won't (V3)** | Social · copy trade · crypto · gamification · new indicators |

### RICE-style ranking (top 8)

| Rank | Feature | Reach | Impact | Confidence | Effort |
|------|---------|-------|--------|------------|--------|
| 1 | Portfolio Intelligence page | High | High | Medium | L |
| 2 | Weekly Review | High | High | High | M |
| 3 | Decision Receipts | Medium | High | High | M |
| 4 | Monthly Portfolio Doctor | Medium | High | Medium | M |
| 5 | New Capital workflow | Low | High | Medium | S |
| 6 | Thesis Tracker | Medium | Medium | Medium | M |
| 7 | Explore (unified) | Medium | Medium | Low | L |
| 8 | Investor DNA | Low | High | Low | L |

*Full backlog: [APEX_V3_FEATURE_BACKLOG.md](./APEX_V3_FEATURE_BACKLOG.md)*

---

## 9. Information Architecture

V3 evolves from **3-dock partner shell** (Today / Trades / You) toward **5-page Investment OS** without breaking V2 daily loop.

| Page | Primary question | V2 carryover |
|------|------------------|--------------|
| **Home** | What should I do today? | Today Command Center (unchanged hierarchy) |
| **Portfolio** | What do I own and is it healthy? | New — absorbs My Portfolio, allocation |
| **Research** | Why is this true for symbol X? | Alpha AI, screener, workbench |
| **Journal** | What happened and what did I learn? | Trades, receipts, calibration |
| **You** | Who am I as an investor? | Reflection, trust, DNA (evolve) |

*Detail: [APEX_V3_INFORMATION_ARCHITECTURE.md](./APEX_V3_INFORMATION_ARCHITECTURE.md)*

---

## 10. UX Navigation

### Primary nav (V3 target)

```text
[ Home ] [ Portfolio ] [ Research ] [ Journal ] [ You ]
```

### Rules (frozen principles applied)

1. **Home remains default landing** — morning verdict unchanged
2. **Max one primary question per screen**
3. **Progressive disclosure** — APS depth pattern reused for Portfolio/Review
4. **Dock → nav migration** — Trades becomes Home › Review or Journal › Execution
5. **Command palette (⌘)** — symbol jump to Research; preserve power-user path
6. **Mobile:** bottom nav, 5 items, Home centered emphasis

### V2 → V3 navigation mapping

| V2 | V3 |
|----|-----|
| Today dock | Home |
| Trades dock | Home › Review Workspace **or** Journal › Active plan |
| You dock | You (+ Investor DNA expand) |
| Legacy tabs | Redirect aliases → Portfolio / Research / Journal |

---

## 11. Screen Map

```text
HOME
├── Command Center (V2 — frozen layout)
├── Understand popover → Review Depth compositor
└── Proof overlay (optional)

PORTFOLIO
├── Overview (allocation, health score)
├── Holdings (broker truth)
├── Positions (intraday if connected)
├── Wealth (SIP / goals — sacred core)
└── Doctor (monthly — drift, concentration)

RESEARCH
├── Symbol workbench
├── Explore / screener
└── Alpha AI deep report

JOURNAL
├── This week (Weekly Review)
├── Decision receipts
├── Trade log (broker reconcile)
└── Calibration

YOU
├── Reflection (existing)
├── Trust depth
├── Investor DNA (V3.2)
└── Settings (nested)
```

*Screen-level specs deferred to Phase 1 ETS documents.*

---

## 12. Roadmap

| Phase | Name | Outcome | Target |
|-------|------|---------|--------|
| **0** | Vision & Strategy | This document set | 2026-08 |
| **1** | Portfolio Intelligence | Portfolio page + contracts | Q4 2026 |
| **2** | Decision Memory | Receipts + Weekly Review | Q1 2027 |
| **3** | Review Cadences | Monthly Doctor + Quarterly | Q2 2027 |
| **4** | Capital & Thesis | New Capital + Thesis Tracker | Q3 2027 |
| **5** | OS Consolidation | 5-page nav, legacy tab retirement | Q4 2027 |

*Detail: [APEX_V3_ROADMAP.md](./APEX_V3_ROADMAP.md)*

---

## 13. Technical Architecture Impact

### Frozen (no change without ADR)

```text
DecisionContextBundle → DecisionArtifact → MorningBriefViewModel
  → Presentation Contracts → Components → Theme → Render-only UI
```

### V3 extensions (allowed pattern)

| Layer | V3 addition | Rule |
|-------|-------------|------|
| **Domain** | `PortfolioViewModel`, `WeeklyReviewViewModel`, `DecisionReceipt` | Domain owns assembly |
| **Contracts** | New presentation contracts per surface | Versioned; APS pattern |
| **Components** | New renderers; reuse `decision_depth_panel` pattern | Compositors, not copies |
| **Theme** | Extend tokens; no duplicate CSS blocks | SSOT in `theme.py` |
| **Navigation** | Shell refactor | Presentation routing only |

### Explicit non-changes

- No verdict logic in UI
- No new decision engine shortcuts
- No analyzer imports for ranking in Tier A projections
- Regression gate grows; never shrinks without ADR

---

## 14. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Scope creep into trading app | High | Constitution + out-of-scope list; design review gate |
| Portfolio page duplicates Kite | Medium | Broker as source of truth; APEX adds *interpretation* |
| Navigation migration confuses V2 users | Medium | Aliases, phased rollout, Home unchanged |
| Contract proliferation | Medium | Compositor pattern; shared section renderers |
| Legacy tab debt | Medium | Phase 5 consolidation; redirect map |
| Over-reliance on manual QA | Medium | Extend RC-001 integration test pattern |
| Wealth plan / DNA scope ambiguity | Low | Phase 4+; explicit defer in backlog |

---

## 15. Success Metrics

### North star

**Decision quality index** — composite of discipline adherence + user-reported clarity (not P&L)

### V3 KPIs

| Metric | Baseline (V2) | V3 target |
|--------|---------------|-----------|
| Morning time-to-verdict | < 30s | Maintain |
| Weekly Review completion | — | 40% of WAU |
| Decision receipt open rate | — | 60% of ACT/WAIT |
| Portfolio page weekly visits | — | 50% of connected users |
| Trust score (in-app) | — | ≥ 4.2 / 5 |
| Test suite | 687/687 | Maintain 100% gate |
| Support tickets "what should I do?" | — | −30% |

### Anti-metrics (watch)

- Trades per user per day (should not increase)
- Session length without review completion (should not be goal)
- Popover depth without primary CTA awareness (confusion signal)

---

## 16. Out-of-Scope Items

Per [MASTER_PROMPT](../../.cursor/MASTER_PROMPT.md) — **never in V3 without constitution amendment:**

- Copy trading · social feed · leaderboards · streaks
- Crypto · futures · gamification · influencer rankings
- Trending stocks · clickbait news · reward systems
- AI chatbot as primary interface
- New technical indicators / prediction engine
- Multi-tenant SaaS (separate RFC-001 track)
- Implementation changes to frozen V2 Home Command Center hierarchy

### Deferred beyond V3 program

- Full mobile native app
- Multi-broker support (non-Zerodha)
- Tax filing automation
- Automated order execution (APEX remains decision, not execution)

---

## Approval

| Role | Name | Status |
|------|------|--------|
| Product | — | Pending review |
| CTO | — | Pending review |
| Engineering | — | Pending review |
| UX | — | Pending review |

**Next step:** Product Review → Phase 1 ETS scoping (Portfolio Intelligence)
