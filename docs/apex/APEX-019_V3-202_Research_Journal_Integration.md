# APEX-019 — V3-202 Research Journal Integration Architecture (FROZEN)

**Document ID:** APEX-019  
**Version:** 1.0  
**Status:** APPROVED — FROZEN (V3-202)  
**Date:** 2026-08-06  
**Milestone:** V3-202 Research Journal Integration  
**Baseline:** V3-201 @ `fae0b92` · v2.0.0 GA (unchanged)  
**References:** [V3_RESEARCH_JOURNAL_INTEGRATION.md](../product/V3_RESEARCH_JOURNAL_INTEGRATION.md), [APEX-018](./APEX-018_V3-201_Research_Workbench.md), [product/CHANGELOG.md](../../product/CHANGELOG.md)

---

## 1. Frozen data flow (V3-202 additive)

```
Research Workbench Q7 (session narrative + disposition)
        ↓
ResearchWorkspaceContract + DecisionContextBundle refs (cached)
        ↓
research_journal_draft_from_workspace()        ← projection only
        ↓
ResearchJournalDraftContract (session store)
        ↓
Journal › Confirm Draft (SCR-J-003)
        ↓
draft_to_confirmed_entry()
        ↓
ResearchDecisionEntryContract (immutable, session store)
        ↓
research_journal_experience.py                 ← render-only UI
        ↓
Journal › Timeline (SCR-J-001) · Entry Detail (SCR-J-002)
```

**V2 frozen pipeline unchanged.** V3-201 Research Workbench unchanged except Save-to-Journal handoff.

---

## 2. Presentation Single Source of Truth

| Concern | Owner | Notes |
|---------|-------|-------|
| Draft projection | `research_journal_ui.py` | Copies workspace + session Q7 + frozen bundle refs |
| Confirmed entry | `research_journal_ui.py` | Immutable `ResearchDecisionEntryContract` |
| Journal render | `research_journal_experience.py` | Render-only; no analyzer imports |
| Understand | `understand_popover.py` | Frozen on entry from workspace contract |
| Proof overlay | `proof_state.open_proof_overlay` | Reuses `DecisionArtifact` / evidence packet |
| Storage | `st.session_state` | Drafts + confirmed entries — no disk persistence |
| Outcome Review | Entry Detail placeholder | Disabled CTA only — V3-203+ |
| Shared CSS | `APEX_PARTNER_EXPERIENCE_CSS` | `.apex-research-journal` in bundle |
| Page entry | `ui/pages/research_journal.py` | Journal tab |

---

## 3. Screen relationship (frozen — Journal pillar)

| Surface | Question | Owner |
|---------|----------|-------|
| **Timeline** (SCR-J-001) | What decisions have I recorded? | Confirmed entries only |
| **Confirm Draft** (SCR-J-003) | What happens when I commit? | Editable draft → immutable entry |
| **Entry Detail** (SCR-J-002) | What did I believe? | Read-only frozen record |
| **Research Workbench** (V3-201) | What is my investment decision? | Handoff source |

**Rule:** Journal records what the investor **believed**; Outcome Review (future) records what **happened** — separate layers.

---

## 4. Immutability model (frozen)

| State | Editable | Timeline |
|-------|----------|----------|
| Draft | Narrative + disposition | Drafts inbox only |
| Confirmed entry | None | Timeline + Entry Detail |

Corrections require a **new** entry with evolution linkage — never in-place edit.

---

## 5. Regression gate (V3-202)

| Suite | Count |
|-------|-------|
| `tests/test_v3_202_research_journal.py` | 10 |
| `tests/test_v3_201_research_workspace.py` | 11 |
| `tests/test_v3_103_portfolio_review.py` | 7 |
| `tests/test_v3_102_holdings_experience.py` | 9 |
| `tests/test_v3_101_portfolio_command_center.py` | 8 |
| `tests/test_v2_rc001_render_integration.py` | 5 |
| `tests/test_apex_012_phase0` (UI guardrails) | 19 |
| **V3 Phase 1–2 gate total** | **69** |

---

## 6. Out of scope (frozen for V3-202)

- No analyzer or decision-engine changes
- No new evidence model for Proof overlay
- No disk persistence backend
- No Outcome Review implementation (SCR-J-004 reserved only)
- No scheduling / review_timing computation
- Confirmed entries never mutate in session

---

*Frozen at Engineering Review approval — 2026-08-06.*
