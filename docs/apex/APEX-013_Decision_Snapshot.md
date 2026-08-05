# APEX-013 — Decision Snapshot (Flight Recorder E0)

**Status:** E0 IMPLEMENTED — awaiting CTO review before E1  
**Priority:** P0 Strategic  
**Last updated:** 2026-08-05

---

## Mission

Immutable ledger of every Morning Brief at decision time — **what APEX believed**, not what happened.

```
Decision Engine → MorningBriefViewModel → Snapshot Writer → decision_snapshots.db
                                                      ↓ (future E1)
                                              Outcome Evaluation
```

---

## Schema v1

| Field | Source |
|-------|--------|
| `snapshot_id` | UUID4, globally unique |
| `schema_version` | `"1"` |
| `created_at` | UTC ISO8601 |
| `market_session` | `brief.meta` + context session |
| `decision` | `brief.decision` (ids, verdict, source) |
| `confidence` | level + band |
| `reason` / `mentor_message` | `brief.decision.reason` |
| `cta` | label + action |
| `best_opportunity` | `brief.opportunity` |
| `risk` | `brief.risk` |
| `trust` | stale/freshness/gaps (no learning) |
| `portfolio_context` | `brief.portfolio` |
| `broker_sync_state` | trust freshness |
| `evidence_summary` | counts + key reasons (not full packet) |
| `context_summary` | regime, risk_mode, hash |
| `decision_engine_version` | artifact version |
| `morning_brief_version` | `"0.2"` |

**Never stored:** outcomes, P&L, calibration, learning, future prices.

---

## Production paths

| Path | `record_snapshot` |
|------|-------------------|
| `build_morning_brief()` | ✅ |
| `load_today_core()` (fresh domain) | ✅ |
| `load_brief_from_cache()` / UI rehydration | ❌ |

---

## Failure policy

Persist failure → log + continue Morning Brief. No retroactive reconstruction.

---

## Module map

| Module | Role |
|--------|------|
| `analyzer/intelligence_lab/snapshot_schema.py` | Payload builder v1 |
| `analyzer/intelligence_lab/snapshot_store.py` | SQLite insert-only ledger |
| `analyzer/use_cases/morning_brief.py` | Snapshot hook after assembly |

Store: `data/intelligence_lab/decision_snapshots.db`

---

## Tests

`tests/test_apex_013_e0.py` — immutability, uniqueness, no hindsight, failure isolation, roundtrip.

---

## Future (not E0)

E1 Outcome scoring · E2 Baselines · E3 Calibration · E4 Learning · E5 Threshold optimization
