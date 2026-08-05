# ETS-003 — Today Surface Product Specification

**"What Should I Do Today?"**

**Document ID:** ETS-003  
**Version:** 0.1  
**Status:** DRAFT — Product Specification (no implementation)  
**Date:** 2026-08-05  
**Owner:** ChatGPT (CTO / CPO)  
**Author:** Cursor AI (Engineering — Principal PM / UX / Investment Product)  
**Reviewers:** Pratham Prakash (Founder) — pending · ChatGPT (CTO) — pending  
**References:** [APEX-000](../APEX-000_Company_Constitution.md), [APEX-001](../APEX-001_Sprint0_Engineering_Assessment.md), [APEX-003](../APEX-003_Product_Strategy_and_PRD.md), [APEX-004](../APEX-004_Experience_Operating_System.md), [APEX-005](../APEX-005_System_Architecture_Blueprint.md), [ETS-002.1](./ETS-002.1_Broker_Auth_Session.md), [Phase 1 Verdict Canvas Spec](../../design/Phase_1_Verdict_Canvas_Spec.md)

**Scope:** Product experience design only. No code, components, CSS, APIs, or database schema.

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)  
2. [Jobs To Be Done](#2-jobs-to-be-done)  
3. [Success Criteria](#3-success-criteria)  
4. [30-Second User Journey](#4-30-second-user-journey)  
5. [Information Hierarchy](#5-information-hierarchy)  
6. [Today's Decision Card](#6-todays-decision-card)  
7. [Portfolio Intelligence Card](#7-portfolio-intelligence-card)  
8. [Top Opportunity Card](#8-top-opportunity-card)  
9. [Risk Monitor](#9-risk-monitor)  
10. [Market Context](#10-market-context)  
11. [AI Insight of the Day](#11-ai-insight-of-the-day)  
12. [Discipline Score](#12-discipline-score)  
13. [Quick Actions](#13-quick-actions)  
14. [Loading Strategy](#14-loading-strategy)  
15. [Failure Modes](#15-failure-modes)  
16. [Performance Budget](#16-performance-budget)  
17. [KPIs](#17-kpis)  
18. [Engineering Traceability](#18-engineering-traceability)  
19. [Closing — Decisions, Risks, MVP, Recommendation](#19-closing--decisions-risks-mvp-recommendation)

---

## The Product Question (Answer First)

When Arjun opens APEX at **9:15 AM**, the first five things he must know — in order:

| # | Question | Answer source on Today |
|---|----------|------------------------|
| **1** | **Should I trade today at all?** | Decision Card verdict word (`ACT` / `WAIT` / `PAUSE` / `DEFENSIVE` / `REDUCE`) |
| **2** | **Why — in plain language I trust?** | CIO mentor block (max 4 lines, labeled uncertainty) |
| **3** | **Is this based on *my* portfolio or generic noise?** | Sync indicator + portfolio intelligence footnote |
| **4** | **What is the one thing worth attention if I act?** | Top Opportunity zone (below fold) OR primary CTA to Trades |
| **5** | **What could block or hurt me today?** | Risk Monitor ambient ribbon + dams state |

Everything else is optional depth — not required in the first 30 seconds.

---

## 1. Problem Statement

### 1.1 User problem

Indian retail investors with limited morning time face **decision overload**: too many charts, too many alerts, too little confidence. They open trading apps and leave more anxious than when they arrived.

Arjun specifically:

- Has **15–30 minutes** before work  
- Uses **Zerodha** for execution  
- Needs **permission to wait** as much as permission to trade  
- Cannot trust black-box tips or unverified P&L claims  

### 1.2 Product problem

Stock Analyzer V2 and legacy Streamlit home surfaces behave like **dashboards** — they expose everything the engine can compute. APEX constitution ([APEX-000 §4.1](../APEX-000_Company_Constitution.md)) requires the opposite: **one answer, one reason, one action**.

Without a dedicated Today Surface specification, engineering will:

- Reintroduce metric grids and expanders  
- Split morning brief from Today (forbidden by [APEX-004 §17.1](../APEX-004_Experience_Operating_System.md))  
- Emit parallel verdicts from legacy drivers ([APEX-005 AP2](../APEX-005_System_Architecture_Blueprint.md))  
- Optimize for engagement instead of **Calibrated Decision Quality Score (CDQS)**  

### 1.3 Opportunity

Today is **the product** ([APEX-000 §4.3](../APEX-000_Company_Constitution.md)). If APEX nails the 9:15 AM experience — verdict in hand, confidence up, app closed — every other surface (Trades, Proof, Trust, You) becomes depth, not distraction.

---

## 2. Jobs To Be Done

### 2.1 Primary JTBD

> **When** the market opens and I have limited time,  
> **I want to** know whether to act on my capital today and why,  
> **So I can** trade with discipline or walk away without guilt.

### 2.2 Related jobs (Today enables; other surfaces complete)

| Job | Today role | Completion surface |
|-----|------------|-------------------|
| Size a trade correctly | Verdict + risk context | Trades |
| Verify the reasoning | "See the proof" CTA | Proof |
| Check honest track record | Discipline score teaser | Trust |
| Resolve one doubt | Ask pill (ambient) | Ask |
| Improve process over weeks | One line coach hint | You |

### 2.3 Anti-jobs (explicitly not Today)

| Anti-job | Why excluded |
|----------|--------------|
| Browse every holding | You / broker app |
| Screen the market | Not a screener product |
| Chat about markets | Ask is one-shot, not threads |
| Prove I'm smart | Trust is accountability, not vanity |

---

## 3. Success Criteria

### 3.1 User success (qualitative)

| Criterion | Pass definition |
|-----------|-----------------|
| **Clarity** | User can state verdict + reason aloud within 30s |
| **Confidence** | User reports lower anxiety vs. opening Kite alone (Founder dogfood) |
| **Discipline** | WAIT days feel valid — no "empty product" feeling |
| **Actionability** | ACT days lead to Trades within 60s without confusion |
| **Trust** | User knows if answer is personalized (broker sync state visible) |

### 3.2 Product success (measurable — see §17)

| Criterion | Target (MVP) |
|-----------|--------------|
| Time to Decision | ≤ 30s median (verdict readable) |
| Time to Clarity | ≤ 60s ([APEX-004 §46](../APEX-004_Experience_Operating_System.md)) |
| Daily morning open | Founder 5×/week; beta users 3×/week |
| Proof attach (ACT days) | Track; no gamification |
| Sync health | > 90% sessions green or qualified stale |

### 3.3 Engineering success

| Criterion | Pass definition |
|-----------|-----------------|
| Single verdict path | Only `DecisionEngine` → `DecisionArtifact` on Today |
| Contract binding | UI reads `DecisionArtifact`, `BrokerSnapshot`, `ContextSnapshot` — not raw engine internals |
| Failure scoped | Proof/broker errors do not blank Today if decision cached |
| ETS-002.1 integration | Sync indicator from `BrokerSessionService` / `BrokerSnapshot` |

---

## 4. 30-Second User Journey

**Persona:** Arjun · Wednesday · 9:12 AM IST · Pre-open complete · Broker connected last night

### 0–5 seconds — Orient

| Second | User sees | User thinks |
|--------|-----------|-------------|
| 0 | App opens to **Today** (not legacy Home) | "Good — I'm home" |
| 1 | Dark canvas, **sync dot green**, IST time | "My portfolio is live" |
| 2 | Verdict word animates in: **Wait** (amber) | "Okay — what's the call?" |
| 3–5 | Eyes lock on verdict; header/session ribbon peripheral | "One word — not a dashboard" |

**System:** Cached `DecisionArtifact` from morning pipeline OR skeleton verdict with mentor loading.

### 5–15 seconds — Understand

| Second | User sees | User thinks |
|--------|-----------|-------------|
| 5–8 | CIO mentor block (3 lines max): regime + portfolio context | "Choppy open — no edge for MIS" |
| 9–12 | Primary button: **See why we're waiting** | "I can go deeper if I want" |
| 13–15 | Optional: session ribbon — "Prep fresh · Nifty gap +0.4%" | "Market context without leaving" |

**System:** Mentor text from CIO template + `DecisionArtifact.summary`; no metric grid.

### 15–30 seconds — Decide to stay or leave

| Second | User sees | User thinks |
|--------|-----------|-------------|
| 16–20 | User reads; **does not scroll** on typical WAIT day | "I'm done — no FOMO" |
| 21–25 | Taps **See why** OR closes app | Proof optional; closing is success |
| 26–30 | If scroll: Portfolio + Risk zones below fold | "Extra context if curious" |

**Success outcome:** Arjun closes APEX by 9:13 AM feeling **relief**, not missing out.

**ACT alternate path (15–30s):** Primary button **Review trade plan** → Trades surface with E/SL/T pre-filled.

---

## 5. Information Hierarchy

### 5.1 Above the fold (default view — no scroll)

Per [APEX-004 §14](../APEX-004_Experience_Operating_System.md) and [Verdict Canvas Spec](../../design/Phase_1_Verdict_Canvas_Spec.md):

| Priority | Element | Max visual weight |
|----------|---------|-------------------|
| P0 | **Verdict word** | Hero — 56px |
| P0 | **CIO mentor block** | Secondary — 4 lines |
| P0 | **Primary CTA** (one button) | Tertiary — 52px height |
| P1 | **Sync indicator** | Ambient — header right |
| P1 | **Session ribbon** | Ambient — single line under header |

**Rule:** Maximum **two typographic sizes** on default view (verdict + mentor). No cards. No section headers. No grids.

### 5.2 Below the fold (scroll reveals — optional depth)

| Zone | Purpose | Format |
|------|---------|--------|
| Portfolio Intelligence | Personalization proof | Prose block, not card grid |
| Top Opportunity | One symbol/setup if ACT-adjacent | Single-row focus |
| Risk Monitor | Dams, blocks, session gates | Prose + status chips |
| Market Context | Regime, gap, VIX band | 2–3 sentences |
| Discipline Score | CDQS teaser | One metric + link to Trust |
| Quick Actions | Secondary navigation | Icon row (max 4) |

**Scroll is optional on WAIT days.** 70%+ of sessions should end above the fold.

### 5.3 Deferred (one tap / overlay)

| Content | Entry |
|---------|-------|
| Full evidence | Proof overlay via CTA |
| Full CDQS history | Trust surface |
| Trade ticket | Trades surface |
| One-shot question | Ask pill |
| Behaviour coaching | You surface |

### 5.4 Hidden (never on Today default)

| Banned | Reason |
|--------|--------|
| Screener tables | Not command center |
| Holdings grid | You / broker app |
| Multiple equal CTAs | Violates XOS |
| Engine vocabulary ("EvidencePacket") | User-facing prohibition |
| Legacy nav tabs | Phase 1a six-surface only |
| Chart workspace | Proof owns charts |

---

## 6. Today's Decision Card

### 6.1 Purpose

The **hero** of APEX. Answers the only question that matters above the fold:

> **"What should I do today?"**

It is not a widget — it **is** the Today surface default view.

### 6.2 Content

| Field | Source | Display rule |
|-------|--------|--------------|
| `verdict` | `DecisionArtifact.verdict` | Single word, title case |
| `confidence_band` | `DecisionArtifact.confidence` | Influences mentor tone — not numeric on default view |
| `mentor_summary` | CIO template × artifact | Max 4 lines, 358px width |
| `primary_symbol` | `DecisionArtifact.symbol` | Only if ACT — in mentor, not ticker grid |
| `evidence_id` | `DecisionArtifact.evidence_id` | Links to Proof — not shown as ID |
| `built_at` | Artifact timestamp | Header time |
| `personalization_scope` | broker + portfolio flags | Footnote if market-only |

### 6.3 Fields (data contract)

```
DecisionCardView {
  verdict: ACT | WAIT | PAUSE | DEFENSIVE | REDUCE
  mentor_lines: string[1..4]
  primary_cta: { label, destination: TRADES | PROOF | TRUST | NONE }
  secondary_hint: string | null     // ghost hint below button
  sync_state: CONNECTED | STALE | OFFLINE | NOT_CONFIGURED
  session_ribbon: string | null       // ambient strip
  confidence_band: HIGH | MEDIUM | LOW
  labels: FACT | ASSUMPTION | ESTIMATE | OPINION[]  // inline in mentor
}
```

### 6.4 Verdict → visual mapping

| Verdict | Color | CIO tone | Primary CTA |
|---------|-------|----------|-------------|
| **WAIT** | `#FFC107` | Calm, permissive | See why we're waiting → Proof |
| **ACT** | `#00E676` | Clear, not hype | Review trade plan → Trades |
| **PAUSE** | `#FF9800` | Session / loss context | View risk status → Trust |
| **DEFENSIVE** | `#90CAF9` | Protection mode | See what's blocked → Proof/Trust |
| **REDUCE** | `#FF6B6B` | Risk reduction | Review exposure → You/Trades |

### 6.5 State variants

#### Empty (first launch, no decision yet)

| Element | Content |
|---------|---------|
| Verdict | **Prepare** (neutral gray) |
| Mentor | "APEX is getting today's context. This takes a moment on first open." |
| CTA | Disabled — "Building today's call" |
| Sync | Reflects broker state |

#### Loading

| Phase | User sees |
|-------|-----------|
| L1 (0–2s) | Skeleton verdict shimmer + last-known verdict if ≤24h stale acceptable |
| L2 (2–8s) | Mentor skeleton lines |
| L3 (8s+) | "Still working" single line — no spinner wall |

**Rule:** Never blank the canvas. Show stale decision with "Updating…" badge if refresh in flight.

#### Error (decision pipeline failed)

| Element | Content |
|---------|---------|
| Verdict | **Pause** |
| Mentor | "Today's call couldn't be computed. Your last synced portfolio is available. **ESTIMATE:** market-only context shown." |
| CTA | Retry · Connect broker (if relevant) |
| Scope | Error on Proof must not block decision retry |

#### Weekend

| Element | Content |
|---------|---------|
| Verdict | **Wait** |
| Mentor | "Markets are closed. Review the week in Trust, or set up Monday in You. No action required today." |
| CTA | Open Trust → weekly review |
| Ribbon | "Weekend · NSE closed" |

#### Market Closed (weekday after hours)

| Element | Content |
|---------|---------|
| Verdict | **Wait** or last intraday verdict frozen |
| Mentor | "Session closed. Intraday plans are inactive. Here is what mattered today." |
| CTA | View today's record → Trust |

#### High Confidence ACT

| Element | Content |
|---------|---------|
| Verdict | **Act** (green) |
| Mentor | "One setup meets your rules: **FACT:** regime supportive · **FACT:** risk headroom OK · Symbol in Trades." |
| CTA | Review trade plan |
| Hint | "See the proof" ghost link |

#### Low Confidence ACT

| Element | Content |
|---------|---------|
| Verdict | **Act** (muted green) |
| Mentor | "**ASSUMPTION:** edge is marginal. Size down. Proof shows two conflicts." |
| CTA | See the proof first (Proof before Trades) |

#### No Trade (WAIT — default constitution)

| Element | Content |
|---------|---------|
| Verdict | **Wait** |
| Mentor | "No setup passes your rules today. Preserving capital is the active choice." |
| CTA | See why we're waiting |
| Emotion target | Relief, not emptiness ([APEX-004 DDR-007](../APEX-004_Experience_Operating_System.md)) |

### 6.6 Examples (copy)

**WAIT — choppy regime:**  
*"Nifty is range-bound with low ADX. Your tactical pool has room, but there is no asymmetric setup in watchlist. **OPINION:** sitting out preserves optionality for a cleaner open tomorrow."*

**ACT — MIS setup:**  
*"One MIS candidate cleared gates: RELIANCE long above opening range. **FACT:** daily loss dam at 62% used. Plan is sized for tactical pool in Trades."*

**DEFENSIVE — dam near limit:**  
*"You are within ₹800 of today's loss limit. **FACT:** no new tactical risk is permitted. Sacred core is unaffected."*

---

## 7. Portfolio Intelligence Card

### 7.1 Naming note

Despite "Card" in working title, this zone is a **prose intelligence block** below the fold — not a card-stack component ([APEX-004 §14.3](../APEX-004_Experience_Operating_System.md)).

### 7.2 Purpose

Prove Today is **about Arjun's capital**, not generic market commentary.

### 7.3 Content

| Field | Source |
|-------|--------|
| Tactical pool value | `BrokerSnapshot` + portfolio store |
| Sacred core status | Portfolio memory — "not in today's MIS plan" |
| Holdings count | `BrokerSnapshot.holdings_count` |
| Concentration note | PM voice — one sentence if sector > threshold |
| Freshness | Sync indicator echo |

### 7.4 Display rules

- Max **3 sentences**  
- PM specialist voice ([APEX-004 §16](../APEX-004_Experience_Operating_System.md))  
- Never a holdings table on Today  
- If broker offline: "Portfolio as of {last_sync_at} — **ESTIMATE**"

### 7.5 Example

*"Your tactical pool is **₹38,200** after yesterday's MIS. Sacred core (SIP holdings) is not in today's plan. **FACT:** 12 holdings synced 6 minutes ago."*

---

## 8. Top Opportunity Card

### 8.1 Purpose

Answer: **"If I act, what is the one thing?"** — without becoming a watchlist.

### 8.2 Content (ACT or ACT-adjacent days only)

| Field | Source |
|-------|--------|
| Symbol | `DecisionArtifact.symbol` or top ranked watchlist candidate |
| Setup name | Plain language ("Opening range breakout") |
| Lane | MIS / swing / options — one tag |
| Gate status | Passed / marginal |
| Link | Trades pre-filled plan |

### 8.3 Display rules

- **Hidden entirely on WAIT days** (no FOMO list)  
- One opportunity only — never a ranked list on Today  
- RA voice for setup description  
- If no symbol: zone omitted, not "empty state card"

### 8.4 Example

*"**RELIANCE** · MIS long · Opening range above ₹2,945 · Gates: 4/5 passed · **OPINION:** marginal volume — size down."*

---

## 9. Risk Monitor

### 9.1 Purpose

Surface **blocks** before they surprise Arjun on Kite.

### 9.2 Content

| Signal | Source | Display |
|--------|--------|---------|
| Daily loss dam | Risk memory | % used + plain consequence |
| Max trades / day | Session rules | "2/3 tactical trades used" |
| Session phase | `market_session` | Pre-open / open / square-off |
| Broker blocks | `DecisionArtifact` risk flags | RO voice |
| Token expiry | `BrokerSnapshot.state` | Sign in required |

### 9.3 Format

**Session ribbon (above fold)** — compact:  
`Prep ✓ · Sync ✓ · Dam 62% · Open in 8m`

**Risk block (below fold)** — RO voice prose:  
*"Daily loss dam: **₹1,240 / ₹2,000** used. One more loss near limit triggers **Pause** for the session."*

### 9.4 States

| State | Ribbon | Block |
|-------|--------|-------|
| All clear | Green chips | Omitted or one-line OK |
| Warning | Amber dam | Expanded prose |
| Blocked | Red pause | Verdict should be PAUSE/DEFENSIVE |

---

## 10. Market Context

### 10.1 Purpose

Minimum market literacy to interpret verdict — **not** a research portal.

### 10.2 Content

| Field | Source |
|-------|--------|
| Regime | Context engine (trend/range/volatile) |
| Index gap | Gift Nifty / Nifty open context |
| Event flag | High-impact day if known |
| Global spillover | One line if material |

### 10.3 Display rules

- Max **2 sentences** below fold  
- CIO/RA blended — factual labels required  
- Weekend/market closed: folded into Decision Card mentor — duplicate zone hidden

### 10.4 Example

*"**FACT:** Nifty gap +0.4% · regime: range-bound. **ASSUMPTION:** first 15 minutes may mean-revert."*

---

## 11. AI Insight of the Day

### 11.1 Purpose

One **memorable, actionable insight** — not a second verdict.

### 11.2 Relationship to mentor block

The CIO mentor block **is** the primary insight. This zone is **optional enrichment** below fold — only when mentor block cannot carry all context without exceeding 4 lines.

### 11.3 Content

| Field | Rule |
|-------|------|
| Insight | One sentence |
| Label | FACT / ASSUMPTION / OPINION |
| Source | Decision reasoning or learning loop |
| Refresh | Once per session |

### 11.4 Example

*"**OPINION:** Your last five MIS wins came on trend days — today is not one."*

### 11.5 Banned

- Generic motivational quotes  
- Predictions without labels  
- "AI says buy" without Proof path  

---

## 12. Discipline Score

### 12.1 Purpose

Teaser for **CDQS** ([APEX-003 North Star](../APEX-003_Product_Strategy_and_PRD.md)) — process quality, not vanity P&L.

### 12.2 Content

| Field | Source |
|-------|--------|
| CDQS rolling value | Learning / broker truth |
| Trend arrow | vs. 7-day |
| One-line interpretation | CIO + Trust voice |
| CTA | View full record → Trust |

### 12.3 Display rules

- Single number + one sentence — not a chart on Today  
- If insufficient broker history: "Building your score — N verified trades needed"  
- Never gamified badges or streak flames  

### 12.4 Example

*"**CDQS 0.71** · improving · You followed wait rules on 4/5 choppy days this week. Details in Trust."*

---

## 13. Quick Actions

### 13.1 Purpose

Secondary navigation without competing with primary CTA.

### 13.2 Allowed actions (max 4)

| Action | Destination | When shown |
|--------|-------------|------------|
| Ask | Ask overlay | Always (also pill) |
| Proof | Proof overlay | WAIT / ACT |
| Trust | Trust surface | Always |
| You | You surface | Always |

### 13.3 Rules

- **Never** equal visual weight to primary CTA  
- Icon + label row below fold only  
- No "Screener", "Charts", "Settings" on Today quick row — those are not partner surfaces  

---

## 14. Loading Strategy

### 14.1 What loads immediately (T+0 → T+2s)

| Asset | Source | Fallback |
|-------|--------|----------|
| Canvas chrome | Static | — |
| Sync indicator | `BrokerSnapshot` from ETS-002.1 session | Offline state |
| Cached verdict | Last `DecisionArtifact` if fresh | Skeleton |
| Session ribbon partial | Cached context | Omit chips |

### 14.2 What loads next (T+2s → T+8s)

| Asset | Pipeline |
|-------|----------|
| Fresh decision | Context → Evidence → Decision |
| Mentor block | CIO template render |
| Primary CTA | Derived from verdict |

### 14.3 What loads later (lazy, on scroll or idle)

| Asset | Trigger |
|-------|---------|
| Portfolio intelligence | Scroll OR post-decision idle |
| Top opportunity | Only if ACT |
| CDQS teaser | Trust service async |
| Market context enrichment | Background fetch |

### 14.4 Caching policy

| Data | TTL | Invalidation |
|------|-----|--------------|
| DecisionArtifact | Session + calendar day | Broker sync, manual refresh |
| BrokerSnapshot | Session | ETS-002.1 bootstrap |
| Context regime | 15 min pre-open; 5 min open | Session phase change |
| Proof bundle | On demand | Evidence ID change |

### 14.5 Refresh triggers

- App open (main `initialize`)  
- Pull-to-refresh (optional Phase 1b)  
- Broker OAuth complete  
- Session phase transition (pre-open → open)  

---

## 15. Failure Modes

| Mode | User experience | System behavior |
|------|-----------------|-----------------|
| **No broker** | Banner: "Connect Zerodha for personalized risk and CDQS." Market-only verdict qualified. | `BrokerSnapshot.state = not_configured` |
| **No portfolio** | Mentor: "No holdings synced — verdict is market-level only." | Skip portfolio zones |
| **API down (Kite)** | Sync red · stale holdings · WAIT bias | `BrokerSnapshot.state = offline` |
| **Decision engine error** | §6.5 Error state | Show last good artifact if available |
| **Evidence timeout** | Verdict still shown · Proof CTA disabled with reason | Scoped failure ([APEX-004](../APEX-004_Experience_Operating_System.md)) |
| **Market closed** | §6.5 Market Closed | No intraday ACT |
| **Weekend** | §6.5 Weekend | Trust/You CTAs only |
| **No opportunities** | WAIT verdict — zone 8 hidden | Default constitution |
| **Token expired** | Sync indicator · Sign in · PAUSE bias | ETS-002.1 `validate_session` cleared token |
| **Partial personalization** | Labels: **ESTIMATE** on affected claims | Never silent degradation |

---

## 16. Performance Budget

| Metric | Target | Hard ceiling |
|--------|--------|--------------|
| **Time To First Meaningful View (TTFMV)** | ≤ 1.5s | 3s |
| **Time To Decision (verdict readable)** | ≤ 30s user; ≤ 8s system | 15s system |
| **Time To Clarity (verdict + reason)** | ≤ 60s | 90s |
| **Primary render (P0 elements)** | ≤ 200ms after data | 500ms |
| **Max blocking API calls on critical path** | 3 (broker status, context, decision) | 5 |
| **Scroll zone load** | Non-blocking | Must not delay P0 |

### 16.1 API call budget (morning critical path)

1. Broker session validate / snapshot (ETS-002.1)  
2. Context snapshot (regime + session)  
3. Decision compute OR cache read  

Evidence assembly for Proof is **not** on critical path.

---

## 17. KPIs

| KPI | Definition | MVP target | Owner |
|-----|------------|------------|-------|
| **Daily Active Usage (DAU)** | Unique opens Today per calendar day | Founder 5/wk; beta 3/wk | Founder |
| **Time To Decision** | Open → verdict visible | Median ≤ 30s | CTO |
| **Time To Clarity** | Open → user can state reason | Median ≤ 60s | CTO |
| **Decision Confidence** | In-app micro-prompt: "How confident?" 1–5 | Baseline → +0.5 over 30d | Founder |
| **Proof Opens** | % sessions opening Proof | Track; no target pressure | CTO |
| **Session Length** | Today surface duration | WAIT median < 45s | CTO |
| **Return Rate** | DAU / WAU on Today | > 60% | Founder |
| **Sync Health** | Green sync % | > 90% | Engineering |
| **CDQS comprehension** | Qual interview | 80% can explain | Founder |

**North star alignment:** All KPIs serve **CDQS improvement** — not raw engagement ([APEX-004 §46](../APEX-004_Experience_Operating_System.md)).

---

## 18. Engineering Traceability

| Spec section | APEX-003 | APEX-004 | APEX-005 |
|--------------|----------|----------|----------|
| Decision Card hero | §18 P1 verdict, §19 Model C CIO | §14 Decision Card, §17 Morning | §20 Decision Pipeline, `DecisionArtifact` |
| 30s journey | §8.3 sacred window | §17.2 sequence, §46 TTC | §5 `MorningBrief` use case |
| Portfolio intelligence | §15 Portfolio Memory | §16 Portfolio Experience | Context boundary, `portfolio_live` |
| Risk monitor | Risk Memory | §8 Risk Officer, §17.3 ribbon | Risk settings in `DecisionEngine` |
| Top opportunity | E-2 Trades path | §18 ACT → Trades | `ActPlan` use case |
| Proof / Ask CTAs | E-3 Proof | §15 Evidence Card, §19 IA | Proof overlay routing |
| Discipline / CDQS | North Star CDQS | §46 metrics, Trust | Learning boundary, `broker_truth` |
| Loading / failure | §18 P6 speed | §13 scoped failure | §19–21 pipelines, caching |
| Sync indicator | Flywheel breakers | §14.4, broker disconnected | §31 Broker, ETS-002.1 |
| Six surfaces only | §19 UX Model | §19 IA | Six deployable boundaries |
| No dashboard | Feature reduction § | §11 banned patterns | AP2 single verdict |
| Verdict vocabulary | ACT/WAIT | §14.2 colors | §20 canonical verdicts |

### 18.1 Primary code paths (future ETS implementation — not this doc)

| Concern | Current module | Target |
|---------|----------------|--------|
| Today render | `ui/pages/unified_home.py`, `home_dashboard.py` | `today_canvas` per Verdict Spec |
| Decision | `analyzer/decision_engine/` | Sole authority |
| Morning orchestration | `analyzer/investment_os.py` | `MorningBrief` use case |
| Broker state | `BrokerSessionService` (ETS-002.1) | `BrokerSnapshot` |
| Legacy parallel verdicts | `mis_trade_advisory.py`, etc. | REFACTOR per APEX-005 |

---

## 19. Closing — Decisions, Risks, MVP, Recommendation

### 19.1 Founder Decisions Required

| ID | Decision | Options | Default if deferred |
|----|----------|---------|---------------------|
| **FD-T01** | Approve Today as **only** post-login landing (retire legacy Home) | Yes / No | Yes — constitution |
| **FD-T02** | Accept **WAIT-as-success** KPI framing (short sessions OK) | Yes / No | Yes |
| **FD-T03** | MVP includes **options lane** on Today or equity-only | Both / equity-only | Equity-only MIS |
| **FD-T04** | CDQS visible on Today teaser or Trust-only | Teaser / Trust-only | Teaser one-liner |
| **FD-T05** | In-app confidence micro-prompt (1–5) | Ship / defer | Defer Phase 1b |

### 19.2 CTO Decisions Required

| ID | Decision | Recommendation |
|----|----------|----------------|
| **CD-T01** | Model C Hybrid CIO voice on Today | Approve per APEX-003 §19 |
| **CD-T02** | Stale verdict policy (show last ≤24h with badge) | Approve |
| **CD-T03** | Below-fold zones ship in MVP or Phase 1b | MVP: Decision Card only; 1b: scroll zones |
| **CD-T04** | Implementation ETS split: ETS-003a canvas / ETS-003b data wiring | Split recommended |
| **CD-T05** | Retire `verdict_bridge` before Today launch | Required per AP2 |

### 19.3 Engineering Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Parallel verdict drivers still emit UI data | High | Gate Today on `DecisionEngine` only |
| Streamlit layout fights pixel spec | Medium | Phase 1 Verdict Canvas custom CSS |
| Morning pipeline latency > 8s | Medium | Cache + stale-while-revalidate |
| Broker sync failures degrade trust | Medium | ETS-002.1 + qualified copy |
| Scope creep below-fold cards | Medium | This spec — scroll zones are prose |

### 19.4 Product Risks

| Risk | Mitigation |
|------|------------|
| Today feels empty on WAIT days | CIO copy + discipline teaser; constitution Default WAIT |
| Users expect dashboard | Onboarding: "One answer, not a terminal" |
| CDQS confusing | Trust owns explanation; Today one-liner only |
| Founder dogfood mismatch | Arjun persona validation weekly |

### 19.5 MVP Recommendation

**Phase 1a MVP (ship first):**

- Decision Card only (§6) — above the fold  
- Sync indicator (ETS-002.1)  
- Session ribbon (minimal)  
- Six-surface nav shell  
- ACT → Trades / WAIT → Proof CTAs  

**Phase 1b (fast follow):**

- Below-fold zones §7–12  
- CDQS teaser  
- Pull-to-refresh  
- Confidence micro-prompt  

**Explicitly exclude from MVP:** holdings grid, screener embed, chart on Today, chat threads, seventh surface.

### 19.6 Recommendation to Begin Implementation

**Recommend proceeding to implementation** via separate engineering ETS specs — **after**:

1. Founder approves **FD-T01** (Today-only landing) and **FD-T03** (lane scope)  
2. CTO approves **CD-T03** (MVP scope split) and **CD-T04** (ETS-003a/b)  
3. ETS-002.1 Phase A frozen (complete)  
4. ETS-001 test suite green (recommended gate)  

**Do not begin Phase B (Keychain)** or Today implementation in the same sprint.

**Suggested next documents:**

| Doc | Purpose |
|-----|---------|
| **ETS-003a** | Verdict Canvas implementation (UI) |
| **ETS-003b** | `MorningBrief` → `DecisionCardView` wiring |
| **ETS-009** | Phase 1 navigation unification (if not exists) |

---

*Repository: stock-analyzer · Product: APEX · Document: ETS-003 · Category: Product Specification*
