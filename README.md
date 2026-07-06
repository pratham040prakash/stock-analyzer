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
| **Intraday** | MIS workflow — **Prep all**, top 5 equity, Nifty/Bank Nifty CE/PE, track record, learning |
| **Live Charts** | All Nifty stocks — 1m narratives + buy/sell grid (60s) |
| **NSE Options** | Live CE/PE chain, PCR, max pain |
| **Batch Scanner** | Parallel multi-ticker batch scanner |
| **Zerodha Portfolio** | Holdings + **portfolio risk** (β, sectors, concentration) |
| **Backtest** | Long-only strategy vs buy-hold and Nifty; options premium history (experimental) |
| **Varsity TA** | 22 cached Zerodha chapters |

## Intraday MIS workflow

1. **Intraday** tab → **Prep all tonight** (Quick scan + CE/PE + Telegram in one click)
2. Or step-by-step: **Quick scan** → **Load CE/PE** → **Send MIS prep to Telegram**
3. Bedtime **prep checklist**: equity ✓ · options ✓ · telegram ✓ · **2 trades** ✓ · MIS checklist
4. **9:15** / **3:15** / **3:20** Telegram session reminders (if subscribed)
5. After close → **EOD summary** Telegram (~3:35 PM) + **Score watchlist** in app
6. **Scheduled jobs** (macOS, system time = IST):

```bash
bash scripts/install_all_schedules.sh        # one-shot: all jobs below
bash scripts/install_nightly_schedule.sh   # 9:00 PM — Prep all + Telegram
bash scripts/install_trade_selection_auto.sh  # 9:10 PM — auto-pick top 2 if not starred
bash scripts/install_prep_morning_nag.sh   # 8:45 AM — nag if prep incomplete
bash scripts/install_session_reminders.sh  # 9:15 / 3:15 / 3:20 — open & square-off
bash scripts/install_live_alerts_schedule.sh  # every 5m — entry/stop/target on your 2
bash scripts/install_eod_schedule.sh       # 3:35 PM — MIS EOD summary
bash scripts/install_morning_schedule.sh   # 8:30 AM — morning briefing
```

Learning tightens screening when stops dominate; it **does not guarantee 100% wins**.

**Position sizing:** Top 5 table shows **Shares** and **Risk ₹** using **per-trade budget** (MIS pool ÷ 2) capped by your risk %. Telegram prep includes share counts. **Star 2** names on Intraday so reminders, live alerts & EOD focus on those only.

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
4. Choose alert types: morning briefing, EOD track record, optional pulse, **SIP reminders**.

No `TELEGRAM_CHAT_ID` required. Subscribers are stored in `data/telegram/subscribers.db`.

**SIP reminders:** Save a goal in **SIP & Goals → Export & share**, enable monthly reminder, and tick **SIP reminders** in the sidebar. Schedule:

```bash
python scripts/sip_reminder.py   # runs on reminder day (1–28)
```

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
