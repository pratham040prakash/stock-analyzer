# 19 — Product Improvement Backlog

**Role:** Chief Product Officer  
**Persona:** Serious Indian investor — delivery + tactical MIS, Zerodha/Kite, SIP wealth track, opens app **every morning before market open (8:30–9:15 AM IST)**  
**Constraint:** **No new features.** Reorganize, surface, simplify, and de-clutter what already exists.  
**Benchmark:** Bloomberg discipline · TradingView execution clarity · PMS truthfulness  
**Date:** 2026-07-15  
**Related:** [18_Product_UX_Review.md](./18_Product_UX_Review.md) · [08_Final_Investment_OS_Architecture.md](./08_Final_Investment_OS_Architecture.md)

---

## Executive Summary

The Investment OS has strong **decision infrastructure** (context → evidence → verdict → broker learning) but weak **morning choreography**. A serious Indian investor opening at 8:45 AM does not need more analysis — they need **one trusted answer**, **one starred plan**, and **one checklist before 9:45**.

Today the product feels like a capable Streamlit research app with an OS dashboard bolted on. It does not yet feel like a **morning command center**.

**Morning readiness grade: C+**

| Question | One-line answer |
|----------|-----------------|
| Difficult decisions | Whether to deploy tactical capital today; equity vs options lane; size vs gate timing |
| Missing information | Gift Nifty cue, Kite health, OR plan, options ★, prep completeness, broker-truth P&L |
| Unnecessary information | Duplicate opportunity lists, Learning pre-open, capital sliders, seven market tiles |
| Simplification | One verdict, one opportunity list, one morning strip, session-mode layout |
| Above the fold | Session ribbon → canonical verdict → starred execution card → top 3 risks |
| Bloomberg feel | Persistent status bar, monospace numbers, data freshness, no page-title clutter |

---

## 1. What Decisions Are Difficult?

Decisions are hard when the UI forces the investor to **reconcile multiple truths** or **leave Home** to act.

| Decision | Why it is hard today | Morning pain (8:45 AM) |
|----------|----------------------|-------------------------|
| **Deploy tactical capital today?** | Two verdict surfaces: Market tile shows legacy `PREP`/`CLOSED`; Decision card shows `WAIT`/`DEFENSIVE`. Investor must mentally merge them. | High — this is the first question every morning |
| **Equity MIS vs index options MIS?** | `_pick_decision()` prefers equity when starred, else MIS session — **lane not labeled**. Serious options traders misread the headline. | High — dual workflow is core to Indian retail |
| **Wait for 9:45 or act at 9:30?** | Opening gate exists in `trading_restrictions` and MIS flags but not in hero. Investor scrolls to Watchlist risks. | High — most common discipline failure |
| **Which single name to execute?** | Five full-width Select buttons; no inline E/SL/T on Home. Star state scattered across Opportunities + Watchlist. | Medium — after prep night before |
| **How much to risk?** | Risk budget shown; no “remaining dam” vs loss already taken today. Journal P&L may be empty pre-open. | Medium |
| **Is my data/truth stack ready?** | Home fast path skips Kite hydrate, data health sidebar, autopilot strip. Investor discovers stale state mid-session. | High — silent failure mode |
| **SIP wealth vs tactical pool** | Architecture defines sacred core vs tactical pool; UI treats one `capital` slider. Investor conflates long-term and MIS risk. | Medium — wealth preservation decision |
| **Trust the overnight scan?** | Opportunities are static pins; no prep date / freshness / “last scan” prominence on Home. | Medium |

**CPO judgment:** The product optimizes for **comprehensiveness** when the morning user optimizes for **commitment under uncertainty**. Hard decisions are hard because **the UI debates itself**, not because analysis is missing.

---

## 2. What Information Is Missing?

Information that **already exists in the codebase** but is **not on Home before open**:

| Missing signal | Source (existing) | Morning value |
|----------------|-------------------|---------------|
| **Gift Nifty / gap cue** | `morning_cockpit.fetch_gift_nifty_cue()` | Sets overnight bias before NSE open |
| **Kite connection + NFO** | `kite_connection_status()` in `morning_cockpit` | Without this, live OR and options are fiction |
| **Equity ★ + options ★ status** | `selection_status_line()`, `option_selection_status_line()` | Confirms last night’s prep is complete |
| **9:46 AM options re-scan state** | `was_morning_options_rescan_sent()` in `unified_prep` | Critical for index CE/PE after OR |
| **Opening range plan** | `confirm_or_entry()` / OR fetch in `morning_cockpit` | Bridges 9:15–9:45 observe window |
| **Prep checklist progress** | `prep_status_for()` in `unified_prep` | Answers “am I ready?” |
| **Decision lane label** | `_pick_decision()` metadata | Equity vs session/options |
| **`why_not` + invalidation** | `DecisionArtifact.explainability` | Professional invert-always discipline |
| **MIS `best_pick` + gate** | `MisTradeAdvisory` | Options-first investors’ primary setup |
| **Data health summary** | `build_data_health()` | Macro/regime wrong if feeds stale |
| **Autopilot / prep job status** | `autopilot_status` sidebar | Did nightly scan actually run? |
| **Broker-truth freshness** | `learning_source_stats()` | Trust in calibration before sizing up |
| **Prep date on pins** | `PinnedPlan.prep_date` | Stale picks from prior session |

**CPO judgment:** The app **knows** the morning story but tells it on **Suggestions**, **Intraday**, and **sidebar** — not on the default landing screen.

---

## 3. What Information Is Unnecessary?

For a **pre-market** open, these elements add scroll and cognitive load without improving the first decision:

| Element | Location | Why unnecessary before open |
|---------|----------|----------------------------|
| **Learning section** | Home §6 | Yesterday’s calibration irrelevant until after close |
| **Capital settings sliders** | Home footer | Configuration, not decision support; belongs in Settings / after close |
| **Duplicate opportunity lists** | Top Opportunities + Watchlist › Best | Same pins twice |
| **Five Select buttons** | Top Opportunities | Repeats star action; wastes vertical space |
| **Seven market tiles** | Today’s Market | Regime + risk + global bias sufficient; macro/session strings are diagnostic |
| **“Stock Analyzer” title** | `app.py` | Wrong product frame at moment of trust |
| **Full portfolio allocation** | Home §4 pre-open | Delivery book secondary to tactical deploy decision |
| **Quick actions row (4 buttons)** | Home footer | Duplicates nav; buried below fold |
| **Suggestions tab overlap** | Separate tab | Repeats picks, cockpit, stats — splits morning workflow |
| **Evidence fallback chain** | Decision card | Pillars + flags + evidence when packet empty — reads as inconsistency |
| **snapshot_id in footer** | Home caption | Engineer-facing; not investor-facing |

**CPO judgment:** ~40% of Home scroll depth before 9:15 AM is **review content** (learning, settings, duplicates), not **prep content**.

---

## 4. What Can Be Simplified?

| Simplify | From → To | Investor benefit |
|----------|-----------|------------------|
| **Verdict model** | Legacy tile + canonical card → **one headline verdict** + optional sub-label | Stops self-debate |
| **Opportunities** | Table + 5 buttons + watchlist repeat → **one ranked list** (tap row = star) | One glance, one action |
| **Navigation** | Category + Page + hidden Intraday → **Today / Execute / Research / Portfolio** | Matches mental model |
| **Morning workflow** | Home + Suggestions + Intraday → **Home = morning command center**; Suggestions = archive/detail | One morning entry point |
| **Market context** | 7 tiles → **3 primaries** (Regime · Risk · Global) + expand | Faster scan |
| **Portfolio on Home** | 4 metrics always → **readiness chip pre-open**; full metrics after 9:30 | Right weight by clock |
| **Settings** | Always-visible sliders → **gear drawer / after-close only** | Removes config noise |
| **Decision evidence** | Long bullet list → **3 supports + 1 why-not + conflict chip** | Munger-style clarity |
| **Page shell** | Title + tagline + brand + sections → **ribbon + hero only above fold** | Terminal density |

---

## 5. What Should Appear Above the Fold?

**Target viewport (desktop ~900px height, 8:45 AM):**

```text
┌──────────────────────────────────────────────────────────────────┐
│ 1. SESSION RIBBON (sticky)                                       │
│    08:47 IST · pre_market · CLOSED · RISK-ON · Gift Nifty +0.4%  │
│    Kite ✅ · Equity ★ RELIANCE · Options ★ NIFTY CE · Prep 4/5   │
├──────────────────────────────────────────────────────────────────┤
│ 2. TODAY'S DECISION (hero)                                       │
│    WAIT · 62% · [Session lane: Options]                          │
│    Why: Market closed — no new MIS entries until open            │
│    Next: Wait for 9:45 OR confirm on ⭐ RELIANCE               │
│    [Open Intraday checklist]  [Live Options Coach]               │
├──────────────────────────────────────────────────────────────────┤
│ 3. EXECUTION CARD (starred setup)                                │
│    RELIANCE LONG · Entry ₹2,450 · SL ₹2,420 · T ₹2,510 · 2.0R   │
│    OR status: pending · Ladder: —                                  │
├──────────────────────────────────────────────────────────────────┤
│ 4. RISKS (max 3 chips)                                           │
│    Before 9:45 — observe only · Loss streak 0 · IV elevated      │
└──────────────────────────────────────────────────────────────────┘
```

**Below fold (still on Home, not other tabs):** condensed opportunities (max 5), portfolio readiness chip, collapsed market context.

**Not above fold before open:** Learning, capital sliders, weekly stats, full evidence dump, duplicate watchlist.

---

## 6. What Would Make This Feel Like Bloomberg Instead of Streamlit?

| Streamlit tell | Bloomberg / terminal antidote | UI-only path |
|----------------|------------------------------|--------------|
| Page title “Stock Analyzer” | Product = **Investment OS** | Rename shell; remove emoji H1 on Home |
| Vertical scroll essay | **Fixed status ribbon** + scannable panels | Sticky header; reduce section count |
| Generic `st.metric` cards | **Monospace figures**, aligned columns, delta arrows | Typography + layout CSS |
| Mystery data age | **“Live · 12s ago” / “Saved · 6h ago”** badges | Surface timestamps already in snapshot |
| Buttons everywhere | **Dense rows** with inline actions | Row-click patterns |
| Two-step nav radios | **Flat command bar** or persistent sidebar modules | IA simplification |
| Sidebar hidden on Home | **Infrastructure always visible** (Kite, data health) | Read-only chips on ribbon |
| Mixed verdict languages | **ACT/WAIT/PASS only** in headline | Copy + hierarchy fix |
| Research tabs upfront | **Decision-first, research-second** | Default Home; research deprioritized AM |
| No clock / phase | **Session phase is first-class** | `market_phase` in ribbon |
| Config sliders on dashboard | **Settings in separate surface** | Time-gate settings panel |

**CPO line:** Bloomberg does not ask “which page?” at 8:45 AM. It shows **state, constraint, and action** in one band.

---

## Scoring Method

Each backlog item is scored **1–5** on:

| Dimension | 5 means |
|-----------|---------|
| **Impact on investment decisions** | Directly changes deploy / wait / size / avoid catastrophic mistake |
| **Implementation complexity** | 5 = hardest (many files, Streamlit constraints, edge cases) |
| **User value** | Daily morning value for serious Indian investor |

**Priority index** = `(Impact × 3) + (User Value × 2) − Complexity`  
Higher = ship first. Ties broken by Impact.

**Effort bands:** S ≤ 1 day · M 2–4 days · L 1–2 weeks · XL structural

---

## Ranked Product Improvement Backlog

### Tier P0 — Ship first (Priority index ≥ 18)

| Rank | ID | Recommendation | Impact | Complexity | User Value | Priority | Effort |
|------|-----|----------------|--------|------------|------------|----------|--------|
| **1** | P0-01 | **Single canonical verdict** — remove/relabel Market “Decision” tile; one ACT/WAIT/PASS headline | 5 | 2 | 5 | **21** | S |
| **2** | P0-02 | **Morning session ribbon** — time, phase, risk mode, Gift Nifty, Kite status, prep progress (reuse `morning_cockpit` data) | 5 | 3 | 5 | **19** | M |
| **3** | P0-03 | **Label decision lane** — “Equity” vs “Options/Session” under verdict | 5 | 1 | 5 | **20** | S |
| **4** | P0-04 | **Starred execution card** — E/SL/T, side, R:R, OR status for ★ symbol on Home | 5 | 3 | 5 | **19** | M |
| **5** | P0-05 | **9:45 gate in hero** — promote `trading_restrictions` / MIS time flags to decision ribbon | 5 | 2 | 5 | **20** | S |
| **6** | P0-06 | **Session-mode Home layout** — hide Learning + capital settings before `opening`; collapse market tiles | 4 | 3 | 5 | **18** | M |

### Tier P1 — High value (Priority index 14–17)

| Rank | ID | Recommendation | Impact | Complexity | User Value | Priority | Effort |
|------|-----|----------------|--------|------------|------------|------------|--------|
| **7** | P1-01 | **Merge duplicate opportunity lists** — one ranked panel; remove Watchlist repeat | 4 | 2 | 4 | **16** | S |
| **8** | P1-02 | **Row-tap star selection** — replace five full-width Select buttons | 4 | 2 | 4 | **16** | S |
| **9** | P1-03 | **Surface options ★ + 9:46 rescan status** on Home (from `unified_prep`) | 4 | 2 | 5 | **17** | S |
| **10** | P1-04 | **Kite + data health chips on Home** — surface sidebar signals on fast path | 4 | 3 | 5 | **16** | M |
| **11** | P1-05 | **Portfolio truth labels** — “Modeled cash” vs broker; P&L source badge; stale holdings warning | 4 | 3 | 4 | **15** | M |
| **12** | P1-06 | **Show `why_not` + top invalidation** from `DecisionArtifact` (max 2 lines) | 4 | 2 | 4 | **16** | S |
| **13** | P1-07 | **Rename product shell** — “Investment OS” not “Stock Analyzer” on Home | 3 | 1 | 5 | **16** | S |
| **14** | P1-08 | **MIS best pick + gate line** on Home when options lane active | 4 | 2 | 4 | **16** | S |
| **15** | P1-09 | **Prep completeness indicator** — `prep_status_for()` as ribbon chip | 4 | 2 | 4 | **16** | S |
| **16** | P1-10 | **Data freshness badges** — context timestamp, portfolio last sync | 3 | 2 | 4 | **14** | S |

### Tier P2 — Medium value (Priority index 10–13)

| Rank | ID | Recommendation | Impact | Complexity | User Value | Priority | Effort |
|------|-----|----------------|--------|------------|------------|--------|
| **17** | P2-01 | **Sticky decision ribbon** on scroll (verdict + phase + day P&L) | 4 | 3 | 3 | **13** | M |
| **18** | P2-02 | **Collapse market context to 3 tiles** + “More context” expander | 3 | 2 | 4 | **13** | S |
| **19** | P2-03 | **Move capital settings to gear / after-close panel** | 2 | 2 | 4 | **12** | S |
| **20** | P2-04 | **IA: add Intraday + Live Options to default morning nav** | 3 | 2 | 4 | **13** | S |
| **21** | P2-05 | **Clarify Suggestions vs Home** — Suggestions becomes detail/archive; Home owns morning | 3 | 3 | 4 | **12** | M |
| **22** | P2-06 | **Autopilot last-run chip** — nightly prep / morning list status on ribbon | 3 | 3 | 4 | **12** | M |
| **23** | P2-07 | **Evidence summary → 3 bullets + conflict chip** | 3 | 2 | 3 | **11** | S |
| **24** | P2-08 | **Prep date on opportunities** — show stale pin warning | 3 | 1 | 3 | **12** | S |
| **25** | P2-09 | **Portfolio section: readiness-only pre-open** (Kite linked? holdings count?) | 3 | 2 | 3 | **11** | S |
| **26** | P2-10 | **Quick links: Intraday checklist + Live Options** in execution card, not footer | 3 | 1 | 3 | **12** | S |

### Tier P3 — Polish / structural (Priority index < 10)

| Rank | ID | Recommendation | Impact | Complexity | User Value | Priority | Effort |
|------|-----|----------------|--------|------------|------------|------------|--------|
| **27** | P3-01 | **Terminal typography** — tabular nums, tighter row height, semantic colors | 2 | 3 | 3 | **8** | M |
| **28** | P3-02 | **Remove engineer footer** (snapshot_id) → investor freshness line | 1 | 1 | 3 | **8** | S |
| **29** | P3-03 | **⌘ Jump on Home fast path** | 2 | 2 | 3 | **9** | S |
| **30** | P3-04 | **Learning section: after-close only** with yesterday verdict + broker P&L | 2 | 2 | 3 | **9** | S |
| **31** | P3-05 | **Separate SIP vs tactical capital labels** (prefs copy; no new engine) | 3 | 4 | 3 | **8** | L |
| **32** | P3-06 | **Flat nav: Today / Execute / Research / Portfolio** | 2 | 4 | 3 | **6** | L |
| **33** | P3-07 | **Live LTP distance on opportunities** (when pulse/cache has price) | 3 | 4 | 3 | **7** | L |
| **34** | P3-08 | **Remaining risk budget vs used today** (journal-aware display) | 3 | 4 | 3 | **7** | L |
| **35** | P3-09 | **Wind-down / 3:10 PM urgency styling** in ribbon (phase-aware) | 3 | 2 | 2 | **9** | S |

---

## Morning-Only Acceptance Criteria (P0 bundle)

When a serious investor opens the app at **8:45 AM IST**, within **5 seconds** and **without scrolling** they can answer:

| # | Question | Pass condition |
|---|----------|----------------|
| 1 | Is the market context hostile or supportive? | Ribbon: regime + risk + Gift Nifty |
| 2 | Should I deploy tactical capital at open? | Single canonical verdict + lane label |
| 3 | What is my one plan? | Execution card: ★ symbol + E/SL/T |
| 4 | What must I wait for? | 9:45 / prep / Kite gate visible in hero |
| 5 | Is my stack truthful? | Kite + data health + freshness chips |

---

## What We Will Not Do (Scope Guard)

Per CPO mandate — **no new features** in this backlog:

- New scanners, strategies, or AI models  
- New broker integrations beyond surfacing existing Kite state  
- New decision rules in Context / Evidence / Decision engines  
- New data feeds (only surface existing Gift Nifty, OR, etc.)  
- Mobile native app / separate frontend framework  

This backlog is **presentation, information architecture, and time choreography** only.

---

## Recommended Sequencing (No new features)

```text
Sprint A (P0)     Verdict unification · ribbon · execution card · 9:45 gate · session layout
Sprint B (P1)     Dedupe opportunities · options ★ · truth labels · why_not · product rename
Sprint C (P2)     Nav IA · settings relocation · evidence compression · autopilot chip
Sprint D (P3)     Terminal typography · flat nav · live distance · risk-used display
```

**Expected outcome after Sprint A+B:** Morning readiness **C+ → B+**. Investor stops leaving Home before 9:15 AM.

**Expected outcome after Sprint C+D:** Terminal feel **B− → B+** without leaving Streamlit.

---

## CPO Verdict

The Investment OS **won the architecture migration** but has not yet **won the morning**. The serious Indian investor does not fail for lack of modules — they fail because the app still asks them to **integrate** Suggestions, Home, Intraday, and sidebar state at 8:45 AM.

**Ship P0-01 through P0-06 before any new capability.** That is the highest ROI path to decision quality — not more analysis, but **one screen that commits the investor to a single disciplined action**.

---

*End of backlog. No application code modified.*
