# APEX-012 — Single Truth Migration

**Status:** Phase 0 IMPLEMENTED — awaiting CTO review before Phase 1  
**Priority:** P0 (Strategic)  
**Owner:** Principal Engineer  
**Last updated:** 2026-08-05

---

## Mission

Achieve **One Decision · One Evidence · One Trust · One Story** by making `MorningBriefViewModel` the sole daily contract and eliminating parallel user-facing verdict paths.

Design approved. Phase 0 implements **guardrails only** — no migration, no deletion.

---

## CTO Amendments (binding)

### Amendment 1 — Legacy lifecycle

```
ACTIVE → QUARANTINED → DORMANT → (2 weeks Founder dogfood) → DELETE
```

No production code may skip a stage.

### Amendment 2 — Projection hierarchy

| Tier | Surfaces | Rules |
|------|----------|-------|
| **A — Decision** | Today, Trades, Ask | Must consume `MorningBriefViewModel`; never compute investment reasoning; never override `DecisionArtifact` |
| **B — Reflective** | Proof, Trust, Reflection, Research | May enrich/explain/visualize; must **never contradict** Today |

---

## Phase 0 deliverables (this sprint)

| Item | Location |
|------|----------|
| Lifecycle registry | `analyzer/architecture/legacy_lifecycle.py` |
| Architecture guard tests | `tests/test_apex_012_phase0.py` |
| Lifecycle markers | `# APEX-012-LIFECYCLE: {STATE}` in registered modules |
| This document | `docs/apex/APEX-012_Single_Truth_Migration.md` |

---

## Legacy module lifecycle registry

| Module | State | Owner | Replacement | Removal criteria |
|--------|-------|-------|-------------|------------------|
| `analyzer/decision_engine/engine.py` | **ACTIVE** | Decision Engine | N/A | Never |
| `analyzer/evidence_engine/engine.py` | **ACTIVE** | Evidence Engine | N/A | Never |
| `analyzer/use_cases/morning_brief_assembly.py` | **ACTIVE** | Morning Brief | N/A | Never |
| `analyzer/use_cases/morning_brief_models.py` | **ACTIVE** | Morning Brief | N/A | Never |
| `ui/components/morning_brief_ui.py` | **ACTIVE** | Projection | N/A | Never |
| `ui/components/decision_card.py` | **ACTIVE** | Projection | N/A | Never |
| `ui/components/home_dashboard.py` | **ACTIVE** | Today | N/A | Never |
| `ui/components/plan_canvas.py` | **ACTIVE** | Trades | Phase 3 brief-only inputs | Never |
| `ui/components/answer_canvas.py` | **ACTIVE** | Ask | Phase 3 brief-only inputs | Never |
| `ui/components/proof_mapper.py` | **ACTIVE** | Proof | N/A | Never |
| `ui/components/today_intelligence.py` | **QUARANTINED** | Duplicate intel | MBVM projection (Phase 2) | 2 wk dogfood after DORMANT |
| `ui/components/investment_os_ui.py` | **QUARANTINED** | OS tile | Today hero | 2 wk dogfood after DORMANT |
| `ui/components/mis_trade_advisory.py` (UI) | **QUARANTINED** | MIS strip | brief.risk/trust | 2 wk dogfood after DORMANT |
| `analyzer/investment_os.py` | **QUARANTINED** | Legacy input | Assembly input only | 2 wk dogfood after DORMANT |
| `ui/components/trust_canvas.py` | **QUARANTINED** | Trust depth | brief.trust + journal (Phase 4) | 2 wk dogfood after DORMANT |
| `ui/components/reflection_canvas.py` | **QUARANTINED** | Reflection | brief.meta (Phase 4) | 2 wk dogfood after DORMANT |
| Research pages (`alpha_ai`, `daily_advisor`, etc.) | **QUARANTINED** | Research | Labeled; must not override Today | 2 wk dogfood after DORMANT |
| `analyzer/morning_briefing.py` | **DORMANT** | CLI legacy | `build_morning_brief` | 2 wk dogfood after DORMANT |
| `scripts/morning_briefing.py` | **DORMANT** | CLI wrapper | Same | 2 wk dogfood after DORMANT |
| `ui/components/morning_cockpit.py` | **DORMANT** | Old dashboard | Today shell | 2 wk dogfood after DORMANT |

Full machine-readable registry: `LEGACY_MODULE_REGISTRY` in `analyzer/architecture/legacy_lifecycle.py`.

**Note:** `EvidenceEngine.recommend_from_packet` is tracked as duplicate verdict path — QUARANTINED logically; removal in Phase 4.

---

## Architecture guards (Phase 0)

| Guard | Invariant |
|-------|-----------|
| `TestLegacyLifecycleRegistry` | Registered modules contain `# APEX-012-LIFECYCLE:` marker |
| `TestDecisionEngineOwnership` | `DecisionVerdict` assignment only in `decision_engine` + `use_cases` |
| `TestEvidenceEngineOwnership` | UI must not import/call Evidence Engine builders |
| `TestMorningBriefViewModelContract` | Assembly + projection signatures use MBVM |
| `TestTierAProjectionGuards` | Tier A: no DE runtime imports; no opportunity ranking functions |
| `TestUIGuardrails` | `build_mis_trade_advisory` quarantined to data-loader allowlist |
| `TestProjectionDeterminism` | Same MBVM → same verdict/reason/symbol/confidence on Today/Trades/Ask/Proof |
| `TestQuarantinedModuleIsolation` | `today_intelligence` must not spread beyond `home_dashboard` |

---

## Phase 1 — Hero Opportunity intel (IMPLEMENTED)

**Status:** Awaiting CTO review before Phase 2  
**Slice:** One runtime migration only — hero **Opportunity** block on Today.

| Before | After |
|--------|-------|
| `build_today_command_center` → `_pick_best` / `_build_opportunity_views` | `project_opportunity_intel_html(card)` from `MorningBriefViewModel` |
| Duplicate symbol ranking could contradict brief | Hero symbol always matches `brief.opportunity` |

**Unchanged (still QUARANTINED):** `do_next`, `risk`, below-fold intel, `build_today_command_center`, legacy actions.

| Guard | Location |
|-------|----------|
| `TestHeroOpportunityFromBrief` | `tests/test_apex_012_phase1.py` |
| `TestPhase1Wiring` | `tests/test_apex_012_phase1.py` |

---

## Phase 2a — Review Setup navigation (IMPLEMENTED)

**Status:** Awaiting CTO review before Phase 2b  
**Slice:** "Review setup" action uses `card.best_opportunity.symbol`, not `center.best_ticker`.

| Before | After |
|--------|-------|
| `center.best_ticker` from `_pick_best` | `hero_review_setup_symbol(card)` → `review_symbol` param |

**Navigation determinism:** When hero displays RELIANCE, Review Setup navigates to RELIANCE.

| Guard | Location |
|-------|----------|
| `TestReviewSetupNavSymbol` | `tests/test_apex_012_phase2a.py` |
| `TestReviewSetupNavigation` | `tests/test_apex_012_phase2a.py` |

---

## Future phases (not implemented)

| Phase | Goal |
|-------|------|
| **2b** | Hero Risk → `brief.risk.warnings` |
| **2c** | Hero Do Next → canonical brief line |
| **3** | Below-fold market / portfolio / next_watch → MBVM |
| **4** | Trust / Reflection brief-backed; delete dormant |

---

## Success criteria (migration complete)

- [ ] `MorningBriefViewModel` is the only Today contract
- [ ] Decision Engine is the only verdict owner
- [ ] Evidence Engine is the only evidence owner
- [ ] No UI computes investment reasoning
- [ ] No duplicate opportunity generation
- [ ] No parallel coach messages
- [ ] No conflicting recommendations
- [ ] Every partner surface tells the same story

Phase 0 guards encode these as testable invariants; full completion requires Phases 1–4.

---

## References

- [ETS-003b Morning Brief Data Wiring](./ets/ETS-003b_Morning_Brief_Data_Wiring.md)
- [Migration Step 4](../../architecture/12_Migration_Step4_Legacy_Elimination.md) (if present)
- TD-P0-06 Technical Debt backlog
