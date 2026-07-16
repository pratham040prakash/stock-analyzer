# AI Trading Decision System — Product & UX Specification

**Version:** 1.0  
**Date:** 2026-07-16  
**Status:** Implementation blueprint — **no code in this document**  
**Audience:** Frontend engineers, product, design  
**Supersedes:** Dashboard-first patterns in Stock Analyzer / Investment OS naming

---

## Document purpose

This specification defines the **entire product experience** for the **AI Trading Decision System** — not a single page, not a feature list, not an architecture diagram.

A frontend engineer should be able to implement the full UI from this document without further UX clarification. Backend engines exist; this document defines **what users see, in what order, in what words, and what they do next**.

**Hard rules:**

- Do not expose AI engines, evidence packets, synthesis, calibration, or internal module names in default UI.
- Do not expose internal architecture (context engine, decision engine, broker truth, etc.).
- Every screen ends with a **recommendation** or a **clear next action** (including explicit permission to stop: *"You're done for today"*).
- The experience must feel like a **trusted trading mentor**, not a dashboard.

---

# 1. Product Vision

## 1.1 Name and positioning

**Product name (user-facing):** AI Trading Decision System  
**Tagline (internal, not shown as hero):** *The smartest thing to do right now.*

**One-line vision:**

> A personal trading mentor that analyses your full situation — market, portfolio, capital, risk, history — and tells you the single smartest action to take right now.

## 1.2 Mission

Help users make more money over the long term by making **better trading decisions** while **protecting capital**.

Success is not "more features." Success is:

- Fewer bad trades
- Better-timed entries
- Respecting risk limits
- Compounding trust over weeks

## 1.3 The one question

Every session, every screen, every refresh ultimately answers:

> **"What is the smartest thing this user should do right now?"**

Examples of valid answers:

| Situation | Smartest thing |
|-----------|----------------|
| Choppy open, no edge | "Do nothing until 9:45 AM. Close the app." |
| One A+ setup, capital available | "Buy RELIANCE above ₹2,850. Risk ₹2,000. Stop ₹2,820." |
| Portfolio overweight financials | "Do not add bank stocks today. Hold existing positions." |
| Loss streak | "No new trades today. Review yesterday's journal." |
| Broker disconnected | "Connect Zerodha before trading — your advice is using stale holdings." |
| Sunday evening | "Nothing to do until Monday 9:00 AM. Last week: 4 of 6 calls correct." |

## 1.4 What we are not

| We are not | We are |
|------------|--------|
| Bloomberg Terminal | A mentor who speaks in plain English |
| TradingView (chart grid) | One chart when you need it, not 200 |
| A screener product | A decision product with discovery on demand |
| An AI demo | A system that scores itself and admits mistakes |
| Investment OS / dashboard | AI Trading Decision System |

## 1.5 Success metrics

| Metric | Target |
|--------|--------|
| Time to primary recommendation (Today) | ≤ 20 seconds read |
| Screens visited before acting on a trade | ≤ 2 (Today → Trade) |
| User can repeat the recommendation aloud | ≥ 90% of sessions |
| Scroll on "do nothing" days | 0 (above fold complete) |
| Weekly return visit (trust) | User opens Results without trading |

---

# 2. Product Philosophy

## 2.1 Think like an experienced trader

The system behaves as a senior trader would when advising a friend:

1. **Check if today is a trading day at all** (macro, session, volatility, loss streak).
2. **Check the friend's book** (holdings, sector concentration, open risk).
3. **Check available firepower** (capital, margin, max loss for the day).
4. **Look for one high-conviction setup** — not ten mediocre ones.
5. **Give a conditional plan** (if/then), not a data dump.
6. **Say when to walk away.**

## 2.2 Inputs the mentor considers (hidden from default UI)

The UI **uses** these inputs but **does not label** them as engine outputs:

| Input | User hears (when relevant) |
|-------|---------------------------|
| Today's market | "Markets are cautious this morning." |
| Zerodha portfolio | "Your portfolio looks healthy." |
| Available capital | "You can risk ₹2,000 today." |
| Existing positions | "You're already long IT — don't add more tech." |
| Risk limits | "You're at your daily loss limit — stop trading." |
| Open trades | "You have an open RELIANCE position — don't double up." |
| Trading history | "You've lost three days in a row — sit out today." |
| Learning history | "We were right on 4 of 6 calls last week." |
| Sector exposure | "40% in financials — too concentrated." |
| Correlation | "These two picks move together — pick one." |
| News | "RBI decision at 10 AM — wait for clarity." |
| Macro conditions | "US futures are flat — no strong spillover." |

## 2.3 Capital protection over activity

**Inactivity is a valid recommendation.** The mentor must explicitly release the user:

- "Nothing requires your attention today."
- "Close the app — you're done for the morning."
- "Come back after 3:30 PM to review today's results."

Forcing engagement (scoring, starring, scanning) on no-trade days violates the philosophy.

## 2.4 Long-term wealth via better decisions

Short-term MIS trades and long-term holdings coexist, but the **default path is today's decision**. Long-term research (3-year view) lives behind **Research** mode, not the morning path.

## 2.5 Accountability builds trust

The system tracks whether its advice worked. Users see this weekly, not as a calibration dashboard:

- "Last 7 days: 4 of 6 stock calls correct."
- Not: "Confidence calibration 90d · broker-backed 67%."

---

# 3. UX Principles

## P1 — One primary message per screen

One headline recommendation. Everything else is secondary or hidden behind "See why."

## P2 — Recommendation before explanation

Layout order is always:

```
1. Recommendation (what to do)
2. Reason (one sentence)
3. Plan (if/then, levels, size — only if acting)
4. Action button(s)
5. Details (collapsed)
```

Never:

```
Metrics → Charts → Tables → Recommendation
```

## P3 — Every screen ends with an action

| Action type | Example |
|-------------|---------|
| **Execute** | Open trade plan · Connect Zerodha · Place via Kite |
| **Review** | Review RELIANCE setup · See full research |
| **Record** | Log today's result · Score yesterday's picks |
| **Release** | You're done today · Close the app · Come back at 3:30 PM |
| **Navigate** | Go to Portfolio · Back to Today |

## P4 — No engine vocabulary in default UI

**Banned in default view:** Context, Evidence, Decision Engine, Synthesis, Calibration, Investment OS, evidence packet, snapshot ID, combined score, prep score, gate, module, schema.

**Allowed:** "Here's why," "What we looked at," "How often we were right," "We're fairly sure."

## P5 — Qualitative conviction, not percentages

Default UI uses **High / Medium / Low** conviction. Numeric percentages only inside collapsed "See why" sections.

## P6 — Progressive disclosure

| Level | Content |
|-------|---------|
| **L0 (default)** | Recommendation + one reason + action |
| **L1 (expand)** | 3 bullet "why" + levels + size |
| **L2 (link)** | Full research, charts, history |
| **L3 (settings/advanced)** | Scans, backtest, screener, raw tables |

## P7 — Personal when possible

Use broker profile name when available (`BrokerSnapshot.user_name` / Kite profile). Fallback: "Good morning" without name.

## P8 — Mobile-first Today

Today view must be complete on one phone screen for WAIT days (no scroll).

## P9 — Consistent verdict vocabulary

| Internal | User-facing |
|----------|-------------|
| ACT / TRADE_OK | **Trade today** |
| WAIT / OBSERVE | **Wait** |
| PASS / NO_TRADE | **Don't trade today** |
| REDUCE | **Cut back** |
| DEFENSIVE / CAUTION | **Stay cautious** |
| BUY / SELL / HOLD | Use for single-stock research |

## P10 — Zerodha is source of truth for money

Always attribute live P&L to Zerodha Console when showing fills or holdings. The mentor advises; the broker settles.

---

# 4. Information Architecture

## 4.1 Top-level structure

Replace 20-tab navigation with **5 primary destinations + Settings**.

```
┌─────────────────────────────────────────────────────────────┐
│  AI Trading Decision System                    [🔍 Ask] [⚙️]  │
├─────────────────────────────────────────────────────────────┤
│  Today │ Trade │ Portfolio │ Research │ Results             │
└─────────────────────────────────────────────────────────────┘
```

| Tab | User question | Replaces (current nav) |
|-----|---------------|------------------------|
| **Today** | What is the smartest thing to do right now? | Home, morning cockpit, global bias snippets, MIS strip on other pages |
| **Trade** | What exactly should I execute today? | Suggestions, Live Charts (equity), Live Options Coach, NSE Options |
| **Portfolio** | What should I do with what I own? | My Portfolio, Daily Advisor, portfolio sections on Home |
| **Research** | Should I buy/hold/sell this stock (fast or deep)? | Single Stock, Alpha AI, Compare |
| **Results** | Was the advice good? | Track Record, trade journal, exports |
| **Settings** *(icon, not equal tab)* | Is everything configured? | Sidebar Setup, broker wizard, Risk & Goals prefs, Autopilot, Telegram, data health |

## 4.2 Demoted surfaces (Advanced — not in primary nav)

Accessible via Settings → Advanced or contextual links from Today/Research:

| Surface | Access path |
|---------|-------------|
| Market Pulse | Today → "See full market scan" |
| Live Charts (full grid) | Trade → "All live charts" |
| Screener | Research → "Find new stocks" |
| Batch Scanner | Research → "Paste ticker list" |
| Penny Picks | Research → "High-risk picks" preset |
| Global Markets | Today → "World markets" (one paragraph default) |
| SIP & Goals | Portfolio → "Long-term plan" |
| Backtest | Settings → Advanced |
| Varsity TA | Research → "Learn this pattern" links |

## 4.3 Global chrome (all pages)

### Header (persistent, 56px)

```
┌──────────────────────────────────────────────────────────────┐
│ ◉ AI Trading Decision System          [Ask…]  [⚙️ Settings] │
└──────────────────────────────────────────────────────────────┘
```

- **No** "Stock Analyzer" title.
- **No** disclaimer banner above content — footer only.
- **Ask** opens universal symbol/search overlay (replaces command palette).
- **Settings** opens Settings page (not sidebar expander).

### Primary nav (persistent, 48px)

Five tabs. Active tab underline + bold. Badge dots optional:
- **Trade** — dot if starred plan exists
- **Portfolio** — dot if action required on a holding
- **Results** — dot if unscored session after 3:30 PM

### Footer (persistent, minimal)

```
Varsity/NSE disclaimer · Not financial advice · Updated 9:14 AM IST
```

### Removed from default chrome

- Sidebar market/period selectors → Settings → Preferences
- Sidebar Setup expander → Settings
- Sidebar Autopilot → Settings → Automation
- Sidebar Data health → Settings → Data
- Sidebar Telegram → Settings → Alerts
- Onboarding expander → first-run modal only
- "Start here" strip on every page → first-run only

## 4.4 First-run flow (before Today is useful)

```
Step 1: Welcome
  "I'm your trading mentor. I'll tell you the smartest thing to do each day."

Step 2: Risk profile (was Risk & Goals)
  Capital · max daily loss · experience
  → End: "You can risk ₹X per trade."

Step 3: Connect Zerodha
  OAuth flow
  → End: "I can see your real portfolio."

Step 4: Release
  "Come back at 9:00 AM on trading days."
  [Go to Today]
```

Broker gate: if Zerodha API keys missing, show Step 3 only until complete. Portfolio advice shows "Connect broker" state — not empty dashboard.

## 4.5 Simple mode (cloud / new users)

Default nav for `SIMPLE_CLOUD_MODE`:

**Today · Trade · Research · Results · Settings** (Portfolio hidden until broker connected).

---

# 5. Daily Decision Journey

## 5.1 Journey map

```
                    ┌─────────────┐
                    │  Open app   │
                    └──────┬──────┘
                           ▼
                    ┌─────────────┐
              ┌────│    Today    │────┐
              │    └──────┬──────┘    │
              │           │           │
         WAIT │      ACT  │     ISSUE │
              │           │           │
              ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌────────────┐
        │  Close   │ │  Trade   │ │ Portfolio  │
        │   app    │ │   plan   │ │  or Setup  │
        └──────────┘ └────┬─────┘ └────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │ Execute on  │
                     │   Kite      │ (external)
                     └──────┬──────┘
                            ▼
                     ┌─────────────┐
                     │ 3:30 PM+    │
                     │  Results    │
                     └─────────────┘
```

## 5.2 Scenario A — Morning WAIT day (9:00 AM)

| Step | Screen | Time | Outcome |
|------|--------|------|---------|
| 1 | Today | 15s | Read: WAIT until 9:45, portfolio healthy, one watch item |
| 2 | — | — | Tap **You're done** or close app |
| **Total** | **1 screen** | **≤20s** | No scroll |

## 5.3 Scenario B — Morning ACT day (10:00 AM)

| Step | Screen | Time | Outcome |
|------|--------|------|---------|
| 1 | Today | 15s | "Trade today — RELIANCE setup" |
| 2 | Trade | 30s | Entry ₹2,850 · Stop ₹2,820 · Target ₹2,920 · Size 40 shares |
| 3 | Kite | — | User executes externally |
| 4 | Results (3:30+) | 20s | Score today's pick |

## 5.4 Scenario C — Portfolio issue (any time)

| Step | Screen | Time | Outcome |
|------|--------|------|---------|
| 1 | Today | 10s | "One position needs review — INFY" |
| 2 | Portfolio | 30s | "Trim INFY if below ₹1,450" |
| 3 | Research (optional) | — | Deep dive on INFY |

## 5.5 Scenario D — Research ask (any time)

| Step | Screen | Time | Outcome |
|------|--------|------|---------|
| 1 | Ask overlay | 5s | Type TCS |
| 2 | Research (fast) | 10s | "Wait — fairly valued, buy at ₹3,800" |
| 3 | Research (deep, optional) | 2m | Full long-term report |

## 5.6 Scenario E — Sunday / market closed

| Step | Screen | Time | Outcome |
|------|--------|------|---------|
| 1 | Today | 10s | "Markets closed. Nothing to do until Monday 9 AM." |
| 2 | Results (optional) | 30s | Weekly scorecard |

## 5.7 Time-of-day behavior (Today copy adapts)

| Time (IST) | Today emphasis |
|------------|----------------|
| Pre-market (< 9:15) | Tonight's plan preview or "Wait for open" |
| Opening (9:15–9:45) | Opening range rules · "Do not trade before 9:45" |
| Session (9:45–15:00) | Live recommendation · open trade monitoring |
| Last hour (> 14:30) | "No new positions" if engine says so |
| Post-close (> 15:30) | Score today · preview tomorrow |
| Weekend | Weekly results · no trade urgency |

---

# 6. Screen-by-Screen Redesign

Each screen spec includes: **Decision · Primary message · Layout · States · Data mapping (implementation) · End action · Remove.**

*Data mapping references existing backend modules for engineers — these names are **implementation notes only**, never shown to users.*

---

## 6.1 Today

### Decision
What is the smartest thing I should do right now?

### Primary message (one sentence)
Template: `[Greeting]. [Verdict sentence]. [Portfolio sentence]. [Watch sentence or "Nothing to watch"].`

Example:
> Good morning, Pratham. Today is a wait day — do not deploy fresh capital before 9:45 AM. Your portfolio looks healthy. The only setup worth watching is RELIANCE above ₹2,850.

### Layout structure

```
┌─────────────────────────────────────────────┐
│ TODAY                                       │
│                                             │
│ Good morning, Pratham.                      │  ← 18px, regular
│                                             │
│ Today is a WAIT day.                        │  ← 32px, bold, verdict color
│                                             │
│ Do not deploy fresh capital before 9:45 AM. │  ← 18px
│                                             │
│ Your portfolio looks healthy.               │  ← 16px
│                                             │
│ ─────────────────────────────────────────── │
│                                             │
│ ONE THING TO WATCH                          │  ← 12px label, caps
│                                             │
│ RELIANCE                                    │  ← 24px bold
│ If it breaks ₹2,850 after 9:45 AM → buy.  │  ← 16px
│ Otherwise, you're done for today.           │  ← 16px, muted
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │  You're done for today                  │ │  ← primary button (WAIT)
│ └─────────────────────────────────────────┘ │
│   or                                        │
│ ┌─────────────────────────────────────────┐ │
│ │  Open trade plan                        │ │  ← primary (ACT)
│ └─────────────────────────────────────────┘ │
│                                             │
│ ▸ See why we think this                     │  ← collapsed expander
│                                             │
│ Estimated reading time: 20 sec              │  ← 12px muted
│ Updated 9:14 AM IST                         │
└─────────────────────────────────────────────┘
```

### Component spec: `TodayBriefing`

| Field | Source (implementation) | Display rule |
|-------|-------------------------|--------------|
| `user_name` | `BrokerSnapshot.user_name` | First name only |
| `verdict` | `DecisionArtifact.verdict` or `MisTradeAdvisory` / `snapshot.risk_mode` | Map to Trade/Wait/Don't trade/Stay cautious |
| `verdict_reason` | `decision.explainability.why` or `os_report.next_step` or `mis.summary` | Max 2 sentences |
| `timing_rule` | `snapshot.trading_restrictions[0]` or `OPENING_OBSERVE_UNTIL` | Plain English time |
| `portfolio_status` | `os_report.module("risk")` + holdings | Healthy / Needs review / High risk |
| `portfolio_note` | `os_report.next_step` or weakest holding | One line |
| `watch_symbol` | `os_report.starred_symbol` or top pin | Single symbol only |
| `watch_trigger` | Pin entry/target | If/then format |
| `conviction` | `decision.confidence` | High/Med/Low in expander only |
| `updated_at` | `built_at` | Footer |

### States

| State | Headline | Primary button | Secondary |
|-------|----------|----------------|-----------|
| **WAIT** | Today is a wait day. | **You're done for today** | See why |
| **ACT** | Today is a trade day. | **Open trade plan** → Trade tab | Review [symbol] → Research |
| **DON'T TRADE** | Not a trading day. | **You're done for today** | See why |
| **STAY CAUTIOUS** | Protect capital today. | **Review portfolio** → Portfolio | See why |
| **NO_SETUPS** | No high-conviction setups. | **You're done for today** | Scan picks tonight → Trade (post-close) |
| **BROKER_STALE** | Connect Zerodha for accurate advice. | **Connect broker** → Settings | Continue with saved data (muted) |
| **MARKET_CLOSED** | Markets are closed. | **See weekly results** → Results | Preview tomorrow (post-close only) |

### "See why" expander (L1 — max 6 bullets)

Pull from (implementation): evidence packet items, `mis.flags`, `mis.synthesis_pillars` — display as plain bullets:

- "Nifty opened choppy — wait for opening range."
- "VIX elevated — size down."
- "You lost ₹3,200 yesterday — sit out or trade half size."

**Never label** evidence packet or synthesis.

### End actions (exactly one primary)

| Verdict | Primary CTA | Navigation |
|---------|-------------|------------|
| WAIT / DON'T TRADE | You're done for today | Dismiss / optional close hint |
| ACT | Open trade plan | `nav_tab = Trade` |
| Portfolio issue | Review portfolio | `nav_tab = Portfolio` |
| Broker | Connect Zerodha | `nav_tab = Settings` (broker section) |

### Remove from current Home

- Five question-cards
- Separate broker card
- Bottom search bar (moves to header Ask)
- Confidence label in default view
- Entry/stop/target grid in default view (move to Trade or expander)
- Snapshot ID / engine metadata in footer

---

## 6.2 Trade

### Decision
What exactly should I execute today — and at what levels?

### Primary message
> Your plan for today is one trade: **RELIANCE long** — enter above ₹2,850, stop ₹2,820, target ₹2,920. Risk ₹2,000 (40 shares).

### Layout

```
┌─────────────────────────────────────────────┐
│ TRADE · Tuesday 16 Jul                      │
│                                             │
│ Your plan today                             │
│ ┌─────────────────────────────────────────┐ │
│ │ ★ RELIANCE · Long · High conviction      │ │
│ │                                         │ │
│ │ Enter   above ₹2,850                    │ │
│ │ Stop    ₹2,820                          │ │
│ │ Target  ₹2,920                          │ │
│ │ Risk    ₹2,000 · 40 shares              │ │
│ │                                         │ │
│ │ [ Review full setup ]  [ Log trade ]    │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Session: Market open · safe to trade after  │  ← one line
│ 9:45 AM                                     │
│                                             │
│ ─── Options (if applicable) ───              │  ← sub-section, collapsed if empty
│ │ No options trade recommended today.   │ │
│                                             │
│ ▸ Yesterday's picks · ▸ All live charts     │  ← links to advanced
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │  Back to Today                          │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Sub-modes (tabs within Trade — not top-level nav)

| Sub-tab | When visible | Content |
|---------|--------------|---------|
| **Equity plan** | Always | Starred MIS picks (max 2) |
| **Options** | India market + expiry session | Live Options Coach primary action |
| **Live chart** | User expands | Single-symbol chart for starred pick only |

### Data mapping

| UI field | Source |
|----------|--------|
| Starred picks | `load_pinned_plans()` + `is_selected` / `load_selected_symbols` |
| Levels | `PinnedPlan` entry/stop/target |
| Size | `intraday_prefs` + `suggest_position_size` |
| Session note | `market_session_status()` + `MisTradeAdvisory.time_note` |
| Options action | `build_mis_trade_advisory` + options coach |

### States

| State | Message | CTA |
|-------|---------|-----|
| **PLAN_READY** | Your plan today: [symbol] | Review setup / Log trade |
| **NO_PICKS** | No saved setups. Run tonight's scan after 3:30 PM. | **Set up tonight's scan** |
| **TOO_LATE** | Too late for new MIS entries today. | **You're done** |
| **LOSS_STREAK** | Three losing days — no new trades recommended. | **Review what went wrong** → Results |

### End action
- **Log trade** → Results journal OR external Kite
- **Back to Today** → Today tab

### Remove
- Weekly hit-rate strip (→ Results)
- Morning cockpit duplicate
- Autopilot loop strip on main view
- Full watchlist table (→ show starred only; link "See all picks")
- Capital sliders on this page (→ Settings)
- Scoring UI (→ Results)
- Phase/engine banners

---

## 6.3 Portfolio

### Decision
Do I need to change anything in what I already own?

### Primary message
> Your portfolio is healthy. Hold all positions — no changes required today.

OR

> One position needs attention: **INFY** is down 8% and overweight at 22%. Consider trimming if it breaks ₹1,450.

### Layout

```
┌─────────────────────────────────────────────┐
│ PORTFOLIO                                   │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │  HOLD — no changes required today       │ │  ← verdict banner
│ └─────────────────────────────────────────┘ │
│                                             │
│ Today: +₹4,200 unrealized · 12 positions   │  ← one line
│ Sector note: Heavy in IT (38%) — don't add  │
│ more tech today.                            │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │  No changes needed                      │ │  ← primary (healthy)
│ └─────────────────────────────────────────┘ │
│   or                                        │
│ ┌─────────────────────────────────────────┐ │
│ │  Review INFY                              │ │  ← primary (action)
│ └─────────────────────────────────────────┘ │
│                                             │
│ ▸ Your holdings (12)                        │  ← collapsed table
│ ▸ Sector breakdown                          │
│ ▸ Upcoming events (earnings)                │
│                                             │
│ Zerodha connected · synced 9:02 AM          │
└─────────────────────────────────────────────┘
```

### Data mapping

| UI field | Source |
|----------|--------|
| Briefing verdict | `build_daily_briefing()` / `generate_portfolio_advice()` |
| Holdings | `load_tracked_portfolio()` / `zd_import` |
| Sector exposure | `compute_portfolio_risk()` |
| Weakest position | Sort holdings by P&L % |
| P&L | Holdings unrealized or journal |
| Broker status | `BrokerSnapshot` |

### Holdings table (collapsed by default)

Columns: Symbol · Qty · P&L · **Today's action** (one word: Hold / Trim / Add / Watch)

Hide: weight formulas, beta tables, raw CSV import UI above fold.

### States

| State | Headline | CTA |
|-------|----------|-----|
| **HEALTHY** | Hold — no changes required | **No changes needed** |
| **ACTION_REQUIRED** | [Symbol] needs review | **Review [symbol]** → Research |
| **EMPTY** | Connect Zerodha to advise on your real book | **Connect Zerodha** |
| **STALE** | Last synced yesterday — refresh | **Refresh holdings** |

### End action
Always one of: **No changes needed** · **Review [symbol]** · **Connect Zerodha**

### Remove / merge
- Entire **Daily Advisor** tab — merge briefing here
- Manual entry radio as first UI element
- "Analyze my portfolio" as separate step — briefing IS the analysis
- Live 15s refresh panel as hero

---

## 6.4 Research

### Decision
Should I buy, hold, or sell this stock — and at what price?

### Primary message
> **TCS — Wait.** Fairly valued. Consider buying closer to ₹3,800. Stop ₹3,720.

### Entry: Ask overlay (global)

```
┌─────────────────────────────────────────────┐
│ 🔍 Ask about any stock…                     │
├─────────────────────────────────────────────┤
│ RELIANCE — Reliance Industries              │
│ TCS — Tata Consultancy Services             │
│ ...                                         │
└─────────────────────────────────────────────┘
```

Triggered from header. Uses `unified_search()`.

### Layout: Fast research (default)

```
┌─────────────────────────────────────────────┐
│ RESEARCH · TCS                              │
│                                             │
│ Wait                                        │  ← 32px verdict
│                                             │
│ Fairly valued — don't chase. Buy near       │
│ ₹3,800 if market pulls back.                │
│                                             │
│ Entry zone   ₹3,780 – ₹3,820                │
│ Stop         ₹3,720                         │
│ Target       ₹4,100                         │
│ Conviction   Medium                         │
│                                             │
│ ┌──────────────────┐ ┌──────────────────┐ │
│ │ Add to watch     │ │ Full research    │ │
│ └──────────────────┘ └──────────────────┘ │
│                                             │
│ ▸ Why this call (3 bullets)                 │
│ ▸ Chart                                     │
│ ▸ Fundamentals snapshot                     │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │  Compare with another stock             │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Layout: Full research (deep mode)

Triggered by **Full research** — uses Alpha AI report structure but renamed:

| Alpha AI section | User-facing name |
|------------------|------------------|
| Executive Summary | **The bottom line** |
| Quick Snapshot | **At a glance** |
| Buy Decision | **Should you buy?** |
| Entry Strategy | **How to enter** |
| Business Analysis | **The business** |
| Financial Analysis | **Financials** |
| Valuation | **Price vs value** |
| Technical Analysis | **Chart view** |
| Risk Analysis | **What could go wrong** |
| Final Verdict | **Our recommendation** |

Remove "AI" from section titles in UI. Keep export in overflow menu (⋯).

### Compare mode (within Research)

Input: 2–4 symbols → Output headline:

> **Winner: TCS** for long-term quality. **RELIANCE** for today's trade.

Table collapsed by default.

### Data mapping

| Mode | Source |
|------|--------|
| Fast | `analyze_combined()` + `generate_advice()` |
| Deep | `build_alpha_ai_report()` |
| Compare | `compare_alpha_reports()` |

### End actions

| Action | When |
|--------|------|
| **Add to today's watch** | User wants to monitor |
| **Open trade plan** | High conviction + ACT day |
| **Full research** | User wants 3-year view |
| **Compare with another stock** | Decision between names |
| **Back to Today** | Done researching |

### Remove
- Separate **Single Stock** and **Alpha AI** tabs — one Research tab, two depths
- Metric grids before verdict
- Options verdict on equity fast view (link to Trade → Options instead)

---

## 6.5 Results

### Decision
Was the advice good — and can I trust this system?

### Primary message
> Last 7 days: **4 of 6** stock calls correct. Best: RELIANCE (+2.1R). Miss: INFY (stopped out).

### Layout

```
┌─────────────────────────────────────────────┐
│ RESULTS                                     │
│                                             │
│ Last 7 days: 4 of 6 correct                 │  ← 24px
│                                             │
│ ┌────────┐ ┌────────┐ ┌────────┐            │
│ │ 4 wins │ │ 2 loss │ │ 67%    │            │  ← simple tiles
│ └────────┘ └────────┘ └────────┘            │
│                                             │
│ Yesterday: RELIANCE hit target ✓            │
│             INFY stopped out ✗              │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │  Score yesterday's picks (after 3:30)   │ │  ← primary when pending
│ └─────────────────────────────────────────┘ │
│   or                                        │
│ ┌─────────────────────────────────────────┐ │
│ │  You're up to date                      │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ ▸ Trade journal                             │
│ ▸ Export history                            │
│ ▸ How we score picks                        │
└─────────────────────────────────────────────┘
```

### Data mapping

| UI field | Source |
|----------|--------|
| Hit rate | `build_watchlist_success_report()` |
| Options hits | `build_options_success_report()` |
| Yesterday detail | `watchlist_history` / journal |
| Pending score | `can_score_trade_date()` |
| Calibration | `render_confidence_calibration_panel` — **expander only** |

### End actions

| State | CTA |
|-------|-----|
| Pending scores | **Score yesterday's picks** |
| Up to date | **You're up to date** + link to Today |
| No history yet | **Start trading — we'll track results** → Trade |

### Remove from default view
- "Confidence calibration" panel
- Pulse journal validation gates
- Threshold tuning metrics
- "Hit rate dashboard" as title — use plain English

### Rename
Track Record → **Results** (nav label: "Results" or "Did we get it right?")

---

## 6.6 Settings

### Decision
Is the system configured correctly for my trading?

### Layout (section list)

```
┌─────────────────────────────────────────────┐
│ SETTINGS                                    │
│                                             │
│ ✓ Zerodha connected (VQ3897)                │
│ ✓ Risk profile set — ₹2,000 max loss/day    │
│ ○ Telegram alerts off                       │
│ ✓ Autopilot scheduled                       │
│                                             │
│ ── Broker ──                                │
│ ── Risk & capital ──                        │
│ ── Alerts (Telegram) ──                     │
│ ── Automation (Autopilot) ──                │
│ ── Preferences (market, theme) ──           │
│ ── Data sources ──                          │
│ ── Advanced ──                              │
│     Market Pulse · Screener · Backtest      │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │  Back to Today                          │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### End action
**Back to Today** when setup complete.

### Absorb from sidebar
All current sidebar expanders move here. Sidebar removed in default layout.

---

## 6.7 Advanced screens (linked, not nav)

### Market Pulse (Advanced)

**Decision:** What does the full market look like across timeframes?

**One sentence:** "Market is mixed — only 3 intraday setups pass our rules today."

**End action:** **Add [symbol] to watch** or **Back to Today**

Default: show 3 ideas, not Top 10 tables.

---

### Screener / Batch Scanner (Advanced)

**Decision:** Which stocks match my criteria?

**One sentence:** "12 matches — HDFC Bank leads."

**End action:** **Research top match**

Batch Scanner = Screener "Paste list" mode.

---

### Live Charts grid (Advanced)

**Decision:** None daily — power tool.

**End action:** Demote to Trade → "All live charts" link. Default Trade shows **one chart** for starred symbol.

---

### Global Markets (Advanced)

**One sentence on Today:** "US closed flat — no strong spillover for India."

Full page: India action sentence + collapsed heatmap.

---

### SIP & Goals (Advanced)

Access: Portfolio → "Long-term wealth plan"

**One sentence:** "At ₹25,000/month you reach ₹1 Cr in 14 years — stay the course."

---

### Backtest (Advanced)

Access: Settings → Advanced

**One sentence:** "This strategy beat buy-and-hold in 7 of 10 years."

---

### Varsity TA (Advanced)

Access: Research → "What is this pattern?" contextual links only.

---

# 7. Tone of Voice Guide

## 7.1 Persona

**The mentor:** Experienced, calm, direct, slightly conservative. Protects capital first. Not hype. Not a salesman. Not a professor.

**Speaks like:** A senior trader texting a friend before market open.

**Never speaks like:** A Bloomberg terminal, a SaaS dashboard, or an AI research paper.

## 7.2 Voice attributes

| Attribute | Do | Don't |
|-----------|-----|-------|
| **Direct** | "Don't trade today." | "Market regime suggests caution." |
| **Conditional** | "If RELIANCE breaks ₹2,850, buy." | "RELIANCE: bullish, entry 2850" |
| **Personal** | "Your portfolio is heavy in IT." | "Sector exposure: IT 38%" |
| **Humble** | "We were wrong on INFY yesterday." | "Calibration drift detected." |
| **Releasing** | "Close the app — nothing to do." | "Explore more features." |
| **Specific** | "Risk ₹2,000 on this trade." | "Size appropriately." |

## 7.3 Verdict phrases (canonical)

| Verdict | Headline template | CTA |
|---------|-------------------|-----|
| Trade today | "Today is a trade day." | Open trade plan |
| Wait | "Today is a wait day." | You're done for today |
| Don't trade | "Not a day to trade." | You're done for today |
| Stay cautious | "Protect capital today." | Review portfolio |
| Hold (portfolio) | "Hold — no changes required." | No changes needed |
| Trim | "[Symbol] needs a trim." | Review [symbol] |
| Buy (research) | "[Symbol] — buy on pullback to ₹X." | Add to watch |
| Wait (research) | "[Symbol] — wait." | Add to watch |

## 7.4 Banned words (default UI)

```
Investment OS · Decision Engine · Evidence · Context · Synthesis ·
Calibration · Learning loop · Broker truth · Combined score · Prep score ·
Market regime · Risk mode · Capital deployment · Evidence packet ·
Snapshot · Schema · Module · Gate · MTF alignment · Flow snapshot ·
Confidence % (use High/Medium/Low)
```

## 7.5 Allowed alternatives

| Instead of | Write |
|------------|-------|
| Evidence packet | What we looked at |
| Calibration | How often we were right |
| Risk mode RISK-OFF | Markets feel cautious |
| TRADE_OK | Green light to trade |
| NO_TRADE | Not a trading day |
| Combined score 72 | High conviction |
| Sector strength leader IT | IT is leading today |
| Loss streak 3 | Three losing days in a row |

## 7.6 Greeting templates

```
Good morning, {first_name}.     # 5:00–11:59
Good afternoon, {first_name}.   # 12:00–16:59
Good evening, {first_name}.     # 17:00–4:59
```

If no name: drop the name, keep time greeting.

## 7.7 Reading time

Show on Today only: `Estimated reading time: {n} sec`  
Calculate: ~4 words/sec for visible default text.

---

# 8. Wireframes

## 8.1 Design tokens (implementation)

```css
/* Typography */
--font-family: system-ui, -apple-system, sans-serif;
--text-greeting: 18px / 1.4;
--text-body: 16px / 1.5;
--text-headline: 32px / 1.2 / 700;
--text-symbol: 24px / 1.2 / 700;
--text-label: 12px / 1.3 / 600 / uppercase / letter-spacing 0.08em;
--text-muted: 14px / opacity 0.7;

/* Verdict colors (existing theme) */
--verdict-trade: #00c853;
--verdict-wait: #ffd600;
--verdict-no: #ff5252;
--verdict-cautious: #ff9800;

/* Layout */
--content-max-width: 680px;
--page-padding: 20px;
--section-gap: 24px;
--card-radius: 16px;
--button-height: 48px;

/* Components */
--sticky-nav-height: 104px; /* header + tabs */
```

## 8.2 Today — WAIT day (full wireframe)

```
┌────────────────────────────────────────────────────────────┐
│ ◉ AI Trading Decision System              [Ask…]  [⚙️]     │
├────────────────────────────────────────────────────────────┤
│ [Today]  Trade  Portfolio  Research  Results               │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Good morning, Pratham.                                    │
│                                                            │
│  ████████████████████████████████████████                  │
│  ██                                      ██                │
│  ██   Today is a WAIT day.               ██  ← verdict     │
│  ██                                      ██                │
│  ████████████████████████████████████████                  │
│                                                            │
│  Do not deploy fresh capital before 9:45 AM.               │
│                                                            │
│  Your portfolio looks healthy.                             │
│                                                            │
│  ─────────────────────────────────────────────────────     │
│  ONE THING TO WATCH                                        │
│                                                            │
│  RELIANCE                                                  │
│  If it breaks ₹2,850 after 9:45 AM → buy.                 │
│  Otherwise, you're done for today.                         │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           You're done for today                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ▸ See why we think this                                   │
│                                                            │
│  Estimated reading time: 20 sec · Updated 9:14 AM IST       │
│                                                            │
├────────────────────────────────────────────────────────────┤
│ Disclaimer · Not financial advice                          │
└────────────────────────────────────────────────────────────┘
```

## 8.3 Today — ACT day (full wireframe)

```
│  Good morning, Pratham.                                    │
│                                                            │
│  Today is a TRADE day.                         [green]     │
│                                                            │
│  One high-conviction setup — size within your ₹2,000       │
│  daily risk limit.                                         │
│                                                            │
│  Your portfolio looks healthy.                             │
│                                                            │
│  ─────────────────────────────────────────────────────     │
│  YOUR SETUP                                                │
│                                                            │
│  RELIANCE · Long · High conviction                         │
│  Enter above ₹2,850 · Stop ₹2,820 · Target ₹2,920        │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Open trade plan                            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Review RELIANCE setup                      │  │  ← secondary outline
│  └──────────────────────────────────────────────────────┘  │
```

## 8.4 Trade — equity plan

```
│  TRADE · Tuesday 16 Jul · Market open                      │
│                                                            │
│  ┌─ Plan card ─────────────────────────────────────────┐  │
│  │ ★ RELIANCE · Long                                    │  │
│  │                                                      │  │
│  │  Enter     above ₹2,850                              │  │
│  │  Stop      ₹2,820                                    │  │
│  │  Target    ₹2,920                                    │  │
│  │  Risk      ₹2,000  (40 shares)                       │  │
│  │                                                      │  │
│  │  [Review setup]  [Log trade]                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  Safe to enter after 9:45 AM.                              │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Back to Today                              │  │
│  └──────────────────────────────────────────────────────┘  │
```

## 8.5 Portfolio — healthy

```
│  PORTFOLIO                                                 │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  ✓  HOLD — no changes required today               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  +₹4,200 unrealized · 12 positions · Zerodha synced       │
│  IT is 38% of your book — don't add tech today.           │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           No changes needed                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
│  ▸ Your holdings (12)                                      │
│  ▸ Sector breakdown                                        │
```

## 8.6 Research — fast

```
│  ← Back                                    RESEARCH · TCS   │
│                                                            │
│  Wait                                                      │
│                                                            │
│  Fairly valued. Buy closer to ₹3,800 on a pullback.       │
│                                                            │
│  Entry   ₹3,780 – ₹3,820                                   │
│  Stop    ₹3,720                                            │
│  Target  ₹4,100                                            │
│  Conviction  Medium                                        │
│                                                            │
│  [Add to watch]  [Full research]                           │
│                                                            │
│  ▸ Why this call                                           │
```

## 8.7 Ask overlay (modal)

```
│                    ┌─────────────────────────┐             │
│                    │ 🔍 Ask about any stock… │             │
│                    ├─────────────────────────┤             │
│                    │ RELIANCE                │             │
│                    │ Reliance Industries Ltd │             │
│                    ├─────────────────────────┤             │
│                    │ TCS                     │             │
│                    │ Tata Consultancy Svcs   │             │
│                    └─────────────────────────┘             │
```

## 8.8 Results

```
│  RESULTS                                                   │
│                                                            │
│  Last 7 days: 4 of 6 correct                               │
│                                                            │
│  ┌────────┐  ┌────────┐  ┌────────┐                     │
│  │ 4 wins │  │ 2 loss │  │  67%   │                     │
│  └────────┘  └────────┘  └────────┘                     │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │        Score yesterday's picks                       │  │
│  └──────────────────────────────────────────────────────┘  │
```

## 8.9 Mobile breakpoints

| Breakpoint | Behavior |
|------------|----------|
| `< 768px` | Single column; nav tabs scroll horizontal; headline 28px |
| `≥ 768px` | `max-width: 680px` centered content |
| All | Primary CTA full width; secondary outline below |

## 8.10 Component library (new / refactored)

| Component | Used on | Props |
|-----------|---------|-------|
| `MentorBriefing` | Today | `verdict`, `reason`, `portfolioNote`, `watch`, `userName` |
| `VerdictBanner` | Today, Portfolio, Research | `verdict`, `color`, `size` |
| `SetupCard` | Today (ACT), Trade | `symbol`, `side`, `entry`, `stop`, `target`, `risk`, `conviction` |
| `ReleaseButton` | Today, Trade | `label` ("You're done for today") |
| `PrimaryCTA` | All | `label`, `navTarget` |
| `WhyExpander` | All | `bullets[]`, `conviction?` |
| `AskOverlay` | Global | `market`, `onSelect` |
| `HoldingsCollapsible` | Portfolio | `holdings[]`, `defaultOpen=false` |
| `WeeklyScorecard` | Results | `wins`, `losses`, `pct` |
| `SettingsChecklist` | Settings | `items[]` |

---

# 9. Implementation Roadmap

## 9.1 Mapping: current files → new experience

| New surface | Primary files to refactor | Notes |
|-------------|---------------------------|-------|
| **Today** | `ui/components/home_dashboard.py`, `ui/pages/unified_home.py` | Replace cards with `MentorBriefing` |
| **Trade** | `ui/pages/intraday.py`, `ui/components/suggestions_home.py`, `ui/components/intraday_watchlist.py` | Strip to starred plan only |
| **Trade → Options** | `ui/pages/live_options_advisor.py`, `ui/components/mis_trade_advisory.py` | Sub-tab |
| **Portfolio** | `ui/pages/zerodha.py`, `ui/pages/daily_advisor.py` | Merge advisor into portfolio |
| **Research (fast)** | `ui/pages/single_stock.py`, `ui/components/advice.py` | Verdict-first layout |
| **Research (deep)** | `ui/pages/alpha_ai.py` | Rename sections, hide % |
| **Research (compare)** | `ui/pages/compare.py` | Winner-first |
| **Results** | `ui/pages/track_record.py`, `ui/components/watchlist_stats.py` | Plain English scorecard |
| **Settings** | `ui/components/setup_wizard.py`, `broker_startup.py`, `autopilot.py`, `telegram_subscribe.py`, `ui/pages/beginner_risk.py` | New settings page |
| **Ask overlay** | `ui/components/command_palette.py` | Promote to header modal |
| **Nav** | `ui/theme.py`, `ui/components/navigation_bar.py`, `app.py` | 5-tab structure |
| **Chrome** | `app.py` | Remove sidebar defaults; footer disclaimer |

## 9.2 Phase 0 — Foundation (Week 1)

**Goal:** New shell without breaking engines.

| Task | Deliverable |
|------|-------------|
| Rename app title to "AI Trading Decision System" | `app.py`, `theme.py` |
| Implement 5-tab nav + Settings icon | `NAV_GROUPS` rewrite |
| Move disclaimer to footer | `app.py` |
| Create design tokens CSS | `ui/theme.py` → `MENTOR_UI_CSS` |
| Build shared components: `VerdictBanner`, `PrimaryCTA`, `WhyExpander`, `ReleaseButton` | `ui/components/mentor/` |
| Feature flag `MENTOR_UX=1` for gradual rollout | env toggle |

**Exit criteria:** Nav works; old pages still render inside new tabs.

## 9.3 Phase 1 — Today (Week 2)

**Goal:** Morning briefing is one narrative.

| Task | Deliverable |
|------|-------------|
| Implement `MentorBriefing` | `home_dashboard.py` full rewrite |
| Map all Today states (WAIT, ACT, CLOSED, etc.) | State machine doc in code comments |
| Remove five-card layout | Delete assist-card pattern from Home |
| Add reading time + release CTA | Today footer |
| Header Ask overlay (basic) | `command_palette.py` → modal |

**Exit criteria:** WAIT day readable in ≤20s, zero scroll, one CTA.

## 9.4 Phase 2 — Trade + Results (Week 3)

**Goal:** Execution and accountability paths.

| Task | Deliverable |
|------|-------------|
| Trade page: starred picks only | `intraday_watchlist.py` slim |
| Trade → Options sub-tab | embed `live_options_advisor` |
| Remove scoring from Trade | move to Results |
| Results page: weekly sentence headline | `track_record.py` |
| Rename Track Record → Results in nav | `theme.py` |

**Exit criteria:** Today → Trade → Kite path in 2 tabs.

## 9.5 Phase 3 — Portfolio (Week 4)

**Goal:** Merge Daily Advisor into Portfolio.

| Task | Deliverable |
|------|-------------|
| Portfolio briefing banner first | merge `daily_advisor.py` display |
| Collapsed holdings table | `zerodha.py` |
| Remove Daily Advisor tab | nav update |
| Broker connect CTA in empty state | `empty_states.py` |

**Exit criteria:** Portfolio answers "do I need to change anything?" above fold.

## 9.6 Phase 4 — Research (Week 5)

**Goal:** One research entry, two depths.

| Task | Deliverable |
|------|-------------|
| Merge Single Stock + Alpha AI tabs | Research tab with fast/deep |
| Verdict-first `render_advice` | `advice.py` |
| Alpha section rename map | `alpha_ai.py` |
| Compare winner-first | `compare.py` |
| Ask overlay unified search | header |

**Exit criteria:** Search TCS → verdict in <10s.

## 9.7 Phase 5 — Settings + demotion (Week 6)

**Goal:** Clean chrome; advanced tools hidden.

| Task | Deliverable |
|------|-------------|
| New Settings page | absorb sidebar |
| Remove default sidebar | `app.py` |
| Demote Market Pulse, Screener, etc. | Settings → Advanced |
| First-run modal | `onboarding.py` rewrite |
| Remove "Investment OS" copy everywhere | grep sweep |

**Exit criteria:** New user sees 5 tabs + Settings only.

## 9.8 Phase 6 — Polish (Week 7)

| Task | Deliverable |
|------|-------------|
| Mobile QA on Today + Trade | responsive fixes |
| Tone of voice grep lint (banned words CI script) | `scripts/lint_copy.py` optional |
| Empty/error states per spec | all screens |
| Remove `MENTOR_UX` flag — make default | cleanup |

## 9.9 Navigation migration table

| Old tab | New location |
|---------|--------------|
| Home | **Today** |
| Suggestions | **Trade** |
| Track Record | **Results** |
| My Portfolio | **Portfolio** |
| Daily Advisor | **Portfolio** (merged) |
| Single Stock | **Research** (fast) |
| Alpha AI | **Research** (deep) |
| Compare | **Research** (compare mode) |
| Live Options Coach | **Trade → Options** |
| NSE Options | **Trade → Options** (chain detail link) |
| Live Charts | **Trade → Advanced link** |
| Market Pulse | **Settings → Advanced** |
| Screener | **Settings → Advanced** |
| Batch Scanner | **Research → Paste list** |
| Penny Picks | **Research → preset** |
| Global Markets | **Today expander + Advanced** |
| Risk & Goals | **Settings → Risk** |
| SIP & Goals | **Portfolio → Long-term** |
| Backtest | **Settings → Advanced** |
| Varsity TA | **Research contextual links** |

## 9.10 Copy grep checklist (pre-release)

Run before launch — fail build if found in `ui/` default strings:

```
Investment OS
Decision Engine
Evidence packet
Synthesis
Calibration
broker truth
combined score
prep score
Market regime
Risk mode
snapshot_id
```

## 9.11 Testing checklist (UX acceptance)

| # | Test | Pass |
|---|------|------|
| 1 | WAIT day Today fits one iPhone screen without scroll | |
| 2 | User can state recommendation aloud after 20s on Today | |
| 3 | Every screen has exactly one primary CTA | |
| 4 | No banned words on Today, Trade, Portfolio default view | |
| 5 | ACT path: Today → Trade in one tap | |
| 6 | Portfolio shows briefing before holdings table | |
| 7 | Research search → verdict before metrics | |
| 8 | Results headline is plain English sentence | |
| 9 | Broker disconnected → clear Connect CTA on Today + Portfolio | |
| 10 | Post-close → Score picks CTA on Results | |

---

# Appendix A — State machine (Today verdict)

```
Inputs (implementation):
  decision.verdict, snapshot.risk_mode, mis.flags, mis.loss_streak_days,
  market_session.is_open, pins count, broker connected, time of day

Priority (highest wins):
  1. Market closed (weekend/holiday) → MARKET_CLOSED
  2. Broker required but missing (first run) → BROKER_STALE
  3. loss_streak >= 3 → DON'T_TRADE
  4. decision ACT + starred pin → ACT
  5. decision PASS / NO_TRADE → DON'T_TRADE
  6. decision REDUCE / DEFENSIVE → STAY_CAUTIOUS
  7. decision WAIT + restrictions → WAIT
  8. pins empty post-close → NO_SETUPS
  9. Default → WAIT
```

---

# Appendix B — Engineer FAQ

**Q: Do we change backend engines?**  
A: No. This spec changes presentation, navigation, copy, and layout only. Map existing outputs to mentor copy.

**Q: Can we show percentages anywhere?**  
A: Only inside collapsed "See why" sections. Default = High/Medium/Low.

**Q: What about `deep` / live synthesis toggle?**  
A: Remove from default UI. Run automatically on Today load if needed; never expose toggle to user.

**Q: What replaces sidebar market selector?**  
A: Settings → Preferences. Today uses profile market default.

**Q: Simple cloud mode?**  
A: Today · Trade · Research · Results · Settings. Portfolio appears after broker connect.

**Q: Is Home gone?**  
A: Renamed to **Today**. Route `nav_tab == "Home"` → display "Today" label.

---

*AI Trading Decision System — UX Specification v1.0*  
*Implementation-ready. No further UX clarification required for frontend build.*
