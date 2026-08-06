# APEX-014 — V2 Architecture, Journeys, and Release Record

**Document ID:** APEX-014  
**Version:** 1.0  
**Status:** APPROVED — FROZEN (v2.0.0-rc1)  
**Date:** 2026-08-06  
**Baseline commit:** `v2.0.0-rc1` (RC-001)  
**References:** [APEX-000](./APEX-000_Company_Constitution.md), [APEX-004](./APEX-004_Experience_Operating_System.md), [APEX-005](./APEX-005_System_Architecture_Blueprint.md), [product/CHANGELOG.md](../../product/CHANGELOG.md)

---

## 1. APEX V2 Architecture

### 1.1 Frozen data flow

```
DecisionContextBundle
        ↓
DecisionArtifact
        ↓
MorningBriefViewModel
        ↓
Presentation Contracts
  • RecommendationContract
  • InvestmentThesisContract
  • BusinessHealthContract
  • RiskMonitorContract
        ↓
Presentation Components
  • Home Command Center (today_brief_experience)
  • Review Workspace (plan_canvas + investment_hero_experience)
  • Review Depth compositor (decision_depth_panel)
        ↓
Shared Theme System (ui/theme.py)
        ↓
Render-only UI (Streamlit + HTML/CSS)
```

### 1.2 Presentation Single Source of Truth

| Concern | Owner | Notes |
|---------|-------|-------|
| Contract projection | `ui/components/morning_brief_ui.py` | No verdict assignment in UI |
| Card projection | `ui/components/decision_card.py` | Hero intel gating |
| Review Depth (APS-003–006) | `ui/components/decision_depth_panel.py` | **Single compositor** for Today popover and Review page |
| Shared CSS | `APEX_PARTNER_EXPERIENCE_CSS` in `ui/theme.py` | Pre-built bundle; no runtime concatenation |
| Page shell | `ui/components/home_dashboard.py` | Dock routing: Today / Trades / You |

### 1.3 RC-001 hardening (Review Depth unification)

The Today **Help me understand** popover calls `render_decision_depth_panel()` with `include_section_header=False`. The Review Workspace calls the same compositor with the default section header. APS expander logic exists in one place only.

---

## 2. User Journeys

### 2.1 Today — Home Command Center (V2-001)

1. User opens **Today** dock tab.
2. **Verdict Hero** answers: what matters, recommendation badge, why, confidence, freshness.
3. **Action Row**: primary CTA + **Help me understand** (popover gateway).
4. **Status Strip**: portfolio, today's action, review time, connection, freshness.
5. **Supporting context** below fold: priority review, market, connection, learning.

Progressive disclosure: APS-003–006 depth is **not** inline on Brief; reachable via popover → Review Depth compositor.

### 2.2 Understand popover

1. User taps **Help me understand**.
2. Contract explanation popover body (`_render_contract_popover`).
3. Same **Review Depth** expanders as Review page (Recommendation explanation, Investment thesis, Business health, Risk monitor).

### 2.3 Review Workspace (V2-002)

1. User opens **Trades** dock tab (plan canvas).
2. **Investment Review Hero** (APS-002).
3. **Execution Plan** details when a plan exists.
4. **Review Depth** section (APS-003–006 via `decision_depth_panel`).
5. Primary actions: Open in Kite / Not today.

---

## 3. V2 Milestones

| ID | Name | Commit | Summary |
|----|------|--------|---------|
| V2-001 | Home Command Center | (in `aa634cb`) | Brief → command center; APS depth via popover |
| V2-002 | Review Workspace | `aa634cb598390e25fedefdcb1bf7fbdd41b40573` | Hero → Plan → Review Depth hierarchy |
| V2-003 | Visual Polish | `62df0e98ba1209bfebff8c4a2fab46ac6554207a` | `APEX_V2_VISUAL_POLISH_CSS`, shared tokens |
| V2-004 | Performance & Accessibility | `0020ed8e94fce6c5678a86106979c5f9ab6ff083` | CSS bundle, a11y basics, render perf hints |
| RC-001 | Release Candidate Hardening | (this milestone) | Review Depth SSOT, render tests, docs, triage |

**Regression gate:** 49 APS/V2 tests (`test_aps_001` … `test_home_dashboard`).

---

## 4. Frozen Contracts

Presentation contracts in `ui/components/morning_brief_ui.py` are **frozen** for V2:

- `RecommendationContract`
- `InvestmentThesisContract`
- `BusinessHealthContract`
- `RiskMonitorContract`

V2 milestones did not modify contract shapes or recommendation logic. UI consumes contracts via `build_*_view` + `render_*` APS components.

---

## 5. Engineering Principles (V2)

1. **Domain owns business logic** — verdicts and recommendations originate in analyzer/use_cases.
2. **UI is render-only** — presentation maps view models to HTML/Streamlit; no new decision rules in UI.
3. **Presentation Contracts** — stable section order and progressive disclosure fields.
4. **Progressive Disclosure** — answer first; depth on demand (popover / Review Depth).
5. **Presentation Single Source of Truth** — one Review Depth compositor; one shared CSS bundle.
6. **Shared Theme System** — design tokens and polish in `ui/theme.py`.
7. **No duplicated renderers** — APS-003–006 render functions reused, not copied.
8. **No duplicated shared CSS** — `APEX_PARTNER_EXPERIENCE_CSS` pre-built at import.
9. **No analyzer imports in UI** (goal) — presentation files may import domain **types** and bundle assembly at boundaries; no verdict assignment in UI.
10. **One responsibility per screen** — Today = daily verdict; Trades = execution review.

---

## 6. Known Limitations

| Area | Limitation |
|------|------------|
| Session ribbon | `hero_session_ribbon_html()` exists but is not wired on Today surface |
| Intelligence builder | Today still calls `build_today_command_center` from quarantined `today_intelligence.py` |
| Automated a11y | WCAG-oriented CSS/ARIA added; no axe/pa11y CI gate yet |
| Streamlit e2e | No browser/AppTest coverage for dock routing or popover interaction |
| Full test suite | 681 tests include pre-existing failures outside the 49-test V2 gate |
| Legacy CSS | Phase 1 `VERDICT_CANVAS_CSS` remains bundled for dock/overlays compatibility |
| Cross-imports | `investment_hero_experience` imports private helpers from `today_brief_experience` (TODO: shared module) |
| Documentation | ETS-003a Morning Brief spec remains DRAFT; V2 implementation diverges on hierarchy details |

---

## 7. Traceability

| Surface | Primary module | Tests |
|---------|----------------|-------|
| Home Command Center | `today_brief_experience.py` | `test_aps_001`, `test_v2_rc001_render_integration` |
| Understand popover | `today_brief_experience._render_understand_popover` | `test_v2_rc001_render_integration` |
| Review Workspace | `plan_canvas.py` | `test_plan_canvas`, `test_v2_rc001_render_integration` |
| Review Depth SSOT | `decision_depth_panel.py` | `test_aps_003`–`006`, RC-001 integration tests |
| Theme / CSS | `ui/theme.py` | Static + visual manual QA |

---

## 8. Acceptance (RC-001)

- [x] One Review Depth implementation (`decision_depth_panel`)
- [x] Today popover reuses compositor
- [x] Render integration tests added
- [x] `docs/apex` updated with V2 record
- [x] Full suite triaged (see engineering triage report in RC-001 output)
