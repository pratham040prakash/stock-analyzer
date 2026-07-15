# 15 — Migration Step 5: Context Engine

**Constitution:** [08_Final_Investment_OS_Architecture.md](./08_Final_Investment_OS_Architecture.md)  
**Design review:** [13_Context_Engine_Architecture_Review.md](./13_Context_Engine_Architecture_Review.md)  
**Audit:** [Context_Engine_Audit.md](./Context_Engine_Audit.md)  
**Date:** 2026-07-15

---

## Objective

Introduce a **thin composition layer** that produces one immutable `ContextSnapshot` per session tick. No market math moves into Context Engine; existing producers remain authoritative.

**Immutable engines (unchanged public interfaces):** Broker Truth · Evidence Engine · Decision Engine.

---

## Package layout

```
analyzer/context_engine/
  __init__.py       # build_context_snapshot() — public entry
  models.py         # ContextSnapshot (frozen, snapshot_id, context_hash)
  composer.py       # Parallel producer orchestration
  normalizer.py     # risk_mode, volatility, phase, restrictions
  cache.py          # Single RLock cache (60s live / 24h closed)
  migration.py      # market_context_from_snapshot, evidence_items_from_snapshot
```

---

## Producers composed (canonical sources)

| Producer module | Snapshot field(s) |
|-----------------|-------------------|
| `market_session` | `market_session`, session phase inputs |
| `intraday_beginner_tips` | timing gates → `trading_restrictions`, metadata |
| `market_regime` | `market_regime`, `metadata.regime_detail` |
| `india_macro` | `macro_state`, `sector_strength`, volatility |
| `global_impact` | `global_market_state` |
| `data_health` | liquidity proxy, restrictions |
| `prep_status` | prep restrictions |
| `earnings_calendar` | event restrictions |

**Explicit GAP fields:** `market_breadth` → `unknown`; `industry_strength` → `{"status": "GAP"}`.

---

## Public API

```python
from analyzer.context_engine import build_context_snapshot, ContextSnapshot

snap = build_context_snapshot(market="india", include_global=True, use_cache=True)
# snap.snapshot_id, snap.context_hash, snap.risk_mode, snap.trading_restrictions, ...
```

Adapters (no engine modifications):

```python
from analyzer.context_engine.migration import (
    market_context_from_snapshot,
    evidence_items_from_snapshot,
)
```

---

## Consumer migration status

| Consumer | Status | Notes |
|----------|--------|-------|
| `investment_os` | ✅ Migrated | `build_context_snapshot()`; exposes `context_snapshot_id` |
| `strategy_synthesis` | ✅ Migrated | `_context_votes()` reads snapshot for timing/regime/macro/global |
| `mis_trade_advisory` | ✅ Migrated | Context + Decision attach with `context_snapshot` |
| `session_advisory` | ⏳ Phase 2 | Still uses `fetch_pulse_live_update()` direct fetches |
| `morning_briefing` | ⏳ Phase 2 | Direct regime/macro/session |
| `market_pulse_scan` | ⏳ Phase 2 | Header triple-fetch |
| `advisor` / `daily_advisor` | ⏳ Phase 2 | Direct context producers |

---

## Decision / Evidence integration (migration hooks only)

- `decision_engine/migration.attach_decision_to_synthesis` → `market_context_from_snapshot`
- `decision_engine/migration.attach_decision_to_mis_advisory` → snapshot market + evidence
- `decision_engine/verdict_bridge.resolve_verdict` → prefers cached snapshot for `MarketContext`
- `evidence_engine/migration.attach_synthesis_evidence` → prepends `evidence_items_from_snapshot`
- `DecisionArtifact.metadata["context_snapshot_id"]` set at attach time

---

## Cache policy

| Session state | TTL |
|---------------|-----|
| Market open (`is_open=True`) | 60 seconds |
| Closed / weekend | 86,400 seconds |

Single module-level cache in `context_engine/cache.py`. Legacy `pulse_cache` / `macro_cache` remain until Phase 3 dedup.

---

## Tests

`tests/test_context_engine.py` — snapshot immutability, normalizer, cache thread safety, composer mocks, migration adapters, decision metadata.

Updated consumer tests patch `analyzer.context_engine.build_context_snapshot`.

---

## Rollback

1. Consumers can revert to direct producer imports (git revert consumer files only).
2. `context_engine` package is additive — no producer APIs changed.
3. Cache: `clear_cache()` from `analyzer.context_engine`.

---

## Next steps (Phase 2–3)

1. Migrate `session_advisory`, `morning_briefing`, `market_pulse_scan`, `advisor`.
2. Retire duplicate pulse/macro header fetches.
3. Optional: market breadth adapter when producer exists.
