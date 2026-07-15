# 02 — Module Inventory

**Audit date:** 2026-07-15  
**Convention:** **Stay** = keep as-is · **Merge** = combine with related module · **Split** = break into smaller units · **Deprecate** = unused, remove later

---

## Summary counts

| Package | Modules | Total LOC (approx.) |
|---------|--------:|--------------------:|
| `analyzer/` | 163 | ~33,100 |
| `ui/` | 68 | ~8,500 |
| `scripts/` | 19 | ~1,200 |
| `tests/` | 76 | ~12,000 |
| Root (`app.py`, `cli.py`) | 2 | ~500 |

---

## A. Data & providers (16 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `data.py` | Equity OHLCV fetch | Yahoo fetch, NSE suffix, fundamentals attach | `fundamentals`, `markets`, `nse_data` | symbol, period, market | DataFrame, meta | **Stay** |
| `fundamentals.py` | Fundamental metrics | ROE, PE, scoring hints | `data` | ticker data | `FundamentalMetric` list | **Stay** |
| `intraday_data.py` | Intraday bars | Delegates to provider router | `providers.router`, `market_session` | symbol, interval | DataFrame | **Stay** |
| `cache_utils.py` | Disk cache helpers | TTL files under `data/cache/` | pathlib | key, factory | cached object | **Stay** |
| `macro_cache.py` | Macro snapshot cache | Thin wrapper over cache_utils | `cache_utils` | — | macro blob | **Merge** → `pulse_cache` |
| `pulse_cache.py` | Pulse report serialization | JSON-safe MarketPulseReport round-trip | `market_pulse_scan` types | cache key | report, stale flag | **Stay** |
| `nse_data.py` | NSE enrichment | Symbol metadata from NSE | `nse_session` | symbol | enrichment dict | **Stay** (internal) |
| `nse_session.py` | NSE HTTP session | Cookies, JSON fetch, error recording | requests | URL | JSON / error | **Stay** |
| `data_health.py` | Data source health | Provider status summary | multiple | — | health report | **Stay** |
| `env_loader.py` | Environment I/O | Load/save `.env`, validate Telegram token | dotenv, requests | key, value | env dict | **Split** — secrets vs config |
| `asset_class.py` | Asset classification | Equity vs index vs ETF detection | — | symbol | asset class | **Stay** |
| `delivery_quality.py` | Delivery % analysis | NSE delivery snapshots, scoring | `nse_session` | symbol | delivery metrics | **Stay** |
| `providers/__init__.py` | Provider exports | Public API surface | router | — | — | **Stay** |
| `providers/router.py` | Data routing | Kite-first LTP/bars, Yahoo fallback | `kite_status`, `kite`, `yahoo` | symbol | bars, LTP | **Stay** — formalize interface |
| `providers/kite.py` | Kite bar fetch | Kite historical candles | `zerodha` | symbol, interval | DataFrame | **Stay** |
| `providers/yahoo.py` | Yahoo bar fetch | yfinance wrapper | yfinance | symbol | DataFrame | **Stay** |
| `providers/types.py` | Provider types | Shared dataclasses | — | — | types | **Stay** |

---

## B. Markets, India & macro (11 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `markets.py` | Market registry | Exchange labels, India detection | — | market key | config dict | **Stay** |
| `india.py` | India ticker help | NSE symbol conventions, help text | — | — | markdown help | **Stay** |
| `india_macro.py` | India macro snapshot | VIX, sector indices, FII/DII | yfinance, `nse_session` | — | `IndiaMacroSnapshot` | **Stay** |
| `india_enrichment.py` | India-specific enrich | Sector, listing metadata | `data`, `nse_data` | symbol | enrichment | **Merge** → `india.py` or data layer |
| `gift_nifty.py` | Pre-open gap cue | Gift Nifty / fut proxy | `providers`, yfinance | — | gap cue | **Stay** |
| `global_markets.py` | Global indices | US/EU/Asia quotes | yfinance | — | index list | **Stay** |
| `global_impact.py` | Global→India impact | Correlation-based action hints | `global_markets` | — | impact report | **Stay** |
| `nse_holidays.py` | NSE calendar | Trading day checks | — | date | bool | **Stay** |
| `market_session.py` | Session status | Open/closed, phase, date | `nse_holidays`, `session_phase` | now | session dict | **Stay** |
| `session_phase.py` | Intraday phases | Pre/open/close buckets | — | time | phase string | **Stay** |
| `earnings_calendar.py` | Earnings events | Upcoming results, risk notes | NSE/yahoo | symbol | events | **Stay** |

---

## C. Technical analysis & signals (14 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `indicators.py` | Indicator wrapper | pandas-ta / custom indicators | pandas | DataFrame | enriched DF | **Stay** |
| `ta.py` | TA helpers | RSI, MACD computations | pandas | DataFrame | values | **Stay** |
| `signals.py` | Signal generation | Buy/sell from indicators + candlesticks | `candlesticks`, `varsity_knowledge` | DataFrame | signal dict | **Stay** |
| `candlesticks.py` | Pattern detection | Candle pattern rules | pandas | OHLC | patterns | **Stay** |
| `candle_narrative.py` | Live chart narrative | Intraday action summary | `intraday_data`, `options_signal` ⚠️ | df, symbol | narrative | **Split** — decouple from options |
| `combined.py` | Combined analysis | Fundamentals + technical merge | `fundamentals`, `signals` | symbol data | analysis | **Stay** |
| `relative_strength.py` | RS vs benchmark | Relative performance | `data` | symbol, index | RS score | **Stay** |
| `chart_horizon.py` | Horizon analysis | Short/long chart scoring | `data`, `indicators` | DataFrame | `HorizonAnalysis` | **Stay** |
| `multi_timeframe.py` | MTF consensus | Multi-interval alignment | `intraday_data`, `data` | symbol | MTF report | **Stay** |
| `opening_range_confirm.py` | OR breakout gate | Opening range logic | `intraday_data` | symbol | OR status | **Stay** |
| `market_regime.py` | Nifty regime | ADX trend vs range | `data`, `indicators` | — | `MarketRegime` | **Stay** |
| `market_pulse.py` | Index pulse types | Dataclasses for pulse | — | — | types | **Merge** → `market_pulse_scan` |
| `varsity_knowledge.py` | TA education KB | Static Varsity content + thresholds | — | chapter/query | text, constants | **Stay** |
| `backtest.py` | Backtesting | Walk-forward, strategy sim | `data`, `signals` | symbol, params | backtest results | **Stay** |

---

## D. Intraday / MIS core (18 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `intraday_signals.py` | Intraday signals | MIS-specific signal rules | `ta` | intraday DF | signals | **Stay** |
| `intraday_trade_plan.py` | Trade plan builder | E/S/T, R:R, position size | `trade_ladder` | action, levels, capital | `IntradayTradePlan` | **Stay** |
| `intraday_watchlist.py` | Prep watchlist | Top-N picks, checklist, plans | `watchlist_learning`, `market_pulse_scan` | pulse report | `IntradayWatchlistReport` | **Split** — scoring vs plan build |
| `intraday_beginner_tips.py` | Beginner rules | Timing, capital budget | `market_session` | prefs, now | timing advice | **Stay** |
| `intraday_prefs.py` | User prefs | Capital, risk %, modes | JSON file | — | `IntradayPrefs` | **Stay** |
| `intraday_chart.py` | Intraday charts | Chart data prep | `intraday_data` | symbol | chart DF | **Stay** |
| `intraday_stock_picker.py` | Stock picker | Pulse-based pick selection | `market_pulse_scan` | report | picks | **Merge** → watchlist |
| `intraday_pulse_source.py` | Pulse accessor | Cached quick scan | `pulse_cache`, `market_pulse_scan` | market, period | report | **Stay** |
| `trade_ladder.py` | Exit ladder | T1/T2/T3 partial exits | — | side, levels | ladder rules | **Stay** |
| `profit_targets.py` | Profit modes | Aggressive/conservative targets | — | prefs mode | target config | **Stay** |
| `small_trader_intraday.py` | Small capital rules | Affordable MIS guidance | `intraday_prefs` | capital | tips | **Merge** → `intraday_beginner_tips` |
| `live_charts_grid.py` | Multi-chart grid | Live chart batch fetch | `providers`, `cache_utils` | symbols | grid data | **Stay** |
| `mis_trade_advisory.py` | MIS verdict | Trade OK / NO_TRADE synthesis | 14 modules incl. `strategy_synthesis` | now | `MisTradeAdvisory` | **Merge** → strategy layer |
| `mis_printable_checklist.py` | Printable checklist | MIS checklist generation | `mis_checklist_store` | plan | checklist text | **Stay** |
| `mis_checklist_store.py` | Checklist persistence | JSON store | — | checklist | saved state | **Stay** |
| `mis_eod_summary.py` | EOD Telegram summary | Equity+options day summary | `watchlist_eod`, `watchlist_learning` | trade_date | summary | **Stay** |
| `session_advisory.py` | Session guidance | Phase-based market advice | `india_macro` | session | advisory text | **Merge** → `investment_os` |
| `investment_os.py` | **Investment OS** | 7-module daily pipeline | pulse, pins, synthesis, journal | market, prefs | `InvestmentOS` | **Stay** — canonical daily driver |

---

## E. Watchlist system (18 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `watchlist.py` | Legacy watchlist | Simple combined-analysis list | `combined` | tickers | list | **Deprecate** |
| `watchlist_pins.py` | Pinned plans | Top-N JSON persistence | `market_session` | picks | `PinnedPlan` list | **Stay** |
| `watchlist_history.py` | Snapshot DB | SQLite snapshots + EOD join | `watchlist_eod`, `trade_selection` | picks | snapshots | **Split** — persistence vs scoring |
| `watchlist_eod.py` | EOD outcome scoring | Target/stop hit detection | `data` | snapshot | outcomes | **Stay** |
| `watchlist_persist.py` | Persist orchestrator | Fingerprinted save on change | `watchlist_pins`, `watchlist_history` | report | bool | **Stay** |
| `watchlist_learning.py` | Equity learning | Gate tuning from outcomes | `watchlist_history`, `suggestion_journal` | days | strategy JSON | **Stay** |
| `watchlist_plan_tracker.py` | Live plan tracking | Intraday plan state | pins, LTP | symbol | tracker state | **Stay** |
| `watchlist_live_alerts.py` | Live alerts | Telegram on level breach | `providers`, pins | — | alerts sent | **Stay** |
| `watchlist_telegram.py` | TG formatting | Watchlist messages | `gift_nifty`, history | report | markdown | **Merge** → telegram formatters |
| `watchlist_position_size.py` | Position sizing | Share qty from risk | `intraday_trade_plan` | levels, capital | qty | **Merge** → trade plan |
| `watchlist_profit.py` | Profit helpers | Target profit calc | prefs | capital | INR targets | **Merge** → `profit_targets` |
| `watchlist_sector.py` | Sector concentration | Warn on correlated picks | — | picks | warning str | **Stay** |
| `watchlist_pick_display.py` | Display helpers | Format pick for UI | `symbol_track_record` | pick | HTML/text | **Stay** |
| `symbol_track_record.py` | Symbol history | Per-symbol stats | `watchlist_history` | symbol | stats | **Stay** |
| `trade_selection.py` | User star picks | 1–2 symbols for session | `watchlist_pins` | toggle | selected list | **Stay** |
| `prep_status.py` | Prep step tracking | Nightly prep milestones | JSON | step | status | **Stay** |
| `unified_search.py` | Symbol/tab search | Command palette index | nav, symbols | query | results | **Stay** |
| `kite_watchlist_store.py` | Kite WL sync | Import Kite watchlist | `zerodha` | — | symbols | **Stay** |

---

## F. Options (16 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `nse_options.py` | NSE options chain | Scrape/normalize chain | `nse_session`, `kite_options_chain` | index | chain | **Split** — fetch vs normalize |
| `kite_options_chain.py` | Kite options chain | Kite NFO chain | `kite_status`, `zerodha` | symbol | chain | **Stay** |
| `options_analytics.py` | Chain analytics | IV, OI, PCR | chain data | chain | analytics | **Stay** |
| `options_signal.py` | Options signal | Daily CE/PE suggestion | `candle_narrative` ⚠️ | symbol | signal | **Merge** → strategy plugins |
| `options_entry_gate.py` | Entry gate | OR + timing gate | `opening_range_confirm` | symbol, now | gate result | **Stay** — shared service |
| `options_expiry_watchlist.py` | Expiry watchlist | Index CE/PE picks | `affordable_invest`, learning | — | options WL | **Stay** |
| `options_flow_snapshot.py` | Flow snapshot | OI change capture | `nse_options` | index | snapshot | **Stay** |
| `options_reversal_alerts.py` | Reversal alerts | PE/CE reversal cues | `providers` | index | alerts | **Stay** |
| `options_premium_chart.py` | Premium charts | CE/PE premium history | cache, chain | leg | chart data | **Stay** |
| `options_trade_selection.py` | Auto option pick | Selected leg persistence | `options_expiry_watchlist` | — | selected leg | **Stay** |
| `options_watchlist_history.py` | Options snapshot DB | SQLite history + EOD | `watchlist_eod` patterns | picks | outcomes | **Split** — mirror equity pattern |
| `options_watchlist_learning.py` | Options learning | Premium stop/target tune | `options_watchlist_history` | outcomes | strategy JSON | **Stay** |
| `options_backtest.py` | Options backtest | Historical options sim | chain history | params | results | **Stay** |
| `sideways_options_advisor.py` | Sideways strategies | Range/consolidation plays | `nse_options`, analytics | chain | advice (626 LOC) | **Split** — strategy plugins |
| `live_options_coach.py` | Live coach | Real-time CE/PE coach | gates, synthesis, sideways | index | coach state | **Stay** |
| `affordable_invest.py` | Lot affordability | Filter by lot cost | `market_pulse_scan`, chain | max lot INR | affordable legs | **Split** — filter service |

---

## G. Alpha AI & research (16 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `alpha_ai_report.py` | **Research hub** | 15-section institutional report | 22+ modules | symbol | report dict (1008 LOC) | **Split** — orchestrator + sections |
| `alpha_ai_llm.py` | LLM narrative | OpenAI completion | openai | prompt | text | **Stay** |
| `alpha_ai_prompts.py` | Prompt templates | Section prompts | — | context | prompts | **Stay** |
| `alpha_ai_export.py` | PDF export | fpdf2 report export | report dict | report | PDF bytes | **Stay** |
| `alpha_monte_carlo.py` | Monte Carlo | Scenario simulation | `data` | symbol | scenarios | **Stay** |
| `alpha_red_flags.py` | Red flags | Risk flag detection | fundamentals | data | flags | **Stay** |
| `alpha_portfolio_mode.py` | Portfolio mode | Holdings-aware report | `portfolio_store` | holdings | report variant | **Stay** |
| `advisor.py` | Single-stock advisor | Long-term buy/hold | `combined`, `market_pulse` | symbol | advice | **Stay** |
| `daily_advisor.py` | Daily briefing | Holdings + swing scan | `chart_horizon`, `market_pulse_scan` | portfolio | briefing (522 LOC) | **Merge** → slimmer facade |
| `compare.py` | Stock compare | Side-by-side analysis | `combined` | symbols | comparison | **Stay** |
| `screener.py` | Universe screener | Parallel ticker scan | `data`, `combined` | criteria | ranked list | **Stay** |
| `dcf_model.py` | DCF valuation | Discounted cash flow | fundamentals | financials | fair value | **Stay** |
| `etf_analyzer.py` | ETF analysis | ETF-specific metrics | `data` | symbol | ETF report | **Stay** |
| `peer_comparison.py` | Peer comps | Sector peer multiples | `fundamentals` | symbol | peers table | **Stay** |
| `penny_stocks.py` | Penny filter | Low-price stock rules | — | price cap | filter | **Stay** |
| `news_feed.py` | News fetch | Headlines for symbol | requests/yahoo | symbol | news list | **Stay** |

---

## H. Kite / Zerodha (6 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `zerodha.py` | **Kite hub** | OAuth, credentials, holdings, LTP, margins | kiteconnect, `env_loader` | token | client, data (567 LOC) | **Split** — auth / portfolio / marketdata |
| `kite_status.py` | Connect status | Personal vs Connect app probe | `zerodha`, `kite_options_chain` | — | status dict | **Stay** |
| `kite_stream.py` | WebSocket ticker | Nifty 50 LTP cache | `zerodha` | — | LTP dict | **Stay** |
| `kite_health.py` | Health diagnostic | Token/instrument probe | `zerodha` | — | health | **Stay** (dev only) |

---

## I. Portfolio, SIP & wealth (9 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `portfolio.py` | Portfolio types | Holdings dataclasses | — | — | types | **Stay** |
| `portfolio_store.py` | Portfolio persistence | JSON per profile | — | holdings | saved portfolio | **Stay** |
| `portfolio_live.py` | Live portfolio | Kite sync, LTP refresh | `zerodha`, `kite_stream` | profile | live holdings | **Stay** |
| `portfolio_risk.py` | Portfolio risk | Concentration, sector risk | holdings | portfolio | risk report | **Stay** |
| `sip_planner.py` | SIP planner | Allocation math, phases | — | goals | SIP plan (416 LOC) | **Stay** |
| `sip_storage.py` | SIP persistence | goals.json | — | goals | saved | **Stay** |
| `sip_export.py` | SIP export | Export plan formats | `sip_planner` | plan | file | **Stay** |
| `sip_reminders.py` | SIP reminders | Telegram reminders | `telegram_notify` | — | sent | **Stay** |
| `wealth_plan.py` | ₹10 Cr plan | SIP compound projection | — | prefs | wealth plan | **Merge** → SIP UI or **wire to Home** |

---

## J. Learning, journal & calibration (12 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `suggestion_journal.py` | **SQLite journal** | Suggestion log + outcomes | SQLite | suggestion | records | **Stay** — central store |
| `trade_journal.py` | MIS mistake log | JSON mistake/fix log | — | trade | entries | **Merge** → journal facade |
| `intraday_journal.py` | Manual trade log | Entry at trade time | `suggestion_journal` DB | trade | row | **Merge** → journal facade |
| `trade_journal_link.py` | Journal UI link | Cross-reference helper | both journals | — | link | **Deprecate** after merge |
| `suggestion_learning.py` | Suggestion stats | Win rate slices, insights | `suggestion_journal` | — | `LearningReport` | **Stay** |
| `suggestion_validator.py` | Outcome validation | Score vs market move | `data`, journal | pending | validated count | **Stay** |
| `suggestion_features.py` | Feature extraction | Pick feature vectors | `watchlist_history` | picks | features | **Stay** |
| `eod_learning.py` | EOD orchestrator | validate → learn → tune | validator, learning, tuning | — | `EodLearningResult` | **Stay** |
| `threshold_tuning.py` | Pulse thresholds | Auto-tune score gates | `suggestion_learning` | report | thresholds JSON | **Stay** |
| `confidence_calibration.py` | Confidence calibration | Adjust confidence from outcomes | journal | — | calibration | **Merge** → learning facade |
| `strategy_research.py` | Offline research | 6mo backtest → weights | `watchlist_learning` | — | research version | **Stay** (offline) |

---

## K. Orchestration & daily drivers (10 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `market_pulse_scan.py` | **Scan hub** | Universe multi-horizon scan | 22 modules | market, period | `MarketPulseReport` | **Split** — scan vs enrich |
| `strategy_synthesis.py` | **Signal fusion** | Pillar voting → verdict | 21 modules | symbol, levels | `StrategySynthesis` | **Stay** — add plugin registry |
| `daily_playbook.py` | Beginner playbook | Step-by-step day guide | `mis_trade_advisory`, pins | prefs | playbook steps | **Merge** → `investment_os` |
| `morning_briefing.py` | Morning CLI brief | Wraps daily_advisor + pulse | `daily_advisor`, `market_pulse_scan` | — | text | **Merge** → script-only facade |
| `nightly_prep.py` | Nightly prep | Equity + options + Telegram | watchlist, options WL | market | `NightlyPrepResult` | **Stay** |
| `market_risk.py` | Market risk assess | Goal-based risk scoring | `data`, fundamentals | symbol, goal | assessment | **Stay** |
| `risk.py` | Simple risk helpers | Thin risk utilities | — | — | — | **Merge** → `market_risk` |
| `prep_morning_nag.py` | Morning nag | Telegram if no prep | `telegram_notify`, pins | — | sent | **Stay** |
| `setup_status.py` | Setup checklist | Env/config completeness | `env_loader`, kite | — | status | **Stay** |

---

## L. Schedulers & autopilot (9 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `nightly_prep_scheduler.py` | Schedule nightly prep | Time-gated `run_nightly_prep` | `nightly_prep` | — | result | **Stay** |
| `morning_suggestions_scheduler.py` | Morning TG picks | Send morning list | `suggestions_telegram` | — | sent | **Stay** |
| `trade_selection_scheduler.py` | Auto star picks | `auto_select_top_by_rank` | `trade_selection` | — | result | **Stay** |
| `options_trade_selection_scheduler.py` | Auto option leg | Auto option select | `options_trade_selection` | — | result | **Stay** |
| `post_close_scan_scheduler.py` | Post-close scan | Quick scan + learning | pulse, eod | — | result | **Stay** |
| `morning_options_rescan.py` | Options rescan | Re-scan after open | options WL | — | result | **Stay** |
| `session_reminders.py` | Session reminders | Phase Telegram nudges | `market_session` | — | sent | **Stay** |
| `autopilot_status.py` | Autopilot dashboard | launchd + scheduler health | all schedulers | — | status (258 LOC) | **Split** — status vs install |
| `autopilot_alerts.py` | Failure alerts | Prep/selection failure TG | `autopilot_status` | — | alert | **Stay** |

---

## M. Notifications & export (6 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `telegram_notify.py` | Telegram send | Broadcast API | requests | message | ok/err | **Stay** |
| `telegram_subscriptions.py` | Subscriber CRUD | SQLite subscribers (499 LOC) | sqlite | chat_id | subscribers | **Split** — store vs delivery |
| `suggestions_telegram.py` | Suggestion TG format | Nightly/morning messages | formatters | report | markdown | **Merge** |
| `suggestions_export.py` | Export suggestions | CSV/JSON export | journal | — | file | **Stay** |
| `whatsapp_export.py` | WhatsApp format | Message formatting | — | report | text | **Stay** or deprecate |
| `structured_log.py` | JSON logging | Structured log lines | — | event | log row | **Stay** |

---

## N. UI support (analyzer-side, 5 modules)

| Module | Purpose | Responsibilities | Key dependencies | Inputs | Outputs | Verdict |
|--------|---------|------------------|------------------|--------|---------|---------|
| `app_mode.py` | Cloud mode flag | SIMPLE_CLOUD_MODE check | env | — | bool | **Stay** |
| `ui_preferences.py` | UI prefs | Theme, compact nav | JSON | — | prefs | **Stay** |
| `onboarding_state.py` | Onboarding | First-run state | JSON | — | state | **Stay** |

---

## O. UI layer (`ui/` — 68 files)

### Pages (`ui/pages/` — 20 tabs)

| Page | Purpose | Primary analyzer imports | Business logic in UI? | Verdict |
|------|---------|--------------------------|----------------------|---------|
| `unified_home.py` | Home shell | `unified_hub` | No | **Stay** |
| `intraday.py` | Suggestions tab | watchlist, options, cockpit components | Orchestration only | **Stay** |
| `track_record.py` | Journal & learning | `eod_learning`, journal, tuning | No | **Stay** |
| `beginner_risk.py` | Risk education | `market_risk`, prefs | No | **Stay** |
| `sip_goals.py` | SIP UI | `sip_planner`, `sip_storage` | No | **Stay** |
| `market_pulse.py` | Pulse scan UI | `market_pulse_scan`, `pulse_cache` | Triggers scan | **Stay** |
| `daily_advisor.py` | Daily advisor | `daily_advisor` | Fragment refresh | **Merge** tab into Home or deprecate |
| `global_markets.py` | Global indices | `global_markets` | Fragment 30s | **Stay** |
| `single_stock.py` | Single stock | `combined`, `advisor`, options | No | **Stay** |
| `alpha_ai.py` | Alpha AI | `alpha_ai_report`, export, llm | Report trigger | **Stay** |
| `compare.py` | Compare | `compare` | No | **Stay** |
| `live_charts.py` | Chart grid | `live_charts_grid` | Cached fetch | **Stay** |
| `live_options_advisor.py` | Options coach | `live_options_coach` | **5s fragment** | **Stay** — reduce poll rate |
| `nse_options.py` | NSE chain UI | `nse_options`, analytics | No | **Stay** |
| `watchlist.py` | Batch scanner | `watchlist` (legacy) | No | **Deprecate** → screener |
| `screener.py` | Screener | `screener` | No | **Stay** |
| `penny_picks.py` | Penny stocks | `penny_stocks` | No | **Stay** |
| `zerodha.py` | Portfolio | `portfolio_*`, `zerodha` | 15s LTP fragment | **Stay** |
| `backtest.py` | Backtest | `backtest` | No | **Stay** |
| `varsity.py` | Varsity TA | `varsity_knowledge` | No | **Stay** |

### Key components (`ui/components/`)

| Component | Purpose | Analyzer deps | Logic leakage? | Verdict |
|-----------|---------|---------------|------------------|---------|
| `unified_hub.py` | Home OS UI | `investment_os`, `nightly_prep`, `trade_selection` | Orchestration | **Stay** |
| `investment_os_ui.py` | OS module cards | `investment_os` types | Presentation only | **Stay** |
| `intraday_watchlist.py` | Watchlist panel | 15+ analyzer modules | Heavy orchestration (531 LOC) | **Split** — thin UI |
| `options_expiry_watchlist.py` | Options WL panel | options stack | Heavy orchestration (515 LOC) | **Split** |
| `morning_cockpit.py` | Morning dashboard | advisory, pins | Orchestration | **Merge** → Home |
| `kite_auth.py` | OAuth handler | `zerodha`, `env_loader` | **OAuth + env write** | **Split** — move auth to service |
| `kite_connect.py` | Kite sidebar | `zerodha`, `env_loader` | Credential save | **Split** |
| `telegram_subscribe.py` | TG subscribe | `telegram_subscriptions`, `env_loader` | Token save | **Stay** |
| `autopilot.py` | Autopilot panel | `autopilot_status` | Button triggers | **Stay** |
| `navigation_bar.py` | Nav widgets | `theme`, `navigation` | No | **Stay** |
| `daily_playbook.py` | Playbook panel | `daily_playbook` | Overlaps OS | **Deprecate** |
| `mis_trade_advisory.py` | MIS panel | `mis_trade_advisory` | Overlaps OS | **Merge** |
| `strategy_synthesis.py` | Synthesis expander | `strategy_synthesis` | No | **Stay** |
| `suggestions_home.py` | Legacy home | learning, prep | Redirects to Home | **Deprecate** |

### UI infrastructure

| Module | Purpose | Verdict |
|--------|---------|---------|
| `ui/navigation.py` | Tab state machine | **Stay** |
| `ui/theme.py` | Nav registry, CSS | **Stay** |
| `ui/charts.py` | Plotly helpers | **Stay** |

---

## P. Scripts (`scripts/` — 19 files)

| Script | Purpose | Calls | Verdict |
|--------|---------|-------|---------|
| `autopilot_daily.py` | Master autopilot | all schedulers | **Stay** |
| `nightly_prep.py` | Manual nightly prep | `nightly_prep` | **Stay** |
| `post_close_scan.py` | Post-close scan | `post_close_scan_scheduler` | **Stay** |
| `validate_suggestions.py` | EOD validation | `eod_learning` | **Stay** |
| `morning_suggestions.py` | Morning TG | scheduler | **Stay** |
| `trade_selection_auto.py` | Auto selection | `trade_selection_scheduler` | **Stay** |
| `strategy_research.py` | Offline research | `strategy_research` | **Stay** |
| `watchlist_live_alerts.py` | Live alerts daemon | `watchlist_live_alerts` | **Stay** |
| `kite_auth.py` | CLI Kite login | `zerodha` | **Stay** |
| `live_options_coach_watch.py` | Terminal coach | `live_options_coach` | **Stay** |
| `live_equity_coach_watch.py` | Terminal equity coach | synthesis | **Stay** |
| `live_trade_signals.py` | Signal watcher | signals | **Stay** |
| `mis_eod_summary.py` | EOD summary | `mis_eod_summary` | **Stay** |
| `morning_briefing.py` | CLI briefing | `morning_briefing` | **Stay** |
| `prep_morning_nag.py` | Morning nag | `prep_morning_nag` | **Stay** |
| `session_reminders.py` | Reminders | `session_reminders` | **Stay** |
| `sip_reminder.py` | SIP reminder | `sip_reminders` | **Stay** |
| `morning_options_rescan.py` | Options rescan | scheduler | **Stay** |
| `daily_trading_guide.py` | Trading guide CLI | playbook | **Merge** → investment_os CLI |

---

## Q. Sibling projects (not in main app)

| Project | Modules | Purpose | Integration | Verdict |
|---------|---------|---------|-------------|---------|
| `interaction-investigator/` | 6 | Webex/CC log RCA | None | **Stay separate** |
| `local-call-insights/` | 2 | CSV call analytics | None | **Stay separate** |

---

## R. Reusable services (candidates for extraction)

| Service | Current location | Consumers | Extraction priority |
|---------|------------------|-----------|---------------------|
| **MarketDataService** | `providers/router.py` | 40+ modules | High |
| **JournalService** | 3 journal modules | OS, Track Record, learning | High |
| **LearningService** | 4 learning modules | EOD, watchlist, UI | High |
| **WatchlistService** | pins + history + persist | prep, OS, suggestions | Medium |
| **StrategySynthesisService** | `strategy_synthesis.py` | OS, MIS, coach | Medium |
| **NotificationService** | telegram_* | schedulers, UI | Medium |
| **SchedulerRegistry** | 6 schedulers + autopilot_status | scripts, UI | Medium |
| **RegimeService** | `market_regime` + macro | OS, advisory, watchlist | Low |

---

## S. Modules to merge (recommended)

| Merge target | Sources |
|--------------|---------|
| `journal/` package | `suggestion_journal`, `trade_journal`, `intraday_journal` |
| `learning/` facade | `suggestion_learning`, `watchlist_learning`, `options_watchlist_learning`, `threshold_tuning`, `confidence_calibration` |
| `telegram/formatters` | `suggestions_telegram`, `watchlist_telegram`, parts of `mis_eod_summary` |
| `zerodha/auth` + `zerodha/portfolio` + `zerodha/marketdata` | split from `zerodha.py` |
| `daily_driver` | `investment_os` absorbs `daily_playbook`, `session_advisory` data |

---

## T. Modules to split (recommended)

| Module | Split into |
|--------|------------|
| `alpha_ai_report.py` | `report_orchestrator` + section builders |
| `market_pulse_scan.py` | `universe_scanner` + `pulse_enrichment` |
| `watchlist_history.py` | `watchlist_repository` + `outcome_scorer` |
| `intraday_watchlist.py` | `pick_scorer` + `plan_builder` |
| `sideways_options_advisor.py` | strategy plugins |
| `telegram_subscriptions.py` | `subscriber_store` + `delivery_router` |
| `nse_options.py` | `chain_fetcher` + `chain_normalizer` |
| `autopilot_status.py` | `scheduler_registry` + `launchd_installer` |

---

## U. Test inventory (summary)

76 test modules mirroring analyzer features. Patterns:

- Heavy `unittest.mock.patch` for filesystem and APIs
- `test_e2e_smoke.py` — journal DB integration smoke
- Good coverage: watchlist loop, options gates, autopilot, navigation, investment_os
- Gaps: no load tests, limited provider integration tests, no Streamlit E2E

---

## Related documents

- [01_Project_Architecture.md](./01_Project_Architecture.md)
- [03_Technical_Debt.md](./03_Technical_Debt.md)
- [04_Improvement_Plan.md](./04_Improvement_Plan.md)
