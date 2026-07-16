# Local Call Insights

**Dead-simple call report for Indian small teams** — upload a CSV from any dialer, get instant insights + WhatsApp summary.

No Splunk. No Cisco. No enterprise setup. Works with Excel exports from Exotel, Ozonetel, Knowlarity, or manual sheets.

## Run locally

```bash
cd local-call-insights
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Who pays locally (India)

| Customer | Problem you solve | Price |
|----------|-------------------|-------|
| Small BPO (10–50 agents) | Owner gets daily report in 2 min | **₹999–2,999/mo** |
| Insurance / loan calling team | "Why so many missed calls?" | **₹499/report** or monthly |
| Real estate / ed-tech sales | Agent performance without Excel hell | **₹1,499/mo** |
| Local dialer reseller | White-label add-on for clients | **₹5k–15k/mo** rev share |

## How to sell (local, not LinkedIn enterprise)

1. **WhatsApp groups** — BPO owners, dialer reseller groups  
2. **JustDial / local listings** — "Call center daily report tool"  
3. **Walk-in to 5 small offices** in your city with laptop + sample CSV  
4. **Ozonetel / Exotel partner forums** — "I turn your CSV export into daily insights"  
5. **UPI payment** — PhonePe/GPay for ₹499 first report, upsell monthly  

### Pitch (Hindi + English)

```
Aapke dialer se CSV export karo → 1 minute mein report:
- kitni calls answer hui
- kitni miss / fail
- kaun sa agent weak hai
- WhatsApp pe owner ko bhej do

₹999/month — pehla report ₹499 mein try karo.
```

### DM / WhatsApp script

```
Hi, I help small call teams understand daily call data without Excel.

Send your today's CSV export (agent, status, duration).
I'll send back:
1) answer rate
2) top failure reasons  
3) agent-wise summary

First report ₹499. Monthly auto-report ₹999.
```

## What makes this "local market" friendly

- Works offline on your laptop (demo at client office)  
- Accepts messy CSV column names  
- WhatsApp-ready text output (how owners actually communicate)  
- Low price point (₹ not $)  
- No API integration needed to start  

## Sample columns supported

Auto-detects: `agent`, `status`, `duration`, `hangup_reason`, `phone`, `date`, `time`

## Upgrade path (charge more later)

- [ ] Auto email report every evening  
- [ ] Hindi UI toggle  
- [ ] Multi-file weekly trends  
- [ ] Logo on PDF for white-label resellers  

## Cisco employee note

This tool uses **only generic CSV exports** — safe to build and demo with synthetic/sample data on personal time. Still check your employer OBA policy before taking paid clients.
