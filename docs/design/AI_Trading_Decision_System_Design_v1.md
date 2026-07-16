# AI Trading Decision System — Experience Design v1.0

**Role:** Head of Design · Principal Product Designer  
**Status:** Design proposal — **not approved for build**  
**Mode:** Product design only — no code, no engineering  
**Quality bar:** Apple Wallet · Robinhood · Linear · Perplexity · Revolut · Stripe · Notion

---

## Executive challenge to prior assumptions

Your team (and our earlier architecture) made several **reasonable but wrong** choices. This document rejects them and proposes something significantly better.

| Assumption you / we made | Why it fails the "wow" test | What we do instead |
|--------------------------|----------------------------|-------------------|
| **Five top-level tabs** | Equal tabs = equal importance = dashboard. Linear ships 3–4 destinations max; Robinhood's home is *one* number. | **Verdict-first shell:** one home surface; everything else is a sheet or secondary destination. |
| **Five question-cards on Home** | Still a dashboard — the user scans sections. Apple never asks five questions on Wallet's front. | **One Verdict Canvas** — 70% of the viewport is a single human verdict. |
| **"Morning letter" with labeled sections** ("ONE THING TO WATCH") | Labels are taxonomy. Feels like a memo, not a mentor. Reading-time footer feels like Medium, not Apple. | **Mentor voice, zero labels** — one continuous message; details in a sheet. |
| **Cards as primary container** | Cards imply parity. Fintech wow = *one* object deserves elevation (Wallet pass, Robinhood position). | **One elevated surface** or **no card at all** — typography *is* the UI. |
| **Ask AI as a tab** | Tabs compete with Today for attention. Perplexity is *answer-first*, not nav-first. | **Floating Ask** — omnipresent but subordinate; answer takes the screen. |
| **Results as daily destination** | Trust is weekly, not morning. Stripe shows status when you need it — not on the homepage path. | **Results in Profile / weekly nudge** — not morning critical path. |
| **Streamlit mental model** | Expanders, sidebars, dataframes, metric columns — none of this ships at Apple. | **Native-app patterns:** bottom sheets, single column, gesture, intentional motion. |
| **High/Medium/Low badges** | Still metrics. Robinhood uses color + one word, not labels. | **Conviction in prose** — "I'm fairly sure" inside the sentence. |
| **Showing entry/stop/target grid on Home** | Execution detail belongs on the *plan*, not the *decision*. Split violated. | **Verdict on Home · Mechanics on Plan sheet** |

### The design north star (revised)

> **One screen. One breath. One verdict.**  
> Everything else is a quiet invitation — never a demand.

---

## Global experience architecture (replaces 5-tab model)

### Recommended shell: **Verdict OS**

```
┌─────────────────────────────────────┐
│  ░░░ subtle gradient / time-of-day ░░│
│                                     │
│         [ VERDICT CANVAS ]          │  ← 70% viewport
│                                     │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│  mentor message (2–3 lines)         │  ← 20%
│                                     │
│  [ Primary action ]                 │  ← 10%
│                                     │
│  ─────────────────────────────────  │
│   Today          Trades        You  │  ← bottom nav (3 only)
└─────────────────────────────────────┘
        ↑ Ask pill (floating, bottom-right)
```

| Destination | Role | Comparable |
|-------------|------|------------|
| **Today** | Verdict Canvas — default launch | Apple Weather current condition |
| **Trades** | Active + staged plans only | Robinhood position detail |
| **You** | Portfolio · Results · Settings | Apple Health + Settings |
| **Ask** (floating) | Perplexity overlay | Perplexity / Arc command bar |

**Why 3 beats 5:** Cognitive science — humans hold 3–4 chunks in working memory. Five tabs force classification before decision. **The user is not classifying; they are deciding.**

---

## Global design system

### Typography

| Token | Spec | Use |
|-------|------|-----|
| `Verdict` | SF Pro Display / Inter, **56px**, weight 600, -2% tracking | WAIT · TRADE · HOLD |
| `Mentor` | SF Pro Text / Inter, **20px**, weight 400, 1.45 line-height | Human message |
| `Detail` | 17px, weight 400, 65% opacity | Secondary facts |
| `Action` | 17px, weight 600 | Buttons |
| `Micro` | 13px, weight 500, uppercase 0.06em tracking | Rare — timestamps only |

**Rule:** No more than **3 type sizes** visible at once on any screen.

### Spacing (8pt grid)

| Token | Value |
|-------|-------|
| `space-xs` | 8px |
| `space-sm` | 16px |
| `space-md` | 24px |
| `space-lg` | 40px |
| `space-xl` | 64px |
| `space-verdict` | 48px padding around verdict word |

**Rule:** Verdict Canvas minimum **40% empty space** around focal type.

### Color

| Role | Light mode | Dark mode (default for trading) |
|------|------------|--------------------------------|
| Canvas bg | `#FAFAFA` | `#0A0A0B` |
| Verdict Trade | `#00D68F` | `#00E676` |
| Verdict Wait | `#FFB020` | `#FFC107` |
| Verdict Stop | `#FF5A5F` | `#FF6B6B` |
| Verdict Hold | `#8E8E93` | `#A1A1A6` |
| Text primary | `#1C1C1E` | `#F5F5F7` |
| Text secondary | 55% opacity | 55% opacity |
| Action fill | `#F5F5F7` on dark | `#FFFFFF` text on `#1C1C1E` |

**No gradients on verdict text.** Background may have **ultra-subtle** time-of-day ambient (pre-market: cool blue 3% tint; session: neutral).

### Motion

| Moment | Motion | Duration |
|--------|--------|----------|
| App open | Verdict word fades up 12px | 400ms ease-out |
| Verdict change | Crossfade + subtle haptic | 300ms |
| Sheet open | Spring from bottom, 24px radius | 350ms |
| Ask open | Scale from Ask pill + blur backdrop | 280ms |
| Release state | Verdict softens to gray, action morphs to "Done" | 500ms |

**Rule:** Motion communicates *state change*, never decoration.

### Components (minimal set)

| Component | When |
|-----------|------|
| `VerdictCanvas` | Today |
| `MentorBlock` | All screens — 2–3 lines max |
| `PrimaryButton` | One per screen |
| `GhostButton` | Secondary max one |
| `BottomSheet` | Plan, Why, Holdings |
| `TradeTicket` | Trades |
| `AskOverlay` | Global |
| `StatusPill` | You — broker sync |

**No:** metric tiles, dataframes, expander arrows, sidebar, card grids.

---

# SCREEN 1 — TODAY (Verdict Canvas)

## 1. UX critique of current design

| Problem | Severity |
|---------|----------|
| Five question-cards = five bosses | Critical |
| User scans UI instead of absorbing verdict | Critical |
| Section labels ("What should I do today?") = software | High |
| Confidence badges = dashboard metrics | High |
| Entry/stop/target on Home = premature execution | High |
| Broker card on Home = breaks narrative | Medium |
| Search at bottom = competes with verdict | Medium |
| Looks like Streamlit with CSS | Critical |

**Would Apple ship this?** No.  
**Would Robinhood ship this?** No — they'd show one word and a position.  
**Would Linear ship this?** No — too many sections.

---

## 2. Three concepts

### Concept A — "The Letter"
Continuous prose block, memo style, reading time footer.

### Concept B — "Verdict Canvas" *(recommended)*
Single enormous verdict word dominates viewport; mentor speaks in 2 lines beneath; one button.

### Concept C — "Mentor Thread"
iMessage-style single bubble from mentor avatar; feels chatty, younger.

---

## 3. Pros and cons

| | A Letter | B Verdict Canvas | C Mentor Thread |
|---|----------|------------------|-----------------|
| **Pros** | Familiar from architecture doc; readable | Instant comprehension; Robinhood-grade focal point; 5-second understand | Warm; human; memorable |
| **Cons** | Still read-heavy; labels creep in; not visual | Requires discipline — copy must stay short | Avatar feels gimmicky; chat UI ages poorly; implies back-and-forth |
| **15-sec test** | Borderline | Pass | Pass |
| **Apple test** | No | **Yes** | Maybe |

---

## 4–5. Recommendation & why

**Concept B — Verdict Canvas** with **mentor voice in prose** (steal C's warmth, not its chrome).

**Why superior:**
- **Pre-attentive processing:** Color + 56px word understood in **<1 second** (human factors).
- **Emotional clarity:** WAIT in amber *feels* different before reading copy.
- **Scalable:** Same layout works for TRADE, HOLD, DONE — only color + word change.
- **Permission to leave:** DONE state is visually "complete" — gray verdict, soft button — user *feels* finished.

---

## 6. Wireframe

```
┌─────────────────────────────────────┐
│ 9:14 AM                             │  micro, top-left
│                          [synced ●] │  broker dot, top-right
│                                     │
│                                     │
│                                     │
│            W A I T                  │  56px, amber, centered
│                                     │
│                                     │
│                                     │
│  I'd sit on my hands until 9:45.    │
│  Your book is fine. If RELIANCE    │
│  clears ₹2,850, that's the only    │
│  thing worth a look.                 │
│                                     │
│  ┌─────────────────────────────────┐│
│  │      You're done for today      ││  primary — morphs to release
│  └─────────────────────────────────┘│
│                                     │
│  swipe up · why I'm saying this     │  ghost text, not expander
│                                     │
│  Today      Trades        You       │
└─────────────────────────────────────┘
                              [Ask ○]  floating
```

---

## 7. Visual hierarchy

1. **Verdict word** (56px) — 70% visual weight  
2. **Mentor block** (20px) — 25%  
3. **Primary button** — 5%  
4. Everything else — invisible until requested  

---

## 8–11. Typography · Spacing · Color · Behavior

- **Typography:** Verdict 56px → Mentor 20px → Button 17px. Nothing else default.
- **Spacing:** 64px above verdict; 24px verdict-to-mentor; 40px mentor-to-button.
- **Color:** WAIT = `#FFC107`; TRADE = `#00E676`; DONE = `#A1A1A6` verdict + muted button "You're done."
- **Behavior:**
  - Pull down → refresh (subtle spinner on sync dot only)
  - Swipe up → **Why sheet** (3 bullets, no engine names)
  - Tap primary → TRADE day opens **Plan sheet**; WAIT day button does nothing (haptic + "Nothing to do" toast) OR dismisses app psychologically
  - Long-press verdict → copy summary (power user)

---

## 12. Interaction flow

```
Open app → Verdict animates in (400ms)
         → User reads (5–15s)
         → TRADE: tap "See the plan" → Plan sheet
         → WAIT: tap "You're done" → optional haptic, stay or leave
         → Ask pill anytime → Ask overlay
```

---

## 13. Empty / edge states

| State | Verdict | Mentor | Button |
|-------|---------|--------|--------|
| Loading | Pulsing `···` | "Checking your book and the market." | Disabled |
| Broker offline | `CONNECT` | "I can't see your real holdings yet." | Connect Zerodha |
| Market closed | `REST` | "Markets are closed. Nothing to do till Monday." | View your week |
| No setups | `WAIT` | "Nothing worth risking capital on today." | You're done |
| Loss streak | `PAUSE` | "Rough week. Best traders sit out." | You're done |

---

## 14. Mobile adaptation

- Verdict scales 56px → 44px on SE
- Mentor max 4 lines; truncate with sheet
- Bottom nav thumb zone; Ask pill 56px above nav
- Safe area respected — verdict never under notch

---

## 15. Accessibility

- Verdict: `aria-live="polite"` on change
- Color never sole signal — verdict word always text ("WAIT" not color-only)
- Dynamic Type: verdict scales to 40px min
- VoiceOver order: verdict → mentor → button → why hint
- Reduced motion: skip fade, instant show

---

## 16. Why users say "wow"

- **Instant emotional read** — amber WAIT hits before cognition
- **Respect for time** — nothing to tap through to get the answer
- **Feels expensive** — empty space signals confidence, not missing features
- **Human sentence** — not a dashboard pretending to care
- **Explicit release** — "You're done" is permission no competitor gives

---

# SCREEN 2 — TRADES (Trade Ticket)

## 1. UX critique of current design

Suggestions tab is a **warehouse**: watchlists, phase banners, hit-rate strips, expanders, scoring buttons, autopilot. User drowns before finding the plan.

**Violations:** five bosses, engineer copy, tables before action, Streamlit expanders.

---

## 2. Three concepts

### Concept A — List of picks (current, bad)
Table of 5 stocks with confidence %.

### Concept B — Trade Ticket *(recommended)*
Single premium "ticket" per active plan — like a boarding pass or event ticket.

### Concept C — Stepper wizard
Step 1 Trigger → 2 Size → 3 Execute. Feels onboarding, not trading.

---

## 3. Pros and cons

| | A List | B Ticket | C Stepper |
|---|--------|----------|-----------|
| Pros | Shows breadth | One focal plan; finite; actionable; beautiful object | Clear sequence |
| Cons | Screener identity | Only 1–2 visible (feature) | Too slow; patronizing |
| Robinhood test | No | **Yes** | No |

---

## 4–5. Recommendation

**Concept B — Trade Ticket.** One plan per ticket; swipe between max 2 tickets (rare).

**Why:** Trading is **commitment to one plan**. Ticket metaphor = finite, serious, premium. Boarding pass psychology: *I have a seat; I know where I'm going.*

---

## 6. Wireframe

```
┌─────────────────────────────────────┐
│ Trades                    +0 active │
│                                     │
│  ┌─ Ticket ─────────────────────┐   │
│  │  RELIANCE          LONG      │   │
│  │  ─────────────────────────── │   │
│  │  Trigger   Above ₹2,850      │   │
│  │  Stop      ₹2,820            │   │
│  │  Target    ₹2,920            │   │
│  │  Risk      ₹2,000 · 40 sh    │   │
│  │  ─────────────────────────── │   │
│  │  Valid after 9:45 AM         │   │
│  └──────────────────────────────┘   │
│                                     │
│  [ Open in Kite ]  [ Log it ]       │
│                                     │
│  ─── no other trades today ───       │
│                                     │
│  Today      Trades        You       │
└─────────────────────────────────────┘
```

---

## 7–11. Hierarchy · Type · Space · Color · Behavior

- **Hierarchy:** Symbol 28px → levels 17px mono → risk line detail
- **Type:** Symbol sans bold; numbers tabular lining (`₹2,850` aligned)
- **Space:** Ticket internal padding 24px; 16px between level rows
- **Color:** Ticket border 1px `#2C2C2E`; accent line left 4px green (long) / red (short)
- **Behavior:** Swipe ticket → second plan; tap level → copy; Kite opens external; Log → sheet

---

## 12. Interaction flow

Today TRADE → "See the plan" sheet OR Trades tab → same ticket → Kite / Log

---

## 13. Empty states

> **No active plans**  
> That's usually a good thing.  
> [ Back to Today ]

---

## 14–15. Mobile · A11y

- Ticket full-bleed minus 16px margin
- VoiceOver reads ticket as one summary string
- Large tap targets on Kite / Log (48px height)

---

## 16. Wow reasons

- **Boarding pass for money** — novel, premium metaphor
- **Mono numbers** — Stripe-grade precision feel
- **Silence when empty** — validates discipline

---

# SCREEN 3 — YOU → PORTFOLIO (Status + One Alert)

## 1. UX critique

My Portfolio leads with import radio buttons and tables. Daily Advisor duplicates with metric tiles. User sees **CRUD before counsel**.

---

## 2. Three concepts

### Concept A — Holdings table first (current)
### Concept B — Status + One Alert *(recommended)*
### Concept C — Pie chart dashboard
Rejected — chart without action = analytics app.

---

## 3–5. Recommendation

**Concept B.** Apple Health "Summary" pattern: one status sentence, **at most one alert**, holdings behind "View 12 positions."

**Why not pie chart:** User asked *what to change*, not *what's my allocation shape*.

---

## 6. Wireframe

```
┌─────────────────────────────────────┐
│ You                                 │
│                                     │
│  Portfolio                          │
│  ─────────────────────────────────  │
│  ●  Everything looks fine.          │  green dot + sentence
│                                     │
│  +₹4,200 today · 12 positions       │  one line
│                                     │
│  ┌─────────────────────────────────┐│
│  │  No changes needed              ││
│  └─────────────────────────────────┘│
│                                     │
│  View positions ▸                   │  sheet
│  Sector breakdown ▸                 │
│                                     │
│  ─── Results ───                    │
│  4 of 6 right last week  ▸          │
│                                     │
│  ─── Settings ───                   │
│  Zerodha connected  ▸               │
│                                     │
│  Today      Trades        You       │
└─────────────────────────────────────┘
```

---

## 7–16. (Summary)

- **Hierarchy:** Status sentence > CTA > links
- **Type:** Status 24px; details 17px
- **Alert state:** Only if needed — amber row "INFY needs a trim" + Review button
- **Wow:** Portfolio feels **solved** in 3 seconds when healthy
- **A11y:** Status is plain text with icon+text pair

---

# SCREEN 4 — ASK (Perplexity Answer)

## 1. UX critique

Single Stock + Alpha AI = two tabs, metric grids, analyze button, 15 sections. User **runs software** instead of **asking a human**.

---

## 2. Three concepts

### Concept A — Traditional stock page (current)
### Concept B — Perplexity Answer *(recommended)*
### Concept C — Voice-first conversation
Rejected — privacy, context, fintech trust.

---

## 3–5. Recommendation

**Concept B.** Query at bottom (persistent pill expands); **answer fills 80%** of screen.

**Why:** User mental model = "I asked a question, I got an answer." Not "I opened a research tool."

---

## 6. Wireframe

```
┌─────────────────────────────────────┐
│ ← Today                             │
│                                     │
│         Wait                        │  44px verdict
│                                     │
│  TCS is fairly valued. I'd buy      │
│  closer to ₹3,800 — not here.       │
│                                     │
│  ₹3,780 – 3,820  ·  stop 3,720     │  mono strip
│                                     │
│  [ Add to watch ]                   │
│                                     │
│  Full analysis ▸                    │
│  Compare ▸                          │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Ask about any stock…            │ │  pinned input
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## 7–16. (Summary)

- **Hierarchy:** Verdict > 2-line answer > levels > one action
- **Behavior:** Typing shows suggestions; submit replaces screen content with animation
- **Empty:** "Try RELIANCE, TCS, or INFY"
- **Wow:** **Instant oracle** — Perplexity magic for stocks
- **Mobile:** Keyboard pushes input; answer scrolls
- **A11y:** Answer region aria-live

---

# SCREEN 5 — RESULTS (Trust Strip)

## 1. UX critique

Track Record = calibration panels, gates, journal validation, CSV exports — **accountant software**, not trust.

---

## 2. Three concepts

### Concept A — Analytics dashboard (current)
### Concept B — Trust Strip *(recommended)*
### Concept C — Social proof feed
Rejected — not a community product.

---

## 3–5. Recommendation

**Concept B.** One sentence + 3 numbers + yesterday's story. Stripe invoice clarity.

---

## 6. Wireframe

```
┌─────────────────────────────────────┐
│ Results                             │
│                                     │
│  Last 7 days, we were right         │
│  on 4 of 6 calls.                   │  24px
│                                     │
│   4        2        67%              │
│  wins    misses    hit              │
│                                     │
│  Yesterday                          │
│  ✓ RELIANCE — hit target            │
│  ✗ INFY — stopped out               │
│                                     │
│  [ Score yesterday ]  (if pending)  │
│                                     │
│  History ▸                          │
└─────────────────────────────────────┘
```

---

## 16. Wow reasons

- **Honest, compact** — admits misses
- **No vanity charts** — respect intelligence
- **Weekly rhythm** — not morning noise

---

# SCREEN 6 — SETTINGS (iOS Grouped)

## 1. UX critique

Sidebar expanders, setup wizard, autopilot mixed with trading — **settings as junk drawer**.

---

## 2–5. Recommendation

**iOS Settings pattern** inside **You** tab. Grouped rows, checkmarks, no trading content here.

---

## 6. Wireframe

```
Settings
────────────────
BROKER
  Zerodha · Connected        ✓
  Sync now

RISK
  Max daily loss    ₹2,000
  Risk per trade    2%

ALERTS
  Telegram          Off

ADVANCED
  Market scan
  Backtest
```

---

# CROSS-SCREEN INTERACTION MAP

```
                    ┌──────────┐
                    │  TODAY   │◄──── default launch
                    └────┬─────┘
           swipe up      │ tap "See plan"
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         Why sheet   Plan sheet   Ask overlay
                         │
                         ▼
                    Open Kite (ext)
                         │
                         ▼
                    You → Results (score)
```

**Morning critical path:** Today → (optional Plan) → Kite → leave  
**Max taps to action:** 2  
**Max taps to release:** 1  

---

# WHAT WE REJECT FROM YOUR PRIOR REQUESTS

| Your suggestion | Our rejection | Better solution |
|-----------------|---------------|-----------------|
| Five Home cards | Equal weight | Verdict Canvas |
| Five top tabs | Tab overload | 3 bottom + Ask pill |
| Morning letter with sections | Still structured doc | Mentor prose, no labels |
| "Estimated reading time" | Gimmicky | Respect shown through brevity, not meta |
| Confidence High/Med/Low badge | Metric chrome | Conviction inside sentence |
| Results as morning tab | Wrong cadence | Under You, weekly |
| Review Setup button label | Software | "See the plan" / human verbs |
| Cards everywhere | Dashboard | Ticket, Canvas, Sheet |

---

# DELIGHT PRINCIPLES (why this beats engineering-first design)

1. **One breath, one verdict** — matches how pros talk: "Sit on hands today."
2. **Silence is premium** — empty Trades tab congratulates discipline.
3. **Sheets, not pages** — details are invited, not imposed.
4. **Typography > chrome** — no Streamlit cosplay.
5. **Trust through honesty** — Results shows misses first-class.
6. **Release as feature** — "You're done" is the most loving button in fintech.

---

# APPROVAL GATE

Do **not** implement until design sign-off on:

- [ ] Verdict Canvas (not cards, not letter sections)
- [ ] 3-item bottom nav + Ask pill (not 5 tabs)
- [ ] Trade Ticket (not watchlist table)
- [ ] You hub (not separate Portfolio / Results / Settings tabs)
- [ ] Perplexity-style Ask (not Single Stock page)
- [ ] Global design tokens (type, space, color, motion)
- [ ] Streamlit patterns explicitly banned

---

*AI Trading Decision System — Experience Design v1.0*  
*Optimize the user experience, not the user's first idea.*
