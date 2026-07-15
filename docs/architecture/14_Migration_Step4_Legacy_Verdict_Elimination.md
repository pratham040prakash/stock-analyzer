# Migration Step 4 — Legacy Verdict Elimination

**Status:** Complete  
**Date:** 2026-07-15  
**Scope:** Eliminate legacy verdict issuers; route all investment recommendations through Decision Engine only.

## Constitutional Rule

Only `analyzer/decision_engine/` may issue canonical verdicts (`ACT`, `WAIT`, `PASS`, `REDUCE`, `DEFENSIVE`).

All other modules produce **evidence** (scores, votes, signals). Legacy UI strings (`BUY`, `HOLD`, `NO_TRADE`, etc.) are mapped from `DecisionArtifact` via `verdict_bridge.py` and `migration.py`.

**Immutable (not modified):** Broker Truth, Evidence Engine public APIs, Decision Engine public interfaces.

**No UI changes.** Backward-compatible legacy fields preserved.

---

## Architecture

```
Signal modules (scores, votes, reasons)
        ↓
EvidenceBuilder → EvidencePacket
        ↓
DecisionEngine.decide()  ← ONLY verdict issuer
        ↓
legacy_*_mapper() → legacy UI string
```

New bridge: `analyzer/decision_engine/verdict_bridge.py`

---

## Migrated Modules

| Module | Legacy field | Bridge hook | Evidence source |
|--------|-------------|-------------|-----------------|
| `signals.py` | `recommendation` | `attach_decision_to_analysis` | composite score + signal details |
| `fundamentals.py` | `recommendation` | `attach_decision_to_fundamental` | composite score + metrics |
| `combined.py` | `combined_recommendation` | `attach_decision_to_combined` | combined/tech/fund scores |
| `candle_narrative.py` | `action` | `attach_decision_to_live_chart` | directional score + reasons + intraday |
| `chart_horizon.py` | `action` | `attach_decision_to_horizon` | horizon score + chart signals |
| `options_signal.py` | `action` | `attach_decision_to_options_verdict` | directional score + reasons |
| `intraday_signals.py` | `trade_setup` | `attach_decision_to_intraday` | intraday signal votes |
| `multi_timeframe.py` | `consensus_action` | `attach_decision_to_mtf_report` | MTF frame actions + net |
| `strategy_synthesis.py` | `verdict` | `attach_decision_to_synthesis` (existing) | strategy pillar votes |
| `mis_trade_advisory.py` | `verdict` | `attach_decision_to_mis_advisory` (existing) | MIS flags/scores |
| `advisor.py` | `final_action` | `attach_decision_to_advice` (existing) | advisor evidence packet |
| `alpha_ai_report.py` | `recommendation` | `attach_decision_to_alpha_report` (existing) | research packet |
| `investment_os.py` | `verdict` | `attach_decision_to_investment_os` | session/plan/synthesis context |
| `daily_advisor.py` | `today_action` | `attach_decision_to_holding_advice` | portfolio/watchlist context |

---

## Removed Verdict Issuers

| Module | Removed function / path | Replaced by |
|--------|----------------------|-------------|
| `signals.py` | `_score_to_recommendation()` direct assignment | `attach_decision_to_analysis` |
| `fundamentals.py` | `_score_to_rec()` direct assignment | `attach_decision_to_fundamental` |
| `combined.py` | `_score_to_rec()` direct assignment | `attach_decision_to_combined` |
| `candle_narrative.py` | `_score_to_equity_action()` as final verdict | `attach_decision_to_live_chart` |
| `chart_horizon.py` | `_action_short()` / `_action_long()` as final verdict | `attach_decision_to_horizon` |
| `options_signal.py` | score threshold → CE/PE/NO TRADE | `attach_decision_to_options_verdict` |
| `intraday_signals.py` | score → BUY/SELL/WAIT | `attach_decision_to_intraday` |
| `multi_timeframe.py` | `_action_from_net()` | `attach_decision_to_mtf_report` |
| `strategy_synthesis.py` | `_verdict_from_score()` | `attach_decision_to_synthesis` |
| `mis_trade_advisory.py` | heuristic fallback TRADE_OK/CAUTION/NO_TRADE | OBSERVE on DE failure only |
| `daily_advisor.py` | `_today_action()` / `_watchlist_today_action()` | `attach_decision_to_holding_advice` |
| `investment_os.py` | inline TRADE OK / NO TRADE heuristic | `attach_decision_to_investment_os` |

---

## Evidence Producers (not verdict issuers)

| Module | Role |
|--------|------|
| `signals.py` | Technical indicator votes |
| `fundamentals.py` | Fundamental metric votes |
| `chart_horizon.py` | Swing/long horizon scores |
| `candle_narrative.py` | Directional score + candle reasons |
| `options_signal.py` | Directional score for CE/PE |
| `intraday_signals.py` | VWAP/OR/EMA/RSI votes |
| `multi_timeframe.py` | Per-frame action votes |
| `strategy_synthesis.py` | Strategy pillar votes |
| `mis_trade_advisory.py` | MIS composite score, flags, gate |
| `evidence_engine/migration.py` | Packet builders from legacy objects |
| `advisor.py` | Heuristic factors → evidence (pre-DE) |
| `daily_advisor.py` | P&L, weight, session context → evidence |
| `investment_os.py` | Session/plan/gate context → evidence |

---

## Legacy Mappers (`verdict_bridge.py`)

| Mapper | Output family |
|--------|---------------|
| `legacy_equity_recommendation` | STRONG BUY / BUY / HOLD / SELL / STRONG SELL |
| `legacy_chart_action` | STRONG BUY / BUY / WAIT / SELL / STRONG SELL |
| `legacy_short_horizon_action` | STRONG BUY / BUY / WATCH / AVOID / WEAK / NEUTRAL |
| `legacy_long_horizon_action` | CORE BUY / ACCUMULATE / HOLD / AVOID / WATCH |
| `legacy_options_action` | STRONG CE / BUY CE / STRONG PE / BUY PE / NO TRADE |
| `legacy_intraday_setup` | BUY / SELL / WAIT |
| `legacy_mtf_consensus` | MTF consensus action |
| `legacy_daily_holding_action` | TRIM / EXIT / REDUCE / HOLD / ADD |
| `legacy_watchlist_action` | AVOID / BUY WATCH / INTRADAY WATCH / MONITOR |
| `legacy_investment_os_verdict` | PREP / CLOSED / TRADE OK / NO TRADE / WAIT |
| `legacy_synthesis_verdict` (migration.py) | STRONG_BUY / BUY / WAIT / NO_TRADE / CAUTION |
| `legacy_advisor_action` (migration.py) | STRONG BUY / BUY / ACCUMULATE / HOLD / REDUCE / AVOID |
| `legacy_mis_verdict` (migration.py) | TRADE_OK / CAUTION / NO_TRADE / OBSERVE |

---

## Remaining Exceptions

| Module | Exception | Rationale |
|--------|-----------|-----------|
| `evidence_engine/engine.py` | `recommend_from_packet()` still emits STRONG_BUY/NO_TRADE | **Immutable** Evidence Engine; output is `RecommendationFromEvidence` used as evidence hint only — UI verdicts come from Decision Engine attach hooks |
| `evidence_engine/migration.py` | `build_synthesis_packet()` calls `recommend_from_packet` | Immutable; `recommendation_from_evidence` is not displayed as final verdict |
| `investment_os.py` | `PREP` / `CLOSED` set before DE | Operational session status, not investment recommendation |
| `options_entry_gate.py` | prose gate actions | Entry gate coaching — not trade verdict |
| `sideways_options_advisor.py` | directional blocks | Options coaching — evidence input to synthesis |
| `market_pulse_scan.py` | index options scan actions | **Not migrated in Step 4** — consumes migrated `combined`/`candle_narrative` upstream; scan-layer actions remain for Market Pulse UI (next pass) |
| `affordable_invest.py` | options action helper | **Not migrated** — thin wrapper over scan results |
| `intraday_watchlist.py` | BUY/SELL action column | **Not migrated** — uses migrated upstream signals |
| `market_regime.py` | `apply_regime_to_action` | Regime adjustment helper — not primary verdict path |
| `global_impact.py` | BULLISH/BEARISH bias | Macro bias — evidence input, not trade verdict |
| `relative_strength.py` | Outperforming/Underperforming | Relative strength label — evidence |
| `advisor.py` | `_resolve_action` heuristic | Runs before DE; `final_action` overwritten by `attach_decision_to_advice` |
| Error paths | `ERROR`, `—` | Non-verdict error states |

---

## Tests

- `tests/test_migration_step4.py` — legacy mappers, bridge wiring, architecture guard
- `tests/test_decision_engine.py` — existing Step 3 suite (30 tests)

Run:

```bash
python -m unittest tests.test_migration_step4 tests.test_decision_engine -q
```

---

## Backward Compatibility

- All UI pages unchanged; they read the same legacy field names.
- Legacy strings may differ slightly when Decision Engine thresholds differ from old heuristics — this is intentional (single source of truth).
- On Decision Engine failure: safe fallbacks (`HOLD`, `WAIT`, `OBSERVE`, `PREP`, `CLOSED`) — never heuristic BUY.

---

## Next Steps (out of scope)

- Migrate `market_pulse_scan.py`, `affordable_invest.py` scan-layer verdicts
- Deprecate `recommend_from_packet` consumers when Evidence Engine allows extension
- Context Engine (Step 5+)
