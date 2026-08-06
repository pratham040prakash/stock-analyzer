# V3 Research Workspace — Product & UX Design

**Document ID:** V3-RW-001  
**Version:** 1.0  
**Status:** APPROVED — FROZEN (V3-201)  
**Date:** 2026-08-06  
**Owner:** Product · UX · Architecture  
**Baseline:** V3-103 Portfolio Review @ `197ef8a` · Portfolio Pillar COMPLETE · v2.0.0 GA (frozen architecture)  
**Parent:** [APEX_V3_PRODUCT_STRATEGY.md](./APEX_V3_PRODUCT_STRATEGY.md) · [APEX_V3_INFORMATION_ARCHITECTURE.md](./APEX_V3_INFORMATION_ARCHITECTURE.md) · [V3_PORTFOLIO_REVIEW.md](./V3_PORTFOLIO_REVIEW.md)  
**Screen ID:** SCR-R-001 (Research › Workbench)

---

## Design Questions — Answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What should the investor see first? | **Investment View Hero** — one plain-language answer to *"Should I invest in this company?"* (e.g. *Attractive for long-term accumulation with elevated valuation risk*). Not a score grid. Not a chart. |
| 2 | What deserves the largest visual emphasis? | The **current research question** in the guided workflow — seven investor questions from business understanding through investment decision. |
| 3 | What actions should be immediately available? | **Primary:** Continue research · **Secondary:** Help me understand · **Tertiary:** Back to source (Portfolio / Home) · Investment Decision. |
| 4 | What belongs above the fold? | Symbol context bar · Investment View Hero · Research progress strip · Question 1 panel (What does this business do?). |
| 5 | What belongs below the fold? | Remaining research questions · Alpha AI deep report link · portfolio/journal handoff footer. |
| 6 | What should never appear? | Daily verdict duplicate (Home owns ACT/WAIT) · Buy/Sell order CTAs · Analyze gate · Trending stocks · Social · Gamification · New scoring computed in UI. |

**10-second test:** User reads hero → knows whether the company fits their criteria at a high level → knows which research question to explore next.

---

## 1. Executive Summary

**V3-201 Research Workspace** (SCR-R-001) answers:

> **Should I invest in this company?**

It is the **symbol-centric decision intelligence surface** — depth on demand, not a daily trading verdict.

| Surface | Question | Role |
|---------|----------|------|
| **Home** (V2) | What should I do today? | Daily verdict for priority symbol |
| **Portfolio** (V3-101–103) | What do I own and is it healthy? | Holdings + theme review |
| **Research Workbench** (V3-201) | Should I invest in this company? | Guided research workflow |

Research **explains and builds conviction** through **seven research questions** — not numbered procedural steps. Each question maps to existing presentation contracts; only the product framing changed in P1.

| # | Research question |
|---|-------------------|
| 1 | What does this business do? |
| 2 | What evidence supports investing? |
| 3 | What could invalidate the thesis? |
| 4 | How strong is my conviction? |
| 5 | Is valuation attractive? |
| 6 | What are the major risks? |
| 7 | What investment decision have I reached? |

Question 7 is the **Investment Decision** surface — user-authored narrative plus disposition (Watch · Hold · Accumulate Later · Avoid). This is **not** Home's daily verdict.

**Architecture constraint:** Reuses frozen pipeline inputs — `DecisionContextBundle`, `DecisionArtifact`, `MorningBriefViewModel` — and existing presentation contracts (`RecommendationContract`, `InvestmentThesisContract`, `BusinessHealthContract`, `RiskMonitorContract`). Future `research_workspace_from_view_model()` is **projection-only**. Shared Understand framework for depth. Alpha AI report is an **optional L5 deep layer**, not the primary shell.

**Primary entry:** Portfolio / Holdings / Review Research handoff · Home opportunity link · Command palette symbol jump · Research sub-nav Workbench with symbol query.

---

## 2. User Problem

| Problem | Today (legacy Alpha AI tab) | V3 Research Workspace |
|---------|----------------------------|------------------------|
| **Overwhelming report dump** | 15 sections scroll wall; answer buried | Answer-first hero + guided 7-question workflow |
| **No workflow** | User doesn't know reading order | Explicit questions an investor actually asks |
| **Disconnected from portfolio** | Symbol research ignores holdings context | Portfolio context chip when symbol is held or flagged |
| **Verdict confusion** | Alpha AI "Strong Buy" feels like trade order | Investment View (qualitative) distinct from Home daily verdict |
| **Evidence scattered** | Facts mixed with opinion without labels | Q2 with FACT · ASSUMPTION · ESTIMATE · OPINION labels |
| **No decision memory** | Research ends in browser tab | Investment Decision → Journal handoff (Phase 2 receipt) |
| **Inconsistent depth** | Custom popovers per section | Shared Understand framework |
| **Mobile unusable** | Desktop report grid | Card-based mobile question flow |

---

## 3. Primary Workflow

```text
Enter symbol context
    → Load DecisionContextBundle (symbol-scoped assembly — future use case; design assumes same frozen types)
    → Project MorningBriefViewModel + DecisionArtifact
    → Investment View Hero (answer-first)
    → Guided research questions (1–7)
    → Optional: Alpha AI deep report (L5)
    → Investment Decision (session draft → Journal)
    → Return to source (Portfolio / Home) with context preserved
```

**Workflow principle:** Each question stands alone as an investor inquiry. User may jump ahead via question nav, but default path is sequential for learning investors.

| Question | Research question | Primary contract source |
|----------|-------------------|-------------------------|
| 1 | What does this business do? | `BusinessHealthContract` + company metadata |
| 2 | What evidence supports investing? | `RecommendationContract.evidence` + `EvidenceSection` |
| 3 | What could invalidate the thesis? | `InvestmentThesisContract` (sell conditions · watch closely · `what_could_change`) |
| 4 | How strong is my conviction? | `RecommendationContract.why` + confidence from `DecisionSection` / artifact |
| 5 | Is valuation attractive? | Valuation slice from Alpha AI projection (APS pattern — future `ValuationContract`; no UI scoring) |
| 6 | What are the major risks? | `RiskMonitorContract` + `RecommendationContract.risks` |
| 7 | What investment decision have I reached? | User-authored Investment Decision + disposition (presentation state; Journal persists) |

---

## 4. Desktop Wireframes

### 4.1 Default — mid-research (Question 2)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│  [ Home ] [ Portfolio ] [ Research ● ] [ Journal ] [ You ]     🟢 Synced 2m  │
├──────────────────────────────────────────────────────────────────────────────┤
│  Workbench ● │ Explore │ Reports                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│  ← Back to Portfolio Review          WIPRO · Held · 18% weight · ⚠ Flagged     │
│                                                                              │
│  ┌─ INVESTMENT VIEW HERO ────────────────────────────────────────────────────┐ │
│  │  Cautious — investigate before adding                                     │ │
│  │  WIPRO shows solid cash generation but business health declined and       │ │
│  │  valuation is above historical median. Not a clear buy at current levels. │ │
│  │  This is research guidance — not today's trade verdict (see Home).        │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  Research progress · Question 2 of 7                                        │
│  What evidence supports investing?                                            │
│                                                                              │
│  ┌─ QUESTION 2 — WHAT EVIDENCE SUPPORTS INVESTING? ──────────────────────────┐ │
│  │  Supporting                                                                 │ │
│  │  · FACT — Revenue grew 8% YoY (source: filings)                           │ │
│  │  · FACT — Net margin stable at 18%                                        │ │
│  │  Conflicting                                                                │ │
│  │  · ESTIMATE — Client concentration risk in top 3 accounts                   │ │
│  │  · OPINION — Sector headwinds may compress multiples                        │ │
│  │  [ Help me understand ▾ ]     [ View proof overlay ]                        │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─ NEXT QUESTION PREVIEW (collapsed) ───────────────────────────────────────┐ │
│  │  Q3 — What could invalidate the thesis? · 4 conditions listed              │ │
│  │  [ Expand preview ]                                                         │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  [ ← Previous question ]   [ Mark reviewed ✓ ]   [ Next question → ]         │
│  [ Investment Decision ]                                                      │
│                                                                              │
│  Broker + market data sources labeled. Alpha AI deep report available below.  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Desktop — Question 7 Investment Decision

```text
┌─ QUESTION 7 — WHAT INVESTMENT DECISION HAVE I REACHED? ──────────────────────┐
│  System summary (read-only)                                                   │
│  · Business quality: Adequate · Risks: Elevated · Valuation: Full           │
│  Your investment decision (editable)                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │ Hold current position; do not add until health stabilizes for 2 quarters.│ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│  Disposition:  ○ Watch  ● Hold  ○ Accumulate Later  ○ Avoid                  │
│  [ Save to Journal draft ]   [ Help me understand ▾ ]                         │
└───────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Desktop — exploratory (not held, Question 1)

```text
┌─ INVESTMENT VIEW HERO ─────────────────────────────────────────────────────────┐
│  Promising — worth deeper research                                            │
│  TCS is a high-quality compounder with durable moat; valuation fair vs peers. │
└───────────────────────────────────────────────────────────────────────────────┘

Context: TCS · Not in portfolio · Watchlist · IT sector

[ Add to watchlist ]   (secondary — no trade CTA)
```

---

## 5. Mobile Wireframes

### 5.1 Mobile — hero + question card

```text
┌─────────────────────────────┐
│ ☰  Research    WIPRO    Sync │
├─────────────────────────────┤
│ ← Portfolio Review          │
│ WIPRO · Held 18% · Flagged  │
├─────────────────────────────┤
│ INVESTMENT VIEW             │
│ Cautious — investigate      │
│ before adding               │
│ (2-line summary…)           │
├─────────────────────────────┤
│ Q2/7 Evidence         ●●○○○ │
│ What evidence supports      │
│ investing?                  │
├─────────────────────────────┤
│ ┌─ Evidence ──────────────┐ │
│ │ Supporting (2)          │ │
│ │ Conflicting (2)         │ │
│ │ [ Understand ▾ ]        │ │
│ └─────────────────────────┘ │
│                             │
│ [ ✓ Reviewed ] [ Next → ]   │
│ [ Investment Decision ]     │
├─────────────────────────────┤
│ Home Portfolio Research …   │
└─────────────────────────────┘
```

### 5.2 Mobile — question picker (overflow)

```text
┌─ Jump to question ──────────────────────────┐
│ ✓ What does this business do?               │
│ ● What evidence supports investing?         │
│   What could invalidate the thesis?         │
│   How strong is my conviction?              │
│   Is valuation attractive?                  │
│   What are the major risks?                 │
│   What investment decision have I reached?  │
└─────────────────────────────────────────────┘
```

**Mobile rules:** One question card visible at a time · horizontal progress dots · sticky bottom actions · full-width Understand · swipe optional between reviewed questions only.

---

## 6. Component Hierarchy

```text
ResearchWorkbenchSurface
├── ResearchContextHeader
│   ├── BackLink (source-aware: Portfolio Review / Holdings / Home / Explore)
│   ├── SymbolTitleBlock (symbol · name · sector)
│   └── PortfolioContextChip (optional: held · weight · health flag · review theme)
├── InvestmentViewHero
│   ├── ViewLabel (qualitative: Attractive / Cautious / Avoid research / Insufficient data)
│   ├── SummaryParagraph (2–3 sentences — answer-first)
│   └── DailyVerdictDisclaimer (link to Home when same symbol is today's priority)
├── ResearchProgressStrip
│   └── ResearchQuestionTab × 7 (status: pending · active · reviewed)
├── ResearchQuestionPanel (one active)
│   ├── QuestionHeader (number · full research question text)
│   ├── QuestionBody (contract-projected content)
│   ├── EvidenceLabelGroup (FACT / ASSUMPTION / ESTIMATE / OPINION)
│   ├── UnderstandGateway (shared framework)
│   └── ProofLink (when evidence packet available)
├── QuestionNavigationBar
│   ├── PreviousQuestionControl
│   ├── MarkQuestionReviewedControl (session state)
│   └── NextQuestionControl
├── InvestmentDecisionPanel (Question 7 — also reachable via CTA anytime)
│   ├── SystemSummaryBlock (read-only projection)
│   ├── UserDecisionEditor (presentation state)
│   └── DispositionSelector (Watch · Hold · Accumulate Later · Avoid)
├── AlphaDeepReportLink (L5 — collapsed by default)
│   └── Navigate Reports sub-tab with symbol
├── ResearchHandoffFooter
│   ├── InvestmentDecisionCTA → Journal draft
│   ├── PortfolioReturnCTA (preserve symbol + review theme key)
│   └── DataSourcesFooter (broker · filings · market data freshness)
└── EmptyStates / LoadingStates / ErrorStates / StaleDataBanner
```

**Render rule (future):** Projection from `MorningBriefViewModel` + `DecisionArtifact` + optional Alpha report DTO. Question review state and Investment Decision are **session presentation state** until Journal persistence (V3-202+).

---

## 7. Information Hierarchy

### 7.1 Page-level priority (top → bottom)

| Rank | Element | User need |
|------|---------|-----------|
| 1 | Investment View Hero | Should I invest? — the answer |
| 2 | Portfolio context chip | How does this relate to what I own? |
| 3 | Research progress | Where am I in the question flow? |
| 4 | Active question body | Current investor inquiry |
| 5 | Understand / Proof | Evidence on demand |
| 6 | Question navigation | Move forward with discipline |
| 7 | Remaining questions (preview) | What comes next |
| 8 | Investment Decision | Capture decision memory |
| 9 | Alpha deep report link | Optional institutional depth |
| 10 | Data sources footer | Trust |

### 7.2 Per-question content priority

```text
Research question → Top 3 bullets → Labels (FACT/…) → Understand → Proof
```

### 7.3 What sibling screens already answered — do not repeat

| From Home | Do not duplicate on Research |
|-----------|------------------------------|
| Daily verdict hero (ACT/WAIT/HOLD) | Show disclaimer + link; not same component |
| Session ribbon | Not shown |
| Today's priority framing | Context chip only if same symbol |

| From Portfolio | Do not duplicate on Research |
|----------------|------------------------------|
| Full holdings table | Weight + flag chip only |
| Theme review queue | Back link returns to theme; don't re-list all themes |
| Allocation dashboard | One-line portfolio fit note max |

| From Alpha AI Reports tab | Do not duplicate on Workbench |
|---------------------------|-------------------------------|
| Full 15-section scroll | Link to Reports; Workbench owns workflow |

---

## 8. Progressive Disclosure

| Layer | Content | Access |
|-------|---------|--------|
| **L0 — Context header** | Symbol · held? · weight · flag | Always visible |
| **L1 — Investment View Hero** | Qualitative answer + 2-line summary | Always visible |
| **L2 — Active question body** | Current research question essentials | Default viewport |
| **L3 — Understand popover** | Simple / Business / Professional depth | Explicit tap |
| **L4 — Proof overlay** | Evidence packet · decision_id link | Q2+ when available |
| **L5 — Alpha AI deep report** | Full institutional report | Reports sub-tab or expand link |

**Rule:** L0 + L1 answer *"Should I invest?"* at a high level without any tap. L2 completes disciplined research. L5 never blocks L1.

### 8.1 Insufficient data disclosure

When bundle gaps exist (`EvidenceSection.gap_note`, stale trust):

- Hero shows *Insufficient data for a confident view*
- Questions show gap flags; never fabricate metrics
- Primary CTA: Sync / retry · secondary: Explore alternate symbol

---

## 9. Research Workflow

### 9.1 Entry paths

```text
Portfolio Review → Open Research (symbol picker)
    → Workbench Q1 with review_theme context

Portfolio Holdings → Open Research (row)
    → Workbench with holdings_context

Portfolio Overview → Attention row Research
    → Workbench with attention flag context

Home → Opportunity / symbol link
    → Workbench (daily verdict disclaimer visible)

Command palette → symbol jump
    → Workbench bare context

Research sub-nav → Workbench + symbol search
    → Workbench empty → search → load
```

### 9.2 Question review model

| Behavior | Rule |
|----------|------|
| Default | Sequential Q1 → Q7 |
| Skip ahead | Allowed via question nav; unreviewed questions marked hollow |
| Mark reviewed | Session key `research_question_reviewed_{symbol}_{n}` |
| Revisit | Reviewed questions remain expandable |
| Reset | "Start over" clears session keys for symbol |

### 9.3 Question 4 — conviction specifics

- Shows confidence band from `DecisionSection` / artifact (not recomputed)
- Lists top 3 *why* bullets from `RecommendationContract.why`
- Teaches: conviction ≠ certainty; links forward to Q6 risks

### 9.4 Question 3 — thesis invalidation specifics

- Projects sell conditions and watch-closely items from `InvestmentThesisContract`
- Includes `what_could_change` from `RecommendationContract` / artifact invalidation
- Teaches: every thesis has break points — list them before deciding

### 9.5 Question 5 — valuation specifics

- Projects fair/over/full/undervalued label from existing Alpha AI valuation slice (future contract)
- Shows 2–3 multiples vs historical/peers — labeled ESTIMATE
- No price target as guaranteed return
- Chart optional below fold; narrative summary required for accessibility

### 9.6 Question 6 — risks specifics

- Projects `RiskMonitorContract` key business risks and thesis breakers
- Merges `RecommendationContract.risks` without duplication
- Downside before upside — aligned with product constitution

---

## 10. Decision Workflow

Investment Decision is **not** the Home daily verdict.

| Concept | Owner | Research behavior |
|---------|-------|-------------------|
| Daily verdict (ACT/WAIT) | Home | Link only; do not re-issue |
| Investment view (qualitative) | Research Workbench | Hero + questions |
| User Investment Decision | Research Q7 | Editable text + disposition |
| Decision receipt (immutable) | Journal (V3-202+) | Handoff from Investment Decision |

**Disposition options (research-level, not orders):**

| Disposition | Meaning |
|-------------|---------|
| Watch | Track; no action now |
| Hold | Maintain current position |
| Accumulate Later | Positive but wait for price/trigger |
| Avoid | Do not initiate/add |

---

## 11. Portfolio Handoff

### 11.1 Inbound (Portfolio → Research)

| Source | Context preserved |
|--------|-------------------|
| Review theme | `review_theme_key` · investigation guidance pre-loaded in Q2 banner |
| Holdings row | `holdings_weight` · health chip reason |
| Overview attention | `attention_flag_type` · one-line reason |

### 11.2 Outbound (Research → Portfolio)

| Action | Destination | Context preserved |
|--------|-------------|-------------------|
| Back link | Source tab (Review / Holdings / Overview) | Symbol highlight optional |
| After Investment Decision | Journal draft + optional Portfolio Review return | Review theme marked investigated (session) |

### 11.3 Portfolio fit panel (inline — Q1 or chip)

When symbol is held:

```text
Portfolio fit: 18% weight · above 15% guideline · Sector IT 24%
```

Projected from `PortfolioOverviewViewModel` when available — **read-only**; no new concentration math in Research UI.

---

## 12. Journal Handoff

### 12.1 Investment Decision flow

```text
Q7 Save (Investment Decision)
    → Journal › Receipts draft (V3-202)
    → Payload: symbol · timestamp · user text · disposition · question_review_state · decision_id link
    → User confirms in Journal (future immutable receipt)
```

### 12.2 V3-201 scope (design only)

- **In scope:** UX for Investment Decision · draft payload contract (design-level fields)
- **Out of scope:** Receipt persistence · calibration · Weekly Review integration (V3-202+)

### 12.3 Session draft before Journal ships

- Store in `st.session_state.research_investment_decision_{symbol}` (implementation note for engineering — not in V3-201 code)
- Toast: "Investment decision saved for this session — Journal persistence coming in V3-202"

---

## 13. Accessibility

| Requirement | Implementation |
|-------------|----------------|
| **Landmarks** | `main` for workbench; `nav` for question strip; `region` per question |
| **Hero** | Plain language first; qualitative label not color-only |
| **Question progress** | `aria-current="step"` on active question; reviewed questions announced |
| **Evidence labels** | Visible text: FACT · ASSUMPTION · ESTIMATE · OPINION |
| **Charts (valuation)** | Required narrative summary above chart |
| **Understand** | Shared popover — keyboard trap + Escape |
| **Focus** | `:focus-visible` on question tabs, nav buttons (V2-004) |
| **Screen reader** | Hero read as: "Research view for WIPRO: Cautious — investigate before adding" |
| **Motion** | `prefers-reduced-motion` — no question transition animation |
| **Contrast** | WCAG AA; disposition selector not color-only |
| **Touch targets** | ≥44×44px on mobile question controls |

---

## 14. Performance

| Technique | Application |
|-----------|-------------|
| **Cached bundle** | Show last symbol research immediately; stale banner if context age > threshold |
| **Question lazy render** | Mount active question + adjacent only |
| **Understand lazy** | Popover on first open |
| **Alpha L5 deferred** | No report fetch until user taps deep link |
| **Debounced decision editor** | 300ms local save to session |
| **content-visibility** | Below-fold questions and Alpha link |
| **No blocking analyze gate** | Workbench loads from frozen bundle path |

| Target | Value |
|--------|-------|
| LCP (cached symbol) | ≤2.0s |
| Question switch | <100ms |
| Understand open | <200ms |
| Cold symbol (new) | ≤2.5s with loading skeleton |

### 14.1 Scale assumptions

- Single symbol per workbench instance
- Typical 7 questions × <2KB projected text each
- Alpha deep report optional async load

---

## 15. Future Extensibility

| Extension | Slot | Notes |
|-----------|------|-------|
| Compare symbols | Workbench sub-mode | Side-by-side Q5 Valuation; reuse contracts |
| Explore → Research | Explore handoff | Screener row → Workbench with discovery context |
| Thesis Tracker (V3-402) | Q3 enrichment | Link invalidation conditions |
| Decision Receipt (V3-202) | Q7 persistence | Immutable handoff |
| Investor DNA | Q4 calibration | "Matches your patience profile" |
| Offline | Cached bundle | Read-only questions + stale banner |
| Custom question sets | Not planned | Workflow frozen at 7 questions for V3-201 |
| LLM narrative | Alpha AI LLM layer | Optional L5; never replaces labeled evidence |

### 15.1 Contract stability (future)

**`ResearchWorkspaceContract`** (engineering phase) projects from:

- `MorningBriefViewModel`
- `DecisionArtifact | None`
- `RecommendationContract`
- `InvestmentThesisContract`
- `BusinessHealthContract`
- `RiskMonitorContract`
- Optional valuation slice
- Optional `PortfolioOverviewViewModel` slice (weight, flag)
- Session: question review state · investment decision

No analyzer changes in V3-201 implementation phase without approval.

---

## Appendix A — Screen relationship (Research pillar)

| Tab | Question | Status |
|-----|----------|--------|
| Workbench (V3-201) | Should I invest in this company? | **This design** |
| Explore | What should I look at? | Future |
| Reports | Show me the full institutional report | Alpha AI absorption |

---

## Appendix B — References

| Doc | Relationship |
|-----|--------------|
| [APEX-017](../apex/APEX-017_V3-103_Portfolio_Review.md) | Portfolio → Research handoff pattern |
| [APEX-014](../apex/APEX-014_V2_Architecture_and_Release.md) | Frozen pipeline |
| [MASTER_PROMPT](../../.cursor/MASTER_PROMPT.md) | Recommendation contract order |
| [V3_PORTFOLIO_REVIEW.md](./V3_PORTFOLIO_REVIEW.md) | Theme investigation guidance |

---

*Draft v0.2 — P1 question-framing revision — 2026-08-06. No implementation.*
