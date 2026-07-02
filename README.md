# Stock Analyzer (India)

Personal Indian market assistant: multi-timeframe TA, NSE options, Zerodha holdings, global spillover, and Varsity TA knowledge.

## Quick start

```bash
cd stock-analyzer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open http://127.0.0.1:8501 — sidebar **India (Auto)**.

## Tabs

| Section | Purpose |
|---------|---------|
| **Market Pulse** | Nifty 50 scan — intraday + swing + long; live 30s strip when open |
| **Daily Advisor** | Holdings briefing + swing/long ideas |
| **Global Markets** | World indices → Nifty bias (30s refresh) |
| **Single Stock** | TA + fundamentals + position sizing |
| **Intraday** | 5m chart + candle stories (30s); **Kite live** when configured |
| **Live Charts** | All Nifty stocks — 1m narratives + buy/sell grid (60s) |
| **NSE Options** | Live CE/PE chain, PCR, max pain |
| **Watchlist** | Parallel batch scanner |
| **Zerodha Portfolio** | Holdings + **portfolio risk** (β, sectors, concentration) |
| **Backtest** | Long-only strategy vs buy-hold and Nifty |
| **Varsity TA** | 22 cached Zerodha chapters |

## Configuration (`.env`)

```bash
cp .env.example .env
```

| Variable | Purpose |
|----------|---------|
| `ZERODHA_API_KEY` / `SECRET` / `ACCESS_TOKEN` | Kite live LTP, holdings, margins |
| `TELEGRAM_BOT_TOKEN` | Bot from [@BotFather](https://t.me/BotFather) — users **subscribe in the app sidebar** |
| `TELEGRAM_CHAT_ID` | Optional legacy fixed chat (skip if using in-app subscribe) |
| `HOLDINGS_CSV` | Path to holdings CSV for scheduled morning briefing |

### Morning briefing (8:30 AM IST)

```bash
# One-off
python scripts/morning_briefing.py --send-telegram

# macOS daily schedule (uses system local time — set Mac to IST)
bash scripts/install_morning_schedule.sh
```

CLI: `python cli.py --morning-briefing` or `--send-morning-telegram`

Redirect URL for Kite: `http://127.0.0.1:8501`

### Telegram alerts (in-app subscribe)

1. Add `TELEGRAM_BOT_TOKEN` to `.env` (from @BotFather).
2. In the app **sidebar → Telegram alerts**, tap **Open in Telegram** and press **Start**.
3. Return to the app and tap **Verify subscription**.
4. Choose alert types: morning briefing, EOD track record, optional pulse.

No `TELEGRAM_CHAT_ID` required. Subscribers are stored in `data/telegram/subscribers.db`.

## CLI

```bash
python cli.py RELIANCE --market india
python cli.py --watchlist RELIANCE,TCS --market india
python cli.py --pulse-scan --market india
python cli.py --global-impact
python cli.py --daily-briefing holdings.csv
python cli.py --telegram-test
python cli.py --send-morning-telegram --market india
python cli.py --morning-briefing
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Data & limits

- **Kite (preferred)** — live 1m/5m candles + LTP when `ZERODHA_ACCESS_TOKEN` in `.env`
- **Yahoo Finance** — daily/intraday fallback (~15–20 min lag on 5m)
- **NSE** — option chains, FII/DII (cookie session, may break)
- See **[UPGRADE.md](UPGRADE.md)** for path to terminal-grade stack
- **Not financial advice** — verify on Kite before trading

## Performance notes

- Full Nifty 50 scan: 2–5 min (cached 15 min)
- Global/macro live data: cached 60s in-memory (shared across tabs)
- Only the **active section** loads (radio nav) — avoids hidden tab API spam
