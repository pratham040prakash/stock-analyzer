# Phase 2 — Trade Plan (Trades Tab) · Design Specification

**Product:** AI Trading Decision System  
**Screen:** Trades (dock tab 2 of 3)  
**Status:** **FROZEN** — approved with emotional-guidance refinements (2026-07-16)  
**Scope:** Presentation + routing only · backend unchanged  
**Companion:** Phase 1 `Phase_1_Verdict_Canvas_Spec.md` (Today — **do not modify**)

---

## Approved refinements (frozen)

Interaction model unchanged (Plan Canvas + dock). Emotional guidance order:

1. **AI speaks before numbers** — one-sentence mentor opening before any levels.  
2. **Explain before instruct** — reason sentence appears before Entry / Stop / Maximum loss.  
3. **Protection first** — Entry → Stop → **Maximum loss** visually emphasized; Target secondary (40% opacity).  
4. **One lifecycle line** — e.g. “Earliest entry after 9:45.” / “Review if not triggered by noon.” / “This plan expires at market close.”  
5. **Same visual language as Phase 1** — no cards, tables, dashboards, or extra widgets.

**Not a broker. Not OMS. Decision companion only.**

Phase 3 (You) blocked until Phase 2 review.

---

## 0. Product cohesion charter

Every phase must be recognizable **without context** as the same product.

| Dimension | Rule |
|-----------|------|
| **Canvas** | `#0A0A0B` full viewport; 430px max column centered |
| **Margins** | 16px horizontal (`space-sm`) |
| **Type family** | Inter / SF Pro Display / system-ui |
| **Type scale** | Max 3 sizes visible: Hero · Mentor/Detail · Micro |
| **Primary button** | 52px height, 14px radius, `#F5F5F7` fill, `#0A0A0B` text, 17px/600 |
| **Ghost secondary** | 15px/500, `#F5F5F7` at 40%, 44px tap target |
| **Header row** | 44px + safe-top; time left, sync right — **identical to Today** |
| **Dock** | 49px + safe-bottom; Today · Trades · You — **identical chrome** |
| **Ask FAB** | 56px circle, labeled “Ask”, same position above dock |
| **Motion** | 300–400ms ease-out; state change only, never decorative |
| **Tone** | Calm mentor; first-person optional; no engine jargon |
| **Cards** | None — typography is the UI |
| **Charts** | None on default path |

**Mirror principle:** Today answers *whether*. Trades answers *how*. Same room, different focal object.

---

## 1. Mission

Design the most elegant **execution** experience for retail traders.

The user has **already decided** on Today. They do not need analysis, screeners, or alternatives.

They need **confidence**: exact levels, sized risk, one path forward.

---

## 2. The one question

> **“Exactly how should I execute today’s decision?”**

Nothing else. No secondary questions on this screen.

---

## 3. Explicit rejections (Phase 2)

Do **not** build:

- Watchlists, stock grids, screeners, scanners  
- Tables with sortable columns  
- Multiple recommendations or pick lists  
- Charts by default  
- Confidence badges, metric tiles, heatmaps  
- Expanders, sidebars, configuration-first UI  
- “Active trades” counters or portfolio summaries  

Build **one** trade plan for **one** instrument with **one** execution strategy.

---

## 4. Design process — five concepts

### Concept A — Pick List (status quo)

Vertical list of 3–5 stocks with scores, entry zones, and “Review” buttons.

| Pros | Cons |
|------|------|
| Familiar from screeners | Instantly reads as “another trading app” |
| Shows breadth | Forces comparison → analysis paralysis |
| Easy to engineer | Fails one-decision principle |

**Verdict: REJECT.** Warehouse UX. User must choose again after Today already chose.

---

### Concept B — Trade Ticket (card)

Single bordered “boarding pass” object: symbol header, level rows inside a ticket chrome, Kite CTA below.

| Pros | Cons |
|------|------|
| Premium metaphor | **Card** breaks Phase 1 visual language |
| Finite, serious | Border reads as “component,” not canvas |
| Worked in early v1 sketch | Different silhouette than Today in screenshots |

**Verdict: REJECT for cohesion.** Strong metaphor, wrong material. Today has no cards; Trades must not introduce them.

---

### Concept C — Stepper Wizard

Step 1 Confirm trigger → Step 2 Review risk → Step 3 Execute.

| Pros | Cons |
|------|------|
| Clear sequence | Patronizing after AI already decided |
| Onboarding pattern | Adds taps before confidence |
| | Feels like compliance software |

**Verdict: REJECT.** User is not onboarding. They are executing.

---

### Concept D — Chart-Led Execution (Robinhood++)

Symbol header, price chart, position block, then levels.

| Pros | Cons |
|------|------|
| Familiar to traders | **Chart = interpret** → design failure per first principle |
| Rich context | Sends user back to “another app” mental model |
| | Violates invisible AI |

**Verdict: REJECT.** TradingView replacement is not the mission.

---

### Concept E — Plan Canvas (Execution Manifest) ✓

**Recommended.** Same canvas as Today. Stance word shrinks to context; **symbol becomes hero**. Levels unfold as **prose lines** (not grid). One reason sentence. Two visible actions. Empty state uses same calm voice.

| Pros | Cons |
|------|------|
| **Screenshot recognition** — same header, dock, Ask, button | Less “novel” than ticket metaphor |
| Zero new interaction patterns | Requires discipline to keep one plan only |
| Extends Phase 1 type/spacing/motion exactly | |
| User example maps 1:1 | |
| Execution in <10 seconds | |

**Verdict: RECOMMEND.** Futuristic through **restraint**, not experimental chrome.

---

## 5. Comparison matrix

| Criterion | A List | B Ticket | C Stepper | D Chart | **E Plan Canvas** |
|-----------|--------|----------|-----------|---------|-------------------|
| One decision | No | Yes | Yes | No | **Yes** |
| Cohesive with Phase 1 | No | Partial | No | No | **Yes** |
| No analysis required | No | Yes | Partial | No | **Yes** |
| Immediate comprehension | No | Yes | No | Partial | **Yes** |
| Apple / Linear bar | No | Partial | No | No | **Yes** |
| Discoverable actions | Yes | Yes | Yes | Yes | **Yes** |
| WOW without experiment | No | Yes | No | No | **Yes** |

---

## 6. Recommendation: Plan Canvas

**Official name:** `PlanCanvas` (Trades tab default view)

**Why this wins:**

1. **Same product in every screenshot** — only the hero glyph changes (`Wait` → `RELIANCE`).  
2. **Decision → execution is one mental room** — Today says Trade; Trades shows how. No metaphor shift.  
3. **Prose levels match mentor voice** — “Buy above ₹2,850” is instruction, not spreadsheet.  
4. **Visible primary + secondary** — no gestures, no hidden paths.  
5. **Empty state is still Plan Canvas** — same layout, different copy (discipline affirmed).

---

## 7. Layout grid (390 × 844) — frozen content order

```
┌──────────────────────────────────────── 390px ────────────────────────────────────────┐
│ HEADER ROW (identical Phase 1)                                                        │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ PLAN ZONE: Trade (micro) + SYMBOL (48px) + side                                       │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ MENTOR OPENING (20px) — AI speaks before numbers                                      │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ REASON (17px Detail) — explain before instruct                                        │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ ENTRY line (20px, protect)                                                            │
│ STOP line (20px, protect)                                                             │
│ MAXIMUM LOSS line (20px/600, #FF8A80 emphasis)                                        │
│ target line (17px, 40% — secondary)                                                   │
│ LIFECYCLE line (13px micro)                                                           │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ PRIMARY: Open in Kite                                                                 │
│ SECONDARY: Not today (ghost)                                                          │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ DOCK + ASK (identical Phase 1)                                                        │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Component specifications

### 8.1 Header row

**Identical to Phase 1 §4.1.** Time left, sync dot right. No “Trades” title in header — the plan is the title.

---

### 8.2 Plan zone — context + hero

| Element | Typography | Color | Notes |
|---------|------------|-------|-------|
| Context word `Trade` | Micro 13px/500, uppercase, tracking 0.06em | `#00E676` | Same role as time label — orients without competing |
| Symbol `RELIANCE` | 48px/600, -0.02em tracking, centered | `#F5F5F7` | Hero focal point (Today uses 56px stance word) |
| Side | Appended inline or micro under symbol | Long: `#00E676` · Short: `#FF6B6B` | `Long` / `Short` title case |

**Ambient:** Same radial gradient as Today Trade state:

```css
radial-gradient(ellipse 280px 200px at 50% 40%,
  rgba(0, 230, 118, 0.06) 0%, transparent 70%);
```

**Padding:** 40px top, 32px bottom inside plan zone.

---

### 8.3 Execution lines (`ExecutionManifest`)

**Not a table.** Not a 4-column grid. A vertical **instruction stack**.

| Property | Value |
|----------|-------|
| Font | Inter 20px / 400 (Mentor token) |
| Line-height | 1.45 |
| Color | `#F5F5F7` at 88% |
| Alignment | Left, 16px margin |
| Gap between lines | 12px (`space-xs` + 4) |
| Tabular nums | `font-variant-numeric: tabular-nums` on ₹ amounts |

**Canonical line order (fixed):**

1. **Trigger** — `Buy above ₹2,850` / `Sell below ₹2,840` / `At market` (if already triggered)  
2. **Stop** — `Stop ₹2,815`  
3. **Risk** — `Risk ₹1,800` (rupees, pre-sized from user capital × risk rules)  
4. **Target** — `Target ₹2,930`  

**Copy rules:**

- Always plain English verb first — not labels floating left of numbers.  
- INR formatted with ₹ and locale grouping (`₹1,800`).  
- Risk line is **rupee risk**, not % — user thinks in money lost.  
- Optional fifth line only if timing gate exists: `Valid after 9:45 AM` — Detail 17px, 55% opacity.

**Forbidden:** Entry/Stop/Target column headers, R:R ratios, lot size unless user prefs require lots for options (then one extra Detail line max).

---

### 8.4 Reason block

| Element | Spec |
|---------|------|
| Micro label | `Reason` — 13px/500 uppercase, `#F5F5F7` at 45% (same as time) |
| Body | One sentence, 17px Detail, 55% opacity, max 2 lines (~140 chars) |
| Source | `DecisionArtifact.reason` or synthesis headline — presentation map only |

**Not** a bullet list. **Not** evidence packet on default view. Deeper reasoning stays on Today’s “Why this?” or Ask.

---

### 8.5 Primary action (`PrimaryCTA`)

**Identical chrome to Phase 1 §4.5.**

| Label | When | Action |
|-------|------|--------|
| **Open in Kite** | Default when plan exists | Deep link / external Kite with symbol prefilled; fallback: copy symbol + toast |
| **I'm taking this** | Alternative A/B if Kite unavailable | Logs intent locally + toast confirmation |

**Recommendation:** Ship **Open in Kite** as primary — execution-first. User came for *how*, primary takes them *there*.

---

### 8.6 Secondary action (`GhostCTA`)

**Identical ghost style to Phase 1 “Why this?” §4.6.**

| Label | Action |
|-------|--------|
| **Not today** | Marks plan declined for session; soft message; suggest return to Today (stance may remain Trade until refresh — engine truth unchanged) |
| **Copy plan** | Optional alternate secondary if Kite is primary — copies all four lines to clipboard |

**Rule:** One secondary only. Never a third button.

---

### 8.7 Dock · Ask

**Byte-identical to Phase 1.** Trades tab shows active indicator (2px top line, full opacity label). Ask FAB visible on all tabs.

---

## 9. States

### 9.1 Active plan (default when Today stance = Trade)

Full Plan Canvas as §7–8.

**Entry paths (discoverable):**

1. User taps **See the plan** on Today → lands Trades tab.  
2. User taps **Trades** in dock directly.  

Both render the **same** Plan Canvas. No sheet-only variant — tab is canonical.

---

### 9.2 No plan today (empty)

Today stance is Wait / Pause / Rest — Trades tab still works. **Same layout skeleton**, different content:

```
        No plan today

   Sitting out is the trade. Your capital
   is protected when you don't force one.

   ┌─────────────────────────────┐
   │      Back to Today          │  ← Primary (navigate dock tab 1)
   └─────────────────────────────┘
```

| Element | Spec |
|---------|------|
| Hero line | `No plan today` — 48px/600, `#A1A1A6` (Hold token) |
| Mentor sentence | 20px, 2 lines max, affirming tone |
| Ambient | None (neutral canvas) |
| Primary | `Back to Today` — switches dock to Today |

**Forbidden:** “No data”, “Run scanner”, links to Suggestions screener.

---

### 9.3 Stale / partial plan

If symbol exists but levels missing (data gap):

- Show symbol hero.  
- Execution lines show `—` with one Detail line: `Levels update when market data refreshes.`  
- Primary disabled with same visual token as Phase 1 loading.  
- Secondary: `Back to Today`.

---

### 9.4 Connect broker (edge)

If Today would show Connect, Trades shows:

```
        Link Zerodha first

   I'll size risk against your real book
   once holdings sync.

   [ Connect Zerodha ]     primary
   [ Back to Today ]       ghost
```

Same voice. Same buttons pattern.

---

## 10. Motion

| Moment | Animation | Duration |
|--------|-----------|----------|
| Today → Trades (See the plan) | Dock indicator slides; content crossfade | 300ms |
| Plan lines appear on tab open | Stagger fade-up 8px, 50ms between lines | 400ms total |
| Tap Open in Kite | Button scale 0.98 | 100ms |
| Not today | Soft gray flash on hero, toast | 300ms |

**No motion required to understand content.** All states readable if motion disabled.

---

## 11. Tone of voice (Trades)

| Do | Don't |
|----|-------|
| “Buy above ₹2,850” | “Entry level: 2850” |
| “Risk ₹1,800” | “Max risk 1.5% of capital” |
| “Momentum confirms after opening range.” | “ACT verdict with 72% confidence” |
| “Sitting out is the trade.” | “No opportunities found” |

---

## 12. Data mapping (presentation only)

**Do not change engines.** Map existing artifacts to Plan Canvas fields:

| UI field | Source (priority order) |
|----------|-------------------------|
| Symbol | `InvestmentOS.starred_symbol` → first `PinnedPlan.symbol` |
| Side | `PinnedPlan.side` or infer from stop vs entry |
| Trigger copy | Pin entry + side → “Buy above ₹X” / “Sell below ₹X” |
| Stop | `PinnedPlan.stop_loss` |
| Target | `PinnedPlan.target` |
| Risk ₹ | `prefs.capital × prefs.max_risk_pct` capped by MIS advisory |
| Reason | `DecisionArtifact.reason` → `decision.explainability.why` |
| Timing gate | `ContextSnapshot.trading_restrictions[0]` if time-based |

If multiple pins exist, show **only the starred / first decision-linked plan**. Others are invisible on Trades — not a list.

---

## 13. Interaction flows

```
Today (Trade) ──[See the plan]──► Trades / Plan Canvas
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
              [Open in Kite]    [Not today]      [Ask FAB]
                    │                 │
                    ▼                 ▼
              External Kite      Toast + optional
              execution          return Today

Dock [Trades] ──► Plan Canvas (active or empty state)
Dock [Today]  ──► Phase 1 frozen view
```

---

## 14. Accessibility

- VoiceOver: read plan as one utterance:  
  *“Trade RELIANCE long. Buy above 2850 rupees. Stop 2815. Risk 1800. Target 2930. Momentum confirms after opening range.”*  
- All actions ≥ 44px tap height.  
- Contrast: primary text `#F5F5F7` on `#0A0A0B` — WCAG AA minimum.  
- Reduced motion: disable stagger, keep content.

---

## 15. WOW test (Phase 2)

| Question | Plan Canvas |
|----------|-------------|
| Understand without instruction in 10s? | Yes — four lines + two buttons |
| Same product as Phase 1 screenshot? | Yes — header, dock, Ask, button |
| Would Apple ship? | Yes — typography-led, no chrome |
| Would Linear ship? | Yes — one job per tab |
| Replaces TradingView for execution? | Yes — levels pre-digested |
| Feels confident, not analytical? | Yes — no charts, no lists |

---

## 16. Implementation phases (within Phase 2)

| Step | Deliverable |
|------|-------------|
| 2a | Trades tab route + empty state + dock active state |
| 2b | Plan Canvas when stance = Trade + data map |
| 2c | Open in Kite + Not today actions |
| 2d | Motion stagger + a11y pass |

**Do not modify Phase 1 Today layout or copy.**

---

## 17. Open decisions (product owner)

1. **Primary label:** `Open in Kite` vs `I'm taking this` — recommend Kite for execution mission.  
2. **Secondary:** `Not today` vs `Copy plan` — recommend `Not today` for decision completion.  
3. **Fifth line:** Show timing gate (`Valid after 9:45`) when restriction exists? Recommend yes — one Detail line only.

---

*End of Phase 2 specification.*
