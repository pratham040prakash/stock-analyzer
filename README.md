# Stock Suggestions (India)

Nightly **Entry · Stop · Target** picks for NSE MIS trading, with **hit-rate proof** after every session.

## Quick start (Mac — recommended)

```bash
cd stock-analyzer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add TELEGRAM_BOT_TOKEN at minimum
streamlit run app.py
```

1. Sidebar → **⚙️ Setup** — complete `.env` + Telegram subscribe  
2. Sidebar → **🤖 Autopilot** → **Enable autopilot on this Mac**  
3. Set Mac timezone to **Asia/Kolkata**

Open http://127.0.0.1:8501

## Daily loop (hands-free)

| Time (IST) | What happens |
|------------|----------------|
| **3:45 PM** | Quick scan → saves tomorrow's top 5 |
| **3:50 PM** | Scores today vs high/low → EOD hit summary Telegram |
| **4:30 PM** | Autopilot health check (alerts if something missed) |
| **8:50 AM** | Morning pick list Telegram |
| **9:10 PM** | Auto-star top 2 if you didn't pick |

Star **2 names** in the app to compare *your* trades vs full top 5.

## Main tabs

| Tab | Purpose |
|-----|---------|
| **Suggestions** | Quick scan, live cockpit (when open), hit tracking |
| **Track Record** | Win rate, history, CSV export |

**Local only:** Research tabs (Pulse, Options, Screener, etc.) — hidden on Streamlit Cloud.

## Configuration (`.env`)

| Variable | Purpose |
|----------|---------|
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) — subscribe in app sidebar |
| `ZERODHA_API_KEY` / `SECRET` / `ACCESS_TOKEN` | Optional — live LTP + holdings |
| `KITE_REDIRECT_URL` | Streamlit Cloud URL for OAuth |

Kite **market data subscription** (~₹500/mo) needed for real-time cockpit; equity suggestions work on Yahoo without it.

## Autopilot schedules

```bash
bash scripts/install_all_schedules.sh   # or use sidebar one-click
```

Manual test:

```bash
python scripts/autopilot_daily.py post_close --force
python scripts/autopilot_daily.py eod --force
python scripts/autopilot_daily.py morning --force
```

## Streamlit Cloud vs local

| | Cloud | Local Mac |
|---|-------|-----------|
| View track record | ✅ | ✅ |
| Autopilot schedules | ❌ | ✅ |
| NSE options | ❌ unreliable | ✅ |
| Live cockpit | Yahoo lag | Kite if subscribed |

Full nav is shown by default on cloud. Set `SIMPLE_CLOUD_MODE=1` in secrets only if you want a trimmed menu (Suggestions + Alpha AI).

## Docker (optional)

```bash
docker compose up --build
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Docs

- [GETTING_STARTED.md](GETTING_STARTED.md) — first-day checklist  
- [UPGRADE.md](UPGRADE.md) — developer roadmap  

**Not financial advice.** Hit target = price touched your level intraday, not guaranteed profit.
