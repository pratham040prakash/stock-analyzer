# APEX-015 — V3-101 Portfolio Command Center Architecture (FROZEN)

**Document ID:** APEX-015  
**Version:** 1.0  
**Status:** APPROVED — FROZEN (V3-101)  
**Date:** 2026-08-06  
**Milestone:** V3-101 Portfolio Command Center  
**Baseline:** v2.0.0 GA (unchanged)  
**References:** [V3_PORTFOLIO_COMMAND_CENTER.md](../product/V3_PORTFOLIO_COMMAND_CENTER.md), [APEX-014](./APEX-014_V2_Architecture_and_Release.md), [product/CHANGELOG.md](../../product/CHANGELOG.md)

---

## 1. Frozen data flow (V3-101 additive)

```
BrokerSnapshot + ZerodhaImportResult + IntradayPrefs + PortfolioSection
        ↓
assemble_portfolio_overview()          ← use-case layer (health evaluation)
        ↓
PortfolioOverviewViewModel
        ↓
portfolio_overview_from_view_model()     ← projection only
        ↓
PortfolioOverviewContract
        ↓
portfolio_command_center.py              ← render-only UI
        ↓
Shared Theme (APEX_PARTNER_EXPERIENCE_CSS)
        ↓
Streamlit render
```

**V2 frozen pipeline unchanged:** `DecisionContextBundle → DecisionArtifact → MorningBriefViewModel` is not modified.

---

## 2. Presentation Single Source of Truth

| Concern | Owner | Notes |
|---------|-------|-------|
| Health evaluation | `analyzer/use_cases/portfolio_overview_assembly.py` | Concentration, attention, badge, CTA |
| View model | `analyzer/use_cases/portfolio_overview_models.py` | Authoritative DTO |
| Contract projection | `ui/components/portfolio_overview_ui.py` | Formatting only |
| Command Center render | `ui/components/portfolio_command_center.py` | Render-only |
| Understand UX | `ui/components/understand_popover.py` | Shared Home + Portfolio |
| Review Depth (V2) | `ui/components/decision_depth_panel.py` | Home extra_body only |
| Shared CSS | `APEX_PARTNER_EXPERIENCE_CSS` | Portfolio CSS in bundle |
| Page entry | `ui/pages/zerodha.py` | Overview / Holdings sub-nav |

---

## 3. Understand framework (shared)

| Surface | Contract source | Depth extension |
|---------|-----------------|-----------------|
| Home Command Center | `understand_contract_from_recommendation()` | `render_decision_depth_panel` via `extra_body` |
| Portfolio Command Center | `portfolio_understand_contract()` | None (section-based depth) |
| Investments hero (V2) | `_render_contract_popover` → shared renderer | None |

**Rule:** One `render_understand_popover()` — no duplicate popover implementations.

---

## 4. Regression gate (V3-101)

| Suite | Count |
|-------|-------|
| `tests/test_v3_101_portfolio_command_center.py` | 8 |
| `tests/test_v2_rc001_render_integration.py` | 5 |
| `tests/test_apex_012_phase0.TestUIGuardrails` | 3 |
| **V3-101 gate total** | **16** |

---

## 5. Out of scope (frozen for V3-101)

- No changes to decision engine or recommendation logic
- No 5-page primary nav (Holdings sub-tab only)
- Positions / Wealth / Doctor tabs — placeholders only
- No analyzer scoring module changes

---

## 6. Revision policy

Changes to health evaluation require use-case layer revision. Changes to render contracts require presentation layer revision. No business logic in `portfolio_command_center.py` or `portfolio_overview_ui.py` assembly paths.
