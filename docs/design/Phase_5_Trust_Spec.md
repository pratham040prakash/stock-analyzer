# Phase 5 — Trust Canvas · Design Specification

**Product:** AI Trading Decision System  
**Surface:** Trust — depth canvas from You tab  
**Status:** **FROZEN** — approved with mentor refinements (2026-07-16)  
**Scope:** Presentation + routing only · backend unchanged  
**Companions:** Today · Trades · You · Ask — **do not modify**

---

## Approved refinements (frozen)

| Change | Decision |
|--------|----------|
| Micro label | **`I've been reviewing every decision.`** — warm, not mechanical |
| Trust words | **Honest · Learning · Earned** only — relationship, not performance |
| Banned heroes | `Winning` · `Accurate` · `%` · `Correct` |
| Miss tone | Acknowledge → what changed. No excuses. |
| Forward line | Always optimistic — *“I'll continue checking every recommendation against reality. That's how I improve.”* |
| Thin history | Honest copy — no fabricated confidence |
| Entry | You ghost **How we're doing** → Trust Canvas (not legacy Track Record) |
| Exit | Primary **Back to You** |

**Content order:** Micro → Trust word → Last week → This week → Miss (if any) → Forward → Primary → Ghost row.

---

## 0. Product cohesion charter

| Surface | Question | Hero focal |
|---------|----------|------------|
| **Today** | What should I do? | Stance — `Wait` · `Trade` · `Pause` |
| **Trades** | How do I execute? | Symbol |
| **You** | Am I becoming a better trader? | State — `Growing` · `Steady` · `Focused` |
| **Ask** | What about this situation? | Answer word |
| **Trust** | Why should I continue trusting this AI? | **Honest · Learning · Earned** |

| Dimension | Rule |
|-----------|------|
| Canvas | `#0A0A0B`; 430px; 16px margins |
| Typography | Hero 48px · Mentor 20px · Detail 17px · Micro 13px |
| Primary | 52px · `#F5F5F7` |
| Ghost | 15px · 40% opacity |
| Charts / % / tiles | **None** on default path |

---

## 1. Mission

> **“Why should I continue trusting this AI?”**

Trust is earned through **honesty, memory, and improvement** — not hit rates.

End belief: *“This AI gets better over time.”*

---

## 2. Explicit rejections

No charts · no analytics walls · no hit-rate % · no calibration · no metric tiles · no timeline scroll · no Track Record on partner path.

---

## 3. Recommendation: Trust Canvas (Concept E)

One story. Two time windows (last week · this week). One visible miss. One forward line. Ghost depth optional.

---

## 4. Interaction model (frozen)

```
You ──How we're doing──► Trust Canvas
                              │
                    Back to You / Connect Zerodha
                              │
              What we got wrong · How I learn (popovers)
```

- No new dock tab  
- No scroll on default view  
- Dock + Ask FAB unchanged  

---

## 5. Trust word mapping

| Word | When |
|------|------|
| `Honest` | Thin history or default relationship stance |
| `Learning` | Recent miss logged |
| `Earned` | Strong wait-save week + disciplined trades, no recent miss |

Priority: **Honest → Learning → Earned** (relationship over performance).

---

## 6. Implementation (complete)

| File | Role |
|------|------|
| `ui/components/trust_canvas.py` | `build_trust_view()` · `render_trust_canvas()` |
| `ui/components/partner_shell.py` | `PARTNER_DEPTH_KEY` · `is_trust_depth()` |
| `ui/components/reflection_canvas.py` | Routes ghost to Trust |
| `ui/components/home_dashboard.py` | You + trust depth routing |
| `ui/theme.py` | `.trust-canvas-root` styles |
| `tests/test_trust_canvas.py` | Presentation mapping tests |

---

## 7. Final product constitution

The five core surfaces are permanent:

1. **Today**  
2. **Trades**  
3. **You**  
4. **Ask**  
5. **Trust**

Future work: AI quality · TradingView intelligence · broker automation · polish · motion · performance — **not UX architecture**.

**Frozen as of:** 2026-07-16

---

*End of Phase 5 design specification.*
