# 20 — Product Information Architecture & Five-Page OS Redesign

**Role:** Chief Product Officer  
**Goal:** Transform Stock Analyzer into an **Investment Operating System for a single investor**  
**Constraints:** No new engines · No new indicators · No backend changes · **UI/IA only**  
**Date:** 2026-07-15  
**Related:** [19_Product_Improvement_Backlog.md](./19_Product_Improvement_Backlog.md) · [08_Final_Investment_OS_Architecture.md](./08_Final_Investment_OS_Architecture.md)

---

## Executive Summary

The application has **~20 top-level tabs** across **5 nav groups** plus a hidden sidebar of infrastructure (Kite, autopilot, data health, setup). The backend already supports a single-investor OS — context, evidence, decisions, broker truth, Kite sync, portfolio advice, and learning.

The product problem is **fragmentation**: the investor must know that “Suggestions,” “Intraday,” “Daily Advisor,” “My Portfolio,” and “Track Record” are one workflow split across five doors.

**Target state:** Five primary pages with a clear hierarchy:

```text
1. Home        — What should I do today? (tactical OS)
2. Portfolio   — What do I own and how healthy is it? (wealth OS)
3. Research    — Why is this true? (analysis OS)
4. Journal     — What happened and what did I learn? (truth OS)
5. Settings    — How is the system configured? (platform OS)
```

**Design principle:** Every existing feature becomes a **section, panel, or drill-down** — never a standalone top-level tab.

---

## 1. Product Information Architecture

### 1.1 Investor mental model

| Capital layer | Primary page | Question |
|---------------|--------------|----------|
| **Tactical pool** (MIS / intraday) | Home | Deploy, wait, or pass today? |
| **Growth engine** (delivery / swing) | Portfolio | Hold, add, reduce, or exit? |
| **Sacred core** (SIP / goals) | Portfolio › Wealth | Am I on track for long-term goals? |
| **Process truth** | Journal | Did the system and I calibrate? |
| **Thesis depth** | Research | Conviction, valuation, macro, options chain |
| **Platform** | Settings | Kite, capital limits, autopilot, alerts |

### 1.2 Page hierarchy (importance)

```text
                    ┌─────────────┐
                    │    HOME     │  ← default landing, morning command
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌─────────────┐           ┌─────────────┐
       │  PORTFOLIO  │           │  RESEARCH   │
       │  (wealth)   │           │  (thesis)   │
       └──────┬──────┘           └──────┬──────┘
              │                         │
              └────────────┬────────────┘
                           ▼
                    ┌─────────────┐
                    │   JOURNAL   │  ← broker truth, EOD, calibration
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
                    │  SETTINGS   │  ← infra, prefs, education
                    └─────────────┘
```

### 1.3 Content types per page

| Page | Primary content types | Data sources (existing, frozen) |
|------|----------------------|----------------------------------|
| **Home** | Verdict, session ribbon, opportunities, execution card, risks | `ContextSnapshot`, `DecisionArtifact`, `MisTradeAdvisory`, `InvestmentOS`, pins |
| **Portfolio** | Holdings, positions, cash, P&L, allocation, sector, per-holding advice, health | Kite holdings/positions/margins, `portfolio_live`, `daily_advisor`, `portfolio_risk`, `advisor` |
| **Research** | Symbol workbench, scanners, macro, options, Alpha AI | `market_pulse_scan`, `alpha_ai_report`, `screener`, `nse_options`, etc. |
| **Journal** | Trade log, watchlist outcomes, broker reconciliation, calibration | `trade_journal`, `broker_truth`, `watchlist_history`, `confidence_calibration` |
| **Settings** | Setup, Kite, capital, autopilot, Telegram, theme, Varsity | `intraday_prefs`, `setup_status`, `autopilot_status`, `env_loader` |

### 1.4 Navigation rules

1. **One primary nav** — five items, always visible, horizontal on desktop / bottom bar on mobile.  
2. **No category radio** — eliminate “Choose a category, then a page.”  
3. **Sub-nav inside page** — tabs or segmented control within each page (max 5 sub-tabs).  
4. **Command palette (⌘ Jump)** — global symbol + deep-link to Research workbench; available on all pages except Settings.  
5. **Legacy tab names** — redirect aliases for bookmarks (`Suggestions` → Home › Execute).  
6. **Home fast path retired** — Home uses same shell as other pages (Kite hydrate, data health chip in header).

### 1.5 Single-investor assumptions

- One Kite profile, one tactical capital pool, one portfolio profile key.  
- No multi-user, no team roles, no separate watchlists per user (profile name field becomes Settings › Identity).  
- SIP goals and MIS prefs are **views on the same investor**, not separate products.

---

## 2. Navigation Redesign

### 2.1 Primary navigation (new)

| # | Label | Icon cue | Default sub-tab | Opens |
|---|-------|----------|-----------------|-------|
| 1 | **Home** | ◉ Today | Dashboard | Morning OS |
| 2 | **Portfolio** | ◈ Wealth | Overview | Kite-integrated book |
| 3 | **Research** | ◇ Analyze | Workbench | Symbol + tools |
| 4 | **Journal** | ○ Truth | Today | P&L + outcomes |
| 5 | **Settings** | ⚙ System | Setup | Platform config |

### 2.2 Global chrome (all pages)

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Investment OS          [⌘ Jump]    09:12 IST · pre_market    Kite ●   │
├────────────────────────────────────────────────────────────────────────┤
│  Home  │  Portfolio  │  Research  │  Journal  │  Settings              │
├────────────────────────────────────────────────────────────────────────┤
│                        << PAGE CONTENT >>                              │
└────────────────────────────────────────────────────────────────────────┘
```

**Global chrome elements (existing modules):**

| Element | Source |
|---------|--------|
| Clock + phase | `market_session_status()` / `ContextSnapshot` |
| Kite status dot | `kite_connection_status()` |
| Data health dot | `build_data_health()` |
| ⌘ Jump | `command_palette` |

### 2.3 Sub-navigation per page

#### Home

| Sub-tab | Purpose |
|---------|---------|
| **Dashboard** (default) | Verdict, market, opportunities, risks |
| **Execute** | Intraday checklist, live charts strip, options coach entry |
| **Prep** | Nightly scan, stars, options ★, prep checklist |

#### Portfolio

| Sub-tab | Purpose |
|---------|---------|
| **Overview** (default) | Health score, summary metrics, allocation |
| **Holdings** | Delivery book + per-holding AI actions |
| **Positions** | Open MIS/CNC positions from Kite |
| **Wealth** | SIP goals, sacred core, long-horizon plan |
| **Briefing** | Daily advisor narrative (was separate tab) |

#### Research

| Sub-tab | Purpose |
|---------|---------|
| **Workbench** (default) | Single stock + Alpha AI entry |
| **Market** | Pulse, global markets, macro |
| **Discover** | Screener, batch scanner, penny picks |
| **Options** | NSE chain, live options advisor, IV tools |
| **Compare** | Side-by-side symbols |

#### Journal

| Sub-tab | Purpose |
|---------|---------|
| **Today** (default) | Day P&L, open trades, quick log |
| **Track Record** | Watchlist hit rate, options outcomes |
| **Learning** | Calibration, broker truth stats, EOD scoring |
| **Backtest** | Historical strategy replay |

#### Settings

| Sub-tab | Purpose |
|---------|---------|
| **Setup** (default) | Wizard, .env, onboarding |
| **Trading** | Capital, risk %, beginner mode, goals |
| **Connect** | Kite OAuth, Telegram, autopilot |
| **System** | Theme, data health, cloud mode |
| **Learn** | Varsity TA reference |

### 2.4 Legacy route map (redirects)

| Old tab / entry | New location |
|-----------------|--------------|
| `Suggestions` | Home › Execute |
| `Track Record` | Journal › Track Record |
| `My Portfolio` | Portfolio › Holdings |
| `Daily Advisor` | Portfolio › Briefing |
| `Market Pulse` | Research › Market |
| `Global Markets` | Research › Market |
| `Single Stock` | Research › Workbench |
| `Alpha AI` | Research › Workbench (mode) |
| `Live Charts` | Home › Execute or Research › Workbench |
| `Live Options Coach` | Home › Execute or Research › Options |
| `NSE Options` | Research › Options |
| `Batch Scanner` | Research › Discover |
| `Screener` | Research › Discover |
| `Penny Picks` | Research › Discover |
| `Compare` | Research › Compare |
| `SIP & Goals` | Portfolio › Wealth |
| `Risk & Goals` | Settings › Trading |
| `Backtest` | Journal › Backtest |
| `Varsity TA` | Settings › Learn |
| Sidebar Setup | Settings › Setup |
| Sidebar Kite | Settings › Connect |
| Sidebar Autopilot | Settings › Connect |
| Sidebar Telegram | Settings › Connect |

---

## 3. Feature Mapping

### 3.1 Pages → modules (summary)

| Page | Absorbs (current tabs) | Core existing backends |
|------|------------------------|-------------------------|
| **Home** | Home, Suggestions, morning cockpit, unified prep, MIS advisory | `investment_os`, `mis_trade_advisory`, `nightly_prep`, `strategy_synthesis` |
| **Portfolio** | My Portfolio, Daily Advisor, SIP & Goals (wealth slice) | `portfolio_live`, `zerodha`, `daily_advisor`, `portfolio_risk`, `advisor`, `sip_planner` |
| **Research** | Alpha AI, Single Stock, Compare, Market Pulse, Global Markets, Screener, Batch Scanner, Penny Picks, NSE Options, Live Options Coach, Live Charts | `alpha_ai_report`, `market_pulse_scan`, `screener`, `combined`, `signals`, etc. |
| **Journal** | Track Record, trade journal, learning panels | `broker_truth`, `trade_journal`, `watchlist_history`, `confidence_calibration`, `eod_learning` |
| **Settings** | Risk & Goals, setup wizard, kite connect, autopilot, theme, Varsity | `intraday_prefs`, `setup_status`, `autopilot_*`, `varsity_knowledge` |

### 3.2 Complete feature mapping table

| Feature / surface | Current location | New page | New section | Existing backend (no change) |
|-------------------|------------------|----------|-------------|------------------------------|
| Home Dashboard | Home | Home | Dashboard | `home_dashboard`, `build_context_snapshot` |
| Canonical verdict ACT/WAIT/PASS | Home | Home | Dashboard › Decision hero | `DecisionEngine` via `mis_trade_advisory` / `investment_os` |
| Today's Market tiles | Home | Home | Dashboard › Context strip | `ContextSnapshot` |
| Top opportunities / star picks | Home | Home | Dashboard › Opportunities | `watchlist_pins`, `pulse_cache` |
| Watchlist risks | Home | Home | Dashboard › Risks | `MisTradeAdvisory`, snapshot restrictions |
| Learning yesterday | Home | Home | Dashboard (after close only) → move to Journal | `resolve_learning_outcomes` |
| Capital settings sliders | Home footer | Settings | Trading › Capital | `intraday_prefs` |
| Morning cockpit (Gift Nifty, OR, ladder) | Suggestions | Home | Dashboard ribbon | `morning_cockpit` |
| Session timing banner | Intraday | Home | Execute › Checklist | `intraday_beginner_tips` |
| MIS daily checklist | Intraday | Home | Execute › Checklist | `mis_checklist_store` |
| Intraday watchlist block | Suggestions | Home | Execute › Live picks | `intraday_watchlist` |
| Options expiry watchlist | unified_prep | Home | Prep › Options ★ | `options_expiry_watchlist` |
| Prep all / nightly scan | unified_prep | Home | Prep › Scan | `nightly_prep` |
| Equity top 5 / options star | unified_prep | Home | Prep › Stars | `watchlist_pins`, `options_trade_selection` |
| Live charts grid | Live Charts | Home | Execute › Charts **or** Research › Workbench | `live_charts` page |
| Live options advisor | Live Options Coach | Home | Execute › Options **or** Research › Options | `live_options_advisor` |
| MIS trade advisory block | components | Home | Execute › Gate | `mis_trade_advisory` |
| Strategy synthesis UI | components | Home | Execute › Synthesis detail | `strategy_synthesis` |
| Small trader intraday portfolio strip | Intraday | Portfolio | Positions › Tactical overlap | `small_trader_intraday` |
| **Kite holdings sync** | My Portfolio | Portfolio | Holdings | `fetch_holdings_from_kite`, `portfolio_store` |
| Live LTP refresh (15s) | My Portfolio | Portfolio | Holdings › Live table | `portfolio_live`, `kite_stream` |
| Manual / CSV holdings | My Portfolio | Portfolio | Holdings › Import | `parse_holdings_csv`, `make_manual_holding` |
| Kite watchlist mirror | My Portfolio | Portfolio | Holdings › Watchlist mirror | `kite_watchlist_store` |
| Portfolio analyze + recommendations | My Portfolio | Portfolio | Holdings › AI column | `portfolio.analyze_portfolio`, `advisor.generate_portfolio_advice` |
| Portfolio risk / concentration | My Portfolio | Portfolio | Overview › Risk | `portfolio_risk.compute_portfolio_risk` |
| **Live positions (MIS/CNC)** | Kite activity only | Portfolio | Positions | `fetch_kite_activity_symbols`, `kite.positions()` |
| **Available cash** | margins in health check | Portfolio | Overview › Cash | `fetch_kite_margins`, `capital_from_kite_margins` |
| Realized P&L (today / session) | Track Record / journal | Portfolio | Overview › P&L | `trade_journal`, `broker_truth` |
| Unrealized P&L | My Portfolio | Portfolio | Overview › P&L | holding `pnl` from Kite LTP |
| Sector exposure | partial in risk | Portfolio | Overview › Sector chart | `portfolio_risk.sector_weights` |
| Allocation donut | My Portfolio | Portfolio | Overview › Allocation | weights from holdings |
| Per-holding AI recommendation | Daily Advisor | Portfolio | Holdings › row expand | `build_daily_briefing`, `HoldingDailyAdvice` |
| Hold / Add / Reduce / Exit | Daily Advisor `today_action` | Portfolio | Holdings › Action badge | `daily_advisor`, `DecisionEngine` attach on advice |
| Portfolio health score | *composite UI* | Portfolio | Overview › Health (0–100) | **Compose:** `portfolio_risk` warnings + concentration + `daily_briefing` priority count + Kite sync freshness — display only |
| Daily briefing narrative | Daily Advisor | Portfolio | Briefing | `build_daily_briefing` |
| Priority actions today | Daily Advisor | Portfolio | Briefing › Actions | briefing `priority_actions` |
| Earnings on holdings | My Portfolio | Portfolio | Holdings › Events chip | `earnings_calendar` |
| SIP planner & goals | SIP & Goals | Portfolio | Wealth | `sip_planner`, `sip_storage` |
| Alpha AI full report | Alpha AI | Research | Workbench › Alpha mode | `alpha_ai_report` |
| Single stock TA | Single Stock | Research | Workbench › Technical | `combined`, `signals`, `chart_horizon` |
| Compare stocks | Compare | Research | Compare | `compare` page logic |
| Market Pulse scan | Market Pulse | Research | Market › Pulse | `market_pulse_scan` |
| Global markets heatmap | Global Markets | Research | Market › Global | `global_markets` + snapshot |
| India macro panel | global / pulse | Research | Market › Macro | `india_macro` via snapshot |
| Screener | Screener | Research | Discover › Screener | `screener` |
| Batch scanner / watchlist builder | Batch Scanner | Research | Discover › Scanner | `watchlist` page |
| Penny picks | Penny Picks | Research | Discover › Penny | `penny_picks` |
| NSE options chain | NSE Options | Research | Options › Chain | `nse_options`, `kite_options_chain` |
| Sideways options advisor | component | Research | Options › Advisor | `sideways_options_advisor` |
| IV rank banner | components | Research | Options › Context | `iv_rank` |
| Affordable invest / lot cost | components | Research | Options › Sizing | `affordable_invest` |
| Trade journal entry | Track Record | Journal | Today › Log trade | `trade_journal` |
| Intraday journal | component | Journal | Today | `intraday_journal` |
| Watchlist success / hit rate | Track Record | Journal | Track Record | `watchlist_stats` |
| Options watchlist outcomes | Track Record | Journal | Track Record › Options | `options_watchlist_history` |
| Confidence calibration | Track Record | Journal | Learning › Calibration | `confidence_calibration` |
| Broker truth sync stats | learning | Journal | Learning › Broker | `broker_truth.learning` |
| EOD validation / tuning | Track Record | Journal | Learning › Validate | `eod_learning`, `threshold_tuning` |
| Suggestion journal | Track Record | Journal | Learning › Pulse journal | `suggestion_journal` |
| Backtest | Backtest | Journal | Backtest | `backtest` page |
| Setup wizard | sidebar | Settings | Setup | `setup_status` |
| Onboarding tour | app shell | Settings | Setup › Tour | `onboarding_tour` |
| Beginner risk & goals | Risk & Goals | Settings | Trading › Risk profile | `beginner_risk`, `market_risk` |
| Intraday prefs (capital, risk %) | sidebar / Home | Settings | Trading › Capital | `intraday_prefs` |
| Kite Connect OAuth | sidebar | Settings | Connect › Kite | `kite_auth`, `kite_connect` |
| Autopilot status & logs | sidebar | Settings | Connect › Autopilot | `autopilot_status` |
| Telegram subscribe | sidebar | Settings | Connect › Alerts | `telegram_subscribe` |
| Theme toggle | sidebar | Settings | System › Display | `theme_toggle` |
| Data health panel | sidebar | Settings | System › Data | `data_health_panel` |
| Varsity TA guide | Varsity TA | Settings | Learn | `varsity_knowledge` |
| Command palette | app shell | Global | Header | `command_palette` |
| NSE error banner | app shell | Global | Header toast | `nse_error_banner` |
| Disclaimer | app shell | Global | Footer (Research + Home) | `DISCLAIMER` constant |

### 3.3 Scripts & autopilot (not pages — Settings › Connect)

| Script / job | Surfaced in Settings as |
|--------------|-------------------------|
| `nightly_prep` / trade_selection_auto | Autopilot › Prep job status |
| `morning_suggestions_scheduler` | Autopilot › Morning list |
| `live_*_coach_watch` | Autopilot › Coach daemons (local only) |
| `daily_trading_guide` | Learn › Daily cheat sheet link |

---

## 4. UI Wireframes

### 4.1 Home — Dashboard (default sub-tab)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ RIBBON  08:47 IST · pre_market · RISK-ON · Gift +0.4% · Kite ✅ · Prep 4/5│
├──────────────────────────────────────────────────────────────────────────┤
│  [Dashboard]   Execute   Prep                                            │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌─ DECISION ───────────────────────────────────────────────────────────┐ │
│ │  WAIT · 58% · Lane: Options/Session                                  │ │
│ │  Why: Market closed — no new MIS until open                          │ │
│ │  Why not: Loss streak / gate / 9:45 observe                          │ │
│ │  [Open Execute checklist]  [Options coach]                           │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
│ ┌─ EXECUTION CARD (★) ─────────────────────────────────────────────────┐ │
│ │  RELIANCE · LONG · E ₹2,450 · SL ₹2,420 · T ₹2,510 · 2.0R           │ │
│ │  OR: pending · Ladder: —                                              │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
│ ┌─ OPPORTUNITIES (ranked) ────────┐ ┌─ CONTEXT (3-up) ────────────────┐ │
│ │ 1. RELIANCE  72%  2.1R  ★       │ │ Regime · Risk · Global bias     │ │
│ │ 2. TCS       65%  1.8R          │ │ [Expand macro/session]          │ │
│ │ 3. INFY      61%  1.6R          │ └─────────────────────────────────┘ │
│ └─────────────────────────────────┘ ┌─ RISKS (chips) ───────────────────┐ │
│                                     │ 9:45 gate · IV high · narrow    │ │
│                                     └─────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Home — Execute

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  Dashboard   [Execute]   Prep                                            │
├──────────────────────────────────────────────────────────────────────────┤
│ SESSION TIMING BANNER — observe until 9:45                               │
│ MIS CHECKLIST — ☐ Kite live ☐ Star set ☐ Stop defined ☐ Size within dam │
│ ┌─ LIVE PICKS ────────────────────────────────────────────────────────┐ │
│ │ Intraday watchlist (from pins + pulse)                                 │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
│ ┌─ OPTIONS GATE ───────────────────────────────────────────────────────┐ │
│ │ MIS advisory · synthesis pillars · entry gate                        │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
│ [Live charts]  [Options coach]  [Log trade → Journal]                    │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Home — Prep

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  Dashboard   Execute   [Prep]                                            │
├──────────────────────────────────────────────────────────────────────────┤
│ PREP STATUS — equity scan ✓ · options snap ✓ · 9:46 rescan ⏳            │
│ [Prep all]  [Quick scan]  [Re-scan after OR]                             │
│ ┌─ EQUITY TOP 5 ──────────────┐ ┌─ OPTIONS ★ ─────────────────────────┐ │
│ │ rank · symbol · E/S/T · star  │ │ Nifty/BankNifty CE/PE · star        │ │
│ └───────────────────────────────┘ └─────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Portfolio — Overview (second most important page)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ PORTFOLIO HEALTH   78/100   ████████░░   Kite live · synced 2m ago       │
├──────────────────────────────────────────────────────────────────────────┤
│  [Overview]   Holdings   Positions   Wealth   Briefing                   │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌─ P&L ─────────────┬─ CASH ──────────┬─ EXPOSURE ─────┬─ RISK BUDGET ─┐ │
│ │ Today  +₹1,240    │ Available ₹42k  │ Invested 68%   │ Used 35% of dam│ │
│ │ Realized (broker) │ (Kite margins)  │ Delivery+MIS   │ Max loss ₹900  │ │
│ │ Unrealized +₹8.2k │                 │                │                │ │
│ └───────────────────┴─────────────────┴────────────────┴────────────────┘ │
│ ┌─ ALLOCATION ─────────────────────┐ ┌─ SECTOR EXPOSURE ────────────────┐ │
│ │ [donut] Top 5 weights            │ │ IT 28% · Bank 22% · Energy 15%  │ │
│ │ RELIANCE 18% · TCS 14% · …       │ │ ⚠ Top-5 concentration 62%        │ │
│ └──────────────────────────────────┘ └──────────────────────────────────┘ │
│ ┌─ AI PORTFOLIO SUMMARY ────────────────────────────────────────────────┐ │
│ │ "3 holds · 1 reduce candidate · sector IT overweight vs Nifty"        │ │
│ │ Priority: Review INFY — REDUCE per daily advisor                      │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
│ [Sync Kite]  [Open Briefing]  [Research INFY]                            │
└──────────────────────────────────────────────────────────────────────────┘
```

**Portfolio health score (display-only composite, no new engine):**

| Input (existing) | Weight |
|------------------|--------|
| `portfolio_risk` top-5 concentration & warnings | 30% |
| Kite sync freshness + data health | 20% |
| Count of REDUCE/SELL in `daily_briefing` | 25% |
| Diversification (holdings count band) | 15% |
| Broker truth reconciliation matched % | 10% |

### 4.5 Portfolio — Holdings

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  Overview   [Holdings]   Positions   Wealth   Briefing                   │
├──────────────────────────────────────────────────────────────────────────┤
│ Symbol   Qty   Avg    LTP     U-P&L   Wt%   Action   AI Rec    ▸ Detail │
│ RELIANCE 10  2450  2510   +₹600   18%   HOLD    Accumulate  [Research]  │
│ TCS       5  3800  3750   -₹250   14%   REDUCE  Trim on bounce        │
│ INFY      8   420   415    -₹40   11%   HOLD    Hold — range bound     │
├──────────────────────────────────────────────────────────────────────────┤
│ ▸ Detail drawer: Alpha snippet · earnings · delivery quality · DE verdict│
│ Import: [Sync Kite] [CSV] [Manual row]                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

**Action badge mapping (existing `today_action` / DE legacy):**

| Display | Source labels |
|---------|---------------|
| **Hold** | HOLD, WAIT, ACCUMULATE |
| **Add** | BUY, STRONG BUY |
| **Reduce** | REDUCE |
| **Exit** | SELL, STRONG SELL, AVOID |

### 4.6 Portfolio — Positions

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  Overview   Holdings   [Positions]   Wealth   Briefing                   │
├──────────────────────────────────────────────────────────────────────────┤
│ MIS / intraday open positions from Kite (not delivery holdings)          │
│ Symbol   Product   Qty   Avg    LTP    P&L    Age    [Close plan]         │
│ NIFTY…   MIS      50    12.4  11.8   -₹300  2h     → Journal log        │
│ CNC same-day buys merged with note                                       │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.7 Portfolio — Wealth & Briefing

```text
Wealth: SIP goals, ₹10 Cr framing, goal progress charts (from sip_goals page)
Briefing: Daily advisor narrative, priority actions, market verdict for holders
```

### 4.8 Research — Workbench (default)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  [Workbench]   Market   Discover   Options   Compare                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Symbol [RELIANCE ▼]  [Run Alpha AI]  [Technical]  [Fundamental]          │
│ ┌─ ALPHA AI EXEC SUMMARY (sticky) ─────────────────────────────────────┐ │
│ │ Score 72 · Hold · confidence 65%                                     │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
│ ┌─ CHART + SIGNALS ───────────────────────────────────────────────────┐ │
│ │ (single stock + live charts embed)                                   │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
│ [Add to Home prep]  [Portfolio impact]                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.9 Research — Market / Discover / Options

```text
Market:   Pulse report · Global heatmap · Macro · Regime (from snapshot)
Discover: Screener filters · Batch scanner · Penny picks · Export CSV
Options:  NSE chain · Live options advisor · IV rank · Expiry watchlist
Compare:  2–4 symbol table (existing compare page)
```

### 4.10 Journal

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  [Today]   Track Record   Learning   Backtest                            │
├──────────────────────────────────────────────────────────────────────────┤
│ Today: trade journal form · day P&L summary · broker sync status         │
│ Track Record: hit rate dashboards · options outcomes · exports             │
│ Learning: calibration buckets · validate EOD · threshold tuning          │
│ Backtest: historical replay (existing page)                              │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.11 Settings

```text
┌──────────────────────────────────────────────────────────────────────────┐
│  [Setup]   Trading   Connect   System   Learn                            │
├──────────────────────────────────────────────────────────────────────────┤
│ Setup: wizard steps · onboarding tour                                    │
│ Trading: capital · risk % · daily goal · beginner mode · risk & goals      │
│ Connect: Kite OAuth · Telegram · autopilot jobs & logs                   │
│ System: theme · compact nav · data health · cloud/local banner           │
│ Learn: Varsity TA chapters · daily cheat sheet                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Migration Plan

### 5.1 Principles

1. **UI routing only** — `app.py` tab router becomes five-page router; page modules stay, get composed.  
2. **Strangler inside Streamlit** — old tab names call new page + sub-tab via `request_nav_tab("Portfolio", sub="Holdings")`.  
3. **No backend moves** — imports stay `analyzer.*`; only `ui/` and `app.py` routing change.  
4. **Portfolio promoted** — Kite hydrate runs on Home **and** Portfolio load (remove Home-only fast path skip).  
5. **Feature freeze during migration** — IA work only; no new scanners or indicators.

### 5.2 Phases

#### Phase 0 — Foundation (3–5 days)

| Task | Output |
|------|--------|
| Define `PRIMARY_PAGES` + `SUB_TABS` in `ui/theme.py` | Five-page constants |
| Replace `NAV_GROUPS` radio with single five-item nav | `navigation_bar.py` |
| Add `sub_tab` session key + redirect aliases | `ui/navigation.py` |
| Unify app shell — remove Home early-return | `app.py` |
| Global header: clock, Kite, data health | New `ui/components/os_chrome.py` |

**Exit criteria:** User can reach five pages; legacy names redirect.

#### Phase 1 — Home consolidation (4–6 days)

| Task | Maps |
|------|------|
| Merge `Suggestions` / `intraday` hero into Home › Execute | Execute sub-tab |
| Move `unified_prep` into Home › Prep | Prep sub-tab |
| Apply P0 backlog from doc 19 (verdict, ribbon, execution card) | Dashboard |
| Deprecate standalone Suggestions tab (redirect) | IA |

**Exit criteria:** Morning workflow completable without leaving Home.

#### Phase 2 — Portfolio elevation (5–8 days) ★ Priority

| Task | Maps |
|------|------|
| New `ui/pages/portfolio_os.py` shell with 5 sub-tabs | Portfolio page |
| Overview: margins cash, P&L split, allocation, sector, health score | `fetch_kite_margins`, `portfolio_risk` |
| Holdings: merge `zerodha.py` + `daily_advisor` action column | Holdings sub-tab |
| Positions: surface Kite `positions()` net bucket | Positions sub-tab |
| Briefing: embed `daily_advisor` | Briefing sub-tab |
| Wealth: embed `sip_goals` | Wealth sub-tab |
| Redirect `My Portfolio`, `Daily Advisor`, `SIP & Goals` | Aliases |

**Exit criteria:** Investor answers “what do I own and what should I do?” on Portfolio alone.

#### Phase 3 — Research consolidation (4–6 days)

| Task | Maps |
|------|------|
| Workbench hosts Single Stock + Alpha AI toggle | Research |
| Market sub-tab: Pulse + Global | Research |
| Discover: Screener + Batch + Penny | Research |
| Options: NSE + Live Options Coach | Research |
| Compare sub-tab | Research |
| Remove 9 standalone research tabs (redirects) | IA |

**Exit criteria:** Symbol deep-dive never requires leaving Research.

#### Phase 4 — Journal + Settings (3–5 days)

| Task | Maps |
|------|------|
| Journal shell: Today, Track Record, Learning, Backtest | Journal |
| Move learning off Home dashboard (after close) | Home + Journal |
| Settings shell: absorb sidebar expanders | Settings |
| Varsity → Settings › Learn | IA |

**Exit criteria:** Sidebar reduced to market/period only (or moved to Settings).

#### Phase 5 — Polish & cutover (2–4 days)

| Task | Output |
|------|--------|
| Update onboarding tour for five pages | `onboarding_tour` |
| Command palette routes to new IA | `command_palette` |
| Remove dead nav constants | cleanup |
| Update README / in-app copy | “Investment OS” |
| Delete redirects after 30-day deprecation window | optional |

### 5.3 Risk register

| Risk | Mitigation |
|------|------------|
| Streamlit rerun perf with Portfolio live fragment | Keep 15s fragment; load Overview first |
| Kite positions API not in holdings UI today | Positions sub-tab read-only v1 |
| Health score feels arbitrary | Show breakdown tooltip with 5 inputs |
| User bookmark breakage | 90-day redirect map in `navigation.py` |
| Home load slower after unified shell | Keep `load_dashboard_data` cache |

### 5.4 Success metrics

| Metric | Target (30 days post cutover) |
|--------|-------------------------------|
| Morning session: tabs visited before first trade | ≤ 2 (Home + optional Portfolio) |
| Portfolio page DAU / Home DAU | ≥ 0.7 |
| Standalone legacy tab hits via redirect | ↓ 80% |
| Time to “holding action” on Portfolio | < 15 seconds |
| Investor-reported nav confusion | Near zero in feedback |

### 5.5 Team sequencing recommendation

```text
Week 1   Phase 0 + Phase 2 start (Portfolio shell — highest CPO priority)
Week 2   Phase 2 complete + Phase 1 (Home)
Week 3   Phase 3 (Research)
Week 4   Phase 4–5 (Journal, Settings, polish)
```

**Rationale:** Portfolio is the **wealth anchor** for a serious Indian investor; Home alone cannot carry delivery book + tactical book. Building Portfolio second (in parallel with nav foundation) validates the OS story for the full day, not just the open.

---

## 6. CPO Decision Record

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Page count | **5** | Matches investor day parts; fits mobile bottom nav |
| Second page | **Portfolio** | Delivery wealth + Kite truth; distinct from tactical Home |
| Suggestions tab | **Absorbed into Home** | Same user, same morning; stops duplicate |
| Daily Advisor | **Portfolio › Briefing** | Per-holding actions belong with holdings |
| Alpha AI | **Research mode, not page** | Research is verb; Alpha is depth |
| Track Record | **Journal** | Learning is not morning work |
| Sidebar | **Demoted to Settings** | Infrastructure ≠ daily navigation |
| Health score | **Composite display** | No new engine; honest breakdown |
| Backend | **Frozen** | IA proves OS without more architecture |

---

## 7. What This Document Does Not Do

- Does not add features, indicators, or engines  
- Does not change API contracts for Context / Evidence / Decision / Broker Truth  
- Does not prescribe React rewrite — Streamlit remains the shell  
- Does not implement code — engineering picks up Phase 0–5 in `ui/` and `app.py` only  

---

*End of product redesign. No application or backend code modified.*
