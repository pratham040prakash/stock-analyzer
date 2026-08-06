# V3 Portfolio Review — Product & UX Design

**Document ID:** V3-PR-001  
**Version:** 1.0  
**Status:** APPROVED — FROZEN (V3-103)  
**Date:** 2026-08-06  
**Owner:** Product · UX · Architecture  
**Baseline:** V3-102 Holdings Experience @ `c6629cf` · v2.0.0 GA (frozen architecture)  
**Parent:** [V3_PORTFOLIO_COMMAND_CENTER.md](./V3_PORTFOLIO_COMMAND_CENTER.md) · [V3_HOLDINGS_EXPERIENCE.md](./V3_HOLDINGS_EXPERIENCE.md) · [APEX_V3_INFORMATION_ARCHITECTURE.md](./APEX_V3_INFORMATION_ARCHITECTURE.md)  
**Screen ID:** SCR-P-003 (Portfolio › Review)

---

## Design Questions — Answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What should the investor see first? | **Portfolio explanation headline** — one paragraph: why the portfolio is healthy or what needs review. Not a duplicate Health Hero. Not a metrics strip. |
| 2 | What deserves the largest visual emphasis? | The **theme-based review queue** (portfolio problems with affected holdings) or **reassurance themes** when healthy. |
| 3 | What actions should be immediately available? | **Primary:** Review next item · **Secondary:** Help me understand · **Tertiary:** Open Holdings · Back to Overview. |
| 4 | What belongs above the fold? | Context header · explanation summary · first review item (or healthy reassurance block). |
| 5 | What belongs below the fold? | Remaining queue · allocation/policy explanation · broker footer. |
| 6 | What should never appear? | Duplicate Overview hero · full holdings table · buy/sell signal grid · analyze gate · trading CTAs · new health scores computed on-screen. |

**10-second test:** User reads headline → understands *why* the portfolio is in its current state → knows the single next review action.

---

## 1. Executive Summary

**V3-103 Portfolio Review** (SCR-P-003) answers:

> **Why is my portfolio healthy or unhealthy, and what should I review next?**

It is the **explanation and guided review layer** — not a third dashboard.

| Surface | Question | Role |
|---------|----------|------|
| **Overview** (V3-101) | Is it healthy? | Verdict + snapshot |
| **Holdings** (V3-102) | What exactly do I own? | Inventory ledger |
| **Review** (V3-103) | Why, and what next? | Theme-based review workflow |

Overview tells the user *that* something needs attention. Review explains *why* at the **portfolio-theme level** — Sector Concentration, Single Position Risk, Policy Drift, etc. — and lists **affected holdings** under each theme. The portfolio problem owns the holdings; holdings do not own the queue.

**Queue model (P1):** Each review item is a **portfolio theme**, not a ticker row. Every theme item includes: explanation · affected holdings · investigation guidance · Understand · Open Research (symbol picker when multiple holdings affected).

**Architecture constraint:** Reuses `PortfolioOverviewViewModel` (`attention_items`, `depth_sections`, `allocation`, `holdings_rows`). Theme grouping is **projection-only** in a future `portfolio_review_from_view_model()` — no new health rules, no analyzer changes. Shared Understand framework for depth.

**Primary entry:** Overview Primary CTA (`Review N items`). Secondary: Review sub-nav tab.

---

## 2. User Problem

| Problem | Today | V3 Portfolio Review |
|---------|-------|---------------------|
| **Verdict without reasoning** | Overview says "Needs attention" but user must open Understand popover for depth | Dedicated screen synthesizes *why* in plain language first |
| **Attention list too shallow** | Overview shows max 3 one-line rows | Review expands each item with context, implication, and suggested next step |
| **Healthy = no guidance** | Healthy portfolio offers reassurance only | Review explains *why* healthy (diversification, policy alignment) — teaches discipline |
| **Review workflow unclear** | User doesn't know order to tackle items | Prioritized queue with explicit "review next" progression |
| **Explanation scattered** | Allocation, concentration, policy spread across popover sections | Unified **Portfolio Explanation Model** on one screen |
| **Holdings confusion** | User opens Holdings looking for "why" | Review owns explanation; Holdings owns inventory |
| **Research handoff abrupt** | Attention row jumps to Research without framing | Each item includes "what to verify in Research" before handoff |

---

## 3. Wireframes (ASCII)

### 3.1 Desktop — needs attention (2 themes)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  [ Home ] [ Portfolio ● ] [ Research ] [ Journal ] [ You ]     🟢 Synced 2m  │
├──────────────────────────────────────────────────────────────────────────────┤
│  Overview │ Review ● │ Holdings │ Wealth │ Doctor                             │
├──────────────────────────────────────────────────────────────────────────────┤
│  ← Back to Overview                                                          │
│                                                                              │
│  ┌─ PORTFOLIO EXPLANATION ──────────────────────────────────────────────────┐ │
│  │  Your portfolio needs review because concentration in Financial Services │ │
│  │  exceeds your policy limit, and one holding shows deteriorating health.  │ │
│  │  This does not require immediate trading — review before your next       │ │
│  │  decision window.                                                        │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Review progress · 0 of 2 themes reviewed                                    │
│                                                                              │
│  ┌─ REVIEW QUEUE (portfolio themes) ────────────────────────────────────────┐ │
│  │  1. ● Sector Concentration                                  [ Current ▾ ] │ │
│  │     Financial Services is 62% of your portfolio vs 40% policy limit.    │ │
│  │     Affected holdings: HDFCBANK (14%) · ICICIBANK (11%) · SBIN (9%)      │ │
│  │     Investigate: Is sector overweight intentional? Rebalance plan?        │ │
│  │     [ Help me understand ▾ ]  [ Open Research ▾ ]  [ Mark reviewed ✓ ]  │ │
│  │  ─────────────────────────────────────────────────────────────────────── │ │
│  │  2. ○ Single Position Risk — WIPRO                                        │ │
│  │     WIPRO is 18% of portfolio — above 15% single-name guideline.          │ │
│  │     Affected holdings: WIPRO (18%)                                      │ │
│  │     [ Expand ]                                                            │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ ALLOCATION & POLICY (collapsed summary) ────────────────────────────────┐ │
│  │  Core 58% · Tactical 32% · Cash 10% — vs policy: concentration review    │ │
│  │  [ Help me understand ▾ ]                                                  │ │
│  └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Zerodha Console is source of truth for holdings and P&L.                    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Desktop — healthy portfolio

```text
┌─ PORTFOLIO EXPLANATION ──────────────────────────────────────────────────────┐
│  Your portfolio is healthy. Holdings are diversified across 12 names with no  │
│  single position above guideline weight, and allocation matches your policy.  │
└──────────────────────────────────────────────────────────────────────────────┘

┌─ REASSURANCE BLOCK ──────────────────────────────────────────────────────────┐
│  ✓ Concentration within limits                                               │
│  ✓ Allocation on track (Core / Tactical / Cash)                              │
│  ✓ No sync or data freshness issues                                          │
│  Nothing requires review today.                                              │
└──────────────────────────────────────────────────────────────────────────────┘

[ View holdings ]          [ Help me understand ▾ ]

Optional: "Last reviewed · today" (session marker — future Journal link)
```

### 3.3 Desktop — theme expanded (Understand inline)

```text
┌─ Sector Concentration — Understand ──────────────────────────────────────────┐
│  ▾ Why this theme was flagged                                                │
│     Financial Services at 62% vs 40% policy limit.                           │
│  ▾ Affected holdings                                                         │
│     HDFCBANK 14% · ICICIBANK 11% · SBIN 9%                                   │
│  ▾ Investigation guidance                                                    │
│     Confirm whether sector overweight is intentional; check next-buy plan.    │
│  ▾ What could change                                                         │
│     New buys, sector rotation, or policy update.                              │
│  [ Open Research ▾ ]  HDFCBANK · ICICIBANK · SBIN                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Mobile

```text
┌─────────────────────────┐
│ ← Overview    Review ●  │
├─────────────────────────┤
│ Your portfolio needs    │
│ review because…         │
│ (2–3 lines max)         │
├─────────────────────────┤
│ 0 of 2 reviewed         │
├─────────────────────────┤
│ ┌─ 1. Sector Conc. ───┐ │
│ │ 62% vs 40% policy   │ │
│ │ HDFCBANK · ICICI…   │ │
│ │ [Understand][Research]│
│ └─────────────────────┘ │
│ ┌─ 2. Single Position ┐ │
│ │ WIPRO 18% · tap     │ │
│ └─────────────────────┘ │
├─────────────────────────┤
│ ▾ Allocation & policy   │
│ Broker truth footer     │
└─────────────────────────┘
```

### 3.5 Disconnected / stale

```text
┌─ PORTFOLIO EXPLANATION ──────────────────────────────────────────────────────┐
│  Review is based on your saved snapshot (Aug 5). Connect for live review.   │
└──────────────────────────────────────────────────────────────────────────────┘

[ Connect Zerodha ]     [ Continue with snapshot review ]
```

---

## 4. Component Hierarchy

```text
PortfolioPageShell (shared)
├── PrimaryNav
├── PortfolioSubNav (Overview | Review ● | Holdings | Wealth | Doctor)
└── PortfolioReviewExperience (Review tab / route only)
    ├── ReviewContextHeader
    │   ├── BackLink (→ Overview)
    │   └── SyncChip (reuse pattern — optional)
    ├── PortfolioExplanationBlock
    │   ├── ExplanationHeadline (synthesized narrative)
    │   └── ExplanationQualifier (stale / snapshot / calm framing)
    ├── ReviewProgressStrip (N of M reviewed — attention mode only)
    ├── ReviewActionRow
    │   ├── PrimaryCTA (Review next · View holdings · Connect)
    │   └── UnderstandGateway (portfolio-level — reuse framework)
    ├── ThemeReviewQueue
    │   └── ThemeReviewItem (repeat, max 3 themes — projected from VM)
    │       ├── PriorityIndex
    │       ├── ThemeTitle (e.g. Sector Concentration)
    │       ├── ThemeExplanation (portfolio-level narrative)
    │       ├── AffectedHoldingsList (symbols + weights — subordinate)
    │       ├── InvestigationGuidance (what to verify)
    │       ├── ThemeUnderstandPopover (shared framework)
    │       ├── ResearchHandoffMenu (single symbol or picker if N holdings)
    │       └── MarkReviewedControl (session state — presentation only)
    ├── HealthyReassuranceBlock (when attention empty)
    │   └── ReassuranceChecklist (from depth_sections + health state)
    ├── AllocationPolicyReviewSection
    │   ├── SummaryLine (from allocation + policy_line)
    │   └── UnderstandGateway (depth sections — no duplicate popover impl)
    ├── ReviewCompleteState (all items marked — optional inline)
    └── BrokerTruthFooter (reuse copy pattern)
```

**Render rule (future):** Projection from `PortfolioOverviewViewModel` only. Session "reviewed" markers are UI state — not business logic.

---

## 5. Information Hierarchy

### 5.1 Page-level priority (top → bottom)

| Rank | Element | User need |
|------|---------|-----------|
| 1 | Explanation headline | Why healthy or unhealthy — the answer |
| 2 | Review progress | Where am I in the workflow |
| 3 | Current / next queue item | What to review now |
| 4 | Item explanation body | Understand the flag in context |
| 5 | Suggested next step | Actionable guidance (not trade order) |
| 6 | Understand / Research actions | Depth on demand |
| 7 | Remaining queue items | What's next after current |
| 8 | Allocation & policy summary | Structural context (collapsed when queue active) |
| 9 | Broker footer | Trust |

### 5.2 Per theme item priority

```text
Theme title → Explanation (portfolio fact) → Affected holdings → Investigation guidance → Actions
```

**Rule:** Theme title leads. Holdings are evidence listed under the theme — never the queue headline.

### 5.3 What sibling screens already answered — do not repeat

| From Overview | Do not duplicate on Review |
|---------------|----------------------------|
| Health Hero badge + headline | Use explanation synthesis, not same hero component |
| Status Strip chips | Optional sync chip only |
| Standouts card | Not shown |
| Holdings preview | Link to Holdings tab instead |
| Full allocation bar chart | Summary line + Understand only |

| From Holdings | Do not duplicate on Review |
|---------------|----------------------------|
| Full holdings table | Not shown |
| Search / filter / sort | Not shown |
| Quantity / avg cost columns | Reference weight % only when relevant to flag |

---

## 6. Review Workflow

### 6.1 Entry paths

```text
Overview Primary CTA ("Review N items")
    → Portfolio Review (focus first queue item)

Overview Understand popover → "Review in depth"
    → Portfolio Review

Portfolio sub-nav → Review tab
    → Portfolio Review (default: explanation + queue or reassurance)

Holdings row Understand → "See portfolio review"
    → Portfolio Review (scroll to symbol's queue item if flagged)
```

### 6.2 Attention workflow (primary)

```text
1. READ    Explanation headline (why portfolio flagged)
2. ORIENT  Progress strip (N of M)
3. FOCUS   First queue item expanded by default
4. DEEPEN  Optional Understand popover per item
5. ACT     Research handoff OR Mark reviewed (session)
6. ADVANCE Primary CTA → next item auto-expands
7. COMPLETE All reviewed → reassurance + "Back to Overview"
```

### 6.3 Healthy workflow

```text
1. READ    Explanation (why healthy)
2. SCAN    Reassurance checklist (3–4 bullets from depth_sections)
3. OPTIONAL Understand popover (allocation / policy education)
4. EXIT    View holdings OR Back to Overview
```

### 6.4 Edge — zero attention but stale sync

Explanation qualifies review scope · Primary CTA = Sync · Queue hidden.

### 6.5 Session rules

- `Mark reviewed` is **session-only** — resets on reload (no persistence in V3-103)
- Future Journal links decision receipts to reviewed items (Phase 2)

---

## 7. Portfolio Explanation Model

### 7.1 Source of truth (frozen)

All explanation content projects from **`PortfolioOverviewViewModel`** fields already assembled in V3-101:

| VM field | Review use |
|----------|------------|
| `health.badge_key` | Modes: healthy · attention · connect · stale qualifier |
| `health.headline` + `supporting_reason` | Seeds explanation headline (rephrased, not copied verbatim) |
| `attention_items[]` + `holdings_rows[]` + `allocation` | Grouped into theme queue items (projection) |
| `allocation` + `policy_line` | Allocation/policy section |
| `depth_sections[]` | Understand popover + item implication text |
| `attention_empty_message` | Healthy reassurance fallback |

**No new assembly functions for health.** Future implementation adds `portfolio_review_from_view_model()` — projection only.

### 7.2 Explanation headline synthesis (projection rules)

| State | Headline pattern |
|-------|------------------|
| Attention | "Your portfolio needs review because {primary reason}. {Calm qualifier}." |
| Healthy | "Your portfolio is healthy. {Supporting reason from health section}." |
| Connect | "Connect your broker to review portfolio health and allocation." |
| Stale | Prefix: "Based on {snapshot date} — " then attention/healthy pattern |

Primary reason = first `attention_items[0].reason` or synthesized concentration summary.

Calm qualifier (fixed copy pool): *"This does not require immediate trading — review before your next decision window."*

### 7.3 Theme item template (P1)

Each **theme** queue item renders five blocks (projected from existing VM data — no new scoring):

| Block | Source | Example |
|-------|--------|---------|
| **Theme title** | Theme taxonomy (see §8) | Sector Concentration |
| **Explanation** | `attention_items` + `depth_sections` | Financial Services 62% vs 40% policy |
| **Affected holdings** | `holdings_rows` filtered by theme | HDFCBANK 14% · ICICIBANK 11% |
| **Investigation guidance** | Theme template + depth lines | Is overweight intentional? Check next-buy plan. |
| **Actions** | Shared UX | Understand · Open Research (menu) · Mark reviewed |

**Open Research:** Single holding → direct handoff. Multiple holdings → compact symbol menu (max 5 shown + "View all in Holdings").

### 7.4 Healthy reassurance checklist

Derived from depth_sections + health badge — not new scoring:

- Concentration within limits (from Concentration section negative)
- Allocation on track (`allocation.policy_line` contains "on track")
- No attention items
- Sync fresh (when `stale_qualified` false)

---

## 8. Theme Review Queue (P1 — portfolio themes, not holdings)

### 8.1 Design principle

The queue is **theme-first**. Each row is a portfolio-level review topic. Holdings appear as **affected symbols under the theme** — evidence, not the headline.

```text
Sector Concentration          ← theme owns the queue
    ↓
Affected: HDFCBANK · ICICIBANK · SBIN
    ↓
Investigation guidance
    ↓
Understand · Open Research
```

### 8.2 Theme taxonomy (V3-103)

| Theme | When surfaced | VM projection inputs |
|-------|---------------|-------------------|
| **Sector Concentration** | Sector/group weight exceeds policy | `attention_items` Concentration + sector grouping from `holdings_rows` |
| **Single Position Risk** | One name above single-stock guideline | `attention_items` Concentration per symbol + `holdings_rows.weight_pct` |
| **Cash Allocation** | Cash buffer below policy minimum | `allocation.cash_pct` + `policy_line` |
| **Diversification** | Healthy — positive reassurance theme | No attention + depth Concentration lines negative |
| **Policy Drift** | Core / Tactical / Cash off policy | `allocation` + `policy_line` |
| **Tax Review** | Future — tax-loss / STCG flags | Placeholder; not in V3-103 VM — extensibility slot |

Themes are **deduplicated** at projection: two concentration flags on symbols in the same sector merge into one **Sector Concentration** theme.

### 8.3 Theme item structure (required fields)

Every surfaced theme includes:

1. **Explanation** — portfolio-level fact in plain language  
2. **Affected holdings** — bullet or inline list: `SYMBOL (weight%)`  
3. **Investigation guidance** — what to verify before acting  
4. **Help me understand** — theme-scoped Understand popover (`depth_sections` subset)  
5. **Open Research** — navigation only; symbol menu when N > 1  

### 8.4 Prioritization order (projection rules)

Max **3 themes** (matches Overview attention cap). Priority:

1. Sector Concentration  
2. Single Position Risk  
3. Policy Drift  
4. Cash Allocation  
5. Diversification (healthy mode only — reassurance, not queue)  
6. Tax Review (future)

Within a theme, affected holdings sort by **weight ↓**.

### 8.5 Priority visual encoding

| Position | Visual |
|----------|--------|
| Current theme | Expanded · `●` · focus ring |
| Pending theme | Collapsed · `○` |
| Reviewed (session) | Muted · `✓` · collapsed |

### 8.6 Healthy portfolio themes

When no attention themes qualify, **Diversification** and **Policy Drift** (on track) appear in the **Reassurance block** — not as action queue items.

---

## 9. Progressive Disclosure

| Layer | Content | Access |
|-------|---------|--------|
| **L0 — Explanation headline** | Why healthy / unhealthy | Always visible |
| **L1 — Queue item summary** | Flag + one-line reason | Always visible (collapsed siblings) |
| **L2 — Item body** | Implication + verify hint | Expanded item |
| **L3 — Item Understand popover** | Full depth_sections subset | Explicit tap |
| **L4 — Portfolio Understand popover** | All depth sections | Action row |
| **L5 — Research Workbench** | Symbol APS depth | Handoff button |
| **L6 — Holdings tab** | Inventory confirmation | Tertiary link |

**Rule:** L0 answers the primary question. L3 never gates L0.

### 9.1 Allocation section disclosure

- **Attention mode:** Collapsed summary line; expand or Understand for full policy math
- **Healthy mode:** Inline reassurance bullet; Understand optional

---

## 10. Research Handoff

### 10.1 Handoff rules

| Trigger | Behavior |
|---------|----------|
| Queue item **Open Research →** | `request_nav_tab("Single Stock", symbol)` — navigation only |
| Understand **Open Research →** | Same — no analysis executed on Review screen |
| Symbol "—" (portfolio-level flag) | No Research handoff — link to Overview Understand or Settings |

Reuse `_research_handoff()` from V3-101 — no duplicate navigation logic.

### 10.2 Framing before handoff

Each item shows **"What to verify in Research"** line before button — sets expectation, reduces FOMO.

### 10.3 Return path

Research → Back → Portfolio Review (preserve session reviewed state via session key).

---

## 11. Accessibility

| Requirement | Implementation |
|-------------|----------------|
| **Landmarks** | `main` for review region; `region` + `aria-labelledby` per queue item |
| **Headline** | `h2` for explanation; not `role="status"` (not live updating like hero) |
| **Queue** | Ordered list semantics (`ol`) or `role="list"` with position labels |
| **Progress** | `aria-valuenow` / `aria-valuemax` on progress strip |
| **Expand/collapse** | `aria-expanded` on queue items |
| **Health chips** | Text + icon — not color alone |
| **Focus** | `:focus-visible` on all CTAs (V2-004 pattern) |
| **Screen reader** | Progress announces "Review theme 1 of 2. Sector Concentration. Three holdings affected." |
| **Motion** | `prefers-reduced-motion` — no expand animation |
| **Touch targets** | ≥44×44px on mobile item actions |

---

## 12. Performance

| Technique | Application |
|-----------|-------------|
| **Single VM assembly** | Same `assemble_portfolio_overview()` call as Overview — cache in page session |
| **No second health pass** | Review projection reads cached VM |
| **Lazy popover** | Understand body on first open |
| **Queue cap** | Max 3 items — no virtualization needed |
| **content-visibility** | Allocation section + collapsed items deferred |
| **Targets** | LCP ≤2.5s cached · expand item <100ms |

---

## 13. Future Extensibility

| Extension | Hook | Phase |
|-----------|------|-------|
| Persist reviewed state | Journal decision receipts | V3-2 |
| Weekly Review integration | Link queue items to Weekly Review ritual | V3-2 |
| Doctor tab handoff | Monthly deep report replaces session review | V3-3 |
| Sector filter in queue | When sector map in VM | V3-104 |
| Policy editor inline | You › Capital Allocation | V3-4 |
| Review history | "Reviewed Aug 1" audit trail | V3-2 |

**Contract stability:** Future `PortfolioReviewContract` projects from existing VM fields + optional `review_synthesis_lines: tuple[str, ...]` if assembly adds narrative (requires approval — not V3-103).

**Architecture alignment (future implementation):**

```text
PortfolioOverviewViewModel (unchanged assembly)
    → portfolio_review_from_view_model()   [projection only]
    → PortfolioReviewContract
    → portfolio_review_experience.py       [render-only]
    → understand_popover.py                [shared]
```

---

## Appendix A — Sub-nav placement

Phase 1 sub-nav when Review ships:

```text
Overview | Review | Holdings | Wealth | Doctor
           ●
Positions tab deferred — Review occupies second slot as explanation route.
```

Overview remains default landing. Review tab visible always; badge dot when `attention_items` non-empty (optional).

---

## Appendix B — State matrix

| Broker | Attention | Screen mode | Primary CTA |
|--------|-----------|-------------|-------------|
| Connected | >0 | Review queue | Review next item |
| Connected | 0 | Healthy reassurance | View holdings |
| Connected · stale | any | Qualified explanation | Sync now |
| Disconnected · snapshot | >0 | Snapshot review | Connect |
| Disconnected · empty | 0 | Connect empty | Connect |

---

## Appendix C — Acceptance criteria (Product Review)

- [ ] Primary question answered in explanation headline without scrolling
- [ ] No duplicate Overview Health Hero component
- [ ] No duplicate Holdings table
- [ ] Queue is theme-first; holdings subordinate (P1)
- [ ] Each theme item includes explanation · affected holdings · guidance · Understand · Research
- [ ] Max 3 themes; projection from VM without new health rules
- [ ] Healthy state provides educational reassurance, not empty page
- [ ] Shared Understand framework specified — no duplicate popover UX
- [ ] Research handoff navigation-only
- [ ] Review workflow documented (read → focus → deepen → act → advance)
- [ ] Accessibility and performance sections complete
- [ ] Future implementation respects frozen architecture

---

## Appendix D — Related documents

| Document | Relationship |
|----------|--------------|
| [V3_PORTFOLIO_COMMAND_CENTER.md](./V3_PORTFOLIO_COMMAND_CENTER.md) | Entry via Primary CTA |
| [V3_HOLDINGS_EXPERIENCE.md](./V3_HOLDINGS_EXPERIENCE.md) | Sibling — inventory only |
| [APEX-015](../apex/APEX-015_V3-101_Portfolio_Command_Center.md) | Assembly SSOT |
| [APEX-016](../apex/APEX-016_V3-102_Holdings_Experience.md) | Holdings sibling pattern |

---

*End of document — awaiting Product Review.*
