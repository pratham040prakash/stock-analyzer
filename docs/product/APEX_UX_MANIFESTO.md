# APEX UX Manifesto

**Document ID:** UX-000  
**Version:** 1.0  
**Status:** DRAFT — Product Review  
**Date:** 2026-08-06  
**Owner:** Product · UX  
**Program:** APEX V3.5 — UX Excellence  
**Baseline:** V3-202 @ `0d44c9c` · Architecture FROZEN  
**Authority:** Highest-level product document — every future feature must comply  
**References:** [MASTER_PROMPT](../../.cursor/MASTER_PROMPT.md) · [APEX_V3_PRODUCT_STRATEGY.md](./APEX_V3_PRODUCT_STRATEGY.md) · [APEX-000](../apex/APEX-000_Company_Constitution.md)

---

## Executive Summary

The **APEX UX Manifesto** is the constitution for how APEX looks, reads, and behaves. It exists because investing software too often optimizes for urgency, volume, and engagement — and investors pay for that with anxiety, impulsive trades, and lost trust.

APEX exists to help people make **better decisions, not more decisions**. Every screen must answer one primary question. Every answer must come before explanation. Depth is available on demand — never forced. Evidence is labeled; uncertainty is visible; the user always owns the final call.

Decision memory is **append-only**: the Journal preserves what the investor believed at a moment in time and never rewrites history. Navigation must feel continuous — Research, Portfolio, Home, and Journal are one operating system, not disconnected tabs.

This document does not describe features or wireframes. It defines the **non-negotiable UX law** that Product, Design, and Engineering must apply before any surface ships. If a proposed change violates this manifesto, the change is rejected — regardless of technical elegance or schedule pressure.

**Success looks like:** investors who feel calmer after using APEX, understand *why* a view is shown, trust that nothing is hidden, and leave with a clearer next step — not a dopamine hit.

---

## 1. Vision

### Why APEX exists

Investing is hard because information is abundant, emotions are loud, and most tools are built to **activate** users — not to **clarify** them.

APEX exists to be the investor's **decision companion**: a calm, evidence-aware system that helps serious retail investors in India understand what they own, what they are considering, and what they decided — with enough depth to trust the answer and enough restraint to respect their time.

APEX is **not** a trading terminal, a social feed, a news aggregator, or an AI chatbot dressed as advice. It is an **Investment Decision Platform** — portfolio intelligence, research discipline, and decision memory in one coherent experience.

> *Better decisions. Not more decisions.*

The UX mission is inseparable from the product mission: reduce anxiety, increase understanding, preserve discipline, and compound trust over years — not sessions.

---

## 2. Design Philosophy

### How APEX should feel

APEX should feel like a **trusted analyst's briefing room** — not a casino floor, not a Twitter timeline, not a homework assignment.

| Feel | Means | Does not mean |
|------|-------|---------------|
| **Calm** | Measured tone, generous whitespace, no alarm colors by default | Boring, empty, or evasive |
| **Clear** | One headline answer, plain language, visible hierarchy | Oversimplified or patronizing |
| **Honest** | Uncertainty shown; gaps labeled | False precision or hidden caveats |
| **Respectful** | User time protected; depth optional | Rushing to verdict without context |
| **Institutional** | Structured reasoning, labeled evidence | Jargon-heavy or academic walls of text |
| **Personal** | Portfolio-aware, decision-aware | Generic tips or one-size-fits-all hype |

Design serves **decision quality**, not engagement metrics. If a pattern increases clicks, screen time, or trade frequency without improving understanding, it fails — even if it looks polished.

---

## 3. One Primary Question Per Screen

Every screen answers **one important question** — stated explicitly in design review, reflected in the headline, and testable in ten seconds.

| Pillar | Screen | Primary question |
|--------|--------|------------------|
| Home | Command Center | What should I do today? |
| Portfolio | Overview | Is my portfolio healthy? |
| Portfolio | Holdings | What do I own? |
| Portfolio | Review | What deserves my attention? |
| Research | Workbench | Should I invest in this company? |
| Journal | Timeline | What decisions have I recorded? |
| Journal | Entry Detail | What did I believe when I decided? |

**Rules:**

- One hero answer or status per screen — not three competing headlines.
- Secondary questions belong below the fold or in progressive disclosure.
- If a screen cannot name its primary question in one sentence, it is not ready to ship.
- Tabs and sub-nav may exist, but each **view** within them still owns one question.

---

## 4. Answer Before Explanation

Never overwhelm users with context before they know **what matters**.

**Order of information (frozen):**

1. **Answer** — verdict, status, disposition, or headline (what is true right now)
2. **Why (short)** — one supporting line or badge cluster
3. **Evidence on demand** — Understand, Proof, depth panels
4. **Full detail** — contracts, history, footnotes, broker truth

**Anti-patterns (forbidden):**

- Opening with charts, tables, or paragraphs before the answer
- Burying the recommendation below marketing copy
- Forcing scroll to learn "Hold vs Wait"
- Showing ten metrics when one status suffices

The **10-second test:** a user landing cold can state the screen's answer and their next sensible action without reading fine print.

---

## 5. Progressive Disclosure

Surface depth **only when requested**. Default views stay lightweight; experts drill down without penalizing beginners.

| Layer | Purpose | Examples |
|-------|---------|----------|
| **Surface** | Answer + minimal context | Hero, status badge, one-line summary |
| **Explain** | Structured reasoning | Understand popover, labeled evidence |
| **Prove** | Verifiable artifacts | Proof overlay, decision_id, packet refs |
| **Archive** | Historical record | Journal entries, evolution chain |

**Rules:**

- Popovers, expanders, and overlays preferred over new pages for depth — unless the depth itself is the primary question (e.g., Entry Detail).
- Never auto-expand anxiety-inducing detail (risks, losses, conflicts) above the fold without user intent.
- "Help me understand" is always available; it is never mandatory reading.
- Adding a new data field does not justify showing it by default — justify **withholding** it first.

---

## 6. Calm Over Urgency

Reduce anxiety. **Never encourage impulsive investing.**

| Do | Don't |
|----|-------|
| Use neutral language for mixed signals | Flash "ACT NOW" or countdown timers |
| Frame patience as discipline | Frame waiting as failure or FOMO |
| Show risk before upside when material | Lead with gain targets to trigger action |
| Separate daily verdict from long-term research | Blur intraday noise with investment thesis |
| Offer "wait" as a valid outcome | Shame users for not trading |

**Visual calm:**

- No pulsing CTAs, ticker-style motion, or red/green dominance on overview screens
- Alerts are **specific and actionable** — not ambient fear
- P&L appears where portfolio truth requires it — not as a leaderboard or scoreboard on decision screens

APEX may inform urgency when **facts** require attention (e.g., flagged health, stale sync) — never manufacture urgency for engagement.

---

## 7. Evidence Before Opinion

Clearly distinguish what is known, inferred, estimated, or judged.

**Label taxonomy (mandatory where applicable):**

| Label | Meaning | Example use |
|-------|---------|-------------|
| **FACT** | Verified data with stated source | Broker holding qty, filed metric, synced price |
| **ASSUMPTION** | Explicit premise not yet verified | "If margins stabilize for two quarters…" |
| **ESTIMATE** | Model or heuristic output | Valuation band, scenario target, confidence % |
| **OPINION** | System or user judgment | Recommendation narrative, disposition, thesis |

**Rules:**

- Never present ESTIMATE or OPINION as FACT.
- Never fabricate metrics — state gaps plainly.
- Conflicting evidence is shown **labeled**, not averaged into false consensus.
- User narrative in Journal is **OPINION** (user-owned); system summary is frozen **ESTIMATE/OPINION** at record time — not live recomputation.

If a surface cannot label its claims, it cannot ship.

---

## 8. Decision Ownership

APEX supports decisions. **Users own decisions.**

| APEX provides | User owns |
|---------------|-----------|
| Structured research questions | Final investment judgment |
| System view + labeled evidence | Whether to accept or reject the view |
| Disposition options (Watch, Hold, etc.) | Which disposition fits their plan |
| Journal capture workflow | Confirming and standing behind recorded text |
| Proof and Understand gateways | Whether to verify before acting |

**Forbidden:**

- Language implying APEX "tells you what to do" without user confirmation
- Auto-executing trades or one-click buy/sell from research surfaces
- Rewriting user Journal entries post-confirm
- Implying guaranteed outcomes or certainty

Copy pattern: *"Based on available evidence…"* · *"Your decision:"* · *"You recorded:"*

---

## 9. Immutable Decision Memory

Journal preserves history. **History is append-only.**

| Layer | Records | Rule |
|-------|---------|------|
| **Journal Entry** | What the investor **believed** at decision time | Immutable after confirm |
| **Outcome Review** (future) | What **actually happened** | Separate record; never edits original belief |

**UX implications:**

- Confirmed entries display **Recorded** — never "Updated"
- Corrections require a **new linked entry**, not silent overwrite
- Frozen portfolio snapshot and system context shown as **at decision time**
- Draft state is clearly labeled; confirm step teaches immutability before commit

Trust in decision memory is trust in APEX. Breaking append-only semantics breaks the product.

---

## 10. Navigation Continuity

Every workflow should feel **uninterrupted** — one operating system, not a bag of legacy tabs.

**Principles:**

- Handoffs preserve context: symbol, back tab, portfolio origin, review theme
- Return paths are explicit: Back to Portfolio · Open Research · Open Journal
- Cross-pillar jumps do not reset unrelated state without user intent
- Primary nav reflects pillars (Home · Portfolio · Research · Journal · You) — legacy tabs redirect, not duplicate

**Anti-patterns:**

- Dead-end screens with no return path
- Losing symbol context when moving Research → Journal → Portfolio
- Duplicate answers on Home and Research for the same question
- Surprise tab switches without user action

Continuity is a UX feature — not a routing implementation detail.

---

## 11. Language Guidelines

Professional. Calm. Educational. **Never sensational.**

| Use | Avoid |
|-----|-------|
| "Mixed signals" | "Explosive opportunity" |
| "Cautious" | "Don't miss out" |
| "Hold — do not add yet" | "Strong buy before it's too late" |
| "Insufficient data" | "Hidden gem" |
| "Your decision" | "Our pick" |
| "Recorded" | "Locked in profits" |

**Tone rules:**

- Short sentences; active voice; Indian context (₹, IST, NSE/BSE) where relevant
- Explain terms on first use in a surface — link to learning, don't lecture
- Disclaimers visible but not dominant — trust through transparency, not legalese walls
- No emoji as primary status communication (badges and text labels first)

Language is interface. Hype is a defect.

---

## 12. Visual Principles

### Whitespace

Whitespace is structure. Dense screens signal panic; breathable layouts signal control. Below-the-fold content may be rich; above-the-fold must breathe.

### Hierarchy

One dominant element per viewport region: hero > supporting > tertiary. Typography scale and weight — not color alone — carry meaning.

### Consistency

Shared theme system (`APEX_PARTNER_EXPERIENCE_CSS` and successors). No one-off screens. Cards, badges, and section labels reuse the same patterns across Home, Portfolio, Research, and Journal.

### Motion with purpose

Motion clarifies state change (confirm, navigate, expand) — never decorates. Respect `prefers-reduced-motion`. No infinite loops, parallax, or gamified celebrations on financial outcomes.

### Accessibility

Contrast, focus, landmarks, and readable type are non-negotiable — see Section 15.

---

## 13. Trust Principles

Show evidence. Explain reasoning. **Never hide uncertainty.**

| Principle | UX expression |
|-----------|---------------|
| **Verifiable** | Proof overlay, decision_id, evidence packet links |
| **Transparent** | Stale sync labels, data gaps, broker vs market source |
| **Calibrated** | Confidence shown with limits — not false precision |
| **Consistent** | Same symbol → same canonical fields across surfaces (projection SSOT) |
| **Accountable** | Journal records what was shown **then** — not retroactive rewrite |

Trust is eroded by: hidden assumptions, live-updating historical entries, contradictory headlines on sibling screens, and certainty language when data is incomplete.

---

## 14. Performance Principles

Fast answers. **Heavy detail on demand.**

| Tier | Target | Content |
|------|--------|---------|
| **Answer** | Perceived instant (<200ms cached) | Hero, status, primary CTA |
| **Explain** | Lazy on interaction | Understand popover, depth panel |
| **Prove** | On explicit tap | Proof overlay, charts |
| **Archive** | Paginated / lazy | Journal timeline, long history |

**Rules:**

- Never block the headline on optional modules
- Skeleton or stale labels beat silent spinners
- Confirmed Journal entries read stored contracts — no live re-assembly from bundle on scroll
- Performance regressions on primary question are P0 UX bugs

Speed is respect. Slowness is anxiety.

---

## 15. Accessibility Principles

Keyboard-first. Screen-reader friendly. Reduced motion. Responsive.

| Requirement | Standard |
|-------------|----------|
| **Keyboard** | Logical tab order; visible focus; Escape closes overlays |
| **Screen readers** | Landmarks (`main`, `nav`, `article`); `aria-label` on heroes; `time` elements with `datetime` |
| **Color** | Status never color-only — text labels always paired |
| **Motion** | Honor reduced-motion; no essential info in animation alone |
| **Responsive** | Usable at 320px mobile; touch targets ≥44px |
| **Forms** | Labels visible or programmatically associated; errors specific |

Accessibility is not a Phase 5 polish item — it is a ship gate for every milestone.

---

## 16. Design System Rules

One system. No orphan patterns.

### Typography

- One sans stack; max 3 sizes above the fold per screen
- Hero: decision/status · Section labels: uppercase tracked small caps · Body: 14–16px readable line height

### Spacing

- 4px base grid; consistent section padding (12–16px cards; 8px inter-element)
- Below-fold grouped in `.apex-*-below-fold` patterns where applicable

### Color semantics

| Semantic | Use | Avoid |
|----------|-----|-------|
| Neutral | Default text, structure | — |
| Accent (blue) | Links, primary actions, evidence labels | Decorative fills |
| Positive (green) | Confirmed healthy, recorded badge | Entire profit screens |
| Warning (amber) | Stale, attention flags, immutability note | Generic urgency |
| Negative (red) | Errors, critical flags only | Emotional P&L emphasis |

### Cards

- Rounded 12px; subtle border; one concept per card
- Entry cards: type badge → symbol + disposition → narrative preview → meta

### Badges

- Text always visible; `data-badge` or aria-label for status
- Disposition, health, sync — never interchangeable visually

### Buttons

- One primary per viewport region
- Destructive actions (Discard) secondary styling — never primary red by default
- Disabled with explanation — not silent disabled (especially future features)

### Empty states

- State the primary question answer ("No decisions yet")
- One calm CTA to the natural next step — not guilt

### Loading states

- Preserve layout; label stale vs loading vs error
- Never flash misleading defaults before data arrives

---

## 17. Review Checklist

Every feature must answer **yes** to all questions before Product approval.

### Primary question

- [ ] What is the **one primary question** this screen answers?
- [ ] Can a user answer it in **10 seconds** without scrolling?

### Answer-first

- [ ] Is the **answer above the fold**?
- [ ] Is explanation **below or behind** Understand / Proof?

### Calm & ownership

- [ ] Does copy avoid urgency, hype, and FOMO?
- [ ] Is the **user** clearly the decision owner?

### Evidence

- [ ] Are claims labeled FACT / ASSUMPTION / ESTIMATE / OPINION where needed?
- [ ] Are data gaps and uncertainty visible?

### Memory & trust

- [ ] If recording a decision, is immutability taught before confirm?
- [ ] Are historical views frozen — not live-recomputed?

### Navigation

- [ ] Is there a clear **return path**?
- [ ] Does handoff preserve symbol and origin context?

### System fit

- [ ] Does it reuse shared theme, Understand, Proof — not duplicate?
- [ ] Does it violate **no analyzer in render layer** architecture?

### Accessibility & performance

- [ ] Keyboard, screen reader, and contrast checked?
- [ ] Is headline path fast; heavy detail lazy?

**If any answer is no:** revise or reject — do not ship and fix later.

---

## 18. Success Metrics

UX quality is measured by **decision quality proxies** — not vanity engagement.

| Metric | What good looks like | What we reject |
|--------|----------------------|----------------|
| **10-second comprehension** | ≥90% of moderated sessions state the screen answer correctly | Users lost in first viewport |
| **Understand usage depth** | Users who need depth find it; beginners aren't forced | Mandatory walls of text |
| **Decision recording rate** | Research → Journal confirm without drop-off confusion | Toast-only "saved" with no memory |
| **Journal immutability trust** | Zero support reports of "APEX changed my decision" | Editable confirmed history |
| **Anxiety proxy (qual)** | Users describe feeling "clearer" or "calmer" | "Overwhelmed" / "pressured to trade" |
| **Navigation continuity** | Cross-pillar tasks complete without dead ends | Abandoned handoffs Research ↔ Journal |
| **Accessibility gate** | WCAG baseline checks pass per milestone | Color-only status, missing landmarks |
| **Performance gate** | Hero LCP targets met on cached paths | Spinner-first headlines |
| **Trust incidents** | Zero fabricated metrics shipped | Any unlabeled certainty claim |

**Review cadence:** Each milestone includes UX manifesto checklist sign-off alongside engineering gate.

**North star sentence:** *Investors leave APEX with fewer open questions, not more open trades.*

---

*Draft for Product Review — UX-000 — 2026-08-06. No implementation.*
