# APEX v2.0.0 GA — Engineering Review Archive

**Document ID:** APEX-ARCHIVE-v2.0.0-GA  
**Version:** 1.0  
**Status:** ARCHIVED — FROZEN  
**Date:** 2026-08-06  
**Tags:** `v2.0.0-rc1` → `v2.0.0`

---

## 1. Release Candidate Readiness Review

**Recommendation:** Minor fixes before release (addressed in RC-001 + V2.1-T001)

**Release readiness score:** 79 / 100 (pre-RC audit)

**RC-001 closed:**

- P1-001 — Unified Review Depth compositor
- P1-005 — Render integration tests
- P1-006 — `APEX-014` engineering documentation
- P1-008 — Full suite triaged

---

## 2. V2.1-T001 Test Suite Triage (Final)

**Before:** 10 failures (3 FAIL + 7 ERROR) on 686 tests  
**After:** **687 / 687 passing — 0 failures**

| Test | Resolution |
|------|------------|
| `test_pdf_unicode_safe` | Fix — `fpdf2` from requirements-lock |
| `test_intraday_chart` | Fix — `plotly` from requirements-lock |
| `test_options_premium_chart` | Fix — `plotly` from requirements-lock |
| `test_fetch_merges_same_day_cnc_when_holdings_empty` | Fix — `kiteconnect` from requirements-lock |
| `test_home_dashboard_composes_hero_intel_from_brief` | Replace — V2 delegation test |
| `test_home_dashboard_passes_review_symbol_from_card` | Replace — `today_brief_experience` wiring test |
| `test_tier_a_baseline_imports_do_not_expand` | Fix — allowlist `morning_brief_ui.py` |
| `test_changed_files_parses_name_status` | Replace — platform git mock paths |
| `test_get_aps_context` | Replace — `search_aps` tool |
| `test_get_adr_context` | Replace — `search_adr` tool |

---

## 3. GA Exit Criteria (RELEASE_PLAN)

| Criterion | Status at GA |
|-----------|----------------|
| Obsolete static tests updated | ✅ Done (V2.1-T001) |
| Review Depth single compositor | ✅ Done (RC-001) |
| Full suite clean | ✅ 687 / 687 |
| Manual QA sign-off | Deferred — post-GA operational |
| Session ribbon product decision | Deferred — backlog |

---

## 4. Frozen Baselines

| Milestone | Commit / Tag |
|-----------|--------------|
| V2-004 | `0020ed8e94fce6c5678a86106979c5f9ab6ff083` |
| RC-001 | `v2.0.0-rc1` (`a72710bde00da4fe8110743b1b75971f28e764cc`) |
| GA | `v2.0.0` (this release) |

---

## 5. Known Limitations (Carried Forward)

See [APEX-014 §6 Known Limitations](../APEX-014_V2_Architecture_and_Release.md).

No new limitations introduced at GA.
