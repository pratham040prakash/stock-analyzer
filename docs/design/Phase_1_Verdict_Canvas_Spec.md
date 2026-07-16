# Phase 1 — Verdict Canvas · Pixel-Perfect Specification

**Product:** AI Trading Decision System  
**Screen:** Today (flagship)  
**Status:** Official UX — **awaiting mockup approval before Streamlit implementation**  
**Scope:** Presentation only · backend unchanged · no other screens  
**Companion mockup:** `docs/design/mockups/phase-1-verdict-canvas.html` (open in browser)

---

## 1. Purpose of this document

This is the **implementation blueprint for Phase 1 only**. A frontend engineer (or designer) can build the Today screen from this spec without guessing.

**Frozen principles (non-negotiable):**
- One focal object: the **verdict word**
- One recommendation (mentor block, max 4 lines)
- One primary action
- No cards, no section labels, no metric grids, no Streamlit expanders on default view
- No engine vocabulary

**Out of scope for Phase 1:**
- Trade Ticket, You hub, Ask overlay, Results redesign
- Bottom nav functional routing (may show **visual shell only** as placeholder)
- Why sheet content from live evidence (use mapped copy from existing `TradingDecision` / `home_dashboard` data)
- Plan sheet (Phase 2) — TRADE state button may show disabled hint or "Coming in Phase 2" in dev; mockup shows intended label

---

## 2. Canvas & device targets

| Target | Width | Height (min) | Notes |
|--------|-------|--------------|-------|
| **Primary** | 390px | 844px | iPhone 14 Pro logical |
| **Desktop** | 430px centered | 100vh | Content column max 430px on wide screens |
| **Minimum** | 320px | 568px | iPhone SE — verdict scales down |

**Background:** Full viewport `#0A0A0B` (dark default). No Streamlit default white.

**Safe areas:**
- Top: 59px (status + header row) includes notch padding `env(safe-area-inset-top)`
- Bottom: 83px (nav + home indicator) includes `env(safe-area-inset-bottom)`

---

## 3. Layout grid (390 × 844)

```
┌──────────────────────────────────────── 390px ────────────────────────────────────────┐
│ HEADER ROW                                    height: 44px + safe-top                 │
│ y: safe-top → safe-top+44                                                             │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ VERDICT ZONE                                  height: ~380px (flex-grow)              │
│ Verdict word vertically centered in zone                                              │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ MENTOR BLOCK                                  y: verdict zone bottom + 40px            │
│ max-width: 358px (16px side margin)                                                   │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ PRIMARY BUTTON                                y: mentor bottom + 32px                 │
│ width: 358px, height: 52px                                                            │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ GHOST HINT                                    y: button bottom + 16px                 │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ FLEX SPACER                                                                               │
├───────────────────────────────────────────────────────────────────────────────────────┤
│ BOTTOM NAV                                    height: 49px + safe-bottom              │
│ ASK PILL                                      56×56, 16px above nav top               │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

**Horizontal margins:** 16px (`space-sm`) on all content except full-bleed background.

---

## 4. Component specifications

### 4.1 App chrome — Header row

| Element | Position | Typography | Color |
|---------|----------|--------------|-------|
| Time | left 16px, vertically centered in 44px row | Inter 13px/500, letter-spacing 0.06em, uppercase | `#F5F5F7` at 45% |
| Product mark | hidden on Today | — | — |
| Sync indicator | right 16px | See §4.2 | — |

**Decision:** No "AI Trading Decision System" title on Today — the verdict *is* the title. Time orients; branding would compete with focal point.

**Data mapping (implementation note):** Time = `built_at` or device local IST. Sync = `BrokerSnapshot.connected()`.

---

### 4.2 Sync indicator (broker)

| State | Visual | Copy (tooltip / a11y) |
|-------|--------|------------------------|
| Connected | 8px circle `#00E676` + 13px "Synced" | "Zerodha connected" |
| Stale | 8px circle `#FFC107` + "Stale" | "Holdings not fresh" |
| Offline | 8px circle `#FF6B6B` + "Offline" | "Connect Zerodha" |

Layout: dot + 6px gap + label, `display: flex; align-items: center`

**Decision:** Broker status is **ambient**, not a card. User must know data freshness without leaving the verdict trance.

---

### 4.3 Verdict word (`VerdictCanvas`)

| Property | Value |
|----------|-------|
| Font | `Inter`, fallback `SF Pro Display`, system-ui |
| Size | **56px** (44px at ≤360px width) |
| Weight | **600** (Semibold) |
| Letter-spacing | **-0.02em** (-1.12px at 56px) |
| Line-height | **1.0** |
| Text-align | center |
| Width | 100% of content area |
| Padding | 48px top + 48px bottom inside verdict zone |
| Text-transform | **none** (use natural casing: `Wait` not `WAIT` — feels human, not alarm) |

**Decision on casing:** Title case `Wait` / `Trade` / `Pause` reads as mentor speech. All-caps `WAIT` reads as Bloomberg. **Mockup uses title case.**

#### Verdict color tokens

| Verdict key | Display word | Color | Hex |
|-------------|--------------|-------|-----|
| `wait` | Wait | Amber | `#FFC107` |
| `trade` | Trade | Green | `#00E676` |
| `pause` | Pause | Muted red | `#FF6B6B` |
| `rest` | Rest | Gray | `#A1A1A6` |
| `hold` | Hold | Gray | `#A1A1A6` |
| `connect` | Connect | Blue-gray | `#64B5F6` |
| `loading` | ··· | Pulse gray | `#A1A1A6` at 50% |

**Decision:** Color is **pre-attentive signal** before reading copy. Green never used for Wait — avoids bullish misread.

#### Verdict zone background ambient

Ultra-subtle radial gradient behind verdict only:

```css
background: radial-gradient(
  ellipse 280px 200px at 50% 45%,
  rgba(255, 193, 7, 0.06) 0%,    /* tint matches verdict — swap per state */
  transparent 70%
);
```

| State | Tint hue |
|-------|----------|
| Wait | amber `255,193,7` at 6% |
| Trade | green `0,230,118` at 6% |
| Pause | red `255,107,107` at 5% |
| Rest/Hold | none |

**Decision:** Ambient glow = emotional context without card chrome. 6% opacity — invisible if you look for it, felt if you don't.

---

### 4.4 Mentor block (`MentorBlock`)

| Property | Value |
|----------|-------|
| Font | Inter 20px / 400 |
| Line-height | **1.45** (29px) |
| Color | `#F5F5F7` at **88%** opacity |
| Max lines | **4** (truncate with ellipsis — never scroll on default) |
| Max width | 358px |
| Text-align | **left** (not center) |

**Decision:** Left-aligned mentor copy after centered verdict = **conversation**: the market shouts the verdict (center); the mentor explains quietly (left). Mirrors Apple Weather: big condition centered, detail left in stack below.

#### Copy composition rules (NL generation)

Mentor block is **one paragraph**, no bullets, no labels. Template:

```
{timing_sentence} {portfolio_sentence} {watch_sentence_optional}
```

| Slot | Max chars | Example |
|------|-----------|---------|
| Timing | 80 | "I'd sit on my hands until 9:45." |
| Portfolio | 60 | "Your book looks fine." |
| Watch | 100 | "If RELIANCE clears ₹2,850, that's the only name worth a look." |

**Total max ~240 chars ≈ 4 lines at 20px.**

**Decision:** No "ONE THING TO WATCH" label — the sentence *is* the watch. No confidence badge — weave in: "I'm fairly sure" inside prose when needed.

**Backend mapping (presentation only):**
- `timing` ← `snapshot.trading_restrictions[0]` or MIS `time_note` or opening observe rule
- `portfolio` ← portfolio health NL from `os_report.module("risk")` / `_portfolio_health`
- `watch` ← starred symbol + pin entry condition from `os_report.starred_symbol` + pins

---

### 4.5 Primary button (`PrimaryCTA`)

| Property | Value |
|----------|-------|
| Width | 358px (100% - 32px margin) |
| Height | **52px** |
| Border-radius | **14px** |
| Font | Inter 17px / **600** |
| Background | `#F5F5F7` |
| Text color | `#0A0A0B` |
| Border | none |
| Shadow | `0 1px 2px rgba(0,0,0,0.24)` |

#### Pressed state
- Background `#E8E8ED`
- Scale `0.98` for 100ms

#### Disabled state
- Background `#F5F5F7` at 30%
- Text at 40%

#### Labels by verdict state

| Verdict | Button label | Action (Phase 1) |
|---------|--------------|------------------|
| Wait | **You're done for today** | Haptic + toast "Nothing to do" (no nav) |
| Trade | **See the plan** | Phase 2 — stub toast "Plan coming soon" OR scroll hint |
| Pause | **You're done for today** | Same as Wait |
| Rest | **View your week** | Nav to existing Track Record (temporary) |
| Connect | **Connect Zerodha** | Nav to existing My Portfolio broker flow |
| Loading | **···** | Disabled |

**Decision:** Button label is **release** on wait days, not "Learn more." Most fintech buttons demand engagement; ours gives permission to leave — memorable and respectful.

**Secondary button:** None on Phase 1 default. One action only.

---

### 4.6 Ghost hint (Why affordance)

| Property | Value |
|----------|-------|
| Text | `Why I'm saying this` |
| Font | Inter 15px / 500 |
| Color | `#F5F5F7` at **40%** |
| Text-align | center |
| Margin-top | 16px below button |
| Tap target | 44px min height (padding vertical) |

**Interaction:** Tap opens **Why Sheet** (bottom sheet). Phase 1 may implement sheet with static structure; content from `_evidence_summary` + flags mapped to plain bullets.

**Decision:** Not an expander arrow — ghost text feels optional. "Swipe up" removed from primary mockup — **tap is more discoverable** on desktop/web; swipe added on mobile Phase 1.1 if needed.

---

### 4.7 Why sheet (collapsed by default)

| Property | Value |
|----------|-------|
| Sheet radius | 24px top corners |
| Sheet bg | `#1C1C1E` |
| Handle | 36×5px pill, `#3A3A3C`, centered, 8px from top |
| Max height | 70vh |
| Padding | 24px horizontal, 32px bottom + safe-area |

**Content:**
- Title: none (no "Evidence")
- 3–6 bullets, Inter 17px / 1.5, `#F5F5F7` 85%
- Optional last line: conviction in prose — "I'm fairly sure about this."

**Decision:** Sheet = iOS native pattern. Streamlit expander banned.

---

### 4.8 Bottom navigation (visual shell — Phase 1)

| Property | Value |
|----------|-------|
| Height | 49px + safe-bottom |
| Background | `#0A0A0B` with top border `1px solid #1C1C1E` |
| Items | 3: Today · Trades · You |

| Item | Icon | Label | State |
|------|------|-------|-------|
| Today | Sun/dot 24px | Today | Active: `#F5F5F7`, inactive: 40% |
| Trades | Ticket outline 24px | Trades | Inactive Phase 1 |
| You | Person 24px | You | Inactive Phase 1 |

Active indicator: 2px line `#F5F5F7` above label, 24px wide, centered.

**Decision:** Show nav shell so Today doesn't feel orphaned — but **only Today is interactive** in Phase 1. Tapping Trades/You = subtle toast "Coming soon" (no broken nav).

---

### 4.9 Ask pill (visual shell — Phase 1)

| Property | Value |
|----------|-------|
| Size | 56×56px circle |
| Position | fixed; right 16px; bottom: nav height + 16px + safe-bottom |
| Background | `#1C1C1E` |
| Border | 1px `#2C2C2E` |
| Icon | Search/magnifier 22px, `#F5F5F7` |
| Shadow | `0 4px 12px rgba(0,0,0,0.4)` |

**Phase 1:** Visible but tap → toast "Ask — Phase 4". **Decision:** Establishes product silhouette without building Ask yet.

---

## 5. Verdict states — complete catalog

### 5.1 WAIT (default flagship mockup)

| Element | Value |
|---------|-------|
| Verdict | `Wait` · `#FFC107` |
| Mentor | "I'd sit on my hands until 9:45. Your book looks fine. If RELIANCE clears ₹2,850, that's the only name worth a look." |
| CTA | You're done for today |
| Ambient | Amber glow 6% |

**User feels:** Relief, patience, permission to close app.

---

### 5.2 TRADE

| Element | Value |
|---------|-------|
| Verdict | `Trade` · `#00E676` |
| Mentor | "One setup worth risking capital on. Stay within your ₹2,000 daily limit. Your book can handle it." |
| CTA | See the plan |
| Ambient | Green glow 6% |

**Decision:** No entry/stop on canvas — plan is Phase 2. Mentor mentions limit only.

---

### 5.3 PAUSE (loss streak / risk block)

| Element | Value |
|---------|-------|
| Verdict | `Pause` · `#FF6B6B` |
| Mentor | "Three losing days in a row. The smartest trade is no trade. Your book doesn't need changes." |
| CTA | You're done for today |

---

### 5.4 REST (market closed)

| Element | Value |
|---------|-------|
| Verdict | `Rest` · `#A1A1A6` |
| Mentor | "Markets are closed. Nothing to do until Monday 9 AM." |
| CTA | View your week |

---

### 5.5 CONNECT (broker offline)

| Element | Value |
|---------|-------|
| Verdict | `Connect` · `#64B5F6` |
| Mentor | "I can't see your real holdings yet. Connect Zerodha so I can advise on your actual book." |
| CTA | Connect Zerodha |

---

### 5.6 LOADING

| Element | Value |
|---------|-------|
| Verdict | Animated `···` (3 dots pulse) |
| Mentor | "Checking the market and your book." |
| CTA | Disabled |

---

## 6. Motion specification

| Event | Animation | Duration | Easing |
|-------|-----------|----------|--------|
| First paint | Verdict opacity 0→1, translateY 12→0 | 400ms | `cubic-bezier(0.16, 1, 0.3, 1)` |
| Mentor | Delay 150ms, same fade-up | 350ms | same |
| Button | Delay 300ms | 300ms | same |
| Verdict change | Crossfade old→new | 300ms | ease-in-out |
| Why sheet open | translateY 100%→0 | 350ms | spring-like `cubic-bezier(0.32, 0.72, 0, 1)` |
| Button press | scale 0.98 | 100ms | ease-out |

**Reduced motion:** `prefers-reduced-motion: reduce` → instant show, no translate.

---

## 7. Typography scale (Phase 1 only)

| Token | Size | Weight | Line-height | Use |
|-------|------|--------|-------------|-----|
| `verdict` | 56px (44 SE) | 600 | 1.0 | Focal word |
| `mentor` | 20px | 400 | 1.45 | Body |
| `action` | 17px | 600 | 1.0 | Button |
| `ghost` | 15px | 500 | 1.0 | Why hint |
| `micro` | 13px | 500 | 1.0 | Time, sync |

**Max 3 sizes visible:** verdict + mentor + (action OR micro).

---

## 8. Spacing tokens (8pt grid)

| Token | px | Usage in Phase 1 |
|-------|-----|------------------|
| xs | 8 | Handle margin, dot gap |
| sm | 16 | Screen horizontal margin, ghost margin-top |
| md | 24 | Sheet padding |
| lg | 32 | Mentor-to-button gap |
| xl | 40 | Verdict zone internal padding |
| xxl | 48 | Verdict word vertical breathing |

---

## 9. Accessibility

| Requirement | Implementation |
|-------------|----------------|
| Contrast | Verdict amber `#FFC107` on `#0A0A0B` = 9.4:1 ✓ |
| Verdict announced | `role="status"` `aria-live="polite"` on verdict element |
| Button | `aria-label` matches visible label |
| Why hint | `aria-expanded` tied to sheet |
| Focus order | Verdict (read-only) → CTA → Why → Nav |
| Touch targets | Min 44×44px all interactive |
| Color + text | Verdict always textual, never color-only |

---

## 10. What is explicitly removed from current Home

| Removed | Reason |
|---------|--------|
| Five question-cards | Competing focal points |
| "What should I do today?" label | Software taxonomy |
| High/Medium/Low badge | Metric chrome |
| Entry/stop/target grid | Belongs on Trade Ticket |
| Broker card | Ambient sync dot |
| Bottom stock search | Ask pill (Phase 4) |
| Capital settings | Settings (Phase 3) |
| Quick actions row | Violates one action |
| `assist-card` CSS pattern | Card dashboard |
| Reading time footer | Gimmick; brevity is the signal |
| Investment OS / dashboard branding | Product rename |

---

## 11. Phase 1 implementation contract (after mockup approval)

**Files likely touched (presentation only):**
- `ui/components/home_dashboard.py` → rewrite render to Verdict Canvas
- `ui/theme.py` → add `VERDICT_CANVAS_CSS` tokens
- `ui/pages/unified_home.py` / `app.py` → minimal chrome adjustments if needed

**Files NOT touched:**
- `analyzer/*` engines
- `TradingDecision` schema (future)
- Broker OAuth, portfolio store, decision engine

**Data:** Continue `load_dashboard_data()` unchanged; map outputs to verdict state machine:

```
if not broker.connected → CONNECT
elif market closed → REST
elif loss_streak >= threshold → PAUSE
elif decision ACT → TRADE
elif decision PASS/NO_TRADE → PAUSE or REST
else → WAIT
```

**Review gate:** Phase 1 PR requires screenshot match to mockup ±2px on 390×844.

---

## 12. Approval checklist

Before Streamlit implementation begins, confirm:

- [ ] Title case verdict (`Wait` not `WAIT`)
- [ ] 56px verdict, 20px mentor, one 52px button
- [ ] No cards, no section labels, no metrics on default view
- [ ] Wait state CTA = "You're done for today"
- [ ] Trade state shows no entry/stop on canvas
- [ ] Bottom nav + Ask pill visible but stubbed
- [ ] Dark canvas `#0A0A0B` default
- [ ] Mockup HTML reviewed at 390px width

**Sign-off:** _________________ Date: _________

---

*Phase 1 Verdict Canvas — pixel-perfect spec v1.0*
