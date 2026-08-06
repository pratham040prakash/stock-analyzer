# APEX-017 — V3-103 Portfolio Review Architecture (FROZEN)

**Document ID:** APEX-017  
**Version:** 1.0  
**Status:** APPROVED — FROZEN (V3-103)  
**Date:** 2026-08-06  
**Milestone:** V3-103 Portfolio Review  
**Baseline:** V3-102 @ `c6629cf` · v2.0.0 GA (unchanged)  
**References:** [V3_PORTFOLIO_REVIEW.md](../product/V3_PORTFOLIO_REVIEW.md), [APEX-016](./APEX-016_V3-102_Holdings_Experience.md), [product/CHANGELOG.md](../../product/CHANGELOG.md)

---

## 1. Frozen data flow (V3-103 additive)

```
BrokerSnapshot + ZerodhaImportResult + IntradayPrefs + PortfolioSection
        ↓
assemble_portfolio_overview()              ← use-case layer (health SSOT from V3-101)
        ↓
PortfolioOverviewViewModel                 ← attention_items, holdings_rows, allocation, depth
        ↓
portfolio_review_from_view_model()         ← projection + theme grouping only
        ↓
PortfolioReviewContract
        ↓
portfolio_review_experience.py             ← render-only UI
        ↓
Shared Theme (APEX_PARTNER_EXPERIENCE_CSS)
        ↓
Streamlit render
```

**V2 frozen pipeline unchanged.** V3-101 Overview and V3-102 Holdings flows unchanged.

---

## 2. Presentation Single Source of Truth

| Concern | Owner | Notes |
|---------|-------|-------|
| Health evaluation | `portfolio_overview_assembly.py` | Same `_attention_items` as V3-101; no new rules in Review |
| Theme grouping | `portfolio_review_ui.py` | `_build_themes()` — Sector Concentration, Single Position, Policy Drift, Cash Allocation |
| View model | `portfolio_overview_models.py` | Unchanged DTO; Review reuses existing VM |
| Contract projection | `portfolio_review_ui.py` | Formatting + theme taxonomy only |
| Review render | `portfolio_review_experience.py` | Render-only; mark reviewed = session state |
| Theme Understand | `understand_popover.py` | `theme_understand_contract()` |
| Research handoff | `portfolio_command_center._research_handoff` | Navigation only — `request_nav_tab` |
| Shared CSS | `APEX_PARTNER_EXPERIENCE_CSS` | `.apex-portfolio-review` in bundle |
| Page entry | `ui/pages/zerodha.py` | Review sub-tab → `render_portfolio_review_experience` |

---

## 3. Screen relationship (frozen — Portfolio pillar)

| Tab | Question | Owner |
|-----|----------|-------|
| Overview (V3-101) | Is it healthy? | Health Hero, allocation, attention |
| Review (V3-103) | Why, and what next? | Theme-first review queue or healthy reassurance |
| Holdings (V3-102) | What exactly do I own? | Inventory table / cards |

**Rule:** Review owns explanation and guided review workflow. No duplicate Health Hero. No full holdings table on Review. No analyzer imports in render layer.

---

## 4. Theme queue model (frozen)

- Max 3 themes projected from existing VM fields (`attention_items`, `holdings_rows`, `allocation`)
- Theme-first: portfolio problem owns affected holdings
- Healthy state: reassurance checklist, not action queue
- `Mark reviewed`: session-only (`portfolio_review_reviewed_theme_keys`)

---

## 5. Regression gate (V3-103)

| Suite | Count |
|-------|-------|
| `tests/test_v3_103_portfolio_review.py` | 7 |
| `tests/test_v3_102_holdings_experience.py` | 9 |
| `tests/test_v3_101_portfolio_command_center.py` | 8 |
| `tests/test_v2_rc001_render_integration.py` | 5 |
| `tests/test_apex_012_phase0.TestUIGuardrails` | 3 |
| **V3 Phase 1 gate total** | **32** |

---

## 6. Out of scope (frozen for V3-103)

- No new health rules or analyzer scoring in UI
- No separate attention model
- No persistence of reviewed state beyond session
- No trade execution or buy/sell CTAs
- Tax Review theme — future extensibility slot only

---

*Frozen at Engineering Review approval — 2026-08-06.*
