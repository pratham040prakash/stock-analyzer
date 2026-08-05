# APEX-013 E0.5 — Ledger Health Report

**Status:** Validation complete — **HEALTHY_WITH_KNOWN_P1**  
**Date:** 2026-08-05  
**Scope:** E0 flight recorder validation only (no E1 outcome scoring)

---

## Executive Summary

The Decision Snapshot ledger meets E0 immutability, fail-open, and single-production-path requirements. **One P1 correctness defect** was confirmed: snapshots can diverge from the Today hero if broker state changes between `load_today_core` and `home_dashboard` render.

**Recommendation:** Fix P1 in **E0.6** before E1 outcome joins. **Do not start E1** until CTO approves.

---

## Validation Results

| # | Objective | Result | Evidence |
|---|-----------|--------|----------|
| 1 | One snapshot per production | **PASS** | `TestOneSnapshotPerProduction` — 1 persist across production + 5 rehydrations |
| 2 | Cache rehydration never records | **PASS** | `TestCacheRehydrationNeverRecords` — 10× `load_brief_from_cache`, 0 persists |
| 3 | Snapshot immutability | **PASS** | INSERT-only; duplicate ID raises `ImmutableSnapshotError` |
| 4 | Contents match user-visible brief | **PASS** (same assembly) / **FAIL** (broker drift) | Parity perfect when same brief; P1 when broker changes |
| 5 | Write latency & storage | **PASS** | p50 ~0.43ms · p95 ~0.81ms · ~2 KB/snapshot |
| 6 | Fail-open on persist failure | **PASS** | Brief returns; error logged; ledger count unchanged |
| 7 | Ledger Health Report | **PASS** | This document |

---

## Performance Measurements

| Metric | Value |
|--------|-------|
| Payload size (sample) | **~1,971 bytes** |
| Write latency p50 | **~0.43 ms** |
| Write latency p95 | **~0.81 ms** |
| Write latency max | **~2.4 ms** |
| Storage growth | **~2 KB per Morning Brief production** |
| Projected 1 year (1 brief/day) | **~730 KB** |
| Projected 1 year (10 briefs/day) | **~7.3 MB** |

Storage and latency are negligible vs correctness requirements.

---

## Defects Found

### P1-BROKER-DRIFT (Confirmed)

**Symptom:** Snapshot recorded in `load_today_core` uses broker state at production time. Today hero re-assembles from cache via `load_brief_from_cache` with **current** broker state. If broker disconnects/reconnects between steps, `verdict_key` can differ (e.g. `trade` → `connect`).

**Repository evidence:**

```
load_today_core → view_model_from_domain(record_snapshot=True)  # broker A
home_dashboard  → load_brief_from_cache(broker=current)         # broker B possible
```

**Test:** `test_broker_drift_can_diverge_snapshot_from_display` in `tests/test_apex_013_e0_5_ledger_validation.py`

**Impact:** E1 outcome evaluation could score the wrong verdict vs what the user saw.

**Recommended fix (E0.6 — not implemented):**

- Option A (preferred): Persist snapshot on **first `home_dashboard` render** with the same broker used for display, once per cache bundle key.
- Option B: Freeze `broker_snapshot` into cache bundle at production and rehydrate with frozen broker for both display and ledger.

---

## No Defects Found

| Area | Status |
|------|--------|
| Duplicate snapshots on UI rerender | OK |
| INSERT/UPDATE/REPLACE paths | OK — insert-only |
| Hindsight fields in payload | OK — guarded |
| Schema version | OK — all v1 |
| Serialization roundtrip | OK |

---

## Tests Added (E0.5)

| File | Tests |
|------|-------|
| `tests/test_apex_013_e0_5_ledger_validation.py` | 14 validation tests |
| `analyzer/intelligence_lab/ledger_validation.py` | Parity + latency helpers |
| `analyzer/intelligence_lab/ledger_health.py` | Health report builder |

**Regression:** 610 tests run · 606 green · 4 pre-existing env import errors

---

## CTO Review

| Question | Answer |
|----------|--------|
| Ledger trustworthy for 5 years? | **Yes**, with P1 fix before E1 |
| Safe to start E1? | **No** — fix broker drift first |
| Schema change needed? | **No** |
| New features added? | **No** — validation tooling only |

**Recommended decision:** **Approve E0.5 validation** · **Schedule E0.6 broker-drift fix** · **Hold E1**

---

## STOP

No outcome scoring. No analytics. Await CTO approval before E0.6/E1.
