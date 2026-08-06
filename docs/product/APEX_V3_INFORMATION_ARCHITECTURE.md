# APEX V3 — Information Architecture

**Document ID:** APEX-V3-IA  
**Version:** 0.1  
**Status:** DRAFT — Phase 0  
**Date:** 2026-08-06  
**Owner:** Product · UX  
**Parent:** [APEX_V3_PRODUCT_STRATEGY.md](./APEX_V3_PRODUCT_STRATEGY.md)  
**References:** [20_Product_Information_Architecture.md](../architecture/20_Product_Information_Architecture.md) · [APEX-014](../apex/APEX-014_V2_Architecture_and_Release.md)

---

## 1. Design Principles

1. **One primary question per page** (frozen)
2. **Answer before explanation** — hero + progressive disclosure
3. **Home is sacred** — V2 Command Center hierarchy unchanged
4. **Broker is source of truth** for P&L and holdings
5. **Legacy absorbs, never proliferates** — tabs become sections
6. **Composable depth** — reuse Review Depth / APS pattern

---

## 2. Top-Level Structure

### V3 target (5 pages)

```text
┌────────────────────────────────────────────────────────────┐
│  HOME  │  PORTFOLIO  │  RESEARCH  │  JOURNAL  │  YOU       │
└────────────────────────────────────────────────────────────┘
```

### V2 current (3 dock — migration source)

```text
┌──────────────────────────────┐
│  TODAY  │  TRADES  │  YOU     │
└──────────────────────────────┘
```

---

## 3. Page Definitions

### 3.1 HOME — *What should I do today?*

| Attribute | Value |
|-----------|-------|
| **Default landing** | Yes |
| **V2 baseline** | Home Command Center (frozen) |
| **Primary CTA** | Verdict action + Understand |
| **Data sources** | MBVM, DecisionArtifact, broker sync |

**Sections (top → bottom — frozen V2):**

1. Verdict Hero  
2. Action Row  
3. Status Strip  
4. Supporting Context (priority, market, connection, learning)

**Sub-routes (V3):**

| Route | Purpose |
|-------|---------|
| Home › Review | Review Workspace (from V2 Trades) when ACT |
| Home › Proof | Proof overlay |

---

### 3.2 PORTFOLIO — *What do I own and is it healthy?*

| Attribute | Value |
|-----------|-------|
| **New in V3** | Phase 1 |
| **Primary CTA** | View holding · Run Doctor |
| **Data sources** | Kite holdings/positions, portfolio use cases |

**Sub-tabs (max 5):**

| Tab | Question |
|-----|----------|
| Overview | How am I allocated? |
| Holdings | What do I own? |
| Positions | What's active today? |
| Wealth | Am I on SIP/goal track? |
| Doctor | What needs attention? (monthly) |

**Progressive disclosure:** Holding row → symbol Research handoff; depth via APS contracts

---

### 3.3 RESEARCH — *Why is this true?*

| Attribute | Value |
|-----------|-------|
| **Absorbs** | Alpha AI, screener, symbol workbench, Explore |
| **Primary CTA** | Open report · Add to watchlist |
| **Entry** | Command palette, Portfolio tap, Home priority |

**Sub-tabs:**

| Tab | Content |
|-----|---------|
| Workbench | Symbol-centric APS depth + charts |
| Explore | Screener / discovery (curated, not trending) |
| Reports | Alpha AI saved reports |

**Rule:** Research explains; it does **not** issue daily verdict (Home owns that)

---

### 3.4 JOURNAL — *What happened and what did I learn?*

| Attribute | Value |
|-----------|-------|
| **Absorbs** | Trade journal, track record, calibration |
| **Primary CTA** | View receipt · Weekly review |

**Sub-tabs:**

| Tab | Content |
|-----|---------|
| This Week | Weekly Review (V3 Phase 2) |
| Receipts | Decision Receipts |
| Trades | Broker-reconciled log |
| Calibration | System vs outcome |

**V2 migration:** Trades dock execution history → Journal › Trades

---

### 3.5 YOU — *Who am I as an investor?*

| Attribute | Value |
|-----------|-------|
| **V2 baseline** | Reflection + Trust canvases |
| **V3 expand** | Investor DNA, preferences |

**Sub-tabs:**

| Tab | Content |
|-----|---------|
| Reflection | Weekly you (existing) |
| Trust | Trust depth (existing) |
| DNA | Investor profile (Phase 5) |
| Settings | Capital, Kite, prefs (nested) |

---

## 4. Navigation Model

### 4.1 Primary navigation

| Platform | Pattern |
|----------|---------|
| Desktop | Top bar, 5 items, Home visually primary |
| Mobile | Bottom bar, 5 items, safe-area aware |

### 4.2 Secondary navigation

- **Segmented control** inside page (max 5 sub-tabs)
- **Breadcrumbs** for Research symbol depth only
- **No tertiary nav** — use expanders (APS pattern)

### 4.3 Global affordances

| Affordance | Behavior |
|------------|----------|
| ⌘ Jump / Command palette | Symbol → Research workbench |
| Ask FAB | Overlay (existing — unchanged) |
| Broker status chip | Header; sync state |
| Back to Today | Contextual on Review routes |

### 4.4 Redirect map (legacy → V3)

| Legacy | V3 destination |
|--------|----------------|
| Suggestions / Intraday | Home › Review |
| My Portfolio | Portfolio › Holdings |
| Alpha AI | Research › Reports |
| Track Record | Journal › Trades |
| Daily Advisor | Portfolio › Doctor |
| Setup / Kite | You › Settings |

---

## 5. Content Hierarchy Template

Every V3 surface follows V2 Command Center pattern:

```text
┌─────────────────────────────┐
│ HERO — one-line answer      │
├─────────────────────────────┤
│ ACTION ROW — primary CTA    │
├─────────────────────────────┤
│ STATUS STRIP — key facts     │
├─────────────────────────────┤
│ CONTEXT — below fold         │
│   └── progressive disclosure │
└─────────────────────────────┘
```

Apply to: Portfolio Overview, Weekly Review, Monthly Doctor

---

## 6. Data & Trust Boundaries

| Surface | APEX interprets | Broker proves |
|---------|-------------------|---------------|
| Home verdict | ✅ | Sync status |
| Portfolio holdings | Health, allocation | Quantities, P&L |
| Journal trades | Discipline, receipts | Fill prices |
| Research | Thesis, risk | Price data feeds |

Footer pattern (V2): *"Zerodha Console is source of truth for P&L."*

---

## 7. Accessibility & Performance (carry forward)

- Semantic landmarks per page (`main`, `region`, `aria-labelledby`)
- `:focus-visible` on all interactive elements
- `prefers-reduced-motion` respected
- `content-visibility` on below-fold sections
- Pre-built CSS bundles per page family (extend `APEX_PARTNER_EXPERIENCE_CSS` pattern)

---

## 8. IA Migration Phases

| Phase | IA change |
|-------|-----------|
| V2 GA | 3 dock (frozen) |
| V3-1 | Add Portfolio tab (4 items) |
| V3-2 | Add Journal tab (5 items) |
| V3-3 | Rename/route Trades → Home/Journal |
| V3-5 | Retire legacy Streamlit tabs; redirects only |

---

## 9. Wireframe Index (Phase 1 ETS scope)

| Screen ID | Name | Phase |
|-----------|------|-------|
| SCR-H-001 | Home Command Center | V2 ✅ |
| SCR-P-001 | Portfolio Overview | V3-1 |
| SCR-P-002 | Holdings List | V3-1 |
| SCR-P-003 | Portfolio Doctor | V3-3 |
| SCR-J-001 | Weekly Review | V3-2 |
| SCR-J-002 | Decision Receipt Detail | V3-2 |
| SCR-R-001 | Symbol Workbench | V3-4 |
| SCR-Y-001 | Investor DNA | V3-5 |

*High-fidelity design deferred to Phase 1 kickoff.*

---

## 10. IA Success Criteria

- [ ] User can reach any V3 surface in ≤ 2 taps from Home
- [ ] Home Command Center pixel hierarchy unchanged post-migration
- [ ] Zero new top-level Streamlit tabs at V3 GA
- [ ] All legacy bookmarks redirect correctly
- [ ] One compositor pattern per depth type (Review, Portfolio, Journal)
