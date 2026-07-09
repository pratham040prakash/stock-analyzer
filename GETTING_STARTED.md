# Getting started

## 10-minute checklist

### 1. Install and run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

### 2. Telegram (required for autopilot alerts)

1. Create bot via [@BotFather](https://t.me/BotFather) → copy token to `.env` as `TELEGRAM_BOT_TOKEN`
2. App sidebar → **Telegram alerts** → **Open in Telegram** → press **Start**
3. Back in app → **Verify subscription**

### 3. Enable Autopilot (Mac)

Sidebar → **🤖 Autopilot** → **Enable autopilot on this Mac**

Confirm **10/10 schedules** and Mac timezone **Asia/Kolkata**.

### 4. First Quick scan

After market close (or tap **Quick scan now** in Autopilot):

- Saves **top 5** with Entry · Stop · Target for tomorrow
- Star your **top 2** (or wait for 9:10 PM auto-select)

### 5. Next day

- **8:50 AM** — pick list on Telegram  
- **During session** — live OR/ladder on **Suggestions**  
- **3:50 PM** — "Did targets hit?" on Telegram + app

### 6. Proof

- **Suggestions** — weekly metric: "12 suggestions, 7 hit target (58%)"  
- **Track Record** — export CSV  

## FAQ

**Why is the dashboard empty?**  
No scans yet. Run Quick scan or enable Autopilot.

**Cloud vs local?**  
Use **local Mac** for autopilot and options. Cloud is for checking history.

**Hit target vs profit?**  
Hit = session high/low touched your target level. Not the same as your P&L.

**Kite token expired?**  
Re-login sidebar → Zerodha. Token resets ~6 AM IST daily.

## Optional: Kite live data

1. [developers.kite.trade](https://developers.kite.trade/) — create app type **Connect** (not Personal)
2. Add credits (₹500/mo) — Personal apps cannot use quote/historical APIs even with credits
3. Redirect URL `http://127.0.0.1:8501` — add API key/secret to `.env`
4. Sidebar → Login with Zerodha
5. **📡 Data health** should show Kite: **ok** and intraday source **Kite**

## Suggestion intelligence (6-month patterns)

Once after setup (and optionally monthly):

- **Track Record** → **6mo pattern research**, or  
- `python scripts/strategy_research.py`

This mines Nifty 50 daily + session patterns and updates live pick ranking weights.  
Quick scan then shows **Conf.** % on each suggestion. Daily journal learning still runs after close.
