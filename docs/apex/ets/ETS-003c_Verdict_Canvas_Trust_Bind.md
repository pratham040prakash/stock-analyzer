# ETS-003c — Verdict Canvas Trust Bind

**Document ID:** ETS-003c  
**Version:** 0.1  
**Status:** IMPLEMENTED — Awaiting CTO review  
**Date:** 2026-08-05  
**Scope:** Bind Verdict Canvas L0 hero to `MorningBriefViewModel` trust fields (projection only).

**Authority:** [ETS-003b v0.2](./ETS-003b_Morning_Brief_Data_Wiring.md) §6 · [ETS-003a](./ETS-003a_Morning_Brief_Experience_Spec.md) §4, §9

---

## Goal

The first 30 seconds answer:

1. **Should I act?** — `decision.verdict_display`
2. **Why?** — `decision.reason` + `evidence.key_reasons[0]` (teaser)
3. **Why trust?** — `trust.why_this_is_recommended`
4. **Next action?** — `decision.cta_label` / `cta_action`

---

## Implementation

| Layer | Change |
|-------|--------|
| `ui/components/decision_card.py` | `hero_stale_html`, `hero_l0_trust_html`, `hero_header_sync_html` — pure projection from `DecisionCardViewModel` |
| `ui/components/home_dashboard.py` | Hero render consumes `project_decision_card(brief)` only; sync from brief trust |
| `ui/theme.py` | L0 CSS: `.vc-stale`, `.vc-evidence-teaser`, `.vc-trust-line`, `.vc-confidence-band`, `.vc-portfolio-line` |
| `tests/test_ets_003c.py` | Trust bind + 30-second field coverage |

**No** new engines · **No** new view model types · **No** UI business logic.

---

## Rollback

Revert commits touching the four files above. Hero reverts to verdict + mentor + CTA without trust/evidence lines.

---

*Repository: stock-analyzer · Product: APEX*
