# V3 Research Journal Integration — Product & UX Design

**Document ID:** V3-RJI-001  
**Version:** 0.2  
**Status:** DRAFT — Phase 2 Design (P1 revision)  
**Date:** 2026-08-06  
**Owner:** Product · UX · Architecture  
**Baseline:** V3-201 Research Workbench @ `fae0b92` · v2.0.0 GA (frozen architecture)  
**Parent:** [V3_RESEARCH_WORKSPACE.md](./V3_RESEARCH_WORKSPACE.md) · [APEX_V3_INFORMATION_ARCHITECTURE.md](./APEX_V3_INFORMATION_ARCHITECTURE.md) · [APEX-018](../apex/APEX-018_V3-201_Research_Workbench.md)  
**Screen IDs:** SCR-J-001 (Journal › Timeline) · SCR-J-002 (Journal › Entry Detail) · SCR-J-003 (Journal › Confirm Draft) · SCR-J-004 (Journal › Outcome Review — **future slot**)

---

## Design Questions — Answers

| # | Question | Answer |
|---|----------|--------|
| 1 | What should the investor see first in Journal? | **Latest decision headline** — symbol, disposition, one-line user decision — not P&L. |
| 2 | What deserves the largest visual emphasis? | The **confirm draft** step when arriving from Research — preview before immutability. |
| 3 | What actions should be immediately available? | **Primary:** Confirm entry · **Secondary:** Edit draft · **Tertiary:** Back to Research / Portfolio. |
| 4 | What belongs above the fold? | Entry type badge · symbol · disposition · user decision text · recorded time. |
| 5 | What belongs below the fold? | Frozen system context · research question completion · proof link · portfolio snapshot · evolution chain. |
| 6 | What should never appear? | Editable confirmed history · Home verdict rewrite · trade execution CTAs · P&L leaderboard · gamification. |

**10-second test:** User understands *what they decided*, *why they recorded it*, and *when it becomes permanent*.

---

## 1. Executive Summary

**V3-202 Research Journal Integration** answers:

> **How should research decisions become journal entries?**

It connects the **Research Workbench** (V3-201) to the **Journal** decision-memory pillar through a **draft → confirm → immutable entry** workflow. Research produces an **Investment Decision** (user narrative + disposition); Journal preserves it as a **Research Decision Entry** with frozen context references — not a recomputed recommendation.

**P1 extension:** The design **reserves an Outcome Review layer** (future — not V3-202 scope) that closes the loop without mutating the original entry:

```text
Research → Investment Decision → Immutable Journal Entry → Outcome Review (future) → Reflection → Future Research
```

| Layer | Records | Mutable? |
|-------|---------|----------|
| **Journal Entry** | What the investor **believed** at decision time | Immutable after confirm |
| **Outcome Review** (future) | What **actually happened** vs that belief | New record; never edits original |

| Stage | Surface | Outcome |
|-------|---------|---------|
| Research | Workbench Q7 | Investment Decision (session draft) |
| Handoff | Journal › Confirm Draft | Preview + last edit window |
| Memory | Journal › Timeline / Entry Detail | Immutable decision history |
| **Future** | **Outcome Review (SCR-J-004)** | **Compare belief vs reality; reflection linkage** |
| **Future** | **Weekly Review (V3-203+)** | **Reflection cadence; return to Research** |

**Architecture constraint:** Reuses frozen `DecisionContextBundle`, `DecisionArtifact`, `MorningBriefViewModel`, and `ResearchWorkspaceContract` references only. Future `research_journal_entry_from_workspace()` is **projection-only**. Outcome Review is a **reserved presentation slot** only — no analyzer changes, no persistence, no implementation in V3-202.

**Primary entry (V3-202):** Research Q7 → Save to Journal · Journal › Confirm Draft · Timeline / Entry Detail.

---

## 2. User Problem

| Problem | Today (V3-201) | V3-202 Research Journal Integration |
|---------|----------------|-------------------------------------|
| **Decision evaporates** | Session toast only; reload loses work | Draft persists through confirm flow |
| **No audit trail** | Cannot answer "what did I decide about WIPRO?" | Immutable timeline entries |
| **Research disconnected from memory** | Workbench ends in browser | Journal owns long-term record |
| **Afraid to commit** | No preview before save | Confirm Draft screen shows full context |
| **Can't trace why** | User text alone | Entry links proof + frozen system summary |
| **Portfolio context lost** | Weight/flag not stored with decision | Portfolio snapshot embedded in entry |
| **No evolution model** | One-off notes | Linked entries show decision changes over time |
| **Belief vs reality disconnected** | No place to compare decision to outcome | **Outcome Review slot reserved (future)** |

---

## 2.1 Design principle — belief vs outcome (frozen intent)

| Pillar | Question | Owner |
|--------|----------|-------|
| **Journal Entry** | What did I believe and decide? | Immutable Research Decision Entry |
| **Outcome Review** (future) | What actually happened vs that belief? | Separate Outcome Review record |

**Rule:** Outcome Review **never edits** the original Journal Entry. It **references** it and adds reflection + outcome snapshot only.

---

## 3. Journal Entry Creation Flow

```text
Research Workbench Q7 — Investment Decision
    → User writes narrative + selects disposition
    → [ Save to Journal ] creates JournalDraft (presentation state / future store)
    → Navigate Journal › Confirm Draft (SCR-J-003)
    → Preview: user text + system summary + frozen refs + portfolio chip
    → User edits draft OR confirms
    → [ Confirm entry ] → ResearchDecisionEntry (immutable)
    → Journal › Entry Detail (SCR-J-002) + Timeline row (SCR-J-001)
    → Optional: Return to Portfolio Review (theme marked investigated)
    → ─── future boundary (not V3-202) ───
    → Outcome Review due (review timing — future concept)
    → Outcome Review (SCR-J-004) — what happened vs belief
    → Reflection (user narrative + lessons)
    → Future Research (symbol handoff with outcome context)
```

### 3.1 Draft vs confirmed

| State | Editable | Visible in timeline | Proof link |
|-------|----------|-------------------|------------|
| **Draft** | Full (narrative, disposition) | No (Drafts inbox only) | Preview only |
| **Confirmed** | None (body locked) | Yes | Active |
| **Follow-up note** | New draft linked to parent | Yes (as new entry) | Inherits parent refs |

### 3.2 Cancel / abandon

- **Discard draft** — returns to Research with session draft cleared
- **Save draft for later** — stays in Journal › Drafts; Workbench can resume

---

## 4. Investment Decision Schema (Presentation Only)

Future **`ResearchJournalDraftContract`** / **`ResearchDecisionEntryContract`** — projection fields only.

### 4.1 Core fields

| Field | Source | Notes |
|-------|--------|-------|
| `entry_id` | Generated at draft | UUID; stable after confirm |
| `entry_type` | Constant | `research_decision` |
| `symbol` | Research workspace | Normalized ticker |
| `recorded_at` | Draft created / confirm time | ISO + human label |
| `user_narrative` | Q7 text area | User-owned |
| `disposition` | Q7 radio | `watch` · `hold` · `accumulate_later` · `avoid` |
| `disposition_label` | Projection | Watch · Hold · Accumulate Later · Avoid |

### 4.2 Frozen context references (read-only on entry)

| Field | Source | Notes |
|-------|--------|-------|
| `investment_view_label` | `InvestmentViewHeroContract.view_label` | e.g. Cautious |
| `investment_view_summary` | Hero summary at save time | Not recomputed on read |
| `system_summary_lines` | Q7 system block | Business / risks / valuation |
| `questions_reviewed` | Session keys | Tuple of 1–7 reviewed flags |
| `decision_id` | `DecisionArtifact` | Link to Home proof when same symbol |
| `evidence_packet_id` | `DecisionArtifact` | Proof overlay |
| `bundle_built_at` | `DecisionContextBundle` | Context freshness |
| `bundle_version` | Cache metadata | Determinism audit |

### 4.3 Portfolio linkage snapshot

| Field | Source | Notes |
|-------|--------|-------|
| `portfolio_held` | `PortfolioResearchContextContract` | bool |
| `portfolio_weight_label` | Context chip | e.g. 18% |
| `portfolio_health_label` | Context chip | e.g. Attention |
| `portfolio_flag_label` | Context chip | e.g. Health |
| `review_theme_key` | Handoff session | Optional; Portfolio Review origin |
| `research_back_tab` | Handoff session | Overview / Review / Holdings |

### 4.4 Evolution linkage

| Field | Purpose |
|-------|---------|
| `prior_entry_id` | Previous confirmed entry for same symbol (optional) |
| `supersedes_entry_id` | Explicit replacement (user selects on confirm) |
| `follow_up_of_entry_id` | For addendum entries only |

**Rule:** Confirmed entries never mutate `user_narrative` or `disposition`. Changes require a new entry with linkage.

### 4.5 Outcome Review reservation (presentation only — future)

Future **`OutcomeReviewContract`** — linked to immutable entry; **not implemented in V3-202**.

| Field | Purpose | Notes |
|-------|---------|-------|
| `outcome_review_id` | Unique Outcome Review record | Separate from `entry_id` |
| `original_entry_id` | **Original decision reference** | Required FK-style link; read-only display of belief |
| `review_timing` | **When review is due** (future concept) | e.g. `due_at`, `cadence_key` — not computed in V3-202 |
| `reviewed_at` | When user completed Outcome Review | Nullable until future |
| `portfolio_snapshot_at_review` | **Portfolio snapshot at review time** | Separate from decision-time snapshot |
| `outcome_summary` | What actually happened (user + labeled facts) | Process truth, not P&L leaderboard |
| `belief_vs_outcome` | Structured compare lines | "Expected Hold · Still held · Health improved" |
| `reflection_narrative` | **Reflection linkage** — user lessons | Editable only on Outcome Review, not on original entry |
| `reflection_tags` | Optional taxonomy | e.g. patience validated · thesis broken |
| `future_research_context` | Handoff payload | Symbol + outcome_review_id for next Research session |

**Immutability rules (future):**

- Original `ResearchDecisionEntry` — **never edited** by Outcome Review
- Outcome Review — **append-only**; corrections via new Outcome Review linked to same entry (future)
- Decision-time portfolio snapshot — frozen on entry; review-time snapshot — frozen on Outcome Review

---

## 5. Timeline Model

### 5.1 Journal › Timeline (SCR-J-001)

Primary question: *What decisions have I recorded?*

```text
┌─ TIMELINE ────────────────────────────────────────────────────────────────┐
│  Today                                                                     │
│  ┌─ Research Decision ──────────────────────────────────────────────────┐  │
│  │  WIPRO · Hold · 14:32                                                │  │
│  │  "Hold current position; do not add until health stabilizes…"        │  │
│  │  From Research · Held 18% · Proof available                          │  │
│  │  Outcome review due in 4 weeks (future)                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  This week                                                                 │
│  ┌─ Research Decision ──────────────────────────────────────────────────┐  │
│  │  TCS · Watch · Mon 09:15 · Accumulate Later candidate                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Grouping & sort

| Dimension | Default |
|-----------|---------|
| Sort | `recorded_at` descending |
| Groups | Today · This week · This month · Earlier |
| Filters | Symbol · Disposition · Entry type · Source (Research / Home future) |

### 5.3 Entry card priority (timeline row)

```text
Disposition + symbol → user narrative (1 line) → time → source badge → portfolio chip
```

---

## 6. Research-to-Journal Handoff

### 6.1 Trigger (Research Workbench)

Replace V3-201 toast with:

```text
[ Save to Journal ]
    → build ResearchJournalDraftContract from ResearchWorkspaceContract + session Q7
    → st.session_state journal_draft_{entry_id} OR future store
    → request_nav_tab("Journal", journal_draft_id=..., journal_view="confirm")
```

### 6.2 Confirm Draft screen (SCR-J-003)

```text
┌─ CONFIRM JOURNAL ENTRY ───────────────────────────────────────────────────┐
│  Research Decision · WIPRO                                                 │
│  Disposition: Hold                                                         │
│  ┌─ Your decision (editable) ────────────────────────────────────────────┐  │
│  │ Hold current position; do not add until health stabilizes…           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  System context (read-only)                                                │
│  · Business quality: Adequate · Risks: Elevated · Valuation: Full          │
│  · 6 of 7 research questions reviewed                                      │
│  Portfolio: Held 18% · ⚠ Health flagged                                    │
│  [ View proof ]  [ Help me understand ▾ ]                                  │
│  [ Discard ]  [ Back to Research ]  [ Confirm entry ✓ ]                    │
└───────────────────────────────────────────────────────────────────────────┘
```

### 6.3 Post-confirm routing

| User choice | Destination |
|-------------|-------------|
| Default | Journal › Entry Detail (confirmed) |
| If from Portfolio Review | Optional CTA: Return to Review |
| If disposition = Watch | Optional: Add to watchlist (future; navigation only) |

---

## 7. Editing Model

| Object | Rule |
|--------|------|
| **Draft** | User narrative + disposition editable until confirm |
| **Confirmed entry** | Body locked — display only |
| **Correction** | User creates **new** entry; links `supersedes_entry_id` |
| **Addendum** | "Add follow-up note" → new entry with `follow_up_of_entry_id`; shorter form |
| **Delete** | Drafts: discard allowed · Confirmed: no delete (future: archive/hide only) |

**Teaching moment on confirm:** *"Once confirmed, this entry becomes part of your decision history. It cannot be edited — only followed up."*

---

## 8. Read-Only History

### 8.1 Entry Detail (SCR-J-002)

```text
┌─ RESEARCH DECISION · WIPRO ───────────────────────────────────────────────┐
│  Hold · Recorded 6 Aug 2026, 14:32 IST                                     │
│  ┌─ Your decision ──────────────────────────────────────────────────────┐  │
│  │ (read-only user narrative)                                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  System summary (frozen at record time)                                    │
│  Research completion: Q1–Q6 reviewed · Q7 decision                         │
│  Portfolio at decision: Held 18% · Health flagged                          │
│  Context: bundle 09:12 IST · decision_id abc · proof linked                │
│  [ Open Research ]  [ Open Portfolio ]  [ View proof ]                     │
│  Decision history for WIPRO (2 prior entries)                              │
│  ─── Outcome Review (future) ───                                           │
│  Outcome review: Not yet due · Scheduled 4 weeks after decision            │
│  [ Start Outcome Review ] (disabled / future — SCR-J-004)                  │
└───────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Immutability display

- Confirmed entries show **Recorded** badge — never "Updated"
- Frozen fields rendered from entry contract — **never** reassembled from live bundle on read

---

## 9. Decision Evolution

### 9.1 Same symbol, multiple entries

```text
WIPRO timeline:
  2026-07-01  Watch      "Too expensive; wait for pullback"
  2026-08-01  Accumulate "Health stabilizing; add on dip"
  2026-08-06  Hold       "Do not add until 2 quarters recovery"  ← latest
```

### 9.2 Evolution UX

| Pattern | UI |
|---------|-----|
| New decision supersedes old | Optional checkbox on confirm: "Replaces my prior WIPRO decision (Jul 1)" |
| Follow-up note | Shorter form; links to parent; no full 7-question replay required |
| Weekly Review hook | "You recorded 3 research decisions this week" (V3-203) |
| Outcome Review due | Timeline badge when `review_timing` elapsed (future) |

### 9.3 No silent overwrite

Prior entries remain visible in symbol-scoped history chain. Latest disposition shown on symbol summary chip in Journal search only.

### 9.4 Outcome Review evolution (future)

```text
Research Decision Entry (immutable)
    ↓ referenced by
Outcome Review #1 (reflection at 4 weeks)
    ↓ may inform
Future Research session (outcome context chip — navigation only)
    ↓ may produce
New Research Decision Entry (new belief — separate immutable record)
```

**Rule:** Outcome Review informs the **next** research cycle; it does not revise the **prior** belief record.

---

## 10. Portfolio Linkage

| Link | Direction | Behavior |
|------|-----------|----------|
| Research → Journal | Outbound | Draft carries portfolio snapshot |
| Journal → Research | Return | `Open Research` with symbol; no auto-load of old answers |
| Journal → Portfolio | Return | `Open Portfolio` → Holdings row highlight or Review theme if `review_theme_key` set |
| Portfolio Review | Closure | Confirm CTA marks theme investigated (session or future persisted flag) |

**Portfolio snapshot rule:** Store weight/held/flag **at decision time** — do not live-update historical entries when portfolio changes.

---

## 11. Accessibility

| Requirement | Implementation |
|-------------|----------------|
| **Landmarks** | `main` timeline · `article` per entry · `form` on confirm draft |
| **Confirm step** | Announce immutability before Confirm button |
| **Disposition** | Text labels always visible — not color-only |
| **Timeline** | List semantics · `time` element with `datetime` |
| **Read-only sections** | `aria-readonly="true"` on frozen context blocks |
| **Keyboard** | Confirm / Discard focus order; Escape returns to draft list |
| **Screen reader** | Entry: "Research decision for WIPRO, Hold, recorded 6 August" |

---

## 12. Performance

| Technique | Application |
|-----------|-------------|
| **Draft in session first** | V3-202 MVP: session/store draft before confirm |
| **Lazy entry detail** | Load full frozen context on detail view only |
| **Timeline pagination** | 20 entries per page; virtualize >100 |
| **No live re-assembly** | Confirmed entries read stored contract — no bundle fetch |
| **Proof lazy** | Proof overlay on explicit tap |
| **Targets** | Confirm screen <200ms · Timeline scroll 60fps · Detail LCP <1.5s cached |

---

## 13. Future Extensibility

| Extension | Slot | Notes |
|-----------|------|-------|
| **Outcome Review (SCR-J-004)** | **`OutcomeReviewContract`** | **Reserved P1 — belief vs outcome; no V3-202 implementation** |
| Home ACT/WAIT receipts | `entry_type: daily_verdict` | Same timeline; different schema slice |
| Weekly Review (V3-203) | Review queue + Outcome Review cadence | Consumes `review_timing` |
| Export PDF/markdown | Entry detail action | F-203 backlog |
| Thesis Tracker | Link `thesis_id` on entry | V3-402 |
| Broker reconcile | Separate trade entries | Do not merge with research decisions |
| Persistence backend | Journal store facade | Design-only here; `journal/` use case future |
| Notifications | "Outcome review due for WIPRO" | V3-304; uses `review_timing` |
| Future Research handoff | `future_research_context` on Outcome Review | Navigation + read-only chip in Workbench |

### 13.1 Contract stability (future)

**`research_journal_entry_from_workspace()`** projects:

- `ResearchWorkspaceContract`
- Session Q7 fields (narrative, disposition, reviewed questions)
- Handoff session (portfolio snapshot, review theme)
- Frozen refs from bundle (`decision_id`, `evidence_packet_id`, `built_at`)

No analyzer changes without approval.

---

## 14. Design Decisions (P1 — Outcome Review reservation)

| ID | Decision | Rationale |
|----|----------|-----------|
| DD-001 | **Separate Journal Entry from Outcome Review** | Journal records belief; Outcome Review records reality. Mixing them would blur audit trail and invite retroactive edits. |
| DD-002 | **Original decision is never edited** | Confirmed `ResearchDecisionEntry` stays immutable. Outcome Review references via `original_entry_id` only. |
| DD-003 | **Two portfolio snapshots** | Decision-time snapshot on entry; review-time snapshot on Outcome Review. Historical entries must not live-update. |
| DD-004 | **`review_timing` is a future concept only** | Reserved field for cadence/due date — not computed or persisted in V3-202. Weekly Review (V3-203+) owns scheduling UX. |
| DD-005 | **Reflection lives on Outcome Review** | User lessons attach to outcome layer via `reflection_narrative` / `reflection_tags` — not appended to original narrative. |
| DD-006 | **Future Research handoff is navigation-only** | `future_research_context` passes read-only outcome chip into Workbench — no auto-fill of Q1–Q7 answers. |
| DD-007 | **SCR-J-004 reserved, not built in V3-202** | Entry Detail shows placeholder/disabled CTA. No contracts, persistence, or analyzer work in this milestone. |
| DD-008 | **Outcome Review corrections = new record** | Same pattern as decision evolution: append-only; link to same `original_entry_id` if user revises reflection later. |
| DD-009 | **Timeline shows due badge (future)** | Optional "Outcome review due" on entry card — visual only in design; implementation deferred. |
| DD-010 | **V3-202 scope unchanged** | Draft → Confirm → Immutable Entry only. Outcome Review chain documented for product continuity, not delivery. |

---

## Appendix A — Component hierarchy (design)

```text
JournalSurface
├── JournalSubNav (Timeline · Drafts · Receipts · Trades · Calibration)
├── JournalTimeline (SCR-J-001)
│   └── JournalEntryCard (repeat)
│       ├── EntryTypeBadge
│       ├── SymbolDispositionHeader
│       ├── UserNarrativePreview
│       ├── RecordedTime
│       ├── SourceBadge (Research / Home future)
│       └── PortfolioSnapshotChip
├── JournalConfirmDraft (SCR-J-003)
│   ├── DraftPreviewHeader
│   ├── EditableNarrativeBlock
│   ├── DispositionSelector (draft-only edit)
│   ├── FrozenSystemSummaryBlock
│   ├── ResearchCompletionStrip
│   ├── PortfolioLinkageBlock
│   ├── UnderstandGateway
│   ├── ProofLink
│   └── ConfirmDiscardActions
├── JournalEntryDetail (SCR-J-002)
│   ├── ReadOnlyNarrativeBlock
│   ├── FrozenContextSections
│   ├── ResearchQuestionCompletion
│   ├── PortfolioAtDecisionBlock
│   ├── ProofLink
│   ├── EvolutionChain (prior entries)
│   ├── OutcomeReviewPlaceholder (future — SCR-J-004)
│   │   ├── OriginalEntryReference (read-only)
│   │   ├── ReviewTimingBadge (future)
│   │   ├── PortfolioSnapshotAtReview (future)
│   │   └── ReflectionLinkage (future)
│   └── ReturnActions (Research · Portfolio)
├── JournalOutcomeReview (SCR-J-004 — **future slot, not built**)
│   ├── OriginalDecisionReferenceBlock (immutable belief)
│   ├── PortfolioSnapshotCompare (decision time vs review time)
│   ├── OutcomeSummaryBlock
│   ├── ReflectionEditor
│   └── FutureResearchHandoff
└── JournalDraftsInbox
    └── DraftCard → Confirm Draft
```

---

## Appendix B — Information hierarchy

| Rank | Element | User need |
|------|---------|-----------|
| 1 | User narrative | What did I decide? |
| 2 | Disposition + symbol | Outcome at a glance |
| 3 | Recorded time | When did I decide? |
| 4 | Confirm immutability (draft only) | What happens on save? |
| 5 | System summary (frozen) | What did the system say then? |
| 6 | Research completion | Did I do the work? |
| 7 | Portfolio snapshot | How did this relate to holdings? |
| 8 | Proof / Understand | Evidence on demand |
| 9 | Evolution chain | How has my view changed? |
| 10 | Outcome Review placeholder (future) | What happened vs what I believed? |
| 11 | Return links | Continue workflow |

---

## Appendix D — Outcome Review wireframe (future — SCR-J-004)

```text
┌─ OUTCOME REVIEW · WIPRO ──────────────────────────────────────────────────┐
│  Reviewing decision from 6 Aug 2026 · Hold                                │
│  ┌─ What you believed (read-only) ───────────────────────────────────────┐  │
│  │ "Hold current position; do not add until health stabilizes…"          │  │
│  │ Portfolio at decision: Held 18% · Health flagged                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌─ What happened ───────────────────────────────────────────────────────┐  │
│  │ (outcome summary — user + labeled facts)                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌─ Reflection ──────────────────────────────────────────────────────────┐  │
│  │ What did I learn? Was my process sound?                               │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  Portfolio at review: Held 16% · Health stable                           │
│  [ Save Outcome Review ]  [ Open Research with this context ]               │
└───────────────────────────────────────────────────────────────────────────┘
```

*Reserved for V3-203+ — not in V3-202 scope.*

---

## Appendix C — References

| Doc | Relationship |
|-----|--------------|
| [APEX-018](../apex/APEX-018_V3-201_Research_Workbench.md) | Research Workbench frozen handoff |
| [V3_RESEARCH_WORKSPACE.md](./V3_RESEARCH_WORKSPACE.md) | Q7 Investment Decision (V3-201) |
| [APEX_V3_INFORMATION_ARCHITECTURE.md](./APEX_V3_INFORMATION_ARCHITECTURE.md) | Journal sub-tabs |
| [MASTER_PROMPT](../../.cursor/MASTER_PROMPT.md) | Decision memory philosophy |

---

*Draft v0.2 — P1 Outcome Review reservation — 2026-08-06. No implementation.*
