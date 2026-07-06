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

Confirm **7/7 schedules** and Mac timezone **Asia/Kolkata**.

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

1. [developers.kite.trade](https://developers.kite.trade/) — redirect URL `http://127.0.0.1:8501`
2. Add API key/secret to `.env`
3. Sidebar → Login with Zerodha
4. Subscribe to **market data API** on Zerodha for real-time cockpit
