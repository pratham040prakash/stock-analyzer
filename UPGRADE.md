# Production upgrade path

Roadmap to reach **Sensibull / Chartink Pro / Bloomberg**-class reliability.

## Tier 1 — Done in this release

| Item | Status |
|------|--------|
| **Kite-first data router** | `analyzer/providers/` — live candles + LTP when `.env` token set |
| **UI modularization** | `ui/theme.py`, `ui/components/`, `ui/pages/live_charts.py` |
| **Walk-forward backtest** | `run_walk_forward()` in `analyzer/backtest.py` |
| **Expanded tests + CI** | `tests/`, `.github/workflows/ci.yml` |
| **Quiet NSE 403** | Equity quote blocks no longer spam the banner |

## Tier 2 — Done

| Item | Status |
|------|--------|
| **Split `app.py` pages** | All tabs in `ui/pages/`; `app.py` is router + sidebar (~140 lines) |
| **Pin dependencies** | `requirements-lock.txt`; CI uses lockfile |
| **Walk-forward UI** | Backtest tab checkbox + fold table |
| **Gift Nifty pre-open** | `analyzer/gift_nifty.py` — Kite Nifty fut → Yahoo gap proxy |
| **Kite WebSocket all Nifty 50** | `start_kite_ticker_on_app_start()` when NSE open |

## Tier 3 — In progress

| Item | Status |
|------|--------|
| **Suggestion journal** | `analyzer/suggestion_journal.py` — SQLite log from Pulse + Advisor |
| **Outcome validation** | `analyzer/suggestion_validator.py` + `scripts/validate_suggestions.py` |
| **Daily learning** | `analyzer/suggestion_learning.py` + **Track Record** tab |
| **Licensed data** | TrueData / GDFL / NSE NOW for tick + OI without scraping |
| **Signal registry** | YAML-defined strategies with versioned backtests in CI |
| **Observability** | structured JSON logs, health endpoint, Sentry |
| **Deploy** | Docker + auth (Streamlit Cloud or Fly.io with OAuth) |

### Daily suggestion loop (EOD)

```bash
# After 3:30 PM IST — score yesterday's picks vs actual moves
python scripts/validate_suggestions.py
```

Cron example (4 PM IST weekdays): `0 16 * * 1-5 cd /path/to/stock-analyzer && python scripts/validate_suggestions.py`

Journal DB: `data/suggestions/journal.db` (gitignored).

Auto-tuned gates: `data/suggestions/thresholds.json` — updated after EOD validation when enough scored picks exist.

## Tier 4 — Terminal parity

1. **Options analytics depth** — IV rank history, strategy builder (iron condor, straddle)
2. **Screener DSL** — Chartink-style filter language compiled to pandas
3. **Alert engine** — sub-second Kite triggers → Telegram/Webhook
4. **Multi-user** — per-user watchlists, Kite tokens in vault

## Kite setup (required for live data)

```bash
# .env
ZERODHA_API_KEY=your_key
ZERODHA_API_SECRET=your_secret
ZERODHA_ACCESS_TOKEN=daily_token_from_kite_login
```

Re-login daily; token expires at ~6 AM IST. Market data subscription required on Zerodha.

## Honest gap vs Bloomberg

Bloomberg / Refinitiv provide **normalized global data, news, estimates, and compliance**. This tool targets **Indian retail F&O + TA** — comparable to Sensibull for options context and Chartink for scans, not institutional macro terminals.
