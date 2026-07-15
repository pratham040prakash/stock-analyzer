# 18 — Product UX Review: Home Dashboard

**Perspective:** Principal UX Architect × Staff Frontend Engineer  
**Benchmarks:** Bloomberg Terminal · TradingView · Professional Portfolio Management System (PMS)  
**Scope:** Home Dashboard (`ui/components/home_dashboard.py`) and Home session shell (`app.py`, navigation)  
**Constraint:** UI-only recommendations — **no backend or frozen-engine changes**  
**Date:** 2026-07-15

---

## Executive Summary

The new Home Dashboard is a meaningful step from “stock analyzer tabs” toward an **Investment Operating System**. It correctly surfaces market context, a canonical decision verdict, opportunities, portfolio, risks, and learning on one scrollable screen — without nested accordions.

**Grade: B− (functional MVP, not yet terminal-grade)**

| Dimension | Score | Note |
|-----------|-------|------|
| Time-to-answer (<10s) | **B+** | Cached bundle helps; first load + scroll still work against the goal |
| Decision clarity | **C+** | Two competing “decision” surfaces; equity vs options lane invisible |
| Action efficiency | **C** | Too many full-width buttons; execution path not one click |
| Information hierarchy | **C** | Flat sections; no session-aware prioritization |
| Portfolio truth | **C−** | Home skips Kite hydrate; P&L semantics ambiguous |
| Professional visual system | **B−** | Good dark cards; lacks status ribbon, clocks, live deltas |

**Highest business-value gap:** Users cannot trust *one* headline decision at a glance because **Today's Market** and **Today's Decision** tell different stories, and the **options-first** MIS path is not visible when no equity star is selected.

---

## Review Lens

### Bloomberg Terminal
- **Expectation:** One status strip — market state, clock, restrictions, portfolio P&L — always visible. Drill-down is optional; headline is never ambiguous.
- **Gap:** Home has no persistent session ribbon. Macro/session strings are diagnostic, not executive.

### TradingView
- **Expectation:** Primary symbol/setup is hero-sized. Watchlist rows are tappable. Time-sensitive gates (open, lunch, close) are visually urgent.
- **Gap:** Opportunities are a static table + five separate “Select” buttons. No live price vs plan entry. No chart/exec shortcut from a row.

### Professional PMS
- **Expectation:** Positions, exposure, risk budget, and day P&L reconcile to broker truth. Allocation and cash are labeled by source.
- **Gap:** “Cash” is modeled (capital − invested), not broker cash. P&L flips between journal and unrealized without a trust badge. Home does not run portfolio hydrate on the fast path.

---

## Session Walkthroughs

### 8:45 AM — Pre-market prep

**User intent:** *What happened overnight? Can I trade today? What is my starred setup? What must happen at open?*

| What works | What fails |
|------------|------------|
| Market regime, risk mode, global bias tiles | **Learning** section consumes above-the-fold attention before open — low urgency |
| Top Opportunities from last night’s scan | No **9:46 AM options re-scan** reminder (exists elsewhere in `unified_prep`) |
| Canonical WAIT/DEFENSIVE when closed | **Decision** tile in Market section shows legacy `PREP` / `CLOSED` while Decision section shows `WAIT` / `DEFENSIVE` — conflicting mental model |
| Scan tonight CTA when empty | **Capital settings** at page bottom compete with prep actions |

**Unnecessary clicks:** Scroll → Quick actions → Intraday (for checklist/OR context). Pre-market user needs OR checklist on Home or a pinned “Opens in X min” ribbon.

**Hidden information:** `trading_restrictions`, premarket macro note, GIFT/global drivers (truncated in tiles), MIS `time_note`, options ★ pick (`mis.best_pick`).

---

### 9:30 AM — Market open / first decision window

**User intent:** *Deploy or wait? Execute starred equity or index options? What is blocked until 9:45?*

| What works | What fails |
|------------|------------|
| Large ACT/WAIT/PASS badge | Decision source opaque: MIS session verdict used unless equity star — **user does not see which lane** |
| Evidence summary bullets | 9:45 opening gate buried in Watchlist risks / evidence fallback — not in hero |
| Star selection available | **Five full-width Select buttons** — Bloomberg/TradingView use single row tap |
| Next step line | No **entry / stop / target** for starred symbol on Home |
| | **Quick actions** (Intraday, Live synthesis) are below fold after Watchlist + Learning |
| | Page title still **“📈 Stock Analyzer”** — undermines OS positioning at the moment of trust |

**Information overload:** Market (7 tiles) + Decision + Opportunities table + 5 buttons + Portfolio + duplicated Watchlist + Learning — same layout as 8:45 AM though cognitive priority changed.

**Missing decision support:** `explainability.why_not`, `invalidation_conditions`, `alternative_actions` from `DecisionArtifact` are not surfaced. No link to **Live Options Coach** when MIS drives the verdict.

---

### 1:00 PM — Mid-session management

**User intent:** *Am I still allowed to add risk? How is today’s P&L? Is the plan still valid?*

| What works | What fails |
|------------|------------|
| Risk flags in Watchlist | Opportunities are **last-night static levels** — no live LTP distance to entry/target |
| Portfolio exposure % + risk budget | P&L may show **unrealized holdings** while user expects **today’s realized MIS P&L** |
| WAIT/PASS semantics | No open-position row (MIS or delivery) on Home — must leave for Intraday / My Portfolio |
| | **Top Opportunities** and **Watchlist › Best opportunities** duplicate the same three symbols |

**Weak hierarchy:** Portfolio (right column) should gain visual weight mid-session; it has equal weight to stale opportunity prep.

**Poor navigation:** “Intraday” is not in the default nav group tabs — only via Quick actions. Users on Home may not discover the live checklist and capital budget panel.

---

### 3:15 PM — Late session / reduce risk

**User intent:** *Stop new entries. Square-off awareness. Protect day gains.*

| What works | What fails |
|------------|------------|
| MIS flags include late-entry concepts (backend) | **3:10 PM hard stop** and **2:00 PM caution** not promoted to hero or session ribbon |
| REDUCE/DEFENSIVE verdict styling exists | User must scroll to Decision — no sticky “session phase: wind-down” |
| Risk budget metric | No “remaining risk” vs “used today” — only static max loss % |

**Missing decision support:** No explicit **“no new entries”** countdown or phase label (`wind_down`) in the decision card. TradingView-style urgency (color pulse, clock) absent.

---

### After market close — Review and prep

**User intent:** *Log P&L. Did yesterday’s process work? Scan for tomorrow. Tune capital.*

| What works | What fails |
|------------|------------|
| Learning section (yesterday vs broker) | Learning shows **prep score** not **yesterday’s canonical verdict** — calibration story incomplete |
| Scan tonight’s stocks CTA | Learning buried under intraday sections user no longer needs |
| Capital settings visible | Settings should be **primary** after close but still below Quick actions |
| Track Record shortcut | No **one-click EOD journal** on Home (only navigate away) |

**Hidden information:** Broker calibration % is shown but not tied to **confidence bucket** accuracy. `learning_source_stats` could be a single trust meter — currently a footnote in Learning.

---

## Findings by Category

### 1. Unnecessary clicks

| Issue | Severity | Session impact |
|-------|----------|----------------|
| Five separate “Select {ticker}” buttons instead of row selection | High | 9:30 AM |
| Navigate Home → Intraday for checklist, OR, live chart | High | 8:45, 9:30 |
| Navigate Home → My Portfolio for live holdings | High | 1:00 PM |
| Navigate Home → Track Record to log P&L | Medium | After close |
| Save settings requires explicit button (no auto-save on blur) | Low | After close |
| Two-step nav (Category + Page) on every visit | Medium | All |

### 2. Hidden information

| Data already available (APIs frozen) | Where it lives today | Should be visible on Home |
|-----------------------------------|----------------------|---------------------------|
| MIS `best_pick`, `gate_allowed`, `time_note` | `build_mis_trade_advisory()` | Decision hero / options card |
| `trading_restrictions[]` | `ContextSnapshot` | Session ribbon |
| `explainability.why_not`, `invalidation_conditions` | `DecisionArtifact` | Decision card (expand inline) |
| Starred symbol entry/stop/target | `PinnedPlan` + `InvestmentOS` modules | Opportunity hero |
| Options ★ / 9:46 rescan status | `unified_prep` patterns | Pre-market banner |
| Live portfolio / Kite LTP | `portfolio_live` (skipped on Home path) | Portfolio with freshness badge |
| Evidence conflicts/gaps counts | `EvidencePacket` | Evidence summary (not just bullet list) |
| Decision lane (equity vs session) | `_pick_decision()` | Label under verdict badge |

### 3. Information overload

| Overload pattern | Recommendation direction |
|------------------|-------------------------|
| Seven market tiles always shown | Collapse to 3 primaries + “More context” inline |
| Opportunities table + 5 buttons + Watchlist repeat | Single ranked list with inline star |
| Learning always rendered | Session-mode: collapse after open |
| Capital settings always rendered | Session-mode: show after 3:30 PM or via gear icon |
| Evidence bullets + synthesis pillars + flags (fallback chain) | Single evidence block with source tag |
| Legacy + canonical verdict concepts | One verdict language only on Home |

### 4. Weak hierarchy

| Problem | Professional pattern |
|---------|---------------------|
| Brand tagline same visual weight as decisions | Tagline micro; verdict mega |
| Market “Decision” tile ≠ Today’s Decision | Rename tile to “Session status” or remove |
| All sections use identical card chrome | Decision card 2× visual prominence |
| Portfolio metrics equal to opportunity prep at 1 PM | Time-weighted column order |
| Footer caption (snapshot id) more prominent than data freshness | “Live · 45s ago · broker P&L” trust line |

### 5. Poor navigation

| Issue | Business impact |
|-------|-----------------|
| Home fast path hides sidebar: Kite connect, data health, autopilot | User cannot fix stale data without leaving Home |
| “Suggestions” tab duplicates Home overlap | Cognitive duplication; unclear IA |
| Intraday / Live Options Coach not in default group | Execution workflows orphaned |
| No ⌘ Jump on Home | Power users lose fastest nav |
| `page_title` / `st.title` still “Stock Analyzer” | Brand trust at decision moment |

### 6. Missing decision support

| Gap | Available without backend change |
|-----|----------------------------------|
| Dual verdict confusion | UI copy + single primary verdict; secondary as “Equity lane / Options lane” |
| No execution card | Render starred `PinnedPlan` levels + link to Intraday chart |
| No invalidation / why-not | Read from `DecisionArtifact.explainability` |
| No options opportunity row | Surface `mis.best_pick`, `mis.gate_allowed` |
| No session clock / phase | Read `snapshot.market_phase`, `market_session` |
| No broker-truth P&L badge | Label computed vs journal vs Kite clearly |
| No “freshness” on context | Show `snapshot.timestamp`, cache TTL |

### 7. Visual improvements (UI-only)

| Area | Recommendation |
|------|----------------|
| **Status ribbon** | Sticky top: phase clock, risk mode, day P&L, starred symbol |
| **Verdict typography** | ACT green glow; PASS desaturated; DEFENSIVE gray — increase size delta |
| **Semantic color** | Risk mode and breadth use consistent semantic tokens (not just verdict) |
| **Live deltas** | ▲▼ next to P&L and exposure (even if from last hydrate) |
| **Row density** | TradingView-style compact opportunity rows; reduce button height |
| **Conflict UX** | Evidence conflicts as amber chips, not prose bullet |
| **Empty states** | Pre-market vs closed vs open specific illustrations/copy |
| **Mobile** | Decision sticky; market tiles 2×2; hide Learning below fold by default |
| **Dark theme polish** | Reduce border noise; stronger focal gradient on decision card only |

---

## Recommendations Ranked by Business Value

Scores: **Impact** (revenue/retention/trust) · **Effort** (UI-only) · **Confidence**

### Tier 1 — Critical (do first)

| Rank | Recommendation | Impact | Effort | Why |
|------|----------------|--------|--------|-----|
| **1** | **Unify verdict hierarchy** — remove or relabel Market tile “Decision”; show one canonical headline; badge secondary lane (“Equity” / “Options / Session”) | ⬛⬛⬛⬛⬛ | S | Eliminates trust-breaking contradiction at 9:30 AM |
| **2** | **Session-aware layout** — reorder/collapse sections by `market_phase` (pre_open → decision+opps; mid_session → portfolio+decision; closed → learning+scan+settings) | ⬛⬛⬛⬛⬛ | M | Same data, correct priority — Bloomberg day structure |
| **3** | **Sticky decision + session ribbon** — phase, restrictions, countdown to 9:45 / 3:10, verdict, confidence | ⬛⬛⬛⬛⬛ | M | Answers “should I deploy capital?” without scroll |
| **4** | **One-click execution path** — starred row shows E/SL/T; tap row to star; “Open chart” / “Open Intraday” on same row | ⬛⬛⬛⬛ | M | Reduces 3+ clicks to 1 at open |
| **5** | **Portfolio truth labeling** — “Modeled cash” vs broker; P&L source badge; optional “Refresh holdings” calling existing hydrate | ⬛⬛⬛⬛ | M | PMS credibility; avoids false confidence |

### Tier 2 — High value

| Rank | Recommendation | Impact | Effort | Why |
|------|----------------|--------|--------|-----|
| **6** | **Options decision card** — `best_pick`, gate, synthesis one-liner, link to Live Options Coach | ⬛⬛⬛⬛ | S | Surfaces MIS value already computed |
| **7** | **Deduplicate opportunities** — merge Top Opportunities + Watchlist best into one ranked panel | ⬛⬛⬛ | S | Cuts scroll fatigue and repetition |
| **8** | **Surface `why_not` + invalidation** from `DecisionArtifact` under verdict | ⬛⬛⬛ | S | Institutional explainability; no backend work |
| **9** | **Time-critical risk promotion** — 9:45 / 2:00 / 3:10 flags as ribbon alerts, not list items | ⬛⬛⬛ | S | Late-session loss prevention |
| **10** | **Home sidebar essentials** — Kite status, data health dot, autopilot on Home fast path (read-only chips) | ⬛⬛⬛ | M | Fixes “hidden infrastructure” on the default screen |
| **11** | **IA cleanup** — rename app shell to Investment OS; add Intraday + Live Options to default group or Home quick strip | ⬛⬛⬛ | S | Navigation matches user mental model |
| **12** | **Evidence UX upgrade** — category chips, conflict count badge, link to evidence packet id | ⬛⬛⬛ | M | Makes Evidence Engine tangible |

### Tier 3 — Medium value

| Rank | Recommendation | Impact | Effort | Why |
|------|----------------|--------|--------|-----|
| **13** | **Live distance on opportunities** — show LTP vs entry if available from pulse/cache (read-only) | ⬛⬛⬛ | M | TradingView-like plan validity at 1 PM |
| **14** | **Learning upgrade** — show yesterday’s verdict label + outcome + broker P&L in one calibration row | ⬛⬛ | S | Closes the learning loop visually |
| **15** | **Inline EOD actions after close** — “Log P&L” opens modal/sheet on Home via existing journal UI patterns | ⬛⬛ | M | Keeps user on Home for close workflow |
| **16** | **Collapse capital settings** to gear drawer after close only | ⬛⬛ | S | Reduces clutter during market hours |
| **17** | **Pre-market banner** — options rescan status, prep date, star status | ⬛⬛ | S | Reuses `unified_prep` signposting |
| **18** | **Freshness footer** — “Context 12s ago · Portfolio saved 6h ago” | ⬛⬛ | S | Transparency builds trust |

### Tier 4 — Polish (defer until Tier 1–2 done)

| Rank | Recommendation | Impact | Effort |
|------|----------------|--------|--------|
| 19 | Sparkline / heat indicators on regime and breadth tiles | ⬛ | M |
| 20 | Keyboard shortcuts on Home (star, refresh, go intraday) | ⬛ | M |
| 21 | Compact nav default with flat “Today / Trade / Research / Portfolio” | ⬛ | L |
| 22 | Animated phase transitions (wind-down pulse) | ⬛ | S |

---

## Suggested Target Layout (UI-only wireframe)

```text
┌─────────────────────────────────────────────────────────────────┐
│ RIBBON  09:28 IST · opening · RISK-ON · NIFTY bias · ★ RELIANCE │
│         Day P&L +₹420 (journal) · Exposure 62% · Gate: wait 9:45│
├─────────────────────────────────────────────────────────────────┤
│ HERO    WAIT  58%   [Options lane]                               │
│         Reason (why) · why-not (1 line) · invalidation (chips)   │
│         [Open Intraday] [Live Options Coach]                     │
├──────────────────────────────┬──────────────────────────────────┤
│ OPPORTUNITIES (ranked rows)  │ PORTFOLIO (live badge)           │
│ tap row = star · E/SL/T      │ today P&L · exposure · risk used │
├──────────────────────────────┴──────────────────────────────────┤
│ RISKS (restrictions + flags) — amber chips only                  │
├─────────────────────────────────────────────────────────────────┤
│ MARKET CONTEXT (collapsed 3-up) · Learning (after close only)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## What Not to Change (Explicit)

Per product constitution — **do not** solve these in UX by altering:

- `Broker Truth`, `Context Engine`, `Evidence Engine`, `Decision Engine` logic or APIs
- Verdict production path (`DecisionEngine.decide()` only)
- Context snapshot schema or producer orchestration

All recommendations above assume **read-only consumption** of existing artifacts: `ContextSnapshot`, `DecisionArtifact`, `EvidencePacket`, `MisTradeAdvisory`, `InvestmentOS`, `load_saved_portfolio()`, `resolve_learning_outcomes()`.

---

## Success Metrics (post-UX iteration)

| Metric | Target |
|--------|--------|
| Time to answer “deploy capital?” on Home | < 3 seconds, no scroll (ribbon + hero) |
| Clicks from Home to execution-ready (starred + levels visible) | ≤ 1 |
| User-reported verdict confusion | Near zero (single headline) |
| Home → leave rate before 9:45 AM | ↓ (checklist on Home) |
| After-close scan completion from Home | ↑ (learning + scan above fold) |

---

## Summary

The Home Dashboard has the **right sections** for an Investment OS but not yet the **right choreography**. Bloomberg teaches that **time and trust** come from a single status layer; TradingView teaches that **the setup is the hero**; PMS teaches that **P&L and exposure must say where the number came from**.

**Top three moves (UI-only, highest ROI):**

1. One verdict, one hierarchy — kill dual-decision confusion.  
2. Session-mode layout + sticky ribbon — same APIs, different story by clock.  
3. One ranked opportunity list with inline execution — star, levels, and go-live in one gesture.

Implementing Tier 1 alone would move the dashboard from **B− to A−** without touching frozen backend logic.

---

*Related:* [08_Final_Investment_OS_Architecture.md](./08_Final_Investment_OS_Architecture.md) · [16_Migration_Completion_Report.md](./16_Migration_Completion_Report.md)
