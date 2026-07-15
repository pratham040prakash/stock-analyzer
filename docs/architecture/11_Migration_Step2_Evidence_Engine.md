# 11 — Migration Step 2: Evidence Engine

**Status:** Implemented  
**Constitution:** [08_Final_Investment_OS_Architecture.md](./08_Final_Investment_OS_Architecture.md)  
**Prerequisite:** [10_Migration_Step1_Broker_Truth.md](./10_Migration_Step1_Broker_Truth.md)  
**Scope:** Migration Step 2 only — Evidence Engine; no Step 3+

---

## Goal

Make **EvidencePacket** the canonical source of investment evidence. Every recommendation and Alpha AI report is grounded in labeled, mergeable, auditable claims — not raw prose.

**Rule:** Unknown must never become FACT. Missing data surfaces as GAP.

---

## Package: `analyzer/evidence_engine/`

| Module | Role |
|--------|------|
| `models.py` | `EvidencePacket`, `EvidenceItem`, `EvidenceSource`, `EvidenceCategory`, `EvidenceConfidence`, `EvidenceConflict`, `RecommendationFromEvidence` |
| `builder.py` | `EvidenceBuilder` — factory for items with stable IDs |
| `validator.py` | `EvidenceValidator` — downgrade untrusted FACTs, enforce GAP rules |
| `conflicts.py` | `EvidenceConflictDetector`, `merge_duplicate_items` |
| `engine.py` | `EvidenceEngine` — combine, gap-fill, `recommend_from_packet` |
| `serialization.py` | JSON round-trip for packets and items |
| `store.py` | Optional SQLite archive (`data/evidence_engine/evidence.db`) |
| `migration.py` | Legacy adapters: combined, advisor, strategy votes, data health |
| `render.py` | Markdown rendering from `EvidencePacket` for Alpha AI |
| `__init__.py` | Public exports |

---

## EvidenceItem schema

| Field | Description |
|-------|-------------|
| `id` | Stable identifier `{category}:{label_slug}:{hash}` |
| `category` | Market · Technical · Fundamental · Volume · Sentiment · Macro · Options · Risk · Portfolio · Execution |
| `source` | Provenance enum (`yahoo_finance`, `kite`, `internal_model`, …) |
| `timestamp` | IST timestamp |
| `label` | Short claim name |
| `type` | FACT · ESTIMATE · OPINION · ASSUMPTION · GAP |
| `value` | Scalar or string payload |
| `confidence` | high · medium · low · none |
| `weight` | Believability weight (0–10) |
| `explanation` | Human-readable rationale |
| `metadata` | Optional `vote`, `score`, `signal` for synthesis |

---

## Evidence Engine flow

```text
Legacy analyzers (combined, advisor, strategy votes, data health)
        │
        ▼
  migration.py adapters  →  list[EvidenceItem]
        │
        ▼
  EvidenceValidator  →  merge duplicates  →  inject category GAPs
        │
        ▼
  EvidenceConflictDetector
        │
        ▼
  EvidencePacket  →  recommend_from_packet()  →  RecommendationFromEvidence
```

---

## Integration (backward compatible)

| Module | Change |
|--------|--------|
| `strategy_synthesis.py` | `StrategySynthesis.evidence_packet` + `recommendation_from_evidence`; `_finalize_synthesis()` builds packet from pillars and derives verdict from packet |
| `alpha_ai_report.py` | `AlphaAIReport.evidence_packet` + `evidence_summary`; built via `build_equity_research_packet()` |
| `advisor.py` | `InvestmentAdvice.evidence_packet`; built at end of `generate_advice()` |

Existing fields (`verdict`, `recommendation`, prose sections) remain for UI compatibility. New code should read `evidence_packet` first.

---

## Recommendation rule

`EvidenceEngine.recommend_from_packet()` is the **only** scoring path inside strategy synthesis finalization. Legacy pillar math still produces votes; votes become evidence; recommendation consumes the packet.

---

## Alpha AI rendering

`format_evidence_report(packet)` produces a markdown evidence section. `AlphaAIReport.evidence_summary` is populated automatically in `build_alpha_ai_report()`.

---

## Persistence

```python
from analyzer.evidence_engine import save_evidence_packet, fetch_evidence_packet

packet_id = save_evidence_packet(packet)
restored = fetch_evidence_packet(packet_id)
```

Store is optional — in-memory packets work without persistence.

---

## Tests

```bash
python -m unittest tests.test_evidence_engine tests.test_strategy_synthesis tests.test_alpha_ai_report -v
```

---

## Not in scope (Step 3+)

- Daily loss dam
- Uncertainty vector
- Munger invert gate
- Full analyzer refactor (each module returning EvidenceItems natively)
- Event bus / domain folder move

---

## Constitutional alignment

| Principle | Implementation |
|-----------|----------------|
| No invented certainty | Validator downgrades FACT without trusted source |
| Multidisciplinary evidence | Ten categories with required-category GAP injection |
| Explainability | Every packet has IDs, labels, conflicts, gaps |
| Default WAIT | `recommend_from_packet` returns WAIT on insufficient evidence |

---

## Review fixes (post-implementation)

| Area | Issue | Fix |
|------|--------|-----|
| **Validator** | `INTERNAL_MODEL` could remain FACT | Whitelist: only `TRUSTED_FACT_SOURCES` may be FACT |
| **Migration** | Strategy votes / composites labeled FACT | All model-derived items use ESTIMATE |
| **Gaps** | Category GAP injected when category already had GAP item | Skip injection when `gap_categories` present |
| **Conflicts** | Duplicate conflict IDs from pairwise + recommendation | Dedup by `conflict.id` |
| **Performance** | Set comprehension rebuilt per gap in `build_packet` | Precompute `merged_ids` once |
| **Serialization** | No schema version; fragile enum parse | `schema_version=1`; safe enum fallback |
| **Serialization** | Gaps duplicated in items + gaps arrays on load | Derive gaps from items when present |
| **Thread safety** | `fetch_evidence_packet` read without lock | Reads wrapped in `_STORE_LOCK` |
| **Tests** | Missing whitelist, dedup, schema, conflict round-trip | Added 8 tests |

---

## Thread safety

- SQLite store uses `threading.RLock`, WAL mode, 30s timeout
- Path-aware `_STORE_READY_PATH` for test isolation (same pattern as Broker Truth)
- Reads and writes both acquire `_STORE_LOCK`

---

## FACT labeling rule

Only feed-backed sources may produce FACT after validation:

`yahoo_finance`, `kite`, `nse`, `screener`, `data_health`, `news_feed`, `macro_feed`

All other sources (`internal_model`, `coach`, `unknown`, `user`) are downgraded to ESTIMATE, ASSUMPTION, or GAP.
