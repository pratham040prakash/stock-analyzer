# ETS-003a — Morning Brief Experience Specification

**The Signature Experience of APEX**

**Document ID:** ETS-003a  
**Version:** 0.1  
**Status:** DRAFT — Product Experience Specification (no implementation)  
**Date:** 2026-08-05  
**Owner:** ChatGPT (CTO / CPO)  
**Author:** Cursor AI (Engineering — Principal PM / UX / Architect)  
**Reviewers:** Pratham Prakash (Founder) — pending · ChatGPT (CTO) — pending  
**References:** [APEX-000](../APEX-000_Company_Constitution.md), [APEX-001](../APEX-001_Sprint0_Engineering_Assessment.md), [APEX-003](../APEX-003_Product_Strategy_and_PRD.md), [APEX-004](../APEX-004_Experience_Operating_System.md), [APEX-005](../APEX-005_System_Architecture_Blueprint.md), [ETS-002.1](./ETS-002.1_Broker_Auth_Session.md), [ETS-003](./ETS-003_Today_Surface_Product_Spec.md), [Phase 1 Verdict Canvas Spec](../../design/Phase_1_Verdict_Canvas_Spec.md)

**Scope:** Complete Morning Brief *experience* definition. No code, Streamlit, React, CSS, Figma, APIs, or architecture changes.

**Relationship to ETS-003:** ETS-003 defines *what* the Today Surface must accomplish. ETS-003a defines *how the Morning Brief feels, reads, and behaves* across devices — the signature daily ritual.

**Constitutional rule:** Morning Brief **is** the Today surface ([APEX-004 §17.1](../APEX-004_Experience_Operating_System.md)). There is no separate "Brief" tab.

---

## Table of Contents

1. [Morning Brief Philosophy](#1-morning-brief-philosophy)  
2. [Jobs To Be Done](#2-jobs-to-be-done)  
3. [Emotional Design Goals](#3-emotional-design-goals)  
4. [30-Second User Journey](#4-30-second-user-journey)  
5. [Information Hierarchy](#5-information-hierarchy)  
6. [Desktop Experience](#6-desktop-experience)  
7. [Tablet Experience](#7-tablet-experience)  
8. [Mobile Experience](#8-mobile-experience)  
9. [Hero Decision Card](#9-hero-decision-card)  
10. [Best Opportunity Today](#10-best-opportunity-today)  
11. [Risk Monitor](#11-risk-monitor)  
12. [Portfolio Ready Status](#12-portfolio-ready-status)  
13. [Market Context](#13-market-context)  
14. [Coach's Insight](#14-coachs-insight)  
15. [Quick Actions](#15-quick-actions)  
16. [Failure States](#16-failure-states)  
17. [Weekend Experience](#17-weekend-experience)  
18. [Market Closed Experience](#18-market-closed-experience)  
19. [No Broker Experience](#19-no-broker-experience)  
20. [Loading Strategy](#20-loading-strategy)  
21. [Performance Budget](#21-performance-budget)  
22. [Accessibility Requirements](#22-accessibility-requirements)  
23. [Microcopy Guidelines](#23-microcopy-guidelines)  
24. [Animation Principles](#24-animation-principles)  
25. [Acceptance Criteria](#25-acceptance-criteria)  
26. [Engineering Traceability](#26-engineering-traceability)  
27. [Founder Decisions Required](#27-founder-decisions-required)  
28. [CTO Decisions Required](#28-cto-decisions-required)  
29. [Implementation Risks](#29-implementation-risks)  
30. [Recommendation to Begin ETS-003b](#30-recommendation-to-begin-ets-003b)

---

## 1. Morning Brief Philosophy

### 1.1 What the Morning Brief is

The Morning Brief is a **daily decision ceremony** — not a page, not a feed, not a dashboard.

It is the moment APEX earns trust: one calm screen that answers whether today's capital deserves action, why, and what guardrails apply.

### 1.2 What the Morning Brief is not

| Not this | Because |
|----------|---------|
| Home dashboard | Dashboards optimize for time-on-screen; Brief optimizes for clarity-then-exit |
| News aggregator | APEX sells clarity, not headlines |
| Screener | Discovery belongs elsewhere; Brief is about *today's* decision |
| Chat | Ask is one-shot; Brief is authoritative |
| Tip service | No guaranteed returns; no hype |

### 1.3 Sacred window

**8:30–9:15 AM IST** is primary ([APEX-003 §8.3](../APEX-003_Product_Strategy_and_PRD.md)). The Brief must be complete, readable, and actionable in this window. Pre-open and post-open variants adjust copy and ribbon — not structure.

### 1.4 Success definition

A successful Morning Brief session ends with the user **knowing what to do** — including **doing nothing** — and **closing the app without guilt**.

---

## 2. Jobs To Be Done

### 2.1 Core JTBD

> **When** I start my day and markets matter to my capital,  
> **I want** a single trustworthy call on whether to act,  
> **So I can** protect my process and my money before the noise begins.

### 2.2 Morning-specific jobs

| Job | Outcome | Brief element |
|-----|---------|---------------|
| Orient in seconds | "I'm in the right place" | Hero Decision Card |
| Permission to wait | No FOMO on flat days | WAIT verdict + coach copy |
| Permission to act | Clear path when edge exists | ACT + Best Opportunity |
| Risk awareness | No surprise blocks on Kite | Risk Monitor |
| Personalization trust | "This is about *my* money" | Portfolio Ready Status |
| Verify if doubtful | Optional depth | Proof CTA |
| Leave quickly | ≤30s on WAIT days | No scroll required |

### 2.3 Jobs explicitly deferred (other surfaces)

| Job | Surface |
|-----|---------|
| Execute with E/SL/T | Trades |
| Deep evidence | Proof |
| Track record | Trust |
| One doubt | Ask |
| Behaviour change | You |

---

## 3. Emotional Design Goals

### 3.1 Target feelings

| Feeling | Design lever |
|---------|--------------|
| **Calm** | Dark canvas, generous whitespace, slow animations |
| **Confident** | One verdict, labeled reasoning, broker sync visible |
| **Focused** | Single hero; no competing widgets |
| **Trusted** | CDQS honesty; stale states labeled |
| **Relieved** (on WAIT) | Copy validates inaction |

### 3.2 Forbidden feelings

| Forbidden | Anti-pattern |
|-----------|--------------|
| Overwhelmed | Metric grids, multiple CTAs |
| Anxious | Red flashing, "ACT NOW" |
| FOMO | Opportunity lists on WAIT days |
| Dismissed | Empty states without mentor voice |
| Manipulated | Unlabeled predictions |

### 3.3 Emotional arc (typical WAIT morning)

```
Open (mild anxiety) → See verdict (attention) → Read mentor (understanding)
→ Feel permitted to wait (relief) → Close app (confidence)
```

### 3.4 Differentiation summary (see §5.4 in ETS-003; expanded here)

| Product | What user gets | APEX Morning Brief |
|---------|----------------|-------------------|
| **TradingView** | Infinite charts | One verdict — charts only in Proof |
| **Zerodha Kite** | Execution + holdings | Decision before execution |
| **Groww** | Simplicity + MF | Process discipline + verified CDQS |
| **Moneycontrol** | News noise | Zero headlines on default view |
| **Bloomberg** | Information depth | Clarity at 30 seconds |
| **ChatGPT / Claude / Perplexity** | Conversational answers | One authoritative daily call + audit trail |

---

## 4. 30-Second User Journey

**Persona:** Arjun · 9:12 AM IST · Broker synced · Pre-open

| Window | User action | System response | Success signal |
|--------|-------------|-----------------|----------------|
| **0–5s** | Opens app | Today loads; sync green; verdict visible | Eyes on verdict |
| **5–15s** | Reads mentor block | CIO voice; 3 lines max | Nods / exhales |
| **15–25s** | Reads ribbon + optional glance | Session context ambient | No confusion |
| **25–30s** | Taps CTA or closes | Proof path OR exit | Session ≤45s on WAIT |

**ACT path (25–30s):** Taps **Review trade plan** → Trades within 5s.

**Never required in 30s:** Scroll, Portfolio block, Market Context, Coach's Insight below fold.

---

## 5. Information Hierarchy

### 5.1 Layer model

| Layer | Name | Scroll | Content |
|-------|------|--------|---------|
| **L0** | Hero | Never | Verdict + mentor + primary CTA |
| **L0.5** | Ambient | Never | Header time, sync, session ribbon |
| **L1** | Confidence | Optional | Portfolio Ready, Risk prose |
| **L2** | Depth | Optional | Best Opportunity, Market Context, Coach |
| **L3** | Navigation | Optional | Quick Actions, bottom nav, Ask pill |

### 5.2 Never appear (L-ban)

- Watchlists as tables  
- P&L leaderboards  
- "Top gainers / losers"  
- RSI, MACD, indicator values on default view  
- Multiple verdicts or conflicting signals  
- Engine terms (`EvidencePacket`, `DecisionEngine`)  
- News headlines  
- Social sentiment  
- Ads, upsells, upgrade banners  

### 5.3 Information diet rule

> If removing a section does not make today's **decision worse**, remove it from default view.

---

## 6. Desktop Experience

### 6.1 Layout principle

Desktop is **not** a wide dashboard. Content column is **max 430px centered** on viewport ([APEX-004 DDR-006](../APEX-004_Experience_Operating_System.md)). Surrounding space is calm void (`#0A0A0B`) — not secondary panels.

### 6.2 Desktop-specific behaviors

| Behavior | Rule |
|----------|------|
| Column width | 430px fixed content; centered |
| Keyboard | `Enter` activates primary CTA when focused |
| Hover | Subtle opacity on CTA; no hover on verdict |
| Scroll | Mouse wheel reveals L1/L2 only after L0 consumed |
| Window resize | Below 430px → mobile rules; above → centered column |

### 6.3 Desktop wireframe (ASCII)

```
┌────────────────────────────────────────── 1440px viewport ──────────────────────────────────────────┐
│                                                                                                    │
│                          ┌──────────────────── 430px column ────────────────────┐                  │
│                          │ 9:12 IST                              ● Synced        │                  │
│                          │ Prep ✓ · Dam 62% · Open in 8m                      │                  │
│                          │                                                    │                  │
│                          │                                                    │                  │
│                          │                    Wait                            │                  │
│                          │                                                    │                  │
│                          │                                                    │                  │
│                          │   No setup passes your rules today. The best       │                  │
│                          │   trade may be the one you don't make.             │                  │
│                          │   FACT: range regime · OPINION: wait for clarity.  │                  │
│                          │                                                    │                  │
│                          │   ┌──────────────────────────────────────────┐   │                  │
│                          │   │         See why we're waiting              │   │                  │
│                          │   └──────────────────────────────────────────┘   │                  │
│                          │        See the proof (ghost link)                  │                  │
│                          │ ─ ─ ─ ─ ─ scroll optional ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │                  │
│                          │ Portfolio ready · ₹38.2k tactical · synced 6m    │                  │
│                          │ Risk · Dam 62% · one loss to pause limit         │                  │
│                          │ Ask · Proof · Trust · You                          │                  │
│                          │ [Today][Trades][Trust][You]              (Ask ○) │                  │
│                          └────────────────────────────────────────────────────┘                  │
│                                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Tablet Experience

### 7.1 Layout principle

Tablet (768–1024px) uses **same 430px column**, optionally with slightly increased vertical breathing room. No two-column layout. No sidebar widgets.

### 7.2 Tablet-specific behaviors

| Behavior | Rule |
|----------|------|
| Orientation | Portrait = mobile-like; landscape = desktop-like centering |
| Touch targets | Minimum 44×44pt for all actions |
| Split screen | Brief remains single column; no adaptation to 50% width panels |

### 7.3 Tablet wireframe (ASCII) — landscape

```
┌────────────────────────────────────── 1024px ──────────────────────────────────────┐
│                                                                                     │
│              ┌──────────────────────── 430px ────────────────────────┐             │
│              │ 9:12 IST                                    ● Synced      │             │
│              │ Prep ✓ · Dam 62% · Open in 8m                            │             │
│              │                                                           │             │
│              │                        Wait                               │             │
│              │                                                           │             │
│              │   No setup passes your rules today…                       │             │
│              │   [ See why we're waiting ]                               │             │
│              │                                                           │             │
│              │   Portfolio ready · Risk · Quick actions                  │             │
│              │   [Today][Trades][Trust][You]                    (Ask ○)  │             │
│              └───────────────────────────────────────────────────────────┘             │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Mobile Experience

### 8.1 Layout principle

**Primary design target:** 390×844 logical ([Verdict Canvas Spec](../../design/Phase_1_Verdict_Canvas_Spec.md)). Minimum 320×568 (iPhone SE).

### 8.2 Mobile-specific behaviors

| Behavior | Rule |
|----------|------|
| Safe areas | Respect notch + home indicator |
| Thumb zone | Primary CTA in lower-middle reach |
| Ask pill | 56×56 floating above nav |
| Pull to refresh | Phase 1b — optional |
| Haptics | Light tap on CTA only (Phase 1b) |

### 8.3 Mobile wireframe (ASCII)

```
┌──────────────────────── 390px ────────────────────────┐
│ ░░░░░░░░░ safe-top ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
│ 9:12 IST                              ● Synced       │
│ Prep ✓ · Dam 62% · Open in 8m                      │
├──────────────────────────────────────────────────────┤
│                                                      │
│                                                      │
│                      Wait                            │
│                                                      │
│                                                      │
│  No setup passes your rules today.                   │
│  The best trade may be the one                       │
│  you don't make.                                     │
│                                                      │
│  FACT: range regime.                                 │
│  OPINION: preserve optionality.                      │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │       See why we're waiting                │    │
│  └────────────────────────────────────────────┘    │
│         See the proof                              │
│                                                      │
│ ─ ─ ─ scroll ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│ Portfolio ready · synced 6m ago                      │
│ Risk · Dam 62%                                       │
│ Ask · Proof · Trust · You                            │
│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│              ( Ask pill ○ )                          │
│ [ Today ] [ Trades ] [ Trust ] [ You ]               │
│ ░░░░░░░░░ safe-bottom ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
└──────────────────────────────────────────────────────┘
```

---

## 9. Hero Decision Card

*Implements [ETS-003 §6](./ETS-003_Today_Surface_Product_Spec.md) with experience-level detail.*

### 9.1 Role

The **only** focal object above the fold. Occupies ~45% of viewport height on mobile.

### 9.2 Structure (top to bottom)

1. Verdict word (56px mobile / 64px desktop column)  
2. 40px vertical breath  
3. Mentor block (max 4 lines, 16px/1.5)  
4. 32px breath  
5. Primary CTA (358×52px equivalent)  
6. 16px breath  
7. Ghost hint link (optional, one line)

### 9.3 Specialist voice

**Chief Investment Officer (CIO)** — authoritative, calm, never hype ([APEX-004 Model C](../APEX-004_Experience_Operating_System.md)).

### 9.4 Verdict palette

| Verdict | Hex | Meaning |
|---------|-----|---------|
| Wait | `#FFC107` | Default success |
| Act | `#00E676` | Permission, not greed |
| Pause | `#FF9800` | Session halt |
| Defensive | `#90CAF9` | Protection |
| Reduce | `#FF6B6B` | De-risk |

### 9.5 Primary CTA mapping

| Verdict | CTA label | Destination |
|---------|-----------|-------------|
| Wait | See why we're waiting | Proof |
| Act | Review trade plan | Trades |
| Pause | View risk status | Trust |
| Defensive | See what's protected | Proof or Trust |
| Reduce | Review exposure | You or Trades |

---

## 10. Best Opportunity Today

### 10.1 Visibility rule

**Shown only when verdict is ACT or ACT-adjacent (marginal act with Proof-first CTA).**

**Hidden on WAIT, PAUSE, DEFENSIVE, weekend, market closed.**

### 10.2 Content (one row)

| Field | Example |
|-------|---------|
| Symbol | RELIANCE |
| Setup | Opening range breakout |
| Lane | MIS |
| Gates | 4/5 passed |
| Action | Opens Trades pre-filled |

### 10.3 Voice

**Research Analyst** — factual, one sentence, labeled.

### 10.4 Anti-FOMO rule

Never show "other opportunities you missed" or ranked lists.

---

## 11. Risk Monitor

### 11.1 Dual presentation

| Level | Format | Location |
|-------|--------|----------|
| Ambient | Chips in session ribbon | Above fold |
| Narrative | RO voice prose | Below fold (L1) |

### 11.2 Signals

| Signal | Chip example | Prose example |
|--------|--------------|---------------|
| Daily loss dam | `Dam 62%` | "₹1,240 of ₹2,000 daily limit used." |
| Session phase | `Open in 8m` | "Pre-open — plans activate at 9:15." |
| Trade count | `2/3 trades` | "One tactical slot remaining." |
| Hard block | `Paused` | "New risk blocked until tomorrow." |

### 11.3 Specialist voice

**Risk Officer** — firm, protective, never shaming.

---

## 12. Portfolio Ready Status

### 12.1 Purpose

Answer: **"Is this recommendation about my actual capital?"**

### 12.2 States

| State | Copy pattern | Sync dot |
|-------|--------------|----------|
| **Ready** | "Portfolio synced · {n} holdings · {time} ago" | Green |
| **Stale** | "Holdings as of {time} — refresh recommended" | Amber |
| **Offline** | "Connect Zerodha for personalized risk" | Red |
| **Market-only** | "Market context only — connect for your portfolio" | Gray |

### 12.3 Content (max 2 sentences)

Portfolio Manager voice. Distinguish **sacred core** vs **tactical pool** when broker connected.

**Example:**  
*"Tactical pool ₹38,200 ready. Sacred core (SIP) excluded from today's MIS plan. Synced 6 minutes ago."*

---

## 13. Market Context

### 13.1 Purpose

Minimum context to interpret verdict — **not** a market research section.

### 13.2 Max content

Two sentences below fold. Folded into mentor block on weekends/market closed.

### 13.3 Required labels

At least one **FACT** per session when market open.

**Example:**  
*"FACT: Nifty gap +0.4%. ASSUMPTION: first 15 minutes may chop in a range regime."*

---

## 14. Coach's Insight

### 14.1 Purpose

One **process-oriented** insight from Investment Coach — habit, not hot tip.

### 14.2 Relationship to CIO mentor

Mentor block = today's **decision**. Coach's Insight = **longer-loop behaviour** (optional L2).

### 14.3 Frequency

At most one insight per day. Omit if redundant with mentor block.

**Example:**  
*"OPINION: Your edge appears on trend days — today is range-bound. Patience is part of your edge."*

---

## 15. Quick Actions

### 15.1 Row (below fold, L3)

| Icon | Label | Action |
|------|-------|--------|
| ? | Ask | Ask overlay |
| ✓ | Proof | Proof overlay |
| ◎ | Trust | Trust surface |
| ○ | You | You surface |

### 15.2 Rules

- Never compete visually with primary CTA  
- Ask also available as floating pill above nav  
- No Settings, Screener, or Charts here  

---

## 16. Failure States

| Failure | Hero treatment | User action |
|---------|----------------|-------------|
| Decision pipeline error | Verdict: **Pause** | Retry |
| Evidence unavailable | Verdict shown; Proof CTA disabled with reason | Trades if ACT |
| Broker error mid-session | Stale banner; qualified mentor | Reconnect |
| Partial data | **ESTIMATE** labels inline | Proof for detail |
| Timeout >15s | Stale yesterday verdict + "Updating…" | Wait or refresh |

**Scoped failure rule:** Today verdict survives Proof/broker partial failures if `DecisionArtifact` exists ([APEX-004](../APEX-004_Experience_Operating_System.md)).

---

## 17. Weekend Experience

| Element | Treatment |
|---------|-----------|
| Verdict | **Wait** (neutral) |
| Mentor | "Markets are closed. Rest is part of the process." |
| CTA | Review your week → Trust |
| Hidden | Best Opportunity, session dams (intraday), market open countdown |
| Ribbon | "Weekend · NSE closed" |

**Microcopy headline:**  
*"The market is closed. Your best move is to review, not react."*

---

## 18. Market Closed Experience

| Element | Treatment |
|---------|-----------|
| Verdict | **Wait** or frozen last intraday verdict |
| Mentor | Summarize what mattered; forward-looking only for next session |
| CTA | View today's record → Trust |
| Ribbon | "Market closed · {date}" |
| Opportunity | Hidden |

**Microcopy:**  
*"Session closed. Intraday plans are inactive. Protecting capital today was a valid outcome."*

---

## 19. No Broker Experience

| Element | Treatment |
|---------|-----------|
| Banner | Persistent, calm — not modal blocking entire Brief |
| Verdict | Market-level **Wait** or **Act** with **ESTIMATE** scope |
| Mentor | "Connect Zerodha to personalize risk, sizing, and CDQS." |
| CTA | Connect broker → existing wizard |
| Portfolio / Risk | Hidden or generic market-only |
| Sync | Red / Not configured |

**Microcopy:**  
*"This call is based on market context only. Connect Kite to make it about your capital."*

---

## 20. Loading Strategy

### 20.1 Phases

| Phase | Time | User sees |
|-------|------|-----------|
| **T0 Instant** | 0–500ms | Canvas + sync + skeleton or cached verdict |
| **T1 Hero** | 500ms–3s | Verdict + mentor populate |
| **T2 Ambient** | 3–5s | Ribbon chips complete |
| **T3 Depth** | On scroll / idle | L1/L2 zones |

### 20.2 Stale-while-revalidate

If fresh decision >3s away, show last **same-calendar-day** artifact with subtle "Updating…" on header.

### 20.3 Never

- Blank white screen  
- Full-screen spinner  
- Blocking modal on load  

---

## 21. Performance Budget

| Metric | Target | Ceiling |
|--------|--------|---------|
| TTFMV (verdict or skeleton) | 1.5s | 3s |
| Time to readable verdict | 8s system / 30s user | 15s system |
| Time to Clarity (verdict + mentor) | 60s | 90s |
| Critical path API calls | 3 | 5 |
| L0 paint after data | 200ms | 500ms |
| Scroll zone load | Non-blocking | — |

---

## 22. Accessibility Requirements

| Requirement | Standard |
|-------------|----------|
| Color contrast | WCAG 2.1 AA minimum on all text |
| Verdict | Announced first by screen reader (`role="status"`) |
| Sync state | Text label always — not color-only |
| CTA | `aria-label` matches visible label |
| Motion | `prefers-reduced-motion` disables verdict fade |
| Touch targets | ≥44×44pt |
| Focus order | Header → verdict → mentor → CTA → nav |
| Labels | FACT/ASSUMPTION read aloud |

---

## 23. Microcopy Guidelines

### 23.1 Voice

Calm experienced mentor. Short sentences. Labels on uncertainty. Never sensational.

### 23.2 Banned words

`moon`, `rocket`, `guaranteed`, `can't miss`, `urgent`, `last chance`, `buy now`, `strong buy` (use **Act** verdict instead)

### 23.3 Example copy by state

#### ACT

*"One setup meets your rules today. Size matters more than speed. **FACT:** risk headroom available. Review the plan before you open Kite."*

#### WAIT

*"No setup passes your rules today. The best trade may be the one you don't make. **OPINION:** preserving capital is a valid win."*

#### REDUCE

*"Exposure is elevated relative to your rules. **FACT:** concentration above comfort band. Reducing risk is the priority today."*

#### DEFENSIVE

*"Protecting capital is also a winning decision. **FACT:** daily loss limit nearly reached. No new tactical risk today."*

#### NO OPPORTUNITY (WAIT variant)

*"Nothing today meets your standard. Patience is part of your edge. Close the app with confidence."*

#### MARKET CLOSED

*"The session is over. Intraday edge no longer applies. Review what happened in Trust — don't chase after hours."*

#### WEEKEND

*"Markets are closed. Rest, review, and return Monday with a clear head. No action required today."*

#### Coach lines (library)

- *"Patience is part of your edge."*  
- *"The best trade today may be the one you don't make."*  
- *"Protecting capital is also a winning decision."*  
- *"Discipline compounds. So does inconsistency."*  
- *"You don't need more information. You need a clear call."*  

---

## 24. Animation Principles

| Element | Animation | Duration | Easing |
|---------|-----------|----------|--------|
| Verdict appear | Fade + 8px rise | 400ms | ease-out |
| Mentor | Fade after verdict | 300ms delay + 300ms | ease-out |
| CTA | Fade | 500ms delay | ease-out |
| Ribbon chips | None on first paint | — | — |
| Scroll zones | None | — | — |
| Error state | No shake | — | — |

**Reduced motion:** Instant appear, no translate.

**Banned:** Pulse, bounce, confetti, red flash, countdown timers creating urgency.

---

## 25. Acceptance Criteria

### 25.1 Experience AC

- [ ] **AC-E01:** User can state verdict + reason within 30s (usability test)  
- [ ] **AC-E02:** Default view ≤5 elements above fold (verdict, mentor, CTA, sync, ribbon)  
- [ ] **AC-E03:** WAIT session median duration <45s (Founder dogfood)  
- [ ] **AC-E04:** No metric grids on default view  
- [ ] **AC-E05:** Best Opportunity hidden on WAIT days  
- [ ] **AC-E06:** All quantitative claims labeled FACT/ASSUMPTION/OPINION/ESTIMATE  
- [ ] **AC-E07:** Weekend and market closed experiences defined and tested  
- [ ] **AC-E08:** No broker experience clearly scoped as market-only  
- [ ] **AC-E09:** Mobile, tablet, desktop wireframes implemented per column rules  
- [ ] **AC-E10:** Accessibility checklist §22 passes  

### 25.2 Constitution AC

- [ ] **AC-C01:** Morning Brief = Today surface — no separate tab  
- [ ] **AC-C02:** Six surfaces only in nav  
- [ ] **AC-C03:** Single verdict from Decision Engine  
- [ ] **AC-C04:** Aligns with ETS-003 without contradiction  

---

## 26. Engineering Traceability

| ETS-003a section | ETS-003 | APEX-004 | APEX-005 |
|------------------|---------|----------|----------|
| Hero Decision Card | §6 | §14 | `DecisionArtifact`, §20 |
| Morning = Today | §1 | §17.1 | `MorningBrief` use case |
| Session ribbon | §9 | §17.3 | Context snapshot |
| Portfolio Ready | §7 | §16 | `BrokerSnapshot`, ETS-002.1 |
| Risk Monitor | §9 | Risk Officer §8 | Risk in DecisionEngine |
| Best Opportunity | §8 | §18 ACT→Trades | `ActPlan` |
| Coach's Insight | §11 | Investment Coach §7 | Learning boundary |
| Loading / perf | §14–16 | §46 TTC | Pipeline §19–21 |
| Proof / Ask | §13 | §15, §19 | Overlay routing |
| Device column 430px | — | DDR-006 | Platform UI |

**ETS-003b will wire:** `MorningBrief` → `MorningBriefViewModel` (Decision + Evidence + Trust) → `DecisionCardViewModel` hero projection → presentation layer (see [ETS-003b](./ETS-003b_Morning_Brief_Data_Wiring.md)).

---

## 27. Founder Decisions Required

| ID | Decision | Recommendation |
|----|----------|----------------|
| **FD-M01** | Approve Morning Brief as signature daily ritual (not optional feature) | Approve |
| **FD-M02** | WAIT sessions <45s = success metric (not bounce rate) | Approve |
| **FD-M03** | Show Coach's Insight in MVP or Phase 1b | Phase 1b |
| **FD-M04** | Equity-only MIS for MVP Morning Brief | Approve |
| **FD-M05** | Approve microcopy library §23 as canonical voice | Approve with edits |

---

## 28. CTO Decisions Required

| ID | Decision | Recommendation |
|----|----------|----------------|
| **CD-M01** | ETS-003a approved as experience authority for Phase 1 | Approve |
| **CD-M02** | Stale verdict ≤24h same-day with badge | Approve |
| **CD-M03** | Desktop 430px column (no wide layout) | Approve |
| **CD-M04** | Animation spec §24 for Phase 1a or 1b | Phase 1a minimal fade only |
| **CD-M05** | Split ETS-003b: data wiring vs canvas render | Approve split |

---

## 29. Implementation Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Streamlit cannot match experience spec | High | Custom CSS + future shell migration |
| Legacy `unified_home` competes with Brief | High | Feature flag; retire Home |
| Parallel verdict sources | High | Gate on DecisionEngine only |
| Over-scrolling on mobile | Medium | L0 must satisfy 70% sessions |
| Copy feels cold on WAIT | Medium | Founder review microcopy library |
| Performance on cold start | Medium | Stale-while-revalidate |

---

## 30. Recommendation to Begin ETS-003b

**Recommend Founder + CTO approval of ETS-003a**, then begin **ETS-003b — Morning Brief Data Wiring**:

| ETS-003b scope | Out of scope for 003b |
|----------------|------------------------|
| `MorningBrief` use case orchestration | Pixel CSS polish |
| `DecisionCardView` DTO | Below-fold zones (Phase 1b) |
| Bind `BrokerSnapshot` from ETS-002.1 | Keychain (Phase B) |
| Cache / stale policy | New verdict drivers |
| Unit tests on view model | Full Proof overlay |

**Prerequisites before ETS-003b:**

1. ETS-003 + ETS-003a approved  
2. ETS-002.1 Phase A frozen  
3. ETS-001 green (recommended)  
4. Founder sign-off FD-M01, FD-M04  
5. CTO sign-off CD-M01, CD-M05  

**Do not begin implementation until approvals recorded in document headers.**

---

*Repository: stock-analyzer · Product: APEX · Document: ETS-003a · The signature daily experience.*
