# APEX-016 — V3-102 Holdings Experience Architecture (FROZEN)

**Document ID:** APEX-016  
**Version:** 1.0  
**Status:** APPROVED — FROZEN (V3-102)  
**Date:** 2026-08-06  
**Milestone:** V3-102 Holdings Experience  
**Baseline:** V3-101 @ `2df8da1` · v2.0.0 GA (unchanged)  
**References:** [V3_HOLDINGS_EXPERIENCE.md](../product/V3_HOLDINGS_EXPERIENCE.md), [APEX-015](./APEX-015_V3-101_Portfolio_Command_Center.md), [product/CHANGELOG.md](../../product/CHANGELOG.md)

---

## 1. Frozen data flow (V3-102 additive)

```
BrokerSnapshot + ZerodhaImportResult + IntradayPrefs + PortfolioSection
        ↓
assemble_portfolio_overview()              ← use-case layer (health SSOT from V3-101)
        ↓
PortfolioOverviewViewModel                 ← + holdings_rows, watchlist_rows, holdings_context
        ↓
holdings_experience_from_view_model()      ← projection only
        ↓
HoldingsExperienceContract
        ↓
holdings_experience.py                     ← render-only UI
        ↓
Shared Theme (APEX_PARTNER_EXPERIENCE_CSS)
        ↓
Streamlit render
```

**V2 frozen pipeline unchanged.** V3-101 Overview flow unchanged.

---

## 2. Presentation Single Source of Truth

| Concern | Owner | Notes |
|---------|-------|-------|
| Health evaluation | `portfolio_overview_assembly.py` | Same `_attention_items` as V3-101; row chips map attention symbols |
| Holdings rows | `portfolio_overview_assembly.py` | `_holdings_rows`, `_watchlist_rows`, `_holdings_context` |
| View model | `portfolio_overview_models.py` | Extended `PortfolioOverviewViewModel` |
| Contract projection | `holdings_experience_ui.py` | Formatting only |
| Holdings render | `holdings_experience.py` | Render-only; filter/sort on contract rows |
| Row Understand | `understand_popover.py` | `holdings_row_understand_contract()` |
| Research handoff | `portfolio_command_center._research_handoff` | Navigation only — `request_nav_tab` |
| Shared CSS | `APEX_PARTNER_EXPERIENCE_CSS` | Holdings table + card CSS in bundle |
| Page entry | `ui/pages/zerodha.py` | Holdings sub-tab → `render_holdings_surface` |

---

## 3. Screen relationship (frozen)

| Tab | Question | Owner |
|-----|----------|-------|
| Overview (V3-101) | Is it healthy? | Health Hero, allocation, attention |
| Holdings (V3-102) | What exactly do I own? | Inventory table / cards |

**Rule:** No health hero on Holdings. No duplicate allocation dashboard.

---

## 4. Regression gate (V3-102)

| Suite | Count |
|-------|-------|
| `tests/test_v3_102_holdings_experience.py` | 9 |
| `tests/test_v3_101_portfolio_command_center.py` | 8 |
| `tests/test_v2_rc001_render_integration.py` | 5 |
| `tests/test_apex_012_phase0.TestUIGuardrails` | 3 |
| **V3 Phase 1 gate total** | **25** |

---

## 5. Out of scope (frozen for V3-102)

- No separate health rules in Holdings UI
- No analyzer scoring imports in render layer
- No inline analyze gate or legacy CRUD on Holdings tab
- No trade execution or recommendation columns in table
- Sector filter / column picker — future milestones

---

*Frozen at Engineering Review approval — 2026-08-06.*
