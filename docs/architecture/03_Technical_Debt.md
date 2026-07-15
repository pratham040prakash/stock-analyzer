# 03 — Technical Debt

**Audit date:** 2026-07-15  
**Ranking:** Critical → High → Medium → Low  
**Format:** Each item includes **why** it matters and **where** it lives.

---

## Critical

### C1. No authentication or multi-tenant isolation

| Field | Detail |
|-------|--------|
| **Location** | `app.py`, entire Streamlit surface |
| **Why** | App assumes single trusted local user. Deploying to Streamlit Cloud or any shared host exposes Kite tokens, journal data, Telegram subscribers, and prefs with no access control. |
| **Impact** | Data breach, unauthorized trading context exposure, regulatory risk for SaaS |
| **Evidence** | No login middleware; `st.session_state` holds `kite_access_token` |

### C2. Secrets written to plaintext `.env` from UI

| Field | Detail |
|-------|--------|
| **Location** | `analyzer/env_loader.py`, `ui/components/kite_connect.py`, `ui/components/kite_auth.py`, `ui/components/telegram_subscribe.py` |
| **Why** | API keys, secrets, and access tokens persisted via `save_env_key()` to repo-adjacent `.env` without encryption, rotation policy, or OS keychain integration |
| **Impact** | Credential leak via backup, git mistake, or shared machine |
| **Evidence** | `save_env_key` writes directly to filesystem |

### C3. Streamlit security config disabled for local dev

| Field | Detail |
|-------|--------|
| **Location** | `.streamlit/config.toml` |
| **Why** | `enableXsrfProtection = false` and `enableCORS = false` — unsafe if same config ships to hosted deploy |
| **Impact** | CSRF on state-changing actions; cross-origin attacks on hosted instances |
| **Evidence** | Config committed to repo |

### C4. NSE scraping as production data dependency

| Field | Detail |
|-------|--------|
| **Location** | `analyzer/nse_session.py`, `analyzer/nse_options.py` |
| **Why** | Options chain and session data depend on unofficial NSE HTTP scraping — fragile, rate-limited, ToS risk, fails on cloud (403) |
| **Impact** | Core options features break silently; not viable for paid SaaS without licensed data |
| **Evidence** | `UPGRADE.md` Tier 3 lists licensed data as unresolved; `data_health` reports NSE errors |

### C5. P&L truth gap — coach vs broker

| Field | Detail |
|-------|--------|
| **Location** | `investment_os.py`, `live_options_coach.py`, `watchlist_eod.py` vs `trade_journal.py` |
| **Why** | System scores theoretical target/stop hits; user P&L on Zerodha may diverge. Review AI can reinforce false confidence |
| **Impact** | Learning loop tunes on proxy outcomes, not real money; product trust failure |
| **Evidence** | Conversation history: Jul 13 NIFTY CE "profit" was coach-only |

---

## High

### H1. Flat 163-module package with no bounded contexts

| Field | Detail |
|-------|--------|
| **Location** | `analyzer/*.py` |
| **Why** | All domains share one namespace; changes ripple unpredictably; onboarding new contributors is expensive |
| **Impact** | Regression risk, slow refactors, unclear ownership |
| **Evidence** | 19 import cycles; hub modules import 20+ peers |

### H2. Import cycles (19 documented)

| Field | Detail |
|-------|--------|
| **Location** | See § Circular dependency table below |
| **Why** | Lazy imports hide cycles but don't remove coupling; test isolation harder; risk of import-order bugs |
| **Impact** | Fragile startup, difficult extraction to services |
| **Mitigation today** | Lazy `def _gates(): import ...` pattern |

### H3. Triple journal system

| Field | Detail |
|-------|--------|
| **Location** | `suggestion_journal.py`, `trade_journal.py`, `intraday_journal.py` |
| **Why** | Three stores, two formats (SQLite + JSON), overlapping concepts — developers must know which to write/read |
| **Impact** | Review AI incomplete; learning uses only suggestion journal; user logs disconnected |

### H4. Overlapping daily drivers (6 modules)

| Field | Detail |
|-------|--------|
| **Location** | `investment_os`, `daily_playbook`, `mis_trade_advisory`, `daily_advisor`, `session_advisory`, `morning_briefing` |
| **Why** | Same questions answered in multiple places with slightly different logic |
| **Impact** | Verdict inconsistency; duplicate maintenance; user confusion |

### H5. God modules (>500 LOC, mixed responsibility)

| Field | Detail |
|-------|--------|
| **Location** | `alpha_ai_report.py` (1008), `options_watchlist_history.py` (713), `market_pulse_scan.py` (685), `watchlist_history.py` (643), `sideways_options_advisor.py` (626), `zerodha.py` (567), `intraday_watchlist.py` (550), `investment_os.py` (520), `nse_options.py` (519), `telegram_subscriptions.py` (499) |
| **Why** | SRP violation — fetch, score, persist, and format in same file |
| **Impact** | Untestable units, fear of change, merge conflicts |

### H6. Non-Home app rerun tax

| Field | Detail |
|-------|--------|
| **Location** | `app.py` lines 281–295 |
| **Why** | Every widget interaction re-runs Kite hydrate, WebSocket start, portfolio sync, 7 background hooks |
| **Impact** | Latency, duplicate API calls, battery/CPU on Mac |
| **Evidence** | No `st.cache_resource` for Kite client lifecycle |

### H7. SQLite + JSON without encryption or migration framework

| Field | Detail |
|-------|--------|
| **Location** | `data/suggestions/journal.db`, `data/intraday/*.json`, `data/telegram/subscribers.db` |
| **Why** | Schema evolves ad hoc (`init_journal`, `init_watchlist_history`); no Alembic/Flyway; no encryption |
| **Impact** | Data loss on schema change; PII exposure on disk |

### H8. No formal strategy plugin registry

| Field | Detail |
|-------|--------|
| **Location** | `strategy_synthesis.py`, `intraday_watchlist.py`, `sideways_options_advisor.py` |
| **Why** | Strategies are hardcoded branches; JSON tuning only adjusts thresholds, not strategy types |
| **Impact** | OCP violation; commercial "marketplace" vision blocked |

### H9. `wealth_plan.py` built but unwired

| Field | Detail |
|-------|--------|
| **Location** | `analyzer/wealth_plan.py` — only `tests/test_wealth_plan.py` imports |
| **Why** | Dead production code creates false sense of feature completeness |
| **Impact** | Maintenance cost; docs/product drift |

### H10. Live Options Coach 5-second polling

| Field | Detail |
|-------|--------|
| **Location** | `ui/pages/live_options_advisor.py` |
| **Why** | Aggressive `@st.fragment(run_every=5s)` hammers providers |
| **Impact** | Kite rate limits, UI jank, Mac fan spin |

---

## Medium

### M1. UI orchestration components too thick

| Field | Detail |
|-------|--------|
| **Location** | `ui/components/intraday_watchlist.py` (~531 LOC), `ui/components/options_expiry_watchlist.py` (~515 LOC) |
| **Why** | Business orchestration lives in UI layer |
| **Impact** | Can't reuse from CLI/autopilot without Streamlit; testing requires UI mocks |

### M2. Duplicate learning tuners (4+ modules)

| Field | Detail |
|-------|--------|
| **Location** | `watchlist_learning`, `options_watchlist_learning`, `threshold_tuning`, `confidence_calibration` |
| **Why** | No unified learning API; EOD cycle must know all tuners |
| **Impact** | Missed tuning steps when adding new asset class |

### M3. Duplicate options advisors (4 modules)

| Field | Detail |
|-------|--------|
| **Location** | `options_signal`, `sideways_options_advisor`, `live_options_coach`, `options_entry_gate` |
| **Why** | Shared gate logic copied; sideways advisor is 626 LOC monolith |
| **Impact** | Inconsistent CE/PE guidance between tabs |

### M4. Legacy `watchlist.py` still exposed

| Field | Detail |
|-------|--------|
| **Location** | `analyzer/watchlist.py`, `ui/pages/watchlist.py` (Batch Scanner) |
| **Why** | Superseded by `intraday_watchlist` + `screener` but still in nav |
| **Impact** | User-facing duplicate; maintenance burden |

### M5. `providers/router.py` lacks interface contract

| Field | Detail |
|-------|--------|
| **Location** | `analyzer/providers/` |
| **Why** | If/else routing, no `Protocol`/`ABC`; can't mock consistently or add TrueData |
| **Impact** | DIP violation; licensed data swap is invasive |

### M6. Background hooks in `app.py` business layer

| Field | Detail |
|-------|--------|
| **Location** | `app.py` `_maybe_*` functions |
| **Why** | Scheduler logic embedded in UI entry point |
| **Impact** | Double execution risk (app + launchd); hard to test EOD independently |

### M7. Telegram split across 4 modules

| Field | Detail |
|-------|--------|
| **Location** | `telegram_notify`, `telegram_subscriptions`, `suggestions_telegram`, `watchlist_telegram` |
| **Why** | Formatting and delivery concerns mixed |
| **Impact** | Inconsistent message style; duplicate subscriber lookups |

### M8. Autopilot macOS-only coupling

| Field | Detail |
|-------|--------|
| **Location** | `autopilot_status.py` (launchd plist install) |
| **Why** | Scheduler install logic in analyzer module |
| **Impact** | Not portable to Linux server cron without fork |

### M9. Alpha AI LLM optional but not guarded uniformly

| Field | Detail |
|-------|--------|
| **Location** | `alpha_ai_llm.py`, `alpha_ai_report.py` |
| **Why** | Missing key fails at various depths; cost/latency not capped |
| **Impact** | Poor UX on misconfiguration; surprise API bills |

### M10. Test coverage gaps

| Field | Detail |
|-------|--------|
| **Location** | `tests/` — 76 files but no load/integration suite |
| **Why** | Heavy mocking means real Kite/NSE paths untested |
| **Impact** | Production regressions on provider changes |

### M11. `candle_narrative` ↔ `options_signal` cycle

| Field | Detail |
|-------|--------|
| **Location** | `analyzer/candle_narrative.py`, `analyzer/options_signal.py` |
| **Why** | Chart narrative pulls options; options pulls narrative |
| **Impact** | Extraction/refactor hazard |

### M12. Inconsistent session date logic

| Field | Detail |
|-------|--------|
| **Location** | `watchlist_history.session_target_date`, `market_session`, `trade_selection` |
| **Why** | Multiple "trade date" computations; edge cases around holidays |
| **Impact** | Stale pins, wrong selection file |

### M13. HTML injection via `unsafe_allow_html=True`

| Field | Detail |
|-------|--------|
| **Location** | `unified_hub.py`, `investment_os_ui.py`, many components |
| **Why** | Symbol names and journal text embedded in HTML without systematic escaping (partial `html.escape` in OS UI only) |
| **Impact** | Low risk today (local user); XSS if multi-user |

### M14. No observability stack

| Field | Detail |
|-------|--------|
| **Location** | `structured_log.py` (minimal), `UPGRADE.md` Tier 3 |
| **Why** | No metrics, tracing, health endpoint, or error aggregation |
| **Impact** | Incidents invisible until user reports |

### M15. Sibling apps share no code with main product

| Field | Detail |
|-------|--------|
| **Location** | `interaction-investigator/`, `local-call-insights/` |
| **Why** | Duplicate Streamlit boilerplate; pollutes repo perception |
| **Impact** | Not debt per se, but confuses product boundary |

---

## Low

### L1. `macro_cache.py` redundant with `pulse_cache.py`

| Field | Detail |
|-------|--------|
| **Why** | Two cache patterns for macro data |
| **Impact** | Minor confusion |

### L2. `risk.py` (45 LOC) overlaps `market_risk.py`

| Field | Detail |
|-------|--------|
| **Why** | Thin duplicate |
| **Impact** | Import ambiguity |

### L3. `whatsapp_export.py` — likely unused

| Field | Detail |
|-------|--------|
| **Why** | No UI reference found; Telegram is primary channel |
| **Impact** | Dead code candidate |

### L4. `trade_journal_link.py` (19 LOC)

| Field | Detail |
|-------|--------|
| **Why** | Glue for split journal; obsolete after merge |
| **Impact** | Negligible |

### L5. Large CSS blocks in `theme.py`

| Field | Detail |
|-------|--------|
| **Why** | 300+ lines inline CSS per rerun |
| **Impact** | Minor parse cost |

### L6. `README` / `GETTING_STARTED` drift from Home-first flow

| Field | Detail |
|-------|--------|
| **Why** | Docs still describe Suggestions-first workflow |
| **Impact** | Onboarding friction |

### L7. `tmp/` artifacts in repo

| Field | Detail |
|-------|--------|
| **Why** | `tmp/*.md`, `tmp/*.log` untracked but present — workspace clutter |
| **Impact** | Accidental commit risk |

### L8. `penny_picks` tab niche surface

| Field | Detail |
|-------|--------|
| **Why** | Contradicts beginner/small-trader safety messaging |
| **Impact** | Product positioning noise |

### L9. Multiple install shell scripts

| Field | Detail |
|-------|--------|
| **Location** | `scripts/install_*.sh` (5+ scripts) |
| **Why** | Overlapping launchd installers |
| **Impact** | Operator confusion |

### L10. No `pyproject.toml` / modern packaging

| Field | Detail |
|-------|--------|
| **Why** | `requirements.txt` only; no editable install, no ruff/mypy in standard config |
| **Impact** | Tooling friction for contributors |

---

## Circular dependency table

| Cycle | Severity | Modules |
|-------|----------|---------|
| Kite options trinity | High | `kite_status` ↔ `kite_options_chain` ↔ `nse_options` |
| Watchlist learn loop | High | `intraday_watchlist` → `watchlist_learning` → `options_watchlist_learning` → `options_watchlist_history` → `watchlist_history` → `intraday_watchlist` |
| Pin/select/history | High | `trade_selection` ↔ `watchlist_pins` ↔ `watchlist_history` |
| EOD scoring | Medium | `watchlist_history` ↔ `watchlist_eod` |
| Narrative/options | Medium | `candle_narrative` ↔ `options_signal` |
| Pulse/affordable | Medium | `affordable_invest` → `market_pulse_scan` → … → `affordable_invest` |
| Macro/gift | Low | `india_macro` ↔ `gift_nifty` |
| Learning/features | Low | `watchlist_learning` ↔ `suggestion_features` |

---

## SOLID violations summary

| Principle | Severity | Example |
|-----------|----------|---------|
| Single Responsibility | High | `zerodha.py`, `alpha_ai_report.py`, `watchlist_history.py` |
| Open/Closed | High | `strategy_synthesis.py` — new pillar = code change |
| Liskov Substitution | Medium | No provider interface |
| Interface Segregation | Medium | UI imports whole analyzer hubs |
| Dependency Inversion | High | Direct yfinance/kiteconnect throughout |

---

## Security debt summary

| ID | Issue | Rank |
|----|-------|------|
| S1 | No auth | Critical |
| S2 | Plaintext secrets on disk | Critical |
| S3 | XSRF disabled | Critical |
| S4 | Token in session state | High |
| S5 | No HTTPS enforcement (local) | Medium (expected local) |
| S6 | SQLite PII unencrypted | High |
| S7 | NSE scrape legal/ToS | High |
| S8 | `unsafe_allow_html` | Medium |
| S9 | No rate limiting on Telegram subscribe | Medium |
| S10 | No input validation on journal text fields | Low |

---

## Performance debt summary

| ID | Issue | Rank |
|----|-------|------|
| P1 | Full app rerun tax (non-Home) | High |
| P2 | 5s options coach fragment | High |
| P3 | Cold market_pulse_scan | High |
| P4 | Deep synthesis on Home | Medium |
| P5 | Alpha AI full report | Medium |
| P6 | WebSocket + REST duplicate LTP | Medium |
| P7 | Screener sequential fetches | Medium |
| P8 | Large pulse cache deserialize | Low |

---

## Debt scorecard

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Security | 3 | 3 | 4 | 1 |
| Architecture | 1 | 5 | 6 | 2 |
| Data integrity | 1 | 2 | 2 | 0 |
| Performance | 0 | 2 | 4 | 2 |
| Code quality | 0 | 2 | 5 | 5 |
| Documentation | 0 | 1 | 0 | 1 |
| **Total** | **5** | **15** | **21** | **11** |

---

## Related documents

- [01_Project_Architecture.md](./01_Project_Architecture.md)
- [02_Module_Inventory.md](./02_Module_Inventory.md)
- [04_Improvement_Plan.md](./04_Improvement_Plan.md)
