# APEX-018 — V3-201 Research Workbench Architecture (FROZEN)

**Document ID:** APEX-018  
**Version:** 1.0  
**Status:** APPROVED — FROZEN (V3-201)  
**Date:** 2026-08-06  
**Milestone:** V3-201 Research Workbench  
**Baseline:** V3-103 @ `197ef8a` · v2.0.0 GA (unchanged)  
**References:** [V3_RESEARCH_WORKSPACE.md](../product/V3_RESEARCH_WORKSPACE.md), [APEX-017](./APEX-017_V3-103_Portfolio_Review.md), [product/CHANGELOG.md](../../product/CHANGELOG.md)

---

## 1. Frozen data flow (V3-201 additive)

```
DecisionContextBundle (cached) + BrokerSnapshot + Portfolio inputs
        ↓
MorningBriefViewModel + DecisionArtifact          ← frozen pipeline (unchanged)
        ↓
recommendation_contract_from_brief()               ← existing presentation SSOT
investment_thesis_contract_from_brief()
business_health_contract_from_brief()
risk_monitor_contract_from_brief()
        ↓
research_workspace_from_view_model()             ← projection only (7 research questions)
        ↓
ResearchWorkspaceContract
        ↓
research_workspace_experience.py                 ← render-only UI
        ↓
Shared Theme (APEX_PARTNER_EXPERIENCE_CSS)
        ↓
Streamlit render (Single Stock tab → Workbench)
```

**V2 frozen pipeline unchanged.** Portfolio pillar (V3-101–103) unchanged.

---

## 2. Presentation Single Source of Truth

| Concern | Owner | Notes |
|---------|-------|-------|
| Health / conviction / recommendation | `morning_brief_ui.py` + frozen bundle | No new analyzer rules |
| Portfolio context chip | `research_workspace_ui.py` | Read-only slice from `assemble_portfolio_overview()` |
| Question projection | `research_workspace_ui.py` | 7 research questions → existing contracts |
| Workbench render | `research_workspace_experience.py` | Render-only; no scoring imports |
| Understand | `understand_popover.py` | `research_question_understand_contract()` |
| Proof overlay | `proof_state.open_proof_overlay` | Reuses `DecisionArtifact` evidence packet |
| Investment Decision | Session state only | Watch · Hold · Accumulate Later · Avoid |
| Research handoff inbound | `_research_handoff()` | Navigation + back context |
| Shared CSS | `APEX_PARTNER_EXPERIENCE_CSS` | `.apex-research-workbench` in bundle |
| Page entry | `ui/pages/single_stock.py` | Research › Workbench |

---

## 3. Screen relationship (frozen — Research pillar)

| Surface | Question | Owner |
|---------|----------|-------|
| **Workbench** (V3-201) | Should I invest in this company? | 7-question research workflow |
| **Home** (V2) | What should I do today? | Daily verdict — linked, not duplicated |
| **Portfolio** (V3-101–103) | What do I own / why review? | Handoff source + context chip |
| **Alpha AI Reports** | Full institutional report | Optional L5 depth |

**Rule:** Research explains and builds conviction; it does **not** issue Home daily verdict or trade orders.

---

## 4. Research question model (frozen)

| # | Research question | Contract source |
|---|-------------------|-----------------|
| 1 | What does this business do? | `BusinessHealthContract` |
| 2 | What evidence supports investing? | `RecommendationContract.evidence` + labeled `EvidenceSection` |
| 3 | What could invalidate the thesis? | `InvestmentThesisContract` + `what_could_change` |
| 4 | How strong is my conviction? | `RecommendationContract.why` + decision confidence |
| 5 | Is valuation attractive? | Valuation slice (projection from recommendation / brief) |
| 6 | What are the major risks? | `RiskMonitorContract` |
| 7 | What investment decision have I reached? | User Investment Decision + disposition (session) |

---

## 5. Regression gate (V3-201)

| Suite | Count |
|-------|-------|
| `tests/test_v3_201_research_workspace.py` | 11 |
| `tests/test_v3_103_portfolio_review.py` | 7 |
| `tests/test_v3_102_holdings_experience.py` | 9 |
| `tests/test_v3_101_portfolio_command_center.py` | 8 |
| `tests/test_v2_rc001_render_integration.py` | 5 |
| `tests/test_apex_012_phase0.TestUIGuardrails` | 3 |
| **V3 Phase 1–2 gate total** | **43** |

---

## 6. Out of scope (frozen for V3-201)

- No analyzer or decision-engine changes
- No new evidence model for Proof overlay
- Investment Decision does not mutate Home or portfolio health
- Journal receipt persistence deferred to V3-202+
- Legacy Single Stock analyze flow removed from primary path

---

*Frozen at Engineering Review approval — 2026-08-06.*
