# Phase 4 — Answer Canvas (Ask Overlay) · Design Specification

**Product:** AI Trading Decision System  
**Surface:** Ask overlay (global — invoked from Ask FAB on any tab)  
**Status:** **FROZEN** — Phase 1–3 frozen · implementation complete  
**Scope:** Presentation + routing only · backend unchanged  
**Companions:** Phase 1 Today · Phase 2 Trades · Phase 3 You — **do not modify**

---

## 0. Product cohesion charter (inherited — mandatory)

Ask is the **fourth expression of one grammar** — not a fifth app inside the app.

| Surface | Question | Hero focal |
|---------|----------|------------|
| **Today** | Should I act? | Stance word — `Wait` · `Trade` · `Pause` |
| **Trades** | How do I execute? | Symbol — `RELIANCE` |
| **You** | How am I doing? | Trader state — `Growing` · `Steady` · `Focused` |
| **Ask** | What if…? | **Answer word** — `Wait` · `Buy` · `Sell` · `Reduce` · `Pass` |

| Dimension | Rule (unchanged) |
|-----------|------------------|
| Canvas | `#0A0A0B`; 430px column; 16px margins |
| Type scale | Hero 48–56px · Mentor 20px · Detail 17px · Micro 13px |
| Primary button | 52px · `#F5F5F7` fill · 17px/600 |
| Ghost secondary | 15px · 40% opacity |
| Cards / chat bubbles | **None** |
| Charts on default | **None** |
| Tone | Opinionated mentor · transparent uncertainty · no guarantees |

**Overlay rule:** Dock and Ask FAB remain visible *behind* blur, but inactive. User always knows which room they came from. Closing Ask returns to exact prior tab — no navigation stack.

---

## 1. Mission

**Perplexity for trading** — not ChatGPT inside the app.

One question. One answer. One recommendation. Optional reasoning. Dismiss. Done.

The AI answers as if managing its own money, while stating uncertainty when evidence is mixed. Never implies guaranteed outcomes.

---

## 2. The one question

> **“What if…?”**

Examples:
- Should I buy HAL?
- Should I sell Infosys?
- What happens if Nifty falls 2%?
- Can I afford this trade?
- Should I average down?

Ask absorbs questions users would otherwise take to TradingView, Moneycontrol, or a second opinion — **without becoming a conversation product**.

---

## 3. Explicit rejections (Phase 4)

| Rejected | Why |
|----------|-----|
| Chat bubbles | Chatbot identity |
| Conversation history | Endless scroll; user lives in past questions |
| Multi-turn thread | Violates one-question contract |
| Infinite scroll transcript | Software, not oracle |
| Prompt engineering UI | Builder tool, not trader product |
| AI settings / model picker | Breaks invisible AI principle |
| Embedded Single Stock / Alpha AI page | Research tab, not answer |
| Voice conversation | Trust + context issues |
| Suggested follow-up chips after answer | Sneaks in second turn — forbidden |
| “Ask another” on answer screen | Use **Done** → reopen FAB for new question |

---

## 4. Design process — five concepts

### Concept A — Full Chatbot (ChatGPT clone)

Message list, user/assistant bubbles, typing indicator, persistent thread.

| Pros | Cons |
|------|------|
| Familiar from GPT | **Wrong product category entirely** |
| Supports any depth | User chats instead of deciding |
| | Breaks cohesion with three canvases |

**Verdict: REJECT.**

---

### Concept B — Research Tab (Single Stock embed)

Ask FAB opens existing Single Stock / Alpha AI with search prefilled.

| Pros | Cons |
|------|------|
| Reuses backend reports | 15 sections = user interprets |
| Rich data | Metric grids, charts — dashboard |
| | Not “one answer” |

**Verdict: REJECT.**

---

### Concept C — Command Palette Only (Arc-style)

Input at top, answer as one-line toast or inline strip; no full overlay.

| Pros | Cons |
|------|------|
| Fast | Too thin for “Can I afford this trade?” |
| Minimal chrome | No room for recommendation + reasoning |
| | Doesn't feel Perplexity-grade |

**Verdict: REJECT.** Useful as component, insufficient as Phase 4.

---

### Concept D — Side Drawer Chat

Sliding panel with thread history from right edge.

| Pros | Cons |
|------|------|
| Context preserved | History visible = chat product |
| Stays on canvas | Different silhouette from all tabs |
| | Cramped for mentor answer |

**Verdict: REJECT.**

---

### Concept E — Answer Canvas Overlay ✓

**Recommended.** Full-screen overlay from Ask FAB. **Two states only:** `Idle` (input) and `Answer` (verdict). Same hero → mentor → recommendation → primary → ghost grammar. **Done** dismisses; no memory of thread on screen.

| Pros | Cons |
|------|------|
| Instant product recognition | Requires disciplined one-shot NL |
| Perplexity mental model | No “deep research” path on same screen |
| Reuses verdict color tokens | |
| Zero new interaction vocabulary | |
| Subordinate to Today (doesn't compete) | |

**Verdict: RECOMMEND.**

---

## 5. Comparison matrix

| Criterion | A Chat | B Research | C Palette | D Drawer | **E Answer Canvas** |
|-----------|--------|------------|-----------|----------|---------------------|
| One question / one answer | No | No | Partial | No | **Yes** |
| Not a chatbot | No | Yes | Yes | No | **Yes** |
| Cohesive with Phase 1–3 | No | No | Partial | No | **Yes** |
| Perplexity-fast | Yes | No | Yes | Yes | **Yes** |
| Opinionated answer | Partial | No | Partial | Partial | **Yes** |
| Evidence on demand | Yes | Yes | No | Yes | **Yes** |
| Dismiss and done | No | No | Yes | No | **Yes** |

---

## 6. Recommendation: Answer Canvas

**Official name:** `AnswerCanvas` (Ask overlay)

**Why this wins:** Users already learned one grammar on day one:

```
HERO WORD  →  MENTOR VOICE  →  RECOMMENDATION  →  ONE ACTION  →  [optional ghost depth]
```

Ask is the **same sentence structure** applied to ad-hoc questions. The only new chrome is a text field in `Idle` state and a close control — both standard, not experimental.

---

## 7. Interaction model (frozen)

```
[Any tab] ──tap Ask FAB──► Answer Canvas (Idle)
                              │
                    type + submit (Enter)
                              │
                              ▼
                         Answer state
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
      [ Back to Today ]      Why?            ✕ Close
              │          (bottom sheet)
              ▼
    Overlay dismisses → Today tab (primary) or prior tab (✕)
```

**Approved refinements (locked):**
1. **Ask FAB** remains the only entry point (all tabs).
2. Primary dismiss: **Back to Today** — closes overlay and routes to Today tab.
3. Ghost reasoning: **Why?** (not “Why I'm saying this”) → bottom sheet.
4. **Personalize every answer** — opener e.g. *“If I were managing your portfolio today…”*
5. **Tiny context line** — e.g. *“Based on today's market and your portfolio.”*
6. **Two** suggestion chips on idle (not three).
7. **One question / one answer** — no chat history, conversation, scrolling answer, or follow-up prompts.

**Hard rules:**
1. **One submit per overlay open.** After answer, input is hidden — not disabled — **gone**.
2. **Back to Today** closes overlay and sets dock to Today. **✕** closes overlay and keeps prior tab.
3. **No follow-up field** on answer screen. New question = close → tap Ask again.
4. **Backend may log** for learning; **UI shows no history.**

---

## 8. Layout — Idle state (before question)

Full viewport overlay; backdrop blur 12px on content behind; overlay bg `#0A0A0B` at 96%.

```
┌──────────────────────────────────────── 390px ────────────────────────────────────────┐
│ ✕ Close                                                          (44px tap, top-right) │
├───────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│                         What if…                                                      │
│                    (32px/500, centered micro hero)                                    │
│                                                                                       │
│              ┌─────────────────────────────────────────┐                              │
│              │  Should I buy HAL?                      │  ← text input, 52px height   │
│              └─────────────────────────────────────────┘                              │
│                                                                                       │
│   Suggestions (max 2 ghost chips, horizontal):                                         │
│   [ Can I afford this trade? ]  [ What if Nifty falls 2%? ]                            │
│                                                                                       │
│   (Dock visible but dimmed behind blur — spatial anchor)                              │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

| Element | Spec |
|---------|------|
| Close ✕ | Top-right, 44px target, `#F5F5F7` at 55% |
| Idle hero | `What if…` — 32px/500, centered (not 56px — subordinate to tabs) |
| Input | Full width −32px; 52px height; 14px radius; bg `#1C1C1E`; border `1px #2C2C2E` |
| Placeholder | `Ask anything about your trades…` |
| Submit | Keyboard Enter; optional → arrow in field (not a second primary button) |
| Suggestion chips | Ghost pills, 15px/500, 40% opacity; tap fills input only — does not auto-submit |

**Decision:** No separate “Search” button. Enter submits — Perplexity pattern. Reduces chrome.

---

## 9. Layout — Answer state (after question)

Question text echoed once as **micro context** — not a user chat bubble.

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ ✕ Close                                                                               │
│ You asked: Should I buy HAL?         (13px micro, 45%, truncated)                       │
│ Based on today's market and your portfolio.  (13px context, 35%)                        │
├───────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│                         Wait                          (48px answer word, amber)       │
│                    (6% ambient glow — reuse Today tokens)                             │
│                                                                                       │
│   If I were managing your portfolio today, HAL is       (20px mentor — personalized) │
│   extended; I'd wait for a pullback before risking capital.                           │
│                                                                                       │
│   Don't add HAL today — your book has enough            (17px recommendation)        │
│   defence exposure already.                                                           │
│                                                                                       │
│   ┌─────────────────────────────────────────┐                                         │
│   │           Back to Today                 │  ← Primary — dismiss + Today tab      │
│   └─────────────────────────────────────────┘                                         │
│                                                                                       │
│                      Why?                     (ghost → bottom sheet)                  │
│                                                                                       │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

### Content order (mandatory)

1. **Query echo** (micro) — proves what was understood  
2. **Context line** (tiny) — e.g. “Based on today's market and your portfolio.”  
3. **Answer word** (hero) — pre-attentive verdict  
4. **Personalized answer sentence** (mentor, max ~28 words) — opens with portfolio opener  
5. **One recommendation** (detail, max 1 line)  
6. **Primary: Back to Today**  
7. **Ghost: Why?** → sheet (optional depth)

**Forbidden on default answer view:** Bullet lists, confidence %, charts, compare links, “Full analysis”, watchlist buttons, second question input.

---

## 10. Answer word tokens (reuse Today verdict palette)

| Answer word | Color | Hex | When |
|-------------|-------|-----|------|
| `Wait` | Amber | `#FFC107` | Don't act now |
| `Buy` | Green | `#00E676` | Favorable entry / add |
| `Sell` | Muted red | `#FF6B6B` | Exit / reduce |
| `Reduce` | Amber | `#FFC107` | Trim, don't add |
| `Pass` | Gray | `#A1A1A6` | Skip / not in plan |
| `Afford` | Blue-gray | `#64B5F6` | Sizing / capital questions |
| `Risk` | Soft red | `#FF8A80` | Macro / scenario stress |

**Decision:** Reuse Phase 1 color semantics so users **already know** green vs amber without reading.

For sizing questions (“Can I afford…”), hero may be **`Yes`** / **`Tight`** / **`No`** instead — still 48px, same glow rules.

---

## 11. Example answers (tone reference)

### Should I buy HAL?

| Slot | Copy |
|------|------|
| Word | `Wait` |
| Answer | HAL is extended; I'd wait for a pullback toward ₹4,200 before risking capital. |
| Recommendation | Don't add HAL today — your defence book is full enough. |
| Uncertainty | (in sheet) I'm fairly sure — trend is stretched on daily timeframe. |

### Should I sell Infosys?

| Slot | Copy |
|------|------|
| Word | `Hold` → map to `Wait` token gray |
| Answer | INFY is weak but not broken — selling now locks in a recoverable dip. |
| Recommendation | Hold unless it closes below your stop; trim only if you need cash. |

### What happens if Nifty falls 2%?

| Slot | Copy |
|------|------|
| Word | `Risk` |
| Answer | A 2% drop would hit your IT names hardest — roughly ₹X unrealized pressure. |
| Recommendation | No action required today; watch RELIANCE support before adding. |

### Can I afford this trade?

| Slot | Copy |
|------|------|
| Word | `Tight` or `Yes` |
| Answer | You can afford ₹1,800 risk — that's within your 1.8% daily rule. |
| Recommendation | Size down if you already traded once today. |

### Should I average down?

| Slot | Copy |
|------|------|
| Word | `Pass` |
| Answer | Averaging down isn't in your plan — it turns one mistake into two. |
| Recommendation | Wait for a fresh setup with a defined stop instead. |

**Tone:** First-person mentor (`I'd wait`, `Don't add`). Direct. Never “it depends” without a concluding stance.

---

## 12. Why sheet (optional reasoning)

Identical chrome to Phase 1 Why sheet and Phase 2 depth pattern:

| Property | Value |
|----------|-------|
| Trigger | Ghost `Why?` |
| Sheet bg | `#1C1C1E` |
| Radius | 24px top |
| Content | 3–6 bullets, 17px, 85% opacity |
| Closing line | Uncertainty in prose: “I'm fairly sure about this.” / “Mixed signals — I'd stay cautious.” |

**Not visible by default.** User who trusts the oracle taps Done without ever opening sheet.

---

## 13. Loading state

Between submit and answer:

| Element | Behaviour |
|---------|-----------|
| Input | Hidden |
| Hero | `···` at 48px, pulse 50% opacity (same as Today loading) |
| Ambient | Neutral gray glow |
| Duration target | < 3s perceived; show answer partial if slow |

**No** “AI is thinking” paragraph. **No** streaming token animation (feels chatty). Single crossfade to answer.

---

## 14. Error / empty states

| State | Copy | Primary |
|-------|------|---------|
| Unrecognized symbol | “I couldn't map that to a symbol — try NSE tickers like HAL or INFY.” | Back to Today |
| No broker + portfolio question | “Connect Zerodha first so I can answer against your real book.” | Connect Zerodha |
| Engine timeout | “I need fresher data — try again in a minute.” | Back to Today |
| Off-topic question | “I answer trading decisions — try a what-if about a stock or your risk.” | Back to Today |

Errors use same layout — hero `Pass` gray, one sentence, Back to Today. Never raw stack traces.

---

## 15. Motion

| Moment | Animation | Duration |
|--------|-----------|----------|
| FAB → Overlay | Scale from FAB origin + fade; backdrop blur in | 280ms |
| Idle → Answer | Crossfade; answer word rises 8px | 400ms |
| Sheet open | Spring from bottom (Why sheet token) | 350ms |
| Done → Dismiss | Overlay fades; Back to Today routes dock | 250ms |

Motion matches Phase 1–3 token table. No unique Ask-only animations.

---

## 16. Ask FAB behaviour (unchanged chrome)

| Property | Value |
|----------|-------|
| Label | `Ask` |
| Position | Fixed, above dock, right 16px |
| Size | 56px pill (existing Phase 1–3) |
| On Today / Trades / You | Identical |

Tap opens Answer Canvas overlay. FAB does not change label when overlay open.

---

## 17. Data mapping (presentation only)

| Question type | Backend sources (unchanged engines) |
|---------------|-------------------------------------|
| Symbol buy/sell | `unified_search` + `DecisionArtifact` + pins + `ContextSnapshot` |
| Afford / size | `IntradayPrefs` capital × risk % + open exposure |
| Macro what-if | `ContextSnapshot` sector_strength + portfolio holdings |
| Average down | `mis_trade_advisory` flags + journal mistakes + plan rules |
| Why bullets | `_evidence_summary` + flags + restrictions |

**Rule:** One synthesized `AskAnswer` object mapped to UI slots — never dump raw engine JSON.

```text
AskAnswer {
  query_echo: string
  context_line: string
  answer_word: string
  mentor_line: string       // includes personalized opener
  recommendation: string
  why_bullets: string[3..6]
  uncertainty_note: string  // sheet only
  primary_label: "Back to Today" | "Connect Zerodha"
}
```

---

## 18. Accessibility

- Overlay traps focus; Esc dismisses (= Done).
- `aria-live="polite"` on answer region when transitioning from loading.
- VoiceOver reads: “Answer: Wait. HAL is extended…” in one pass.
- Input labelled “What if question”.

---

## 19. WOW test (Phase 4)

| Question | Answer Canvas |
|----------|---------------|
| Same product in screenshot? | Yes — hero word + mentor + button |
| Perplexity-fast? | Yes — one submit, one screen |
| Not a chatbot? | Yes — no bubbles, no history |
| Opinionated? | Yes — answer word forces stance |
| Evidence on demand? | Yes — Why sheet |
| Invisible AI? | Yes — no settings, no model pick |
| Manages-own-money tone? | Yes — with uncertainty in sheet |
| Dismiss and done? | Yes — Back to Today returns to Today tab |

---

## 20. Relationship to other surfaces

| User need | Right surface | Not Ask |
|-----------|---------------|---------|
| Today's decision | Today | — |
| Execute today's plan | Trades | — |
| Am I becoming better? | You | — |
| Ad-hoc what-if | **Ask** | — |
| Deep 15-section research | — | Single Stock (legacy, not dock) |
| Track record | — | How we're doing (You link) |

**Decision:** Ask **replaces the morning habit** of opening other apps for quick questions. It does **not** replace Today’s verdict.

---

## 21. Implementation (complete)

| Step | Deliverable | Status |
|------|-------------|--------|
| 4a | Overlay shell + Idle input + dismiss | `ui/components/answer_canvas.py` |
| 4b | Answer state + verdict mapping | `build_ask_answer()` |
| 4c | Why? sheet + error paths | popover + connect afford |
| 4d | Two suggestion chips + overlay CSS | `ui/theme.py` |

**Do not modify Phase 1–3 frozen screens.**

---

## 22. Resolved decisions (frozen)

1. **Idle hero:** `What if…`  
2. **Answer hero for sizing:** `Yes` / `Tight` / `No`  
3. **Suggestion chips:** **2** on idle  
4. **Query echo:** Show “You asked: …” + context line  
5. **Primary dismiss:** **Back to Today**  
6. **Ghost reasoning:** **Why?**

---

## 23. Freeze criteria

Phase 4 marked **FROZEN** after spec approval + implementation matches §9 content order + screenshot cohesion test with Phase 1–3.

**Frozen as of:** 2026-07-16

---

*End of Phase 4 design specification.*
