# UX & Product Audit — Stock Analyzer Investment OS

**Date:** 2026-07-16  
**Auditor lens:** Principal Product Designer · UX Researcher · Product Manager  
**Benchmarks:** Bloomberg Terminal · TradingView · Tickertape · INDmoney · Zerodha Kite · Smallcase · Moneycontrol  
**Constraint:** Product/UX only — no backend, no code proposals  
**Method:** Full navigation map review, page-by-page evaluation, first-time investor mental walkthrough

---

## 1. Executive Summary

This application is **technically one of the most capable personal investment platforms ever built for a single developer** — broker truth, context/evidence/decision/learning engines, multi-timeframe scans, options coaching, institutional research, and portfolio intelligence coexist in one Streamlit shell.

**The product fails at its job anyway.**

Not because features are missing. Because **the product exposes the machine instead of the decision.**

A first-time investor landing on Home sees: *Investment Operating System · Market · Decision · Opportunities · Risk · Evidence summary · Synthesis · Calibration · Broker-backed outcomes*. They do not see: **"Trade today: No. Reason: choppy open. Best idea: wait for RELIANCE pullback."**

| Dimension | Verdict |
|-----------|---------|
| **Engine depth** | World-class for personal use |
| **Decision clarity** | Weak — buried under implementation language |
| **Navigation** | Overloaded — 20 pages, 5 categories, duplicate entry points |
| **First-time path** | Exists (onboarding) but competes with 19 other tabs |
| **Portfolio UX** | Data-rich, action-poor |
| **Research UX** | Excellent on Alpha AI / Single Stock; fragmented elsewhere |
| **Visual design** | Improving (Home dashboard CSS) but inconsistent across tabs |
| **Morning decision flow** | Partially answerable on Home; not in 30 seconds for a novice |

**Brutal truth:** This is a **Bloomberg Terminal built without a Bloomberg information hierarchy.** Power users will love it after 2 weeks. First-time users will bounce in 2 minutes.

**Strategic recommendation:** Version 2.0 is not "more features." It is **one decision per screen, three primary journeys, everything else in Advanced.**

---

## 2. Overall UX Score: **42 / 100**

| Criterion | Score | Notes |
|-----------|-------|-------|
| First-5-second comprehension | 35 | Home tagline is clear; content is not |
| Navigation efficiency | 40 | 20 pages; 2-click minimum for any task |
| Visual hierarchy | 48 | Home dashboard strong; other pages Streamlit-default |
| Consistency | 38 | Naming mismatches (Suggestions/Intraday), duplicate widgets |
| Error/empty states | 55 | Good empty states on Portfolio, Risk; poor on Home opportunities |
| Mobile | 45 | Compact nav exists; density still high |
| Accessibility of jargon | 30 | Evidence packets, synthesis, calibration — engineer language |
| Delight | 50 | Sticky Alpha summary, verdict colors — underused elsewhere |

---

## 3. Overall Product Score: **68 / 100**

| Criterion | Score | Notes |
|-----------|-------|-------|
| Problem-solution fit (active trader) | 78 | MIS workflow + track record is rare in retail tools |
| Problem-solution fit (long-term investor) | 62 | SIP, Alpha AI, Portfolio — scattered |
| Differentiation vs Kite | 72 | Decision engine + learning loop Kite does not have |
| Differentiation vs Tickertape | 65 | Deeper but less polished |
| Retention mechanics | 70 | Track record, autopilot, journal — strong if user survives week 1 |
| Monetization clarity | N/A | Personal desktop — not assessed |
| Trust & disclaimers | 75 | Varsity alignment, repeated disclaimers |
| Scope discipline | **35** | Too many parallel "find stocks" surfaces |

**Product is strong. Packaging is the bottleneck.**

---

## 4. Top 20 UX Problems

1. **20 top-level pages** — cognitive overload; no single "today" mode vs "research" mode.
2. **Implementation vocabulary on Home** — "Evidence packet," "synthesis," "broker-backed calibration" instead of plain decisions.
3. **Suggestions tab ≠ Intraday naming** — file, copy, and nav disagree; Home quick action links to broken tab `"Intraday"`.
4. **Five different "find stocks" flows** — Quick scan, Batch Scanner, Screener, Market Pulse, Penny Picks — user cannot choose.
5. **Three options surfaces** — NSE Options, Live Options Coach, Single Stock options footer — no guidance which to use.
6. **Home vs Suggestions workflow split** — daily guide on Home, execution on Suggestions; neither is complete alone.
7. **Market Pulse page length** — 1–2 minute load; expert-only density; duplicates Home + Suggestions + Live Charts.
8. **Command palette hidden** — best navigation tool collapsed in expander; most users never find ⌘ Jump.
9. **Sidebar competes with main nav** — Setup, Data health, Autopilot, Telegram, Kite, Varsity — settings mixed with trading.
10. **Track Record before value** — scoring, gates, calibration — meaningless until user has 5+ trading days.
11. **Portfolio page is CRUD-first** — manual entry radio before "what should I do with my holdings."
12. **Daily Advisor duplicates My Portfolio analyze** — two briefing surfaces, unclear precedence.
13. **Confidence scores everywhere** — different scales (%, combined score, penny score, prep score) — incomparable.
14. **Expanders as primary UI** — advanced features buried; critical features also buried (same pattern).
15. **India-first without graceful US mode** — gates, copy, presets assume NSE; US user sees degraded experience silently.
16. **Orphan components** — `unified_prep.py`, `investment_os_ui.py` built but unreachable — sign of IA drift.
17. **Broker gate blocks Portfolio** — correct technically; terrible first-time experience before login works.
18. **No global "Should I trade today?" banner** — exists in pieces across Home, MIS strip, morning cockpit.
19. **Scrolling fatigue** — Alpha AI, Market Pulse, Suggestions, Single Stock — all require long scroll to answer one question.
20. **No progressive disclosure contract** — beginner Risk page is excellent; rest of app ignores that standard.

---

## 5. Top 20 Product Strengths

1. **Closed-loop learning** — prep → trade → broker truth → calibration — genuinely novel for retail.
2. **Home dashboard ambition** — correct V2 north star: market + decision + opportunities + portfolio on one screen.
3. **Entry / Stop / Target on suggestions** — actionable, not just "bullish" — beats Moneycontrol/Tickertape alerts.
4. **Hit target tracking** — Track Record answers "was the app right?" — rare accountability.
5. **Alpha AI v3.0 structure** — Executive Summary first; institutional format done right.
6. **Risk & Goals page** — best beginner UX in the entire app; should be the template.
7. **Varsity TA integration** — education tied to signals; aligns with Zerodha ethos.
8. **Broker-connected portfolio** — when OAuth works, auto-sync + live LTP is Kite-plus.
9. **Global Markets → India bias** — clear narrative; actionable "what to do in India."
10. **Compare page** — focused, fast, understandable in 5 seconds.
11. **Onboarding "Start here"** — 4-step workflow is the right story; needs to be the app, not an expander.
12. **Command palette concept** — power-user navigation done right (when discovered).
13. **MIS trade advisory strip** — TRADE / CAUTION / NO TRADE is correct decision language.
14. **SIP & Goals planner** — serves wealth-building user, not just traders.
15. **Autopilot for Mac** — reduces daily friction for repeat users.
16. **Decision verdict taxonomy** — ACT / WAIT / PASS / REDUCE / DEFENSIVE — good framework if surfaced consistently.
17. **Evidence engine (conceptually)** — "why" behind decisions — product gold, UX lead.
18. **Options OR gate + sideways advisor** — sophisticated; right for advanced lane.
19. **Penny Picks honesty** — prominent risk warning; doesn't pretend safety.
20. **Simple cloud mode** — proves team knows nav is too heavy; should be default for new users.

---

## 6. Navigation Audit

### Structure today

```
Category (5) → Page (20)
Sidebar: Market, Period, Theme, Setup, Data Health, Autopilot, Onboarding, Telegram, Kite
Top: Command palette, Quick links, Disclaimer, Onboarding tour
Home-only: compact nav, no sidebar clutter
```

### Clicks to common tasks (from cold start, default Home)

| Task | Clicks | Path |
|------|--------|------|
| Should I trade today? | 0–1 | Home (if loaded) — **but answer not plain-text** |
| See today's picks | 2 | Category → Suggestions |
| Star a pick | 3+ | Suggestions → find watchlist → star |
| Check portfolio | 2 | Category → My Portfolio |
| Research one stock | 2–3 | Research → Single Stock → Analyze |
| Institutional report | 2–3 | Research → Alpha AI → Generate |
| Options trade idea | 2 | More trading → Live Options Coach |
| Hit rate / accountability | 2 | Suggestions → Track Record |
| Change risk/capital | 2+ | Suggestions → expander → or Home settings |
| Connect Zerodha | 1–2 | Portfolio gate or sidebar |

### Navigation verdict

| Question | Answer |
|----------|--------|
| Can navigation be reduced? | **Yes — 20 → 6 primary surfaces** |
| Unnecessary pages? | Batch Scanner, Penny Picks, Varsity (as tab), Backtest (for beginners), NSE Options (merge) |
| Belongs in Settings? | Setup wizard, Data health, Autopilot, Telegram, Theme, Broker credentials, Score gates |
| Advanced mode? | Market Pulse, Live Charts, Batch Scanner, Screener, Backtest, Live Options Coach, NSE Options |

### Recommendation

**Primary nav (6):** Today · Trade · Portfolio · Research · Learn · Settings  
Everything else: tabs within those shells or Advanced toggle.

---

## 7. Information Architecture Audit

### Duplicate reports

| Content | Locations |
|---------|-----------|
| Market regime / session | Home, Market Pulse, Global Markets, morning cockpit, MIS strip |
| Today's decision | Home, Suggestions phase banner, MIS advisory, Live Options Coach header |
| Top opportunities | Home opportunities, Suggestions watchlist, Market Pulse BUY cards, unified_prep (orphan) |
| Portfolio summary | Home portfolio section, My Portfolio, Daily Advisor |
| Hit rate / learning | Home learning, Track Record, Suggestions weekly metric |
| Confidence | Home opportunities %, pulse combined score, Alpha AI %, prep score, watchlist score |
| Global bias | Home market section, Global Markets page |
| Options idea | NSE Options, Live Options Coach, Market Pulse index options, Single Stock footer |

### Duplicate watchlists

- Suggestions intraday watchlist (pinned plans)
- Home watchlist section (same pins)
- My Portfolio Kite watchlist mirror
- Market Pulse intraday watchlist strip
- Options expiry watchlist component

### Duplicate recommendations

- Investment OS verdict
- MIS trade advisory
- Decision engine artifact
- Pulse BUY suggestions (3 horizons)
- Alpha AI verdict
- Single Stock advice block
- Daily Advisor priority actions

### IA verdict

**The app has one engine and seven mouths.** Users hear seven slightly different answers to the same question.

**Fix (product, not code):** Designate **one canonical answer per question** per session; all other surfaces link to it.

---

## 8. Home Page Audit

### Purpose (intended)

Single-screen Investment OS: market context → today's decision → opportunities → portfolio → learning.

### 5-second test (first-time user)

**Fail.** User sees branded header and section titles but not a plain sentence: *"Do not trade today"* or *"Trade RELIANCE long above ₹2,850."*

### Question answered

*"What should I pay attention to today?"* — partially, if nightly scan ran and portfolio exists.

### Primary action

Unclear. Buttons: star picks, scan tonight, open portfolio, intraday (broken), market pulse, log P&L.

### Verdict: **Keep — but promote to only landing; strip engine jargon; fix broken Intraday nav**

### Widget audit (Home)

| Widget | Purpose | Importance | Confusion | Recommendation |
|--------|---------|------------|-----------|----------------|
| Market section | Regime, VIX, global bias | High | Medium — too many labels | **Keep** — simplify to 3 bullets |
| Decision section | ACT/WAIT verdict | Critical | High — evidence jargon | **Keep** — lead with one sentence verdict |
| Opportunities | Starred picks + levels | Critical | Low when populated | **Keep** — empty state needs CTA to Quick scan |
| Portfolio section | Value, P&L, count | High | Medium | **Keep** — add "weakest / strongest" line |
| Watchlist section | MIS/session context | Medium | High for beginners | **Merge** into Opportunities |
| Learning section | Yesterday vs reality | Medium | High — "calibration" | **Move** to Track Record |
| Quick actions | Nav shortcuts | Medium | High — broken Intraday | **Keep** — fix labels, reduce to 3 |
| Capital settings | Risk prefs | Medium | Low | **Move** to Settings |
| Live synthesis toggle | Deep analysis | Low | Very high | **Hide** in Advanced |

---

## 9. Portfolio Audit

### Purpose

Holdings source of truth + live sync + analysis.

### 5-second test

**Partial pass** if broker connected and holdings synced — user sees count and header.  
**Fail** for "what should I do?" — requires Analyze button + reading signals table.

### Questions answered

- What do I own? **Yes**
- Portfolio health? **Partial** — risk section exists but not above fold
- Weakest holding? **No** — not surfaced
- Best holding? **No**
- Cash available? **Broker header only** — not prominent
- Recommended action? **No** — must open Daily Advisor or Analyze

### Missing for instant clarity

1. **Health score** (0–100) with color — like INDmoney/Smallcase
2. **Today's action per holding** — one line each (Daily Advisor exists but separate page)
3. **Weakest / strongest** — by P&L %, risk, or signal
4. **Cash + margin** — tile at top
5. **Concentration warning** — sector/single-name risk in plain language
6. **Primary CTA** — "Sync" and "What should I do today?" not "Manual entry"

### Page verdict: **Keep — promote Daily Advisor summary inline; demote CRUD to Settings**

### Widget audit (Portfolio)

| Widget | Recommendation |
|--------|----------------|
| Broker gate | **Keep** — add "continue with manual portfolio" faster path |
| Entry mode radio (manual/CSV/paste) | **Move** to Settings/onboarding |
| Manual data editor | **Hide** default — power feature |
| Kite watchlist mirror | **Merge** with watchlist concept app-wide |
| Live prices expander | **Keep** — promote if market open |
| Analyze portfolio | **Keep** — rename "Portfolio health check" |
| Signals table | **Keep** — sort by urgency |
| Risk section | **Promote** above fold |
| Open Daily Advisor | **Merge** — inline briefing |

---

## 10. Research Audit

### User question

Search stock → Should I buy? Why? Risk? Entry? Target? Confidence?

### Surface comparison

| Surface | Buy? | Why? | Risk? | Entry? | Target? | Confidence? | 5-sec? |
|---------|------|------|-------|--------|---------|-------------|--------|
| **Single Stock** | Partial | Yes | Partial | Yes | Yes | Combined score | 7/10 — needs Analyze click |
| **Alpha AI** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** | 6/10 — long scroll |
| **Compare** | Winner only | Limited | No | No | No | Scores | 8/10 |
| **Market Pulse** | BUY cards | Limited | No | Sometimes | Sometimes | Combined | 4/10 |
| **Command palette → Single Stock** | Same | — | — | — | — | — | 8/10 if discovered |

### Verdict

**Alpha AI and Single Stock achieve the research job** — but user must know which to use.  
**Alpha AI** = "should I invest (months)?"  
**Single Stock** = "what's the trade setup (days/weeks)?"  
This distinction is **never explained in product copy.**

### Recommendation

**One Research search box** → routes to Single Stock (fast) or Alpha AI (deep) with one-line choice.  
Remove parallel scan paths from Research mental model.

---

## 11. Visual Design Audit

### Spacing

- **Home:** Good — `dash-wrap`, card padding, section heads (best in app).
- **Other pages:** Default Streamlit — cramped radios, stacked expanders.

### Typography

- Home uses uppercase section labels + hierarchy — **professional**.
- Elsewhere: default Streamlit fonts — **inconsistent brand**.

### Card hierarchy

- Home `dash-card` / verdict classes — excellent pattern.
- Not reused on Suggestions, Market Pulse, Portfolio — **missed system**.

### Scrolling

- **Critical issue** — Alpha AI, Market Pulse, Suggestions are scroll-marathons.
- TradingView solves with fixed header + tabs; Kite with sparse home + depth on demand.

### Accordions / expanders

- Overused as **primary** UI on Suggestions (3 nested), Track Record, sidebar.
- Expanders should hide **advanced**, not **core workflow**.

### Tables

- Functional; dense on Market Pulse and Track Record.
- Missing: row highlighting for "your starred picks" consistently.

### Charts

- Plotly defaults; adequate.
- Live Charts grid — powerful but no visual priority (everything equal weight).

### Consistency

- Verdict colors defined in theme — **not applied app-wide**.
- REC_COLORS, ACTION_COLORS exist — underutilized outside Alpha AI.

### Dark theme

- Default Streamlit dark + custom HOME_UI_CSS.
- Light theme toggle exists — good.
- Cards on Home assume dark rgba backgrounds — may clash in light mode.

### Color usage

- Green/red/yellow semantics consistent in theory; too many badge types in practice.

### Information density

- **Market Pulse:** Bloomberg-level density without Bloomberg layout training.
- **Risk & Goals:** Goldilocks density — **use as reference**.

### Visual score: **45/100** — one polished screen (Home) in a Streamlit-default app.

---

## 12. Decision Flow Audit (9:00 AM)

*Can user answer in 30 seconds?*

| Question | 30-sec answer? | Why not |
|----------|----------------|---------|
| 1. Should I trade today? | **Partial** | Home shows verdict but wrapped in engine terms; MIS strip on other tabs only |
| 2. Should I wait? | **Partial** | WAIT exists as verdict — not plain language |
| 3. Which stock? | **Only if scanned** | Empty opportunities without prior nightly Quick scan |
| 4. Entry? | **Yes** — if picks exist | On Home opportunities / Suggestions |
| 5. Stop loss? | **Yes** — if picks exist | Same |
| 6. Target? | **Yes** — if picks exist | Same |
| 7. Why? | **Fail for novice** | Evidence summary uses packet labels; synthesis toggle hidden |

### 9:00 AM failure modes

1. User skipped last night's Quick scan → **no opportunities anywhere**.
2. User on Portfolio tab → **no decision context**.
3. User expects Kite-like sparse home → **overwhelmed by OS dashboard**.
4. Options trader opens Suggestions → **equity-first workflow**.

### Decision flow score: **55/100** for prepared user · **25/100** for first-time user.

---

## 13. Duplicate Components

| Component | Also appears as | Recommendation |
|-----------|-----------------|----------------|
| `morning_cockpit` | Home decision, MIS strip | **Merge** into Today view |
| `mis_trade_advisory` | Home decision section | **Single canonical strip** |
| `suggestions_home` | Suggestions page, onboarding refs | **Keep** on Trade tab only |
| `intraday_watchlist` | Home watchlist, Market Pulse | **One watchlist** |
| `options_expiry_watchlist` | Suggestions, unified_prep (orphan) | **Merge** into Trade → Options |
| `portfolio_broker_header` | Home portfolio | **Keep** — standardize |
| `kite_banner` / `broker_connect` | Portfolio gate, sidebar | **Settings** |
| `data_health_panel` | Sidebar | **Settings** |
| `autopilot` | Sidebar | **Settings** |
| `setup_wizard` | Sidebar | **Settings** |
| `daily_playbook` / `daily_cheat_sheet` | Overlaps Daily Advisor | **Merge or remove** |
| `strategy_synthesis` | Home toggle | **Advanced** |
| `prep_all` / `unified_prep` | Orphan | **Remove or wire** |
| `investment_os_ui` | Orphan | **Remove or replace Home internals** |
| `watchlist_stats` | Track Record, Suggestions | **Track Record only** |
| `navigation_bar` + `command_palette` + `tab_quick_links` | Triple nav | **One search + 6 tabs** |

---

## 14. Pages to Remove

| Page | Rationale |
|------|-----------|
| **Varsity TA** (as top-level tab) | Move to Learn drawer + contextual links from signals; not a daily destination |
| **Penny Picks** | Niche; inject as Screener preset only |
| **NSE Options** (standalone) | Fully subsumed by Live Options Coach for active traders |
| **Batch Scanner** (as tab) | Merge into Screener as "paste tickers" mode |

*Remove from primary nav, not necessarily delete backend.*

---

## 15. Pages to Merge

| Merge into | Sources |
|------------|---------|
| **Today (Home)** | Home + morning cockpit + learning teaser + global bias tile |
| **Trade** | Suggestions + Live Charts (equity) + Live Options Coach (options sub-tab) |
| **Portfolio** | My Portfolio + Daily Advisor briefing inline |
| **Research** | Single Stock + Alpha AI (one search, two depths) + Compare |
| **Discover** | Screener + Market Pulse (advanced scan) + Penny preset |
| **Accountability** | Track Record + trade journal + exports |
| **Learn** | Varsity TA + Backtest + SIP & Goals |
| **Settings** | Risk prefs, broker, autopilot, telegram, data health, setup |

---

## 16. Pages to Hide (Advanced mode)

| Page | Trigger |
|------|---------|
| Market Pulse | "Full market scan" link from Today |
| Live Charts | Trade → Charts sub-tab |
| Backtest | Learn → Advanced |
| Batch Scanner | Discover → paste list |
| Global Markets | Today → "World markets" expander (summary on Home already) |
| Live synthesis / deep analysis | Settings → Power user |

---

## 17. Pages to Promote

| Page | Why |
|------|-----|
| **Home / Today** | Only landing — the OS promise |
| **Risk & Goals** | Best beginner UX — force onboarding step 1 |
| **My Portfolio** | Wealth identity — connect broker early |
| **Suggestions / Trade** | Core differentiated loop |
| **Alpha AI** | Flagship research — marketing headline |
| **Track Record** | Trust builder — "we score ourselves" |
| **Onboarding** | Not sidebar — modal on first launch |

---

## 18. Quick Wins (High Impact, Low Effort)

1. **Fix Home → "Intraday" button** → navigate to Suggestions (product copy fix).
2. **Rename consistently** — Suggestions everywhere; remove "Intraday" from user-facing text.
3. **Home hero line** — one plain sentence above fold: `Today's call: WAIT — choppy open, no starred setups.`
4. **Empty opportunities CTA** — "Run Quick scan tonight" button with one sentence why.
5. **Promote ⌘ Jump** — visible search bar, not collapsed expander.
6. **Portfolio top tile** — holdings count, today's P&L, cash, `[Sync]` `[What should I do?]`.
7. **Research chooser** — Single Stock caption: "Fast setup · Alpha AI: full report."
8. **Collapse sidebar** on first run — only Market + Start here; rest in Settings.
9. **Apply Home card CSS** to Suggestions header and Portfolio header — visual consistency.
10. **Simple mode default** for new users — 6 tabs not 20; opt into full nav.
11. **Hide orphan features** — don't advertise unified_prep / investment_os_ui until wired.
12. **One confidence legend** — tooltip explaining scores once per session.
13. **Track Record** — rename user-facing: "Did we get it right?"
14. **Daily Advisor** — first panel on Portfolio when holdings exist.
15. **Disclaimer** — move to footer; stop repeating top of every non-Home page.

---

## 19. Major Redesign Opportunities

### A. Three-mode product shell

| Mode | User | Surfaces |
|------|------|----------|
| **Today** | Every morning | Decision, opportunities, portfolio snapshot |
| **Research** | On demand | Search → report |
| **Advanced** | Power users | Scans, charts, options, backtest |

### B. Decision-first language layer

Map every engine output to:

```
VERDICT (1 word) → REASON (1 sentence) → SETUP (entry/stop/target) → WHY (3 bullets) → DETAILS (expand)
```

Never show "evidence packet ID" or "synthesis" to default users.

### C. Unified watchlist object

One starred-picks list — appears on Today, Trade, and Kite sync — not four implementations.

### D. Portfolio as wealth dashboard (INDmoney/Smallcase pattern)

Health score · weakest link · suggested rebalance · today's actions — not a spreadsheet editor.

### E. Settings as first-class destination

Broker, autopilot, telegram, gates, theme, data health, API — **out of trading path**.

### F. Mobile-first Today view

Single column, max 2 screens scroll, no tables before decision.

---

## 20. Vision for Version 2.0

### North star

> **"Open the app at 9:00 AM. In 10 seconds, know whether to trade, what to trade, and why — or confidently wait."**

### V2.0 IA (6 destinations)

```
TODAY          → Decision + opportunities + portfolio pulse + world bias (1 screen)
TRADE          → Starred setups · live session · options (sub-tabs)
PORTFOLIO      → Holdings · health · today's actions · sync
RESEARCH       → Search any stock → Fast / Deep report
RESULTS        → Hit rate · journal · calibration · exports
SETTINGS       → Broker · risk · autopilot · alerts · advanced
```

### V2.0 first-time journey (10 minutes)

1. **Welcome** — "Long-term wealth or active trading?" (routes defaults)
2. **Risk & Goals** — capital, experience (existing page — perfect)
3. **Portfolio** — connect Zerodha or add 3 holdings manually
4. **Tonight** — "Come back after 3:30 PM for tomorrow's picks" (one CTA)
5. **Day 2** — Quick scan → star 2 → trade → Track Record

### V2.0 visual language

- **Home card system everywhere** — verdict colors, section heads, max width 1120px
- **One sticky decision bar** — persists across tabs until dismissed
- **Plain Hindi-English microcopy** optional layer (Kite/Tickertape lesson)

### V2.0 what we deliberately drop from default view

- Market Pulse as daily page
- Triple options entry
- Batch Scanner tab
- Engine internals (packets, synthesis, calibration words)

### V2.0 benchmark ambition

| Competitor | Learn from | Beat them on |
|------------|------------|--------------|
| **Kite** | Sparse home, fast broker actions | Decisions + accountability loop |
| **Tickertape** | Clean screener, stock pages | Entry/stop/target + hit rate |
| **INDmoney** | Portfolio health, simplicity | Depth when user drills in |
| **Smallcase** | Narrative, risk clarity | Custom OS + broker truth |
| **TradingView** | Chart-first, layouts | India MIS workflow + learning |
| **Bloomberg** | Information hierarchy | Approachability + personal scale |
| **Moneycontrol** | News, familiarity | Actionable levels, not just quotes |

---

## Appendix A — Page-by-Page Scorecard

| Page | Purpose (1 line) | 5-sec? | Primary action | Verdict |
|------|------------------|--------|----------------|---------|
| Home | Today's OS dashboard | No | Unclear | **Keep** (promote) |
| Suggestions | Trade workflow hub | No | Quick scan | **Keep** → Trade |
| Track Record | Hit rate accountability | No | Score/validate | **Keep** → Results |
| Risk & Goals | Beginner risk sizing | **Yes** | Analyze risk | **Keep** → onboarding |
| SIP & Goals | Long-term SIP plan | Yes | Build plan | **Keep** → Learn |
| Market Pulse | Full Nifty scan | No | Refresh scan | **Hide** advanced |
| Daily Advisor | Portfolio briefing | Partial | Generate | **Merge** Portfolio |
| Global Markets | World → India bias | Partial | Auto-refresh | **Hide** (summary on Today) |
| Single Stock | One-stock analysis | Yes | Analyze | **Keep** → Research |
| Alpha AI | Institutional report | Partial | Generate | **Keep** → Research |
| Compare | Rank 2–4 stocks | **Yes** | Compare | **Keep** → Research |
| Live Charts | Minute narratives grid | No | Refresh | **Hide** → Trade |
| Live Options Coach | Live CE/PE advisor | No | Auto-refresh | **Keep** → Trade |
| NSE Options | Static chain picks | Partial | Load chain | **Remove** tab |
| Batch Scanner | Paste list scan | Partial | Scan batch | **Merge** Discover |
| Screener | Filter universe | No | Run screener | **Keep** → Discover |
| Penny Picks | Low-price setups | Yes | Scan | **Remove** tab |
| My Portfolio | Holdings + analysis | Partial | Sync/Analyze | **Keep** (promote) |
| Backtest | Historical sim | Partial | Run backtest | **Hide** → Learn |
| Varsity TA | TA encyclopedia | **Yes** | Search chapter | **Remove** tab |

---

## Appendix B — User Journey Scores

| Journey | Steps today | Friction | Score | V2 target |
|---------|-------------|----------|-------|-----------|
| **1. Morning open (9:00)** | Open → Home → interpret jargon | High | **4/10** | **9/10** |
| **2. Portfolio review** | Nav → Portfolio → Analyze → read tables | Medium | **6/10** | **8/10** |
| **3. Research new stock** | Nav → Single Stock OR Alpha AI (guess) | Medium | **7/10** | **9/10** |
| **4. Execute trade** | Suggestions → star → Kite (external) | Medium | **7/10** | **8/10** |
| **5. End-of-day review** | Track Record OR Suggestions score | High — two paths | **5/10** | **9/10** |

---

## Appendix C — Benchmark Summary

### They do better

| Product | Wins |
|---------|------|
| **Kite** | Speed, sparse UI, order placement, trust |
| **TradingView** | Charts, layouts, community, polish |
| **Tickertape** | Stock page clarity, screener UX, visual design |
| **INDmoney** | Portfolio health narrative, simplicity |
| **Smallcase** | Investment story, risk communication |
| **Moneycontrol** | News, familiarity, low learning curve |
| **Bloomberg** | Information hierarchy, keyboard workflow |

### We do better

| Capability | Notes |
|------------|-------|
| **Accountability loop** | Hit target tracking — none of them score themselves daily |
| **Entry/stop/target discipline** | Actionable MIS workflow |
| **Broker truth learning** | Outcomes tied to real fills |
| **Decision + evidence architecture** | Depth of "why" (when surfaced properly) |
| **Alpha AI report depth** | Rivals Tickertape Pro + more structure |
| **Options session coaching** | OR gate, sideways advisor — Kite has nothing similar |
| **Local OS integration** | Autopilot, personal desktop, full pipeline |
| **Global → India bias** | Narrative + spillover in one place |

---

*Audit complete. No code modified. Product design recommendations only.*
