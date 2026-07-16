# Phase 3 — Reflection Canvas (You Tab) · Design Specification

**Product:** AI Trading Decision System  
**Screen:** You (dock tab 3 of 3)  
**Status:** **FROZEN** — approved with personal trader-focused refinements (2026-07-16)  
**Scope:** Presentation + routing only · backend unchanged  
**Companions:** Phase 1 (Today) · Phase 2 (Trades) — **do not modify**

---

## Approved refinements (frozen)

| Change | Decision |
|--------|----------|
| Micro label | **`I've noticed`** — mentor speaks to the trader, not “This week” |
| State words | **Four only:** `Growing` · `Steady` · `Rebuilding` · `Focused` |
| Ghost link 1 | **`What I'd change`** (popover) — not “View holdings” |
| Ghost link 2 | **`How we're doing`** → Track Record — not “See track record” |
| Coaching insight | One block, e.g. *“The hardest trade this week was waiting. You made the right decision.”* |
| Forward line | One line, first-person AI, e.g. *“Tomorrow I'll continue watching for high-quality breakouts.”* |
| Core question | **“Am I becoming a better trader?”** — describe the **trader**, not the portfolio |
| Tone | Encouraged, not evaluated |

**Content order:** Micro → State word → Narrative (trader) → Coaching → Forward → Recommendation → Primary → Ghost links.

---

## 0. Product cohesion charter (inherited — mandatory)

The You tab is the **third room in the same house**. A screenshot must read as the same product without context.

| Tab | Question | Hero focal |
|-----|----------|------------|
| **Today** | Should I act? | Stance word — `Wait` · `Trade` · `Pause` (56px) |
| **Trades** | How do I execute? | Symbol — `RELIANCE` (48px) |
| **You** | How am I doing as a trader? | **Trader state word** — `Steady` · `Disciplined` · `Rebuilding` (48px) |

| Dimension | Rule (unchanged across all tabs) |
|-----------|----------------------------------|
| Canvas | `#0A0A0B`; 430px max column; 16px margins |
| Header | Time left · sync right — identical |
| Dock | Today · Trades · You — identical chrome |
| Ask FAB | Labeled “Ask”, same position |
| Primary button | 52px · 14px radius · `#F5F5F7` on `#0A0A0B` |
| Ghost secondary | 15px · 40% opacity · 44px tap |
| Cards / tables / charts | **None** on default path |
| Tone | Calm mentor · first-person AI · no engine jargon |

**Mirror principle:** Today = decision · Trades = execution · **You = relationship**.

---

## 1. Mission

Design the user's **relationship with the AI** — not their brokerage account.

This is NOT Portfolio. NOT Account. NOT Settings.

The AI has already analyzed portfolio, risk, behaviour, discipline, capital, positions, sector exposure, mistakes, strengths, and broker status. The user sees **only the conclusion**, spoken as a mentor who knows them.

---

## 2. The one question

> **“How am I doing as a trader?”**

Not: *What do I own?* · *What's my P&L?* · *What's my allocation?*

Holdings, numbers, and history are **depth** — never the opening move.

---

## 3. Explicit rejections (Phase 3)

Do **not** build as default view:

| Rejected | Why |
|----------|-----|
| Holdings table first | Answers “what I own,” not “how I'm doing” |
| P&L dashboard / metric cards | Analytics wall; user must interpret |
| Pie charts, heatmaps, sector grids | Portfolio app identity |
| Win-rate tiles, streak counters as hero | Gamification; not mentorship |
| Settings / import / CRUD first | Account page identity |
| Confidence badges, synthetic health scores | Phase 1 already rejected these |
| Multiple sections with equal weight | Dashboard parity |

---

## 4. Design process — five concepts

### Concept A — Portfolio Dashboard

Holdings table, day P&L, exposure %, sector breakdown above the fold.

| Pros | Cons |
|------|------|
| Familiar | Wrong question entirely |
| Data-rich | User interprets; AI silent |
| Easy to build from existing My Portfolio | Breaks product cohesion instantly |

**Verdict: REJECT.** This is Zerodha Console with a dark theme.

---

### Concept B — Analytics Scorecard

Letter grades per dimension: Discipline B+, Risk A-, Behaviour C+. Sparklines for week P&L.

| Pros | Cons |
|------|------|
| Feels “smart” | User decodes grades = thinking |
| Comparable to robo-advisors | Metric cards by another name |
| | School report, not trusted mentor |

**Verdict: REJECT.** Violates “the application should think.”

---

### Concept C — Coach Chat Thread

Weekly messages in chat bubbles; user scrolls history of AI notes.

| Pros | Cons |
|------|------|
| Personal tone | Chatbot identity (Perplexity tab, not You tab) |
| History visible | Trains user to ask, not trust |
| | Different silhouette from Today/Trades |

**Verdict: REJECT.** Wrong interaction model; breaks three-canvas cohesion.

---

### Concept D — Status Dot Only (minimal health)

Green dot + “Everything looks fine.” + one P&L line. Holdings behind link.

| Pros | Cons |
|------|------|
| Extremely calm | Too thin — doesn’t feel “AI understands me” |
| Apple Health-adjacent | Behaviour and mistakes absent |
| Worked as v1 sketch | Underuses relationship depth user requested |

**Verdict: REJECT.** Calm but not sufficient for Phase 3 ambition.

---

### Concept E — Reflection Canvas ✓

**Recommended.** Same canvas architecture as Today and Trades:

1. **Trader state word** (hero)  
2. **AI narrative** (2–4 short sentences — speaks first)  
3. **One recommendation** (prose + primary action)  
4. **Ghost depth links** (holdings, record — discoverable, not hidden)  
5. **Optional bottom sheet** for holdings as **prose**, not table  

| Pros | Cons |
|------|------|
| Instant product recognition | Requires strong NL generation |
| Same dock/header/Ask/buttons | Less “wow” than novel metaphor |
| Answers the right question | |
| Behaviour + portfolio woven in narrative | |
| Trust through restraint | |

**Verdict: RECOMMEND.**

---

## 5. Comparison matrix

| Criterion | A Dashboard | B Scorecard | C Chat | D Status | **E Reflection** |
|-----------|-------------|-------------|--------|----------|------------------|
| Same product as Phase 1–2 | No | No | No | Partial | **Yes** |
| AI speaks first | No | No | Partial | Partial | **Yes** |
| “Understands me” feeling | No | Partial | Partial | No | **Yes** |
| No interpretation required | No | No | Yes | Yes | **Yes** |
| Behaviour coaching | No | Partial | Yes | No | **Yes** |
| Discoverable depth | Yes | Yes | Yes | Yes | **Yes** |
| Not Portfolio/Settings | No | Partial | Yes | Partial | **Yes** |

---

## 6. Recommendation: Reflection Canvas

**Official name:** `ReflectionCanvas` (You tab default view)

**Why this wins:** The product already established a **three-beat grammar**:

```
HERO WORD  →  MENTOR VOICE  →  ONE ACTION
```

Today, Trades, and You are **variations of one pattern**, not three different apps. Users learn the grammar once on day one.

---

## 7. Layout grid (390 × 844)

```
┌──────────────────────────────────────── 390px ────────────────────────────────────────┐
│ HEADER ROW (identical Phase 1–2)                                                      │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ REFLECTION ZONE                                                                       │
│   This week (micro, 13px uppercase)                                                   │
│   Steady (hero state word, 48px, centered)                                            │
│   ambient glow — hue matches state (see §8.2)                                         │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ NARRATIVE BLOCK (AI speaks first — before any numbers)                                │
│   2–4 sentences, 20px Mentor, left-aligned                                            │
│   Example:                                                                            │
│   You avoided three low-quality trades.                                               │
│   That protected your capital.                                                        │
│   Your portfolio stays well diversified.                                                │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ RECOMMENDATION LINE (17px Detail)                                                     │
│   No changes required.                                                                │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ PRIMARY BUTTON                                                                        │
│   I'm good                                                                            │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ GHOST DEPTH (visible, optional — max 2 links)                                         │
│   View holdings                                                                       │
│   See track record                                                                    │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ MEMORY LINE (micro, one line — optional when data exists)                             │
│   Last Tuesday you oversized — today's cap reflects that.                             │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ FOOTER MICRO (identical)                                                              │
│ DOCK + ASK (You tab active)                                                           │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**Scroll rule:** Default view fits **one viewport** above dock. No scroll required to understand. If narrative is long on small devices, max **4 sentences** then truncate with ellipsis — never scroll-as-default.

---

## 8. Component specifications

### 8.1 Header row

Byte-identical to Phase 1 §4.1 and Phase 2 §8.1. Sync dot covers broker ambient status — no broker card on You.

---

### 8.2 Reflection zone — trader state word

| Element | Typography | Color |
|---------|------------|-------|
| Micro label | `This week` — 13px/500 uppercase, tracking 0.06em | `#F5F5F7` at 45% |
| State word | 48px/600, -0.02em tracking, centered | Per state token below |
| Zone padding | 32px top, 24px bottom | — |
| Ambient glow | 6% radial, same mechanics as Today/Trades | Per state |

#### Trader state tokens

| State key | Display | Color | When (presentation map) |
|-----------|---------|-------|-------------------------|
| `steady` | Steady | `#A1A1A6` | Default healthy; no alerts |
| `disciplined` | Disciplined | `#00E676` | Strong sit-out / journal adherence |
| `rebuilding` | Rebuilding | `#FFC107` | Post loss-streak recovery |
| `exposed` | Exposed | `#FF8A80` | Concentration or risk flags |
| `diversified` | Diversified | `#64B5F6` | Book balanced, no action needed |
| `paused` | Paused | `#FF6B6B` | Active loss-streak / defensive mode |

**Decision:** One word summarizes **trader behaviour**, not portfolio value. Never `+₹4,200` as hero.

**Alt micro label when not week-scoped:** `Your book` — only if session is first open of day and week narrative unavailable. Prefer `This week` default.

---

### 8.3 Narrative block (`ReflectionNarrative`)

| Property | Value |
|----------|-------|
| Font | Inter 20px / 400 (Mentor token) |
| Line-height | 1.45 |
| Color | `#F5F5F7` at 88% |
| Alignment | Left |
| Max sentences | **4** |
| Max lines | ~6 at 390px width |
| Structure | Short declarative sentences. One idea per sentence. |

#### Narrative composition (NL slots — presentation mapping)

| Slot | Purpose | Example |
|------|---------|---------|
| **Discipline** | What user did well | “You avoided three low-quality trades.” |
| **Protection** | Capital consequence | “That protected your capital.” |
| **Book** | Portfolio stance | “Your portfolio stays well diversified.” |
| **Behaviour** | Optional coaching | “You sized correctly on both entries.” |

**Order:** Discipline → Protection → Book → Behaviour (omit slots when no data; never pad with fluff).

**Forbidden on default view:** Raw P&L figures, position counts as hero, sector percentages, win rates.

---

### 8.4 Recommendation line

| Property | Value |
|----------|-------|
| Font | 17px Detail, 55% opacity |
| Content | Single sentence — what to do next (or not do) |
| Examples | “No changes required.” · “Trim FINNIFTY exposure before adding risk.” · “Log today's session to keep streak alerts accurate.” |

Sits **after** narrative, **before** primary button — the mentor’s concluding counsel.

---

### 8.5 Primary action

| Property | Value |
|----------|-------|
| Chrome | Identical PrimaryCTA (52px, `#F5F5F7`) |
| Default label | **`I'm good`** |
| Behaviour | Toast: “You're on track.” — permission to leave |

#### Alternate primary labels (contextual — one only)

| Condition | Label | Action |
|-----------|-------|--------|
| Broker disconnected | Connect Zerodha | Nav → existing broker flow |
| Journal empty + market was open | Log today's session | Nav → Track Record journal area |
| Loss streak active | Rest today | Nav → Today tab |

**Decision:** Default is **release**, matching Today’s “You're done for today.” You tab confirms identity — user is doing okay.

---

### 8.6 Ghost depth links (discoverable, not hidden)

Max **two** ghost text buttons below primary (same style as Phase 1 “Why this?” / Phase 2 “Not today”).

| Link | Opens | Content rule |
|------|-------|--------------|
| **View holdings** | Bottom sheet | Prose summary only — see §8.7 |
| **See track record** | Nav → Track Record | Existing page; progressive disclosure |

**Forbidden:** “Settings”, “Import CSV”, “Edit allocation” on default You view. Those live in app settings elsewhere — not relationship screen.

---

### 8.7 Holdings sheet (depth only — never default)

Triggered by **View holdings** ghost link. Bottom sheet — same chrome as Phase 1 Why sheet (`#1C1C1E`, 24px top radius, handle pill).

**No table. No pie chart.** Prose blocks only:

```
You hold 12 positions.

Largest: RELIANCE · IT sector · within your plan.
Weakest: TATASTEEL · down 4% · watch, don't react.

Cash buffer looks fine for your risk rules.
```

| Property | Value |
|----------|-------|
| Font | 17px / 1.5 |
| Max paragraphs | 4 |
| Numbers | Embedded in sentences only — not columnar |

---

### 8.8 Memory line (behaviour coaching)

| Property | Value |
|----------|-------|
| Position | Below ghost links, above footer |
| Font | 13px micro, 45% opacity |
| Max | **One line** |
| Purpose | Historical mistake or strength — proves AI remembers |

Examples:
- “Last Tuesday you oversized — today's cap reflects that.”
- “Four of your last five waits were correct.”

**Only show when backend has signal.** Absence = omit line (no placeholder).

---

### 8.9 Dock · Ask

Byte-identical to Phase 1–2. You tab active = `.vc-nav-you` top border indicator (same pattern as `.vc-nav-trades`).

---

## 9. States

### 9.1 Default — healthy week (flagship)

| Element | Value |
|---------|-------|
| State word | `Steady` or `Diversified` |
| Narrative | User example (4 sentences) |
| Recommendation | “No changes required.” |
| Primary | I'm good |
| Ghost | View holdings · See track record |

---

### 9.2 Disciplined — strong sit-outs

| Element | Value |
|---------|-------|
| State word | `Disciplined` |
| Narrative | “You sat out four noisy sessions. That mattered more than any single win. Your book didn't need a single change.” |
| Recommendation | “Keep waiting for clean setups.” |
| Ambient | Green 6% |

---

### 9.3 Rebuilding — post loss-streak

| Element | Value |
|---------|-------|
| State word | `Rebuilding` |
| Narrative | “Two loss days are behind you. The right move now is smaller size and fewer trades. Your portfolio doesn't need surgery — your habits do.” |
| Recommendation | “One trade max until journal turns green.” |
| Primary | Rest today (nav → Today) |
| Memory | “Loss streak flagged — I'm keeping today's risk tight.” |

---

### 9.4 Exposed — concentration risk

| Element | Value |
|---------|-------|
| State word | `Exposed` |
| Narrative | “IT is carrying too much of your book. It's not a crisis — but don't add correlated risk today.” |
| Recommendation | “No new positions in IT until you trim or hedge.” |
| Ghost | View holdings (sheet shows concentration prose) |

---

### 9.5 Broker disconnected

Same voice as Phase 2 connect state — but You-framed:

| Element | Value |
|---------|-------|
| State word | `Link` (or hero: “Connect”) |
| Narrative | “I can't see your real book yet. Connect Zerodha once and I'll coach you against actual holdings.” |
| Primary | Connect Zerodha |

---

### 9.6 New user — no journal, no history

| Element | Value |
|---------|-------|
| State word | `Starting` |
| Narrative | “We're just getting to know each other. Trade when Today says Trade — log sessions so I can learn how you actually behave.” |
| Recommendation | “Start with one trade at a time.” |
| Primary | I'm good |
| No memory line | — |

---

## 10. Data mapping (presentation only — backend unchanged)

| UI slot | Source (priority order) |
|---------|-------------------------|
| State word | `loss_streak` + `mis.flags` + portfolio concentration heuristics + `resolve_learning_outcomes` |
| Discipline sentence | Journal sit-outs + `mis.loss_streak_days` inverse + wait-day count from track record |
| Protection sentence | Risk mode + trading restrictions + capital headroom from prefs |
| Book sentence | Holdings count + sector_strength from `ContextSnapshot` + `_portfolio_health` logic (existing) |
| Behaviour sentence | `learning` outcomes + journal mistake tags |
| Recommendation | `InvestmentOS.next_step` / `mis.summary` mapped to plain counsel |
| Memory line | Recent journal mistake or `learning` highlight |
| Holdings sheet | `ZerodhaImportResult` holdings → NL summary template |

**Rule:** If data is missing, **omit the sentence** — never show “N/A” or empty widgets.

---

## 11. Tone of voice (You)

| Do | Don't |
|----|-------|
| “You avoided three low-quality trades.” | “Win rate improved 12%.” |
| “That protected your capital.” | “Drawdown reduced.” |
| “No changes required.” | “Portfolio health score: 82.” |
| “Last Tuesday you oversized.” | “Behavioural anomaly detected.” |
| Second person · calm · specific | Dashboard labels · jargon |

---

## 12. Motion

| Moment | Animation | Duration |
|--------|-----------|----------|
| Dock → You | Crossfade content; You indicator slides | 300ms |
| State word arrive | Fade + 8px rise (match Today verdict) | 400ms |
| Narrative stagger | Optional 40ms per sentence | 400ms max |
| Sheet open | Spring from bottom (Why sheet token) | 350ms |

---

## 13. Interaction flows

```
Dock [You] ──► Reflection Canvas (default)

[I'm good] ──► toast → user may leave

[View holdings] ──► bottom sheet (prose)

[See track record] ──► Track Record (existing)

[Ask] ──► Phase 4 overlay (frozen until You approved)

Today [View your week] (Rest stance) ──► should land You tab (Phase 3 wiring)
```

---

## 14. Accessibility

- VoiceOver reads: “This week. Steady. [full narrative]. Recommendation: No changes required.”
- State word + narrative are one semantic region.
- Ghost links ≥ 44px tap height.
- Sheet dismiss: tap outside + swipe (enhancement); **X** button required for discoverability.

---

## 15. WOW test (Phase 3)

| Question | Reflection Canvas |
|----------|-------------------|
| Same product as Today/Trades screenshot? | Yes — hero + narrative + one button + dock |
| Answers “how am I doing as a trader”? | Yes |
| AI speaks before numbers? | Yes |
| Feels “this AI understands me”? | Yes — memory line + behaviour in prose |
| Not Portfolio / Settings? | Yes |
| Discoverable depth without hiding? | Yes — ghost links |
| User can leave feeling good? | Yes — “I'm good” |

---

## 16. Implementation phases (within Phase 3 — after approval)

| Step | Deliverable |
|------|-------------|
| 3a | You tab route + Reflection Canvas shell + dock active |
| 3b | State word + narrative mapping from existing data |
| 3c | Holdings prose sheet + track record link |
| 3d | Memory line + Rest → You nav from Today |
| 3e | Motion + a11y pass |

**Do not modify Phase 1 Today or Phase 2 Trades layouts.**

---

## 17. Open decisions (product owner)

1. **Hero label:** `This week` (recommended) vs `Your book` as micro context.  
2. **Primary default:** `I'm good` (recommended) vs `Got it`.  
3. **Track Record link:** Keep as ghost nav to existing page, or prose-only teaser on You with link? (Recommend ghost nav — discoverable, no new analytics on You.)  
4. **State word set:** Approve six tokens above or reduce to four (Steady / Disciplined / Rebuilding / Exposed).

---

## 18. Freeze criteria

Phase 3 will be marked **FROZEN** after:

- [ ] Product owner approves this spec  
- [ ] Implementation matches layout order §7  
- [ ] Screenshot sits beside Phase 1–2 without visual disconnect  
- [ ] Phase 4 (Ask) not started until You review complete  

---

*End of Phase 3 design specification.*
