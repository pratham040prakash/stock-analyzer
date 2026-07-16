# WOW Experience Redesign

**Role:** Chief Product Officer  
**Date:** 2026-07-16  
**Status:** Proposal — **do not implement until approved**  
**Constraint:** Product and UX only. No backend or engine changes assumed in this document.

---

## Executive Summary

This application has world-class analytical depth trapped inside dashboard thinking.

The user does not want more information. They want **less thinking**.

When Pratham opens the app at 9:00 AM, he should feel:

> *"This app already did the thinking for me."*

That is not a UI polish problem. It is a **product identity** problem.

**Current state:** We moved Home from a data dashboard to five question-cards. That is better. It is still not WOW. Cards are still widgets. Questions are still sections. The user still reads an app instead of hearing an advisor.

**Target state:** One primary message per screen. Natural language. Clear permission to close the app when nothing needs doing. Every surface ends with an action or a release ("you're done for today").

**North star:**

> Open the app. Read for 20 seconds. Know whether to trade, what to watch, what to ignore — or close the app with confidence.

---

## Design Principles (Non-Negotiable)

### 1. One primary message

Every screen has **one** thing the user must remember. Not five cards. Not ten metrics. One sentence.

### 2. Decision before data

Ask: *What decision is the user trying to make?*  
Never ask: *What information can we show?*

### 3. Advisor voice, not dashboard voice

| Never say | Say instead |
|-----------|-------------|
| Context / Evidence / Decision Engine | "Here's why we think so" |
| Confidence 72% | "We're fairly sure" / High / Medium / Low |
| Investment OS | *(remove entirely)* |
| Capital / Exposure / Risk budget | "How much you could lose today" |
| Learning / Calibration | "How often we were right" |
| Synthesis / Evidence packet | "What we looked at" |
| Market regime / Risk mode | "Markets feel cautious today" |
| Holdings reviewed: 12 | "Your 12 stocks look fine" |

### 4. Every screen ends with an action — or permission to stop

**Bad:** Portfolio · Healthy  
**Good:** Your portfolio is healthy. No changes required today. **Close the app.**

**Bad:** Best Opportunity · RELIANCE  
**Good:** Today's only high-conviction setup is RELIANCE. **Review setup →**

### 5. Reduce cognitive load ruthlessly

If it does not change what the user does in the next 30 minutes, it is secondary or hidden.

### 6. Trust over features

The user should think *"I trust this app"* — not *"This app has a lot of features."*

---

## The WOW Morning (Gold Standard)

This is what Home must become — not five cards, **one letter**:

```
Good morning, Pratham.

Today is a WAIT day.

Do not deploy fresh capital before 9:45 AM.

Your existing portfolio looks healthy.

There is only ONE stock worth watching today.

RELIANCE

If it breaks ₹2,850 after 9:45 AM, buy.

Otherwise, close the app.

────────────────────────
Estimated reading time: 20 seconds.
```

**What makes this work:**

- Personalized greeting (name, time of day)
- Verdict in plain English (WAIT day — not "DEFENSIVE" or "72% confidence")
- One timing rule (9:45 AM — not session phase metadata)
- Portfolio in one line (healthy — no exposure %, no P&L table)
- One watch item (not a watchlist table)
- Conditional action (if/then — not entry/stop/target grid)
- Explicit release ("close the app")
- Reading time sets expectation: this is brief on purpose

**Current Home gap:** We have five question-cards with expanders, confidence labels, and multiple buttons. The user still scans a dashboard. They do not feel spoken to.

---

## Application Redesign — Advisor, Not Dashboard

### From 20 pages → 4 daily modes + 2 accountability surfaces

The product should feel like talking to one advisor with four specialties:

| Mode | User question | Replaces (today) |
|------|---------------|------------------|
| **Today** | What should I do this morning? | Home, morning cockpit, global bias snippets, MIS strip duplicates |
| **Trade** | I have a green light — show me the plan | Suggestions, Live Charts (equity), Live Options Coach |
| **Portfolio** | What should I do with what I own? | My Portfolio, Daily Advisor, portfolio sections on Home |
| **Ask** | Should I buy/hold/sell this stock? | Single Stock, Alpha AI, Compare |
| **Results** *(weekly, not daily)* | Was the app right? | Track Record, journal, calibration |
| **Settings** *(setup once)* | Connect broker, set risk, alerts | Sidebar Setup, Autopilot, Telegram, broker wizard, Risk & Goals prefs |

### Remove from daily navigation

These are **tools**, not **advisor conversations**. Hide behind "More" or contextual links:

| Surface | Why remove from daily path |
|---------|---------------------------|
| Market Pulse | 2-minute scan duplicating Today + Trade; expert-only density |
| Live Charts | Grid of 200 verdicts — opposite of "one message" |
| Batch Scanner | Bulk data; belongs in Ask → "Compare these" |
| Screener | Discovery tool; not a morning decision |
| Penny Picks | Niche preset inside Ask/Screener |
| NSE Options (standalone) | Subsumed by Trade → Options |
| Global Markets | One paragraph on Today is enough |
| Varsity TA | Education library — link from signals, not a tab |
| Backtest | Validation for skeptics — Settings → Advanced |
| SIP & Goals | Long-horizon planning session — not daily |

### Simple mode becomes default mode

New users see: **Today · Trade · Portfolio · Ask · Results · Settings** (6 items).  
Power users opt into Market Pulse, Screener, Backtest, etc.

---

## Screen-by-Screen Redesign

For each screen: the decision the user is making, the one sentence they leave with, what to cut, headline, secondary, and closing action.

---

### 1. Today (Home)

**Decision:** Should I trade today, watch one thing, or close the app?

**One sentence to remember:** *"Today is a WAIT day — only watch RELIANCE above ₹2,850 after 9:45."*

| Element | Redesign |
|---------|----------|
| **Headline** | Personalized greeting + verdict in plain English ("Today is a WAIT day") |
| **Secondary** | Portfolio one-liner + single watch setup with if/then trigger |
| **Remove** | Five separate cards; confidence labels; entry/stop/target grid; broker card (move to Portfolio or Settings); "Why this call?" expander on default view; search bar competing with Ask mode |
| **End action** | Primary: **Open trade plan** (only if ACT) OR **Review RELIANCE** (only if one setup) OR **You're done — close the app** (WAIT/PASS) |

**WOW vs current:** Current Home asks five questions in five cards. WOW Home is **one narrative** with at most one button.

---

### 2. Trade (Suggestions)

**Decision:** Which exact trade am I executing today, and when do I exit?

**One sentence to remember:** *"Your plan today is RELIANCE long — enter above ₹2,850, stop ₹2,820, target ₹2,920."*

| Element | Redesign |
|---------|----------|
| **Headline** | "Your trade plan for [date]" — starred pick(s) only, max 2 |
| **Secondary** | Live session status in one line ("Market open · wait until 9:45") |
| **Remove** | Weekly hit-rate strip; autopilot loop strip; morning cockpit duplicate; "Stock picks" subheader; expanders for capital checklist, auto-learning, strategy tuning; full watchlist table before starring; scoring UI (belongs on Results); phase/engine banners |
| **End action** | **Log this trade** / **Open in Kite** / **Back to Today** |

**Dashboard language to kill:** "Score today's picks", "Auto-learning & strategy tuning", "Combined score", "Phase banner"

---

### 3. Results (Track Record)

**Decision:** Can I trust this app's advice over time?

**One sentence to remember:** *"Last 7 days we were right on 4 of 6 stock calls."*

| Element | Redesign |
|---------|----------|
| **Headline** | Plain hit rate sentence — not "Hit rate dashboard" |
| **Secondary** | One example: best call / worst call this week |
| **Remove** | Confidence calibration panel (default view); pulse journal validation gates; threshold tuning metrics; CSV export buttons above fold; multiple sub-panels (equity + options + journal) on one scroll |
| **End action** | **Score yesterday's picks** (after 3:30 PM only) OR **Nothing to score — see you tomorrow** |

**Rename user-facing:** Track Record → **"Did we get it right?"**

---

### 4. Portfolio (My Portfolio + Daily Advisor merged)

**Decision:** Do I need to change anything in what I already own?

**One sentence to remember:** *"Your portfolio is healthy — hold everything, trim only XYZ if it breaks support."*

| Element | Redesign |
|---------|----------|
| **Headline** | Advisor briefing first — not "How to add holdings" |
| **Secondary** | Holdings table — collapsed or below fold |
| **Remove** | Manual entry radio as first UI; Kite watchlist mirror before briefing; live 15s refresh panel as hero; portfolio risk tables before narrative; duplicate Daily Advisor tab; "Analyze my portfolio" as primary CTA before recommendation |
| **End action** | **No changes needed** OR **Review [stock]** OR **Connect Zerodha** (if empty) |

**Dashboard language to kill:** "Holdings reviewed: 12", "Market verdict", "Global bias" as metrics row

---

### 5. Ask — Fast (Single Stock)

**Decision:** Should I buy, hold, or avoid this one stock right now?

**One sentence to remember:** *"RELIANCE — wait for pullback to ₹2,800 before buying."*

| Element | Redesign |
|---------|----------|
| **Headline** | Ticker + one-word call (Buy / Hold / Wait / Avoid) |
| **Secondary** | Entry zone, stop, target — three numbers max |
| **Remove** | Price/combined/technical/fundamental metric rows before verdict; Alpha vs index chart above fold; delivery/earnings/IV banners before recommendation; position sizing calculator before verdict; options verdict footer on equity ask |
| **End action** | **Add to today's watch** OR **Open full research** (deep mode) OR **Back to Today** |

---

### 6. Ask — Deep (Alpha AI)

**Decision:** Is this a good business to own for 3+ years?

**One sentence to remember:** *"TCS is a hold — quality business, fairly valued, wait for ₹3,800 to add."*

| Element | Redesign |
|---------|----------|
| **Headline** | Recommendation + grade in sticky summary — keep Executive Summary pattern |
| **Secondary** | Buy decision YES/NO/WAIT — already correct |
| **Remove** | Evidence expander label; radar checklist above buy decision; 15 sections before user sees verdict; "Confidence %" in hero — use High/Medium/Low; export buttons above fold |
| **End action** | **Buy / Wait / Avoid** + **Compare with another stock** |

**Note:** Alpha AI is closest to correct IA. Trim section count for default view; everything else behind "Full report".

---

### 7. Ask — Compare

**Decision:** Which of these 2–4 stocks wins?

**One sentence to remember:** *"Among RELIANCE, TCS, and INFY — TCS wins for quality; RELIANCE for today's trade."*

| Element | Redesign |
|---------|----------|
| **Headline** | "Winner: TCS" with one-line why |
| **Secondary** | Comparison table — collapsed |
| **Remove** | Full table before winner declaration |
| **End action** | **Open winner in Ask** |

**Verdict:** Already one of the best screens. Promote pattern.

---

### 8. Trade — Options (Live Options Coach)

**Decision:** Should I buy CE, buy PE, or do nothing on the index right now?

**One sentence to remember:** *"Wait — premium too rich until OR breaks 24,800."*

| Element | Redesign |
|---------|----------|
| **Headline** | One live action (BUY CE / BUY PE / WAIT) |
| **Secondary** | Strike + invalidation level |
| **Remove** | Strike picker before recommendation; MIS advisory strip duplicate; sideways strategy expander on default; premium charts above verdict; "How strategies are applied" |
| **End action** | **Wait** OR **Set alert at [level]** |

---

### 9. Trade — Charts (Live Charts)

**Decision:** *(User should not need this daily.)*

**One sentence to remember:** *N/A — this screen violates "one message" by design.*

| Element | Redesign |
|---------|----------|
| **Recommendation** | **Demote entirely.** Link from Trade only when user wants minute-by-minute stories for a starred pick. Default: show one chart for today's starred symbol, not 200 stocks. |

---

### 10. Discover — Market Pulse

**Decision:** What is the broader market doing across timeframes?

**One sentence to remember:** *"Market is mixed — only intraday setups look interesting today."*

| Element | Redesign |
|---------|----------|
| **Headline** | One market sentence |
| **Secondary** | Top 3 ideas across horizons — not Top 10 tables |
| **Remove** | Earnings strip, delivery table, IV strip, affordable invest, index chains on demand, three chart tabs, 1–2 min load as default experience |
| **End action** | **Add to watch** OR **Back to Today** |

**Recommendation:** Hide from nav. Surface one sentence on Today; link "See full market scan" for power users.

---

### 11. Discover — Screener

**Decision:** Which stocks match my filters?

**One sentence to remember:** *"12 stocks match your quality screen — HDFC Bank leads."*

| Element | Redesign |
|---------|----------|
| **Headline** | Top match + count |
| **Secondary** | Filter summary in plain English |
| **Remove** | Raw filter sliders before results; full matches table before top pick |
| **End action** | **Research top match** |

---

### 12. Discover — Batch Scanner

**Decision:** How do my pasted tickers rank?

**One sentence to remember:** *"Of your 8 names, only 2 look buyable today."*

| Element | Redesign |
|---------|----------|
| **Recommendation** | Merge into Screener as "Paste your list" mode — not a separate tab |

---

### 13. Discover — Penny Picks

**Decision:** Any speculative swing plays under ₹100?

**One sentence to remember:** *"High risk — only IDEA meets our rules today, and it's optional."*

| Element | Redesign |
|---------|----------|
| **Recommendation** | Remove tab. Optional preset inside Screener with bold risk warning. |

---

### 14. Discover — Global Markets

**Decision:** How does the world affect my India trades today?

**One sentence to remember:** *"US closed flat — no strong spillover; trade your own levels."*

| Element | Redesign |
|---------|----------|
| **Headline** | India action sentence (already good in engine) |
| **Secondary** | World heatmap — collapsed |
| **Remove** | Correlation charts, 5m intraday US+India, prediction methodology expander on default |
| **End action** | **Back to Today** |

**Recommendation:** One paragraph on Today. Full page hidden.

---

### 15. Plan — SIP & Goals

**Decision:** Am I on track for my wealth goal?

**One sentence to remember:** *"At ₹25,000/month you'll reach ₹1 Cr in 14 years — stay the course."*

| Element | Redesign |
|---------|----------|
| **Headline** | Goal progress sentence |
| **Secondary** | SIP amount, projected corpus |
| **Remove** | Three tabs before headline; Telegram reminders in main flow |
| **End action** | **Adjust SIP** OR **You're on track — no changes** |

---

### 16. Plan — Risk & Goals (onboarding)

**Decision:** How much can I afford to lose on one trade?

**One sentence to remember:** *"Risk ₹2,000 per trade — that means 40 shares of RELIANCE at this stop."*

| Element | Redesign |
|---------|----------|
| **Headline** | Position size recommendation |
| **Secondary** | Experience + goal profile |
| **Remove** | "Where to learn more in this app" table — replace with one link to Settings |
| **End action** | **Save my profile** → route to Today |

**Verdict:** Best beginner screen in the app. Use as onboarding template for all screens.

---

### 17. Learn — Varsity TA

**Decision:** What does this pattern mean?

**One sentence to remember:** *N/A — reference library, not a daily decision.*

| Element | Redesign |
|---------|----------|
| **Recommendation** | Remove from nav. Contextual links from Ask: "What is a hammer candle?" |

---

### 18. Learn — Backtest

**Decision:** Did this strategy work historically?

**One sentence to remember:** *"This strategy beat buy-and-hold in 7 of 10 years — but drawdowns were severe."*

| Element | Redesign |
|---------|----------|
| **Headline** | Beat/miss sentence vs benchmark |
| **Secondary** | Equity curve |
| **Remove** | Walk-forward folds, trade log before summary |
| **End action** | Settings → Advanced only |

---

### 19. Settings (sidebar ⚙️ Setup + broker + autopilot)

**Decision:** Is my app configured correctly?

**One sentence to remember:** *"You're connected to Zerodha — alerts on, autopilot scheduled."*

| Element | Redesign |
|---------|----------|
| **Headline** | Green checklist: Broker ✓ Risk ✓ Alerts ✓ |
| **Secondary** | Individual setup steps |
| **Remove** | Setup expander buried in sidebar competing with trading; broker wizard "Investment OS" welcome copy |
| **End action** | **Done — go to Today** |

**Promote:** Settings becomes a real tab, not sidebar clutter.

---

### 20. App shell — Onboarding / Start here

**Decision:** What do I do first?

**One sentence to remember:** *"Set your risk, connect broker, come back after 3:30 PM for tomorrow's plan."*

| Element | Redesign |
|---------|----------|
| **Headline** | 3-step path only — not 4 competing workflows |
| **Remove** | Collapsed expander in sidebar; tour overlay competing with Today |
| **End action** | **Start with Today** |

---

### 21. App shell — Command palette / Search

**Decision:** Jump to a stock or section fast.

**One sentence to remember:** *N/A — utility, not a destination.*

| Element | Redesign |
|---------|----------|
| **Recommendation** | Merge into **Ask** as persistent search. One search box: "Ask about any stock…" |

---

### 22. App shell — Broker setup wizard

**Decision:** Can the app see my real holdings?

**One sentence to remember:** *"Connect Zerodha once — we'll handle the rest."*

| Element | Redesign |
|---------|----------|
| **Remove** | "Welcome to Investment OS" |
| **Headline** | "Connect your broker so we can advise on your real portfolio" |
| **End action** | **Connect Zerodha** |

---

### 23. App shell — Sidebar (market, period, data health, autopilot, telegram)

**Decision:** Various config — **none belong in the trading path.**

| Element | Redesign |
|---------|----------|
| **Recommendation** | Collapse sidebar by default. Market + period move to Settings. Data health, Autopilot, Telegram → Settings only. Trading screens get zero sidebar noise. |

---

### 24. App shell — Disclaimer banner

**Decision:** None — legal requirement.

| Element | Redesign |
|---------|----------|
| **Recommendation** | Footer on every page. Stop consuming vertical space above the advisor message. |

---

## Information vs Recommendation — Audit Summary

Places where the UI still **shows information** instead of **making a recommendation**:

| Location | Information shown | Should become |
|----------|-------------------|---------------|
| Home (current) | 5 cards, confidence labels, levels grid | One morning letter |
| Suggestions | Phase banners, hit-rate strip, full watchlist | Starred trade plan only |
| Track Record | Calibration, gates, journal metrics | "4 of 6 right this week" |
| Daily Advisor | 5 metric tiles before summary | Briefing sentence first |
| My Portfolio | Import method radio, holdings table | "Hold / trim / add" narrative |
| Single Stock | Metrics grid before advice | Buy/Hold/Wait headline |
| Alpha AI | 15 sections visible | Verdict + 3 bullets; rest hidden |
| Market Pulse | Top 10 tables × 3 horizons | 3 ideas max |
| Live Charts | 200-stock verdict table | Demote or single-symbol |
| Live Options | Charts before action | WAIT / BUY CE / BUY PE |
| Global Markets | Heatmap + correlation first | India action sentence |
| Screener | Filters before results | Top match first |
| Backtest | Metrics grid | Beat/miss sentence |
| Sidebar | Data health, autopilot | Settings tab |
| Broker wizard | Investment OS branding | "Connect broker" |

---

## Language Transformation Guide

### Verdict vocabulary (consistent everywhere)

| Engine term | User hears |
|-------------|------------|
| ACT | "Yes — trade today" |
| WAIT | "Wait" |
| PASS | "Skip new trades today" |
| REDUCE | "Cut back exposure" |
| DEFENSIVE | "Stay cautious" |
| TRADE OK | "Green light to trade" |
| NO TRADE | "Not a trading day" |

### Confidence (never show % on default view)

| Range | User hears |
|-------|------------|
| ≥ 70% | "We're confident" / High |
| 40–69% | "We're moderately sure" / Medium |
| < 40% | "Low conviction — be careful" / Low |

### Portfolio health (never synthetic score)

| State | User hears |
|-------|------------|
| Healthy | "Your portfolio looks healthy" |
| Needs review | "One position needs review" |
| High risk | "Reduce risk before adding new trades" |

### Closing phrases (permission to disengage)

- "Nothing requires your attention today."
- "You're done for the morning."
- "Close the app — we'll alert you if something changes."
- "Come back after 3:30 PM to score today's picks."

---

## Proposed User Journeys (Post-Redesign)

### Journey A — Morning (9:00 AM, 20 seconds)

1. Open app → **Today** loads one letter
2. Read verdict + one watch item
3. If WAIT → close app
4. If ACT → tap **Open trade plan** → **Trade**

**Target:** 20-second read. Zero scrolling on WAIT days.

### Journey B — "Should I buy RELIANCE?"

1. Tap search / **Ask**
2. Type RELIANCE
3. See: *"Wait for ₹2,800"* in 5 seconds
4. Optional: **Full research** for 3-year view

**Target:** 5-second fast answer; deep report on demand.

### Journey C — "What about my portfolio?"

1. **Portfolio** opens with briefing sentence
2. If healthy → **No changes needed** → close app
3. If action → one stock named → **Review**

**Target:** Answer before showing holdings table.

### Journey D — Sunday review (5 minutes)

1. Open **Results**
2. Read: *"4 of 6 right this week"*
3. Optional: score yesterday if post-market

**Target:** Trust-building, not analytics dashboard.

---

## What We Deliberately Do Not Build

- No new dashboard widgets
- No health score rings or gamification
- No "explore features" engagement loops
- No forcing the user to star picks, score picks, and validate journal on the same day
- No duplicate verdict strips across Home, Suggestions, MIS, and morning cockpit
- No engine vocabulary in default UI (evidence packets, synthesis, calibration, context hash)

---

## Implementation Phases (After Approval)

| Phase | Scope | Outcome |
|-------|-------|---------|
| **P0 — Today letter** | Rewrite Home as single narrative block | WOW morning experience |
| **P1 — Language pass** | Ban dashboard terms app-wide in default views | Advisor voice everywhere |
| **P2 — Merge Portfolio** | Daily Advisor into Portfolio; briefing first | One wealth conversation |
| **P3 — Simplify Trade** | Starred picks only; demote charts/scoring | One trade plan |
| **P4 — Nav surgery** | 6-tab default; hide Discover/Learn | Less thinking |
| **P5 — Ask merge** | Single Stock + Alpha AI behind one search | One research entry |
| **P6 — Settings tab** | Sidebar demoted | Clean trading path |

**Do not start P0 until this document is approved.**

---

## Success Metrics

| Metric | Today (est.) | WOW target |
|--------|--------------|------------|
| Time to morning decision | 60–120 sec | **≤ 20 sec** |
| Scroll depth on WAIT days | 2–3 screens | **0** (above fold) |
| Tabs visited before first trade | 3–5 | **≤ 2** (Today → Trade) |
| User can articulate verdict | Low ("lots of info") | High ("WAIT until 9:45") |
| Qualitative trust | "Powerful but overwhelming" | **"It already thought for me"** |

---

## Approval Checklist

Before implementation, confirm:

- [ ] Home is one letter, not five cards
- [ ] WAIT days explicitly say "close the app"
- [ ] Portfolio briefing comes before holdings table
- [ ] Track Record is "Did we get it right?" not calibration dashboard
- [ ] 6-tab default nav approved
- [ ] Market Pulse / Live Charts / Batch Scanner demoted
- [ ] Engine vocabulary banned from default views
- [ ] Backend logic unchanged — presentation layer only

---

*This document is the product blueprint for the world's best investing assistant. Not the world's best investment dashboard.*
