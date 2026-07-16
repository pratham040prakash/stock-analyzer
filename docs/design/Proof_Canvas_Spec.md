# Proof Canvas — Flagship Evidence Experience · Design Specification

**Product:** AI Trading Decision System  
**Capability:** Post-decision visual proof (AI-native charting)  
**Status:** **FROZEN** — implemented 2026-07-16 · architecture permanent  
**Scope:** L2 evidence depth · Phases 1–5 default paths unchanged  
**Rendering:** TradingView Lightweight Charts = invisible engine only (after SVG layer validated)

---

## Product constitution

Proof Canvas is **not** a sixth dock tab. It is evidence depth opened from:

| Origin | Trigger | Primary exit |
|--------|---------|--------------|
| Today | `See the proof` | Back to Today |
| Trades | `See the structure` | Back to Trades |
| Ask | `See the proof` (in Why?) | Back to Ask |
| Trust | `What I saw that day` | Back to Trust |

**Order (non-negotiable):** AI thinks → Decision → Chart explains.

**Question answered:** *"Why is the AI making this recommendation?"*

---

## Frozen principles (do not redesign)

1. SVG annotation layer built **before** TradingView integration.  
2. AI owns every annotation — user never draws or configures.  
3. Human language replaces technical jargon on default view.  
4. Every label answers **Why?** not **What?**  
5. Mentor sentence **above** chart — AI speaks before data.  
6. No toolbars, indicators, timeframes, symbol search, or TV branding.  
7. Visual consistency with Today · Trades · You · Ask · Trust.  
8. If any element competes with AI explanation — remove it.  
9. Optimize for emotional clarity, not analytical completeness.  
10. User leaves understanding the recommendation without becoming a technical analyst.

---

## Banned on default view

Support · Resistance · EMA · RSI · MACD · Fibonacci · Volume · Trendline · indicator menus · drawing tools · raw charting before AI interpretation.

---

## Annotation language (frozen)

| Internal | User sees |
|----------|-----------|
| `support_zone` | Previous buyers defended here. |
| `resistance_zone` | Sellers consistently appeared here. |
| `danger_zone` | Do not buy here — price is extended. |
| `demand_zone` | Buyers stepped in aggressively here. |
| `invalidation` | If price closes below here, the idea is wrong. |
| `expected_path` | This is where buyers regain control. |
| `uncertainty` | Mixed signals — no clear control yet. |

---

## State variants (mockup required)

| State | Visual treatment |
|-------|------------------|
| **Trade** | Green path · entry/stop/target · risk/reward corridors |
| **Wait** | Red/gray danger zone · blurred candles · no entry |
| **Pause** | Amber uncertainty band · loss-context shading |
| **Rest** | Chart 12% opacity · copy only |
| **Ask Proof** | Query echo + answer-scoped zones |
| **Trust Fossil** | Frozen snapshot · miss-day context |

---

## Mockups (signed off)

`docs/design/mockups/proof-canvas.html` — six states approved before implementation.

## Implementation (complete)

| Module | Role |
|--------|------|
| `ui/components/proof_models.py` | `StructureProof` · `ZoneAnnotation` · `PriceMarkers` |
| `ui/components/proof_mapper.py` | `build_structure_proof()` — presentation mapping |
| `ui/components/proof_svg.py` | SVG annotation renderer (default view) |
| `ui/components/proof_lwc.py` | Lightweight Charts ghost embed |
| `ui/components/proof_canvas.py` | Overlay shell · routing · session state |
| `tests/test_proof_canvas.py` | Mapper + SVG tests |

### Entry points

| Surface | Trigger |
|---------|---------|
| Today | `See the proof` |
| Trades | `See the structure` |
| Ask | `See the proof` (in Why?) |
| Trust | `What I saw that day` (when miss exists) |

**Architecture frozen.** Future work: AI reasoning · live intelligence · motion polish — not UX redesign.

---

## Future innovation (not UX architecture)

AI reasoning quality · live market intelligence · broker execution · portfolio learning · motion craftsmanship.

**Architecture freezes permanently after screenshot approval.**

---

*End of Proof Canvas specification (pending mockup sign-off).*
