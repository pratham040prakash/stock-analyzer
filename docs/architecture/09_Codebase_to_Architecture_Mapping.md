# 09 — Codebase to Architecture Mapping

**Role:** Chief Software Architect  
**Constitution:** [08_Final_Investment_OS_Architecture.md](./08_Final_Investment_OS_Architecture.md) — **not redesigned**  
**Method:** Trace every existing module to a Constitutional engine or supporting role  
**Scope:** `analyzer/` (163 files), `ui/` (66 files), `scripts/` (19 files), root entrypoints, sibling projects  
**Date:** 2026-07-15

---

## Executive summary

| Metric | Count |
|--------|------:|
| Modules mapped | **251** |
| Context Engine | 18 |
| Hunt Engine | 42 |
| Judgment Engine | 38 |
| Capital Engine | 22 |
| Evolution Engine | 28 |
| Supporting Module | 89 |
| **Pipeline orchestrator** (spans engines) | 4 |
| **Does not belong** (orphan / out of scope) | 10 |

### Constitutional alignment scorecard

| Constitutional requirement | Codebase status |
|---------------------------|-----------------|
| Five engines separable in logic | **Partial** — logic exists but scattered across 163 files |
| Default WAIT / veto pipeline | **Partial** — `mis_trade_advisory`, `strategy_synthesis`, `investment_os` overlap |
| Broker truth > coach truth | **Missing** — learning uses `watchlist_eod` target/stop hits, not Zerodha P&L |
| Evidence packet (FACT/ESTIMATE/OPINION/GAP) | **Missing** — scores and prose, no labeled evidence model |
| Uncertainty vector | **Missing** — single confidence numbers only |
| Munger invert pass | **Missing** — red flags exist; no mandatory adversarial gate |
| Decision artifact per verdict | **Partial** — `StrategySynthesis`, `MisTradeAdvisory` fragments |
| Sacred core vs tactical pool | **Partial** — SIP separate; MIS pool lacks automatic dam veto |
| n ≥ 30 learning governance | **Missing** — tuners run on small samples |
| AI explains, engines decide | **Violated risk** — `alpha_ai_llm`, coaches can sound like oracles |

---

## Mapping legend

### Target engine / role

| Label | Constitutional role |
|-------|---------------------|
| **CTX** | Context Engine — regime, session, macro, tactical pool open/closed |
| **HUNT** | Hunt Engine — scan, stalk list, triggers, Lynch categories |
| **JUDGE** | Judgment Engine — evidence, invert, uncertainty, confidence |
| **CAP** | Capital Engine — pools, size, dams, concentration, veto → zero |
| **EVOLVE** | Evolution Engine — broker truth, post-mortem, calibration, adapt |
| **SUP-MM** | Supporting: Market memory |
| **SUP-BM** | Supporting: Broker mirror |
| **SUP-CAL** | Supporting: Calendar |
| **SUP-CR** | Supporting: Competence registry |
| **SUP-WL** | Supporting: Wealth ledger |
| **SUP-NG** | Supporting: Narrative guard |
| **SUP-AL** | Supporting: Alert channel |
| **SUP-AT** | Supporting: Audit trail |
| **SUP-UI** | Supporting: Presentation shell (no decision authority) |
| **PIPE** | Pipeline orchestrator — coordinates engines; must stay thin |
| **ORPHAN** | Does not belong in Investment OS |

### Disposition

| Action | Meaning |
|--------|---------|
| **Keep** | Maps cleanly; retain with possible rename |
| **Merge** | Duplicate responsibility; fold into canonical owner |
| **Split** | Multiple Constitutional roles in one file |
| **Remove** | Orphan, dead, or harmful to decision quality |

### Migration priority

| Priority | Meaning |
|----------|---------|
| **P0** | Blocks Constitutional trust (broker truth, dams, pipeline) |
| **P1** | High duplication or wrong learning source |
| **P2** | Engine consolidation |
| **P3** | UI / delivery cleanup |
| **P4** | Deprecate or out-of-scope |

---

## Traceability matrix — `analyzer/` (core logic)

### A. Pipeline orchestrators

| Existing Module | Current Responsibility | Target | Action | Reason | Priority |
|-----------------|------------------------|--------|--------|--------|----------|
| `investment_os.py` | 7-module daily pipeline; regime, sector, stock, strategy, risk, execution, review | **PIPE** (CTX→HUNT→JUDGE→CAP) | **Keep** | Closest to Constitutional pipeline; should become thin coordinator only | P0 |
| `mis_trade_advisory.py` | MIS ACT/WAIT/NO_TRADE synthesis from 14 deps | **PIPE** + JUDGE | **Merge** → `investment_os` | Duplicate verdict authority with OS and synthesis | P1 |
| `daily_playbook.py` | Step-by-step beginner day guide | **PIPE** | **Merge** → `investment_os` | Third daily driver; same user journey | P2 |
| `nightly_prep.py` | Equity + options prep, Telegram, persist pins | **PIPE** + HUNT | **Keep** | Pre-session stalk list builder; not a verdict issuer | P1 |

---

### B. Context Engine (CTX)

| Existing Module | Current Responsibility | Target | Action | Reason | Priority |
|-----------------|------------------------|--------|--------|--------|----------|
| `market_regime.py` | Nifty ADX trend vs range | **CTX** | **Keep** | Core regime label | P0 |
| `india_macro.py` | VIX, sector indices, FII/DII | **CTX** | **Keep** | Macro context input | P1 |
| `global_impact.py` | Global indices → India action hints | **CTX** | **Keep** | Druckenmiller macro layer | P2 |
| `global_markets.py` | US/EU/Asia quotes | **CTX** | **Keep** | Macro input | P3 |
| `gift_nifty.py` | Pre-open gap cue | **CTX** | **Keep** | Session open context | P1 |
| `market_session.py` | Open/closed, phase, date | **CTX** | **Keep** | Session gate | P0 |
| `session_phase.py` | Pre/open/close buckets | **CTX** | **Merge** → `market_session` | Split responsibility with session | P3 |
| `session_advisory.py` | Phase-based market advice text | **CTX** | **Merge** → `investment_os` CTX module | Advisory prose belongs in decision artifact | P2 |
| `market_risk.py` | Goal-based risk scoring | **CTX** + CAP | **Split** | Mixes regime assessment and sizing hints | P1 |
| `intraday_beginner_tips.py` | Timing, capital budget tips | **CTX** | **Merge** → CTX + CAP prefs | Overlaps `small_trader_intraday` | P2 |
| `small_trader_intraday.py` | Affordable MIS guidance | **CTX** + CAP | **Merge** → `intraday_beginner_tips` | Duplicate small-capital rules | P2 |
| `prep_status.py` | Nightly prep milestone tracking | **CTX** | **Keep** | "Is prep done?" context flag | P3 |
| `intraday_prefs.py` | Capital, risk %, beginner/equity modes | **CTX** + CAP | **Split** | Prefs span context dams and allocation | P0 |
| `market_pulse.py` | Pulse dataclasses only | **CTX** + HUNT | **Merge** → `market_pulse_scan` | Types only; no engine boundary | P4 |
| `macro_cache.py` | Macro snapshot cache | **SUP-MM** | **Merge** → `pulse_cache` | Cache, not context logic | P4 |
| `onboarding_state.py` | First-run state | **SUP-CR** | **Keep** | User competence onboarding stub | P3 |
| `app_mode.py` | Cloud/simple mode flag | **SUP-UI** | **Keep** | Deployment flag | P4 |
| `setup_status.py` | Env/config completeness | **SUP-AT** | **Keep** | Operational health, not regime | P3 |

---

### C. Hunt Engine (HUNT)

| Existing Module | Current Responsibility | Target | Action | Reason | Priority |
|-----------------|------------------------|--------|--------|--------|----------|
| `market_pulse_scan.py` | Universe multi-horizon scan (22 deps) | **HUNT** | **Split** | Scan vs enrich; god module | P1 |
| `intraday_pulse_source.py` | Cached quick scan accessor | **HUNT** | **Keep** | Stalk list feed | P2 |
| `pulse_cache.py` | Pulse report serialization | **SUP-MM** | **Keep** | Market memory cache | P2 |
| `intraday_watchlist.py` | Top-N picks, checklist, plans | **HUNT** + CAP | **Split** | Scoring (Hunt) vs plan build (Execution contract) | P1 |
| `intraday_stock_picker.py` | Pulse-based pick selection | **HUNT** | **Merge** → `intraday_watchlist` | Duplicate pick logic | P2 |
| `watchlist_pins.py` | Top-N JSON persistence (stalk list) | **HUNT** | **Keep** | Lynch stalk list store | P0 |
| `watchlist_persist.py` | Fingerprinted save on change | **HUNT** | **Keep** | Stalk persistence orchestrator | P2 |
| `trade_selection.py` | User star picks (1–2 symbols) | **HUNT** | **Keep** | Session focus / trigger selection | P1 |
| `screener.py` | Parallel universe screener | **HUNT** | **Keep** | Discovery scan | P3 |
| `penny_stocks.py` | Low-price stock filter | **HUNT** | **Keep** | Universe filter (competence boundary) | P3 |
| `unified_search.py` | Symbol/tab command search | **HUNT** | **Keep** | Discovery navigation | P3 |
| `opening_range_confirm.py` | OR breakout gate | **HUNT** | **Keep** | Trigger watch (Simons class) | P1 |
| `options_expiry_watchlist.py` | Index CE/PE stalk list | **HUNT** | **Keep** | Options stalk (separate track) | P2 |
| `options_trade_selection.py` | Auto option leg persistence | **HUNT** | **Keep** | Star pick for options | P2 |
| `affordable_invest.py` | Lot affordability filter | **HUNT** + CAP | **Split** | Filter (Hunt) vs budget cap (Capital) | P2 |
| `options_flow_snapshot.py` | OI change capture | **HUNT** | **Keep** | Pattern/anomaly input | P2 |
| `options_reversal_alerts.py` | PE/CE reversal cues | **HUNT** | **Keep** | Trigger class | P3 |
| `relative_strength.py` | RS vs benchmark | **HUNT** | **Keep** | Ranking signal | P2 |
| `intraday_signals.py` | MIS-specific signal rules | **HUNT** | **Merge** → pattern classes | Raw signals, not verdicts | P2 |
| `signals.py` | Buy/sell from indicators | **HUNT** | **Merge** → pattern classes | Duplicate signal layer | P2 |
| `kite_watchlist_store.py` | Import Kite watchlist | **HUNT** | **Keep** | External stalk import | P3 |
| `watchlist.py` | Legacy combined-analysis list | **HUNT** | **Remove** | Superseded by pulse + pins | P4 |
| `morning_options_rescan.py` | Re-scan after open | **HUNT** | **Keep** | Trigger refresh job | P3 |
| `post_close_scan_scheduler.py` | Post-close quick scan | **HUNT** + EVOLVE | **Split** | Scan (Hunt) vs learning trigger (Evolve) | P2 |
| `nse_option_history.py` | Historical option series | **SUP-MM** | **Keep** | Hunt backtest input | P3 |
| `live_trade_signals.py` (script) | Signal watcher | **HUNT** | **Merge** → coach/Hunt triggers | Side-channel discovery | P3 |

---

### D. Judgment Engine (JUDGE)

| Existing Module | Current Responsibility | Target | Action | Reason | Priority |
|-----------------|------------------------|--------|--------|--------|----------|
| `strategy_synthesis.py` | Pillar voting → verdict | **JUDGE** | **Keep** | Core thesis + confidence fusion | P0 |
| `combined.py` | Fundamentals + technical merge | **JUDGE** | **Keep** | Evidence lens assembly | P2 |
| `multi_timeframe.py` | Multi-interval alignment | **JUDGE** | **Keep** | Technical evidence lens | P1 |
| `fundamentals.py` | ROE, PE, scoring | **JUDGE** | **Keep** | Business/balance lens | P2 |
| `dcf_model.py` | DCF fair value | **JUDGE** | **Keep** | Valuation lens | P3 |
| `peer_comparison.py` | Sector peer multiples | **JUDGE** | **Keep** | Valuation lens | P3 |
| `alpha_red_flags.py` | Risk flag detection | **JUDGE** | **Keep** | Partial Munger invert | P1 |
| `delivery_quality.py` | NSE delivery % scoring | **JUDGE** | **Keep** | Sentiment/quality lens | P3 |
| `news_feed.py` | Headlines fetch | **JUDGE** | **Keep** | Sentiment lens (needs rumor label) | P3 |
| `candle_narrative.py` | Intraday action summary | **JUDGE** | **Split** | Narrative vs evidence; couples to options | P2 |
| `candlesticks.py` | Pattern detection | **HUNT** + JUDGE | **Split** | Pattern detect (Hunt) vs interpretation (Judge) | P3 |
| `options_analytics.py` | IV, OI, PCR | **JUDGE** | **Keep** | Options evidence lens | P2 |
| `options_signal.py` | Daily CE/PE suggestion | **JUDGE** | **Merge** → `strategy_synthesis` | Duplicate verdict path | P1 |
| `options_entry_gate.py` | OR + timing gate | **JUDGE** + HUNT | **Split** | Trigger (Hunt) vs pass/fail thesis gate (Judge) | P1 |
| `sideways_options_advisor.py` | Range/consolidation plays | **JUDGE** | **Split** → strategy plugins | 626 LOC monolith | P2 |
| `live_options_coach.py` | Real-time CE/PE coach | **JUDGE** + PIPE | **Split** | Coach issues guidance; must not be sole verdict | P0 |
| `advisor.py` | Long-term buy/hold | **JUDGE** | **Keep** | Growth-engine thesis | P3 |
| `daily_advisor.py` | Holdings + swing briefing | **JUDGE** + CTX | **Merge** → `investment_os` | Fourth daily advisor | P2 |
| `alpha_ai_report.py` | 15-section institutional report | **JUDGE** | **Split** | Report orchestrator; section builders | P2 |
| `alpha_ai_llm.py` | OpenAI narrative | **JUDGE** + SUP-NG | **Keep** | AI prose layer only | P1 |
| `alpha_ai_prompts.py` | Section prompts | **SUP-NG** | **Keep** | Prompt templates | P3 |
| `alpha_monte_carlo.py` | Scenario simulation | **JUDGE** | **Keep** | Uncertainty/scenario lens | P3 |
| `alpha_portfolio_mode.py` | Holdings-aware report | **JUDGE** | **Keep** | Portfolio lens | P3 |
| `compare.py` | Side-by-side analysis | **JUDGE** | **Keep** | Comparative evidence | P3 |
| `etf_analyzer.py` | ETF metrics | **JUDGE** | **Keep** | Asset-class evidence | P3 |
| `chart_horizon.py` | Short/long chart scoring | **JUDGE** | **Keep** | Technical lens | P3 |
| `indicators.py` | Indicator wrapper | **SUP-MM** | **Keep** | Derived metrics feed | P4 |
| `ta.py` | RSI, MACD helpers | **SUP-MM** | **Keep** | Derived metrics feed | P4 |
| `varsity_knowledge.py` | TA education KB | **SUP-CR** | **Keep** | Competence education; not verdict | P3 |
| `confidence_calibration.py` | Adjust confidence from outcomes | **EVOLVE** + JUDGE | **Split** | Calibration is Evolution output feeding Judge | P0 |
| `suggestion_validator.py` | Score vs market move | **EVOLVE** | **Merge** → Evolution | Outcome validation, not pre-trade judge | P1 |
| `mis_printable_checklist.py` | Printable MIS checklist | **JUDGE** | **Keep** | Execution contract artifact | P3 |

---

### E. Capital Engine (CAP)

| Existing Module | Current Responsibility | Target | Action | Reason | Priority |
|-----------------|------------------------|--------|--------|--------|----------|
| `intraday_trade_plan.py` | Entry/stop/target, R:R, position size | **CAP** + Execution contract | **Keep** | Core sizing + plan | P0 |
| `trade_ladder.py` | T1/T2/T3 partial exits | **CAP** | **Keep** | Target ladder (Druckenmiller) | P1 |
| `profit_targets.py` | Aggressive/conservative targets | **CAP** | **Keep** | Target policy | P2 |
| `watchlist_position_size.py` | Share qty from risk | **CAP** | **Merge** → `intraday_trade_plan` | Duplicate sizing | P2 |
| `watchlist_profit.py` | Target profit calc | **CAP** | **Merge** → `profit_targets` | Duplicate | P3 |
| `watchlist_sector.py` | Sector concentration warn | **CAP** | **Keep** | Concentration veto | P1 |
| `portfolio_risk.py` | Holdings concentration | **CAP** | **Keep** | Portfolio exposure check | P2 |
| `portfolio.py` | Holdings dataclasses | **SUP-WL** | **Keep** | Types for wealth/tactical | P3 |
| `portfolio_store.py` | JSON portfolio persistence | **SUP-WL** | **Keep** | Wealth ledger | P3 |
| `portfolio_live.py` | Kite sync, LTP refresh | **SUP-BM** + SUP-WL | **Keep** | Positions mirror | P0 |
| `risk.py` | Thin risk utilities | **CAP** | **Merge** → `market_risk` | Stray duplicate | P4 |
| `sip_planner.py` | SIP allocation math | **CAP** | **Keep** | Growth engine (sacred track) | P1 |
| `sip_storage.py` | goals.json persistence | **SUP-WL** | **Keep** | Wealth ledger | P2 |
| `wealth_plan.py` | ₹10 Cr compound projection | **CAP** | **Keep** | Unwired; growth engine vision | P2 |
| `sip_export.py` | Export SIP plan | **SUP-WL** | **Keep** | Export only | P4 |
| `sip_reminders.py` | SIP Telegram reminders | **SUP-AL** | **Keep** | Alert, not allocation | P4 |
| `mis_checklist_store.py` | Checklist JSON store | **SUP-AT** | **Keep** | Plan persistence | P3 |
| `watchlist_plan_tracker.py` | Intraday plan state | **CAP** | **Keep** | In-trade monitoring | P2 |

---

### F. Evolution Engine (EVOLVE)

| Existing Module | Current Responsibility | Target | Action | Reason | Priority |
|-----------------|------------------------|--------|--------|--------|----------|
| `eod_learning.py` | validate → learn → tune orchestrator | **EVOLVE** | **Keep** | Canonical learning loop driver | P0 |
| `watchlist_learning.py` | Equity gate tuning from outcomes | **EVOLVE** | **Keep** | Adapt gates | P0 |
| `options_watchlist_learning.py` | Options premium tune | **EVOLVE** | **Merge** → learning facade | Parallel tuner | P1 |
| `suggestion_learning.py` | Win rate slices, insights | **EVOLVE** | **Merge** → learning facade | Parallel stats | P1 |
| `threshold_tuning.py` | Auto-tune pulse score gates | **EVOLVE** | **Keep** | Adapt gates (needs n≥30 guard) | P1 |
| `strategy_research.py` | Offline 6mo backtest → weights | **EVOLVE** | **Keep** | Simons decay research | P2 |
| `watchlist_eod.py` | Target/stop hit detection | **EVOLVE** | **Split** | Coach truth only — not broker truth | P0 |
| `watchlist_history.py` | SQLite snapshots + EOD join | **EVOLVE** + SUP-AT | **Split** | Persistence vs outcome scoring | P1 |
| `options_watchlist_history.py` | Options snapshot DB | **EVOLVE** + SUP-AT | **Split** | Mirror equity pattern | P2 |
| `symbol_track_record.py` | Per-symbol stats | **EVOLVE** | **Keep** | Stratified calibration | P2 |
| `suggestion_journal.py` | SQLite suggestion log | **SUP-AT** + EVOLVE | **Keep** | Audit trail; learning input | P0 |
| `trade_journal.py` | JSON mistake/fix log | **EVOLVE** | **Merge** → journal facade | Third journal | P1 |
| `intraday_journal.py` | Manual trade log at entry | **EVOLVE** | **Merge** → journal facade | Third journal | P1 |
| `trade_journal_link.py` | Cross-reference helper | **EVOLVE** | **Remove** | After journal merge | P4 |
| `suggestion_features.py` | Pick feature vectors | **EVOLVE** | **Keep** | Attribution / calibration input | P2 |
| `mis_eod_summary.py` | EOD Telegram summary | **EVOLVE** + SUP-AL | **Split** | Summary vs learning | P2 |
| `backtest.py` | Walk-forward strategy sim | **EVOLVE** + HUNT | **Keep** | Research; not live learning | P3 |
| `options_backtest.py` | Historical options sim | **EVOLVE** + HUNT | **Keep** | Research | P3 |

---

### G. Supporting — Market memory (SUP-MM)

| Existing Module | Current Responsibility | Target | Action | Reason | Priority |
|-----------------|------------------------|--------|--------|--------|----------|
| `data.py` | Equity OHLCV fetch | **SUP-MM** | **Keep** | Price memory | P1 |
| `intraday_data.py` | Intraday bars via router | **SUP-MM** | **Keep** | Intraday memory | P1 |
| `providers/router.py` | Kite-first LTP/bars | **SUP-MM** | **Keep** | Canonical data router | P0 |
| `providers/kite.py` | Kite historical candles | **SUP-MM** | **Keep** | Provider adapter | P2 |
| `providers/yahoo.py` | yfinance wrapper | **SUP-MM** | **Keep** | Fallback provider | P2 |
| `providers/types.py` | Shared dataclasses | **SUP-MM** | **Keep** | Types | P4 |
| `providers/__init__.py` | Public exports | **SUP-MM** | **Keep** | Package surface | P4 |
| `nse_data.py` | NSE symbol metadata | **SUP-MM** | **Keep** | India enrichment | P2 |
| `nse_session.py` | NSE HTTP session | **SUP-MM** | **Keep** | Fetch transport | P2 |
| `nse_options.py` | NSE options chain scrape | **SUP-MM** | **Split** | Fetch vs normalize | P2 |
| `kite_options_chain.py` | Kite NFO chain | **SUP-MM** | **Keep** | Preferred chain source | P1 |
| `cache_utils.py` | Disk TTL cache | **SUP-MM** | **Keep** | Cache layer | P3 |
| `data_health.py` | Provider health summary | **SUP-MM** | **Keep** | GAP surfacing for evidence | P0 |
| `markets.py` | Market registry | **SUP-MM** | **Keep** | Exchange metadata | P4 |
| `india.py` | India ticker help | **SUP-CR** | **Keep** | Competence help text | P4 |
| `india_enrichment.py` | India-specific enrich | **SUP-MM** | **Merge** → `nse_data` / `india` | Thin duplicate | P4 |
| `asset_class.py` | Equity/index/ETF detection | **SUP-MM** | **Keep** | Classification | P3 |
| `intraday_chart.py` | Chart data prep | **SUP-MM** | **Keep** | Visualization feed | P4 |
| `live_charts_grid.py` | Multi-chart batch fetch | **SUP-MM** | **Keep** | Visualization feed | P4 |
| `options_premium_chart.py` | CE/PE premium history | **SUP-MM** | **Keep** | Chart feed | P4 |

---

### H. Supporting — Broker mirror (SUP-BM)

| Existing Module | Current Responsibility | Target | Action | Reason | Priority |
|-----------------|------------------------|--------|--------|--------|----------|
| `zerodha.py` | OAuth, holdings, LTP, margins | **SUP-BM** | **Split** | Auth / portfolio / marketdata — **missing TradeRecord** | P0 |
| `kite_status.py` | Connect status probe | **SUP-BM** | **Keep** | Broker health | P1 |
| `kite_stream.py` | WebSocket LTP cache | **SUP-BM** | **Keep** | Live quotes | P2 |
| `kite_health.py` | Token/instrument diagnostic | **SUP-BM** | **Keep** | Dev diagnostic | P4 |

**Constitutional gap:** No module produces canonical **broker-verified P&L** for Evolution. `portfolio_live` shows positions; learning does not consume fills.

---

### I. Supporting — Calendar (SUP-CAL)

| Existing Module | Current Responsibility | Target | Action | Reason | Priority |
|-----------------|------------------------|--------|--------|--------|----------|
| `nse_holidays.py` | Trading day checks | **SUP-CAL** | **Keep** | Session calendar | P2 |
| `earnings_calendar.py` | Upcoming results | **SUP-CAL** | **Keep** | Event uncertainty window | P1 |
| `session_reminders.py` | Phase Telegram nudges | **SUP-CAL** + SUP-AL | **Keep** | Time-based human nudge | P3 |

---

### J. Supporting — Alert, audit, export, infra

| Existing Module | Current Responsibility | Target | Action | Reason | Priority |
|-----------------|------------------------|--------|--------|--------|----------|
| `telegram_notify.py` | Telegram broadcast | **SUP-AL** | **Keep** | Delivery only | P2 |
| `telegram_subscriptions.py` | Subscriber CRUD | **SUP-AL** | **Split** | Store vs delivery | P3 |
| `suggestions_telegram.py` | Nightly/morning TG format | **SUP-AL** | **Merge** → formatters | Duplicate formatters | P3 |
| `watchlist_telegram.py` | Watchlist TG format | **SUP-AL** | **Merge** → formatters | Duplicate | P3 |
| `prep_morning_nag.py` | TG if no prep | **SUP-AL** | **Keep** | Nudge | P3 |
| `structured_log.py` | JSON log lines | **SUP-AT** | **Keep** | Audit trail | P2 |
| `suggestions_export.py` | CSV/JSON export | **SUP-AT** | **Keep** | Export | P4 |
| `whatsapp_export.py` | WhatsApp formatting | **SUP-AL** | **Remove** | Marginal; duplicate channel | P4 |
| `alpha_ai_export.py` | PDF export | **SUP-AT** | **Keep** | Report export | P4 |
| `env_loader.py` | .env load/save | **SUP-UI** | **Split** | Secrets vs config (security) | P1 |
| `ui_preferences.py` | Theme, compact nav | **SUP-UI** | **Keep** | Presentation prefs | P4 |
| `morning_briefing.py` | CLI morning wrap | **SUP-AL** + PIPE | **Merge** → script facade | Duplicate briefing | P3 |

---

### K. Schedulers & autopilot (SUP-AT + delivery)

| Existing Module | Current Responsibility | Target | Action | Reason | Priority |
|-----------------|------------------------|--------|--------|--------|----------|
| `nightly_prep_scheduler.py` | Time-gated nightly prep | **SUP-AT** | **Keep** | Job runner | P2 |
| `morning_suggestions_scheduler.py` | Morning TG picks | **SUP-AL** | **Keep** | Delivery job | P3 |
| `trade_selection_scheduler.py` | Auto star picks | **HUNT** | **Keep** | Automates stalk focus | P2 |
| `options_trade_selection_scheduler.py` | Auto option leg | **HUNT** | **Keep** | Options stalk automation | P2 |
| `autopilot_status.py` | launchd + scheduler health | **SUP-AT** | **Split** | Status vs installer | P3 |
| `autopilot_alerts.py` | Prep failure TG | **SUP-AL** | **Keep** | Ops alert | P3 |

---

## Traceability matrix — `ui/` (presentation)

**Rule:** UI modules are **SUP-UI** unless they contain decision logic (Constitution violation).

| Existing Module | Current Responsibility | Target | Action | Reason | Priority |
|-----------------|------------------------|--------|--------|--------|----------|
| `app.py` | Streamlit entry, nav routing | **PIPE** + SUP-UI | **Keep** | Shell; Home fast-path | P1 |
| `ui/navigation.py` | Tab state machine | **SUP-UI** | **Keep** | Navigation | P4 |
| `ui/theme.py` | Nav registry, CSS | **SUP-UI** | **Keep** | Chrome | P4 |
| `ui/charts.py` | Plotly helpers | **SUP-UI** | **Keep** | Charts | P4 |
| `ui/pages/unified_home.py` | Home shell | **SUP-UI** | **Keep** | Primary surface | P1 |
| `ui/components/unified_hub.py` | Home OS orchestration | **PIPE** + SUP-UI | **Split** | Thin UI; logic → `investment_os` | P0 |
| `ui/components/investment_os_ui.py` | OS module cards | **SUP-UI** | **Keep** | Decision artifact display | P1 |
| `ui/pages/intraday.py` | Suggestions tab | **SUP-UI** | **Keep** | Hunt/Judge surface | P2 |
| `ui/components/intraday_watchlist.py` | Watchlist panel (531 LOC) | **SUP-UI** | **Split** | Heavy orchestration leakage | P1 |
| `ui/components/options_expiry_watchlist.py` | Options WL (515 LOC) | **SUP-UI** | **Split** | Heavy orchestration leakage | P1 |
| `ui/components/morning_cockpit.py` | Morning dashboard | **SUP-UI** | **Merge** → Home | Duplicate morning surface | P2 |
| `ui/components/mis_trade_advisory.py` | MIS panel | **SUP-UI** | **Merge** → `investment_os_ui` | Duplicate verdict UI | P2 |
| `ui/components/strategy_synthesis.py` | Synthesis expander | **SUP-UI** | **Keep** | Evidence display | P2 |
| `ui/components/daily_playbook.py` | Playbook panel | **SUP-UI** | **Remove** | Superseded by OS | P3 |
| `ui/components/suggestions_home.py` | Legacy home | **SUP-UI** | **Remove** | Redirect only | P4 |
| `ui/pages/track_record.py` | Journal & learning | **SUP-UI** | **Keep** | Evolution surface | P1 |
| `ui/pages/alpha_ai.py` | Alpha AI report | **SUP-UI** | **Keep** | Judge deep-dive | P2 |
| `ui/pages/single_stock.py` | Single stock analysis | **SUP-UI** | **Keep** | Judge surface | P3 |
| `ui/pages/compare.py` | Compare stocks | **SUP-UI** | **Keep** | Judge surface | P3 |
| `ui/pages/screener.py` | Screener | **SUP-UI** | **Keep** | Hunt surface | P3 |
| `ui/pages/market_pulse.py` | Pulse scan UI | **SUP-UI** | **Keep** | Hunt surface | P2 |
| `ui/pages/live_options_advisor.py` | Options coach (5s poll) | **SUP-UI** | **Keep** | Judge/coach display; reduce poll | P1 |
| `ui/pages/nse_options.py` | Chain UI | **SUP-UI** | **Keep** | Market memory view | P3 |
| `ui/pages/live_charts.py` | Chart grid | **SUP-UI** | **Keep** | Charts | P4 |
| `ui/pages/global_markets.py` | Global indices | **SUP-UI** | **Keep** | Context view | P4 |
| `ui/pages/daily_advisor.py` | Daily advisor tab | **SUP-UI** | **Remove** | Merge into Home | P3 |
| `ui/pages/beginner_risk.py` | Risk education | **SUP-UI** + SUP-CR | **Keep** | Education | P4 |
| `ui/pages/sip_goals.py` | SIP UI | **SUP-UI** | **Keep** | Wealth ledger UI | P2 |
| `ui/pages/zerodha.py` | Portfolio | **SUP-UI** | **Keep** | Broker mirror UI | P1 |
| `ui/pages/watchlist.py` | Legacy batch scanner | **SUP-UI** | **Remove** | Use screener | P4 |
| `ui/pages/penny_picks.py` | Penny filter UI | **SUP-UI** | **Keep** | Hunt niche | P4 |
| `ui/pages/backtest.py` | Backtest UI | **SUP-UI** | **Keep** | Research | P4 |
| `ui/pages/varsity.py` | Varsity TA | **SUP-UI** + SUP-CR | **Keep** | Education | P4 |
| `ui/components/kite_auth.py` | OAuth handler | **SUP-UI** + SUP-BM | **Split** | Auth UI vs service | P1 |
| `ui/components/kite_connect.py` | Kite sidebar | **SUP-UI** | **Keep** | Broker connect | P2 |
| `ui/components/kite_banner.py` | Kite status banner | **SUP-UI** | **Keep** | Health display | P4 |
| `ui/components/autopilot.py` | Autopilot panel | **SUP-UI** | **Keep** | Ops | P3 |
| `ui/components/trade_journal.py` | Journal UI | **SUP-UI** | **Keep** | Evolution UI | P2 |
| `ui/components/intraday_journal.py` | Intraday log UI | **SUP-UI** | **Merge** → journal UI | Duplicate | P2 |
| `ui/components/data_health_panel.py` | Data health display | **SUP-UI** | **Keep** | GAP visibility | P1 |
| `ui/components/unified_prep.py` | Prep workflow UI | **SUP-UI** | **Keep** | Hunt prep | P2 |
| `ui/components/prep_all.py` | Prep aggregator | **SUP-UI** | **Merge** → `unified_prep` | Overlap | P3 |
| `ui/components/command_palette.py` | Command palette | **SUP-UI** | **Keep** | Navigation | P4 |
| `ui/components/navigation_bar.py` | Nav widgets | **SUP-UI** | **Keep** | Chrome | P4 |
| `ui/components/onboarding.py` | Onboarding flow | **SUP-CR** | **Keep** | Competence onboarding | P3 |
| `ui/components/onboarding_tour.py` | Product tour | **SUP-UI** | **Keep** | UX | P4 |
| `ui/components/setup_wizard.py` | Setup wizard | **SUP-UI** | **Keep** | Ops onboarding | P3 |
| `ui/components/telegram_subscribe.py` | TG subscribe | **SUP-AL** | **Keep** | Alert signup | P4 |
| `ui/components/*` (remaining) | Advice, tips, cheat sheet, IV, NSE, earnings, affordable, sideways, small_trader, delivery, live_session, theme_toggle, empty_states, watchlist_stats | **SUP-UI** | **Keep** | Presentation fragments | P4 |

---

## Traceability matrix — `scripts/` (jobs)

| Existing Module | Current Responsibility | Target | Action | Reason | Priority |
|-----------------|------------------------|--------|--------|--------|----------|
| `scripts/autopilot_daily.py` | Master scheduler runner | **SUP-AT** | **Keep** | Ops | P2 |
| `scripts/nightly_prep.py` | Manual nightly prep | **HUNT** | **Keep** | Stalk builder | P1 |
| `scripts/post_close_scan.py` | Post-close scan | **HUNT** + EVOLVE | **Keep** | Scan + learn trigger | P2 |
| `scripts/validate_suggestions.py` | EOD validation | **EVOLVE** | **Keep** | Learning job | P0 |
| `scripts/trade_selection_auto.py` | Auto star picks | **HUNT** | **Keep** | Stalk focus | P2 |
| `scripts/strategy_research.py` | Offline research | **EVOLVE** | **Keep** | Research | P3 |
| `scripts/watchlist_live_alerts.py` | Live level alerts | **SUP-AL** | **Keep** | In-trade alert | P2 |
| `scripts/kite_auth.py` | CLI Kite login | **SUP-BM** | **Keep** | Auth | P2 |
| `scripts/live_options_coach_watch.py` | Terminal options coach | **JUDGE** | **Keep** | Coach TUI | P2 |
| `scripts/live_equity_coach_watch.py` | Terminal equity coach | **JUDGE** | **Keep** | Coach TUI | P2 |
| `scripts/mis_eod_summary.py` | EOD summary | **EVOLVE** + SUP-AL | **Keep** | Summary job | P2 |
| `scripts/morning_briefing.py` | CLI briefing | **PIPE** | **Merge** → OS CLI | Duplicate | P3 |
| `scripts/morning_suggestions.py` | Morning TG | **SUP-AL** | **Keep** | Delivery | P3 |
| `scripts/prep_morning_nag.py` | Morning nag | **SUP-AL** | **Keep** | Nudge | P4 |
| `scripts/session_reminders.py` | Session reminders | **SUP-AL** | **Keep** | Nudge | P4 |
| `scripts/sip_reminder.py` | SIP reminder | **SUP-AL** | **Keep** | Wealth nudge | P4 |
| `scripts/morning_options_rescan.py` | Options rescan | **HUNT** | **Keep** | Trigger refresh | P3 |
| `scripts/daily_trading_guide.py` | Trading guide CLI | **PIPE** | **Remove** | Superseded by OS | P4 |

---

## Orphan modules — do not belong

| Module | Why orphan | Action | Priority |
|--------|------------|--------|----------|
| `interaction-investigator/` (6 files) | Webex/CC log RCA — unrelated to investing brain | **Remove** from repo or move to separate product | P4 |
| `local-call-insights/` (2 files) | CSV call analytics — unrelated | **Remove** from repo or separate product | P4 |
| `watchlist.py` | Legacy scanner superseded by pulse + pins | **Remove** | P4 |
| `trade_journal_link.py` | Glue for merged journals | **Remove** after merge | P4 |
| `whatsapp_export.py` | Marginal duplicate channel | **Remove** | P4 |
| `ui/pages/watchlist.py` | Legacy tab | **Remove** | P4 |
| `ui/components/suggestions_home.py` | Legacy home | **Remove** | P4 |
| `ui/components/daily_playbook.py` | Superseded by OS | **Remove** | P3 |
| `scripts/daily_trading_guide.py` | Superseded by OS | **Remove** | P4 |
| `kite_health.py` | Dev-only diagnostic | **Keep** but exclude from Constitutional map | P4 |

---

## Duplicate responsibilities

Constitution allows **one verdict authority** (pipeline). Current duplicates:

| Responsibility | Canonical owner (Constitution) | Duplicates to merge |
|----------------|-------------------------------|---------------------|
| **Daily driver / verdict** | `investment_os` (PIPE) | `mis_trade_advisory`, `daily_playbook`, `daily_advisor`, `morning_briefing`, `session_advisory`, `morning_cockpit` UI |
| **Signal fusion / confidence** | `strategy_synthesis` (JUDGE) | `options_signal`, `live_options_coach` (partial), `mis_trade_advisory`, `candle_narrative` |
| **Opportunity ranking** | `market_pulse_scan` + `watchlist_pins` (HUNT) | `intraday_stock_picker`, `intraday_watchlist` scoring, `screener` overlap |
| **Position sizing** | `intraday_trade_plan` (CAP) | `watchlist_position_size`, `watchlist_profit`, `affordable_invest` (partial) |
| **Learning / calibration** | `eod_learning` facade (EVOLVE) | `watchlist_learning`, `options_watchlist_learning`, `suggestion_learning`, `threshold_tuning`, `confidence_calibration` |
| **Outcome truth** | Broker mirror → Evolution | `watchlist_eod` (coach truth), `suggestion_validator` (price proxy) |
| **Journal / audit** | `suggestion_journal` + broker records | `trade_journal`, `intraday_journal` |
| **Telegram formatting** | Single formatter package | `suggestions_telegram`, `watchlist_telegram`, parts of `mis_eod_summary` |
| **Session / phase** | `market_session` (CTX) | `session_phase`, `session_advisory`, `session_reminders` |
| **Risk assessment** | Context + Capital split | `market_risk`, `risk`, `portfolio_risk`, beginner tips |
| **Options stalk** | `options_expiry_watchlist` | `options_trade_selection`, schedulers, `live_options_advisor` overlap |
| **Morning UI** | `unified_hub` + `investment_os_ui` | `suggestions_home`, `morning_cockpit`, `daily_playbook` component |

---

## Missing responsibilities (Constitutional gaps)

These are **required by Constitution** but **not implemented** as first-class modules:

| Missing capability | Constitutional reference | Severity | Suggested owner |
|--------------------|-------------------------|----------|-----------------|
| **BrokerTruth / TradeRecord** | Law 2: Broker truth beats model truth | **P0** | SUP-BM → feeds EVOLVE |
| **Coach vs broker divergence KPI** | Monitoring three truths | **P0** | EVOLVE |
| **Evidence packet model** | FACT / ESTIMATE / OPINION / GAP labels | **P0** | JUDGE (`strategy_synthesis` output schema) |
| **Uncertainty vector** | Six dimensions, composite ELEVATED | **P0** | JUDGE |
| **Munger invert gate** | Mandatory adversarial pass | **P1** | JUDGE (before confidence) |
| **Decision artifact schema** | Standard ACT/WAIT/PASS artifact | **P1** | PIPE output of `investment_os` |
| **Daily loss dam veto** | Capital flow — dam fills → stop | **P0** | CAP (`intraday_prefs` + session state) |
| **Sacred core enforcement** | SIP never in tactical budget | **P1** | CAP |
| **Competence registry** | Circle of competence stalk permissions | **P1** | SUP-CR (today: prefs stub only) |
| **Execution contract object** | Unified pre-order contract | **P1** | CAP + PIPE (partial in `intraday_trade_plan`) |
| **n ≥ 30 adaptation guard** | Evolution governance | **P1** | EVOLVE |
| **Strategy class health / decay** | Simons model decay | **P2** | EVOLVE |
| **Thesis stub per stalk** | Lynch two-sentence story | **P2** | HUNT (`watchlist_pins` schema) |
| **Personal discipline score** | Evolution personal patterns | **P2** | EVOLVE |
| **Narrative guard on LLM output** | AI must not invent metrics | **P1** | SUP-NG (partial via prompts only) |

---

## Engine coverage heatmap

```text
                    CTX   HUNT  JUDGE  CAP   EVOLVE  SUP
Coverage today:     ███   ████  ████   ███   ██░░    ████
Coverage needed:    ████  ████  █████  ████  █████   ████

░░ = critical gap (broker truth, governance)
```

| Engine | Strongest existing modules | Weakest gap |
|--------|---------------------------|-------------|
| **Context** | `market_regime`, `market_session`, `india_macro` | No unified RISK-ON/OFF/CLOSED verdict |
| **Hunt** | `market_pulse_scan`, `watchlist_pins`, `trade_selection` | No thesis stub; trigger classes informal |
| **Judgment** | `strategy_synthesis`, `alpha_ai_report`, `combined` | No evidence packet, uncertainty vector, invert gate |
| **Capital** | `intraday_trade_plan`, `sip_planner`, `watchlist_sector` | No loss dam auto-veto; sacred/tactical not enforced |
| **Evolution** | `eod_learning`, `watchlist_learning`, journals | **No broker truth**; coach outcomes drive learning |

---

## Migration priority queue (top 25)

| Rank | Work item | Engines | Action | Priority |
|------|-----------|---------|--------|----------|
| 1 | Introduce BrokerTruth / TradeRecord from Zerodha | EVOLVE, SUP-BM | **New** (gap) | P0 |
| 2 | Rewire learning to broker P&L not `watchlist_eod` hits | EVOLVE | **Fix** | P0 |
| 3 | Daily loss dam gate in pipeline | CAP, CTX | **New** (gap) | P0 |
| 4 | Thin `investment_os` as sole PIPE verdict issuer | PIPE | **Keep** + absorb duplicates | P0 |
| 5 | Evidence packet + uncertainty on `StrategySynthesis` | JUDGE | **Extend** | P0 |
| 6 | `data_health` → GAP labels in evidence | SUP-MM, JUDGE | **Wire** | P0 |
| 7 | Merge `mis_trade_advisory` into OS pipeline | PIPE | **Merge** | P1 |
| 8 | Split `intraday_prefs` → context dams vs capital | CTX, CAP | **Split** | P0 |
| 9 | Coach vs broker divergence dashboard | EVOLVE | **New** (gap) | P0 |
| 10 | Merge 3 journals → one facade + broker join | EVOLVE | **Merge** | P1 |
| 11 | Merge 4 learning tuners → Evolution facade | EVOLVE | **Merge** | P1 |
| 12 | Munger invert gate before ACT | JUDGE | **New** (gap) | P1 |
| 13 | Decision artifact standard on Home | PIPE, SUP-UI | **New** (gap) | P1 |
| 14 | Split `live_options_coach` — display vs verdict | JUDGE, PIPE | **Split** | P1 |
| 15 | Split UI orchestration out of `unified_hub` | SUP-UI | **Split** | P1 |
| 16 | Merge daily advisors (`daily_advisor`, `session_advisory`, briefing) | JUDGE, CTX | **Merge** | P2 |
| 17 | Split `market_pulse_scan` scan vs enrich | HUNT | **Split** | P2 |
| 18 | Competence registry (stalk permissions) | SUP-CR | **New** (gap) | P2 |
| 19 | Thesis stub on `PinnedPlan` | HUNT | **Extend** | P2 |
| 20 | n≥30 guard on `threshold_tuning` | EVOLVE | **Extend** | P1 |
| 21 | Remove legacy `watchlist.py` + UI tab | HUNT | **Remove** | P4 |
| 22 | Remove sibling projects from monorepo | ORPHAN | **Remove** | P4 |
| 23 | Merge Telegram formatters | SUP-AL | **Merge** | P3 |
| 24 | Wire `wealth_plan` to Home growth track | CAP | **Keep** | P2 |
| 25 | Split `zerodha.py` auth/portfolio/marketdata | SUP-BM | **Split** | P1 |

---

## Constitutional traceability matrix (requirements → modules)

| # | Constitutional question | Primary modules today | Gap |
|---|-------------------------|----------------------|-----|
| 1 | Capital flow | `intraday_prefs`, `sip_planner`, `intraday_trade_plan` | Loss dam, sacred core enforcement |
| 2 | Opportunity discovery | `market_pulse_scan`, `watchlist_pins`, `screener` | Thesis stub, formal triggers |
| 3 | Evidence collection | `combined`, `strategy_synthesis`, `alpha_ai_report` | Labeled evidence packet |
| 4 | Uncertainty measurement | `confidence_calibration` (partial) | Uncertainty vector |
| 5 | Confidence estimation | `strategy_synthesis`, `confidence_calibration` | Believability weights, caps |
| 6 | Capital allocation | `intraday_trade_plan`, `watchlist_sector` | Auto veto → zero |
| 7 | Decisions made | `investment_os`, `mis_trade_advisory`, `strategy_synthesis` | Single pipeline; invert gate |
| 8 | Trades executed | `intraday_trade_plan`, `trade_ladder`, coaches | Execution contract object |
| 9 | Outcomes monitored | `watchlist_eod`, `mis_eod_summary`, journals | **Broker truth missing** |
| 10 | System learns | `eod_learning`, `watchlist_learning`, tuners | Broker-fed Evolution; n≥30 |

---

## Summary disposition counts

| Action | Analyzer | UI | Scripts | Total |
|--------|--------:|---:|--------:|------:|
| **Keep** | 98 | 48 | 14 | 160 |
| **Merge** | 32 | 8 | 2 | 42 |
| **Split** | 18 | 6 | 0 | 24 |
| **Remove** | 5 | 4 | 1 | 10 |
| **New (gap)** | 8 capabilities | — | — | 8 |

---

## Related documents

| Doc | Relationship |
|-----|--------------|
| [08_Final_Investment_OS_Architecture.md](./08_Final_Investment_OS_Architecture.md) | **Constitution** — authoritative |
| [02_Module_Inventory.md](./02_Module_Inventory.md) | Source inventory for this mapping |
| [07_Architecture_Critique.md](./07_Architecture_Critique.md) | Prior critique; broker truth priority aligned |
| [06_Migration_Plan.md](./06_Migration_Plan.md) | **Superseded** for priority by Section "Migration priority queue" above |

---

*Every module must trace to an engine or supporting role. If it cannot, it does not ship. If it duplicates a verdict, it merges. If learning ignores the broker, it does not learn.*
