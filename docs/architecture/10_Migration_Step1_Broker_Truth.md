# 10 — Migration Step 1: Broker Truth

**Status:** Implemented  
**Constitution:** [08_Final_Investment_OS_Architecture.md](./08_Final_Investment_OS_Architecture.md)  
**Mapping:** [09_Codebase_to_Architecture_Mapping.md](./09_Codebase_to_Architecture_Mapping.md) — P0 item #1  
**Scope:** Migration Step 1 only — no further migrations in this change

---

## Goal

Stop learning from simulated coach/EOD outcomes when real Zerodha executions exist. **Broker Truth** is the single source of truth for completed trades.

---

## What was added

### Package: `analyzer/broker_truth/`

| Module | Role |
|--------|------|
| `models.py` | `TradeRecord`, `PlannedTrade`, `BrokerOrder`, `BrokerTradeFill`, `ReconciliationResult` |
| `store.py` | SQLite persistence (`data/broker_truth/broker_truth.db`) |
| `service.py` | `BrokerTruthService` — import from Kite, build `TradeRecord` |
| `planned.py` | Load planned trades from snapshots/pins (never overwritten) |
| `reconciliation.py` | `ReconciliationService` — planned vs executed |
| `learning.py` | Learning adapter — broker primary, coach fallback |
| `__init__.py` | Public exports |

### Data store

- **Path:** `data/broker_truth/broker_truth.db`
- **Tables:** `broker_orders`, `broker_trade_fills`, `broker_trade_records`, `broker_positions`, `broker_holdings`, `broker_reconciliation`, `broker_sync_runs`

### Canonical `TradeRecord` fields

| Field | Source |
|-------|--------|
| `trade_id` | Generated `{date}:{symbol}:{product}:{side}:{seq}` |
| `symbol`, `exchange`, `product`, `side` | Kite fills |
| `strategy` | Derived from product (e.g. MIS) |
| `entry_time`, `exit_time` | Fill timestamps |
| `entry_price`, `exit_price` | Paired FIFO fills |
| `quantity` | Matched lot size |
| `broker_charges` | Order charges when present (else 0) |
| `realized_pnl` | Computed from entry/exit × qty |
| `holding_period_minutes` | Entry → exit duration |
| `order_ids` | Linked order IDs |
| `execution_status` | `COMPLETE` / `PARTIAL` / `OPEN` |
| `tags`, `notes` | Metadata |
| `planned_id` | Set by reconciliation only — **does not mutate plan** |
| `source` | `kite_api` |
| `synced_at` | Import timestamp |

### Planned vs executed separation

| Type | Storage | Rule |
|------|---------|------|
| **PlannedTrade** | `watchlist_daily_snapshots`, `pinned_watchlist.json` | Loaded read-only via `load_planned_trades()` |
| **TradeRecord** | `broker_trade_records` | Written only by `BrokerTruthService` |
| **Reconciliation** | `broker_reconciliation` | Compares both; never overwrites planned values |

---

## Learning changes (backward compatible)

| Module | Change |
|--------|--------|
| `watchlist_learning.py` | `fetch_pick_features()` → broker truth adapter |
| `watchlist_learning.py` | `run_watchlist_learning_cycle()` → syncs broker before scoring |
| `confidence_calibration.py` | Uses `resolve_learning_outcomes()` (broker when available) |
| `options_watchlist_learning.py` | Syncs broker before cycle; options still use premium EOD fallback* |
| `eod_learning.py` | Step 1: `sync_broker_truth_for_learning()`; reports broker stats |

\* Options FNO symbol matching to broker fills is a follow-up; equity MIS is fully covered.

### Outcome resolution priority

```text
For each (trade_date, symbol):
  1. If broker TradeRecord exists → outcome from realized_pnl
  2. Else → coach/watchlist_eod outcome (legacy fallback)
```

### P&L → legacy outcome mapping

| Realized P&L | Outcome label |
|--------------|---------------|
| > ₹1 | `target_hit` |
| < −₹1 | `stop_hit` |
| otherwise | `flat` |

Preserves existing `WIN_OUTCOMES` / `LOSS_OUTCOMES` tuning logic.

---

## Reconciliation outputs

`ReconciliationService.reconcile_session(trade_date)` produces per plan:

| Metric | Description |
|--------|-------------|
| `slippage_entry` | Actual entry − planned entry (side-adjusted) |
| `slippage_exit` | Actual exit − planned target |
| `execution_quality` | `good` / `loss_controlled` / `poor_entry_slippage` / `missed` |
| `missed_entry` | Plan existed, no broker match |
| `partial_fill` | From execution status |
| `stop_adherence` | `stop_hit` / `worse_than_stop` / `held_or_profit` |

---

## Usage

### Sync broker truth (requires Kite login)

```python
from analyzer.broker_truth import BrokerTruthService, ReconciliationService

svc = BrokerTruthService()
result = svc.sync_session()  # today's session
trades = svc.get_completed_trades(trade_date="2026-07-15")

recon = ReconciliationService(svc)
report = recon.run_full_reconciliation("2026-07-15")
```

### Learning (automatic)

Post-close scripts and `run_eod_learning_cycle()` now call `sync_broker_truth_for_learning()` automatically.

### Check learning source mix

```python
from analyzer.broker_truth.learning import learning_source_stats

learning_source_stats(days=14)
# → {"total": 12, "broker": 8, "coach_fallback": 4, "broker_pct": 66.7}
```

---

## Tests

```bash
python -m unittest tests.test_broker_truth -v
```

Covers: fill pairing, Kite mock sync, reconciliation, broker-over-coach learning priority, planned trade loading.

---

## What did NOT change (intentional)

- UI tabs and flows — unchanged
- `watchlist_eod.score_session_plan()` — still runs for coach diagnostics / Telegram
- `suggestion_validator` — still validates journal suggestions via Yahoo (separate horizon)
- No auto-trading
- No removal of coach logs

---

## Next migrations (not in this step)

| Step | Item |
|------|------|
| 2 | Daily loss dam veto in Capital Engine |
| 3 | Evidence packet schema on Judgment Engine |
| 4 | Options FNO broker matching |
| 5 | Broker divergence KPI on Home / Track Record UI |

---

## Operational notes

1. **Kite token required** for broker sync. If not connected, learning falls back to coach/EOD (same as before).
2. **Kite API** returns today's orders/trades only — sync runs at EOD to capture the session.
3. **Console P&L** remains the user's ground truth for wealth; broker_truth.db is the system's learning truth.
4. Planned trades and executed trades are stored in **separate tables** — reconciliation links via `planned_id` on the executed side only.

---

*Migration Step 1 complete. Learning now prefers broker executions when Kite is connected.*
