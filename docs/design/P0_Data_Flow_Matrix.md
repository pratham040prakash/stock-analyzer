# P0 Data Flow Matrix

**Milestone:** Data-flow restoration only (no new UI, no legacy cards, no orphan mounts).  
**Break origin:** `0240c3f` — partner canvas removed Home card consumers; `b157bb7` partial reconnect.  
**Pipeline:** `Engine → load_dashboard_data() → DTO (TodayCommandCenter + verdict helpers) → existing renderer → visible UI`

**Status legend:** `Rendered` · `Hidden` (popover/overlay/dock) · `Dropped` · `Fallback`

---

## Loader bundle (`load_dashboard_data`)

| Field | Loader | DTO | Renderer | Status |
|-------|--------|-----|----------|--------|
| `snapshot` | ✓ | `ContextSnapshot` | Verdict + Today intel | Rendered |
| `mis` | ✓ | passed through | Verdict + Today intel | Rendered |
| `os_report` | ✓ | passed through | Today intel + mentor | Rendered (partial modules) |
| `pins` | ✓ | `OpportunityView[]` | Opportunity, Next watch, Why | Rendered |
| `pulse` | ✓ | confidence/price/what_to_do | Opportunity, Market | Rendered |
| `portfolio` | ✓ | portfolio lines | Portfolio block | Rendered |
| `prefs` | ✓ | sizing math | Portfolio, Do next | Rendered |
| `journal_today_pnl` | ✓ | portfolio metrics | Portfolio block | **Rendered** (restored) |
| `learning` | ✓ | — | You/Trust dock only | Hidden on Today |
| `built_at` | ✓ | verdict header | Verdict canvas | Rendered |

---

## Context Engine

| Field | Consumer | Status |
|-------|----------|--------|
| `risk_mode`, `trading_restrictions` | Verdict gates, Risk, Why, Market | Rendered |
| `market_regime`, `market_phase`, `volatility_state` | Market gate | Rendered |
| `market_breadth`, `liquidity_state` | Market gate | **Rendered** (restored) |
| `industry_strength.leader` | Market gate | **Rendered** (restored) |
| `metadata.allow_new_entries` | Market support | Rendered |
| `confidence` | Decision conf fallback, Why caption | Rendered |
| `sector_strength` | via InvestmentOS sector module | Rendered (indirect) |
| `macro_state`, `global_market_state` | via InvestmentOS market module | Fallback (partial clause) |
| `snapshot_id`, `context_hash` | internal | Hidden |

---

## InvestmentOS

| Field / module | Consumer | Status |
|----------------|----------|--------|
| `next_step` | Do next, mentor fallback | Rendered |
| `starred_symbol` | Opportunity pick, mentor | Rendered |
| `max_loss_inr`, `goal_inr` | Do next sizing | **Rendered** (max_loss restored; goal via next_step) |
| `verdict`, `can_trade` | — | Dropped (no existing Today consumer; not mounting orphan UI) |
| `decision_artifact` | Verdict, Why, mentor | Rendered when attached |
| **market** module | Market support | Fallback → **Rendered** (detail clause) |
| **sector** module | Market support suffix | **Rendered** (restored) |
| **stock** module | Opportunity selection_reason | Rendered |
| **strategy** module | selection_reason | **Rendered** (detail, not headline-only) |
| **risk** module | Portfolio lines, size blocked | Rendered |
| **execution** module | Opportunity entry_direction, selection_reason | **Rendered** (restored) |
| **review** module | Do next (Rest) | **Rendered** (restored) |
| `deep` / strategy_synthesis | — | Hidden on Home (`deep=False` by design) |

---

## Decision Engine (`DecisionArtifact`)

| Field | Consumer | Status |
|-------|----------|--------|
| `verdict` | Verdict state mapper | Fallback when Rest (rule override) |
| `confidence` | Why popover caption | **Rendered** (restored) |
| `reason` | mentor | Fallback (explainability preferred) |
| `explainability.why` | mentor, Do next pause | **Rendered** (restored) |
| `explainability.why_now/why_not` | — | Dropped (no pre-0240c3f Today consumer) |
| evidence packet | Why popover | Rendered |
| `capital_recommendation` | Why popover | **Rendered** (restored) |
| `execution_recommendation` | Why popover | **Rendered** (restored) |
| `invalidation_conditions` | Why popover | **Rendered** (restored) |
| `alternative_actions`, `uncertainty` | — | Dropped (no existing consumer) |
| Entry/stop/target levels | Opportunity (pins + execution module) | **Rendered** (via existing Opportunity block) |

---

## MIS Trade Advisory

| Field | Consumer | Status |
|-------|----------|--------|
| `flags` | Risk, Why | Rendered |
| `loss_streak_days` | Verdict pause, Risk | Rendered |
| `synthesis_pillars` | Why popover fallback | **Rendered** (restored) |
| `summary` | mentor, Do next pause | **Rendered** (restored) |
| `synthesis_summary` | Risk block | **Rendered** (restored) |
| `mtf_summary`, `flow_summary` | Risk block | **Rendered** (restored) |
| `headline`, `emoji`, `verdict`, `score` | Live Options tab strip | Hidden on Today |
| options `decision_artifact` | — | **Blocked** from equity Home pick (restored) |
| equity `decision_artifact` | Verdict, Why | Rendered |

---

## Market Pulse (cache on Home)

| Field | Consumer | Status |
|-------|----------|--------|
| `stock_map[].combined_score` | Opportunity confidence | Rendered (55 default if missing = Fallback) |
| `stock_map[].price`, `ltp_source` | price_status | Rendered |
| `stock_map[].what_to_do` | price_status suffix | **Rendered** (restored) |
| indices, macro, picks, options pulse | Market Pulse tab | Hidden on Home |

---

## Pulse Engine (`run_market_pulse_scan`)

| Output | Consumer | Status |
|--------|----------|--------|
| Fresh scan | Market Pulse tab / prep | Hidden on Home (cache read only — pre-break behavior) |

---

## Portfolio / Broker

| Field | Consumer | Status |
|-------|----------|--------|
| holdings, exposure, allocation | Portfolio block | **Rendered** (restored) |
| journal today P/L | Portfolio block | **Rendered** (restored) |
| health label + detail | Portfolio block | **Rendered** (restored) |
| weakest / strongest | Portfolio block | **Rendered** (restored) |
| `BrokerSnapshot` sync/holdings | Risk block, verdict sync dot | **Rendered** (restored detail in Risk) |

---

## Pins

| Field | Consumer | Status |
|-------|----------|--------|
| entry/stop/target/side | Opportunity, Next watch, Why | Rendered |

---

## Learning / Track Record

| Field | Consumer | Status |
|-------|----------|--------|
| `learning` outcomes | You/Trust canvases, Track Record tab | Hidden on Today (pre-break) |

---

## Suggestions / Daily Advisor / Alpha AI

| Engine | Consumer | Status |
|--------|----------|--------|
| Full scan engines | Suggestions tab | Hidden on Home (nav only) |
| Daily Advisor | Daily Advisor tab | Hidden on Home |
| Alpha AI | Alpha AI tab / Review setup nav | Hidden on Home |

---

## Today Intelligence DTO → existing blocks

| DTO field | Block | Status |
|-----------|-------|--------|
| `opportunity_name`, `entry_direction`, `selection_reason`, `price_status` | Opportunity | Rendered |
| `market_gate`, `market_support` | Market | Rendered |
| `portfolio_lines` | Portfolio | Rendered |
| `risk_warnings` | Risk | Rendered |
| `next_watch` | Next watch | Rendered (watch bullets restored) |
| `ai_recommendation` | Do next | Rendered |

---

## Verdict Canvas (existing)

| Input | Consumer | Status |
|-------|----------|--------|
| mentor | verdict zone | Rendered |
| why_bullets + confidence | Why popover | Rendered |
| sync status | header | Rendered |

---

## Remaining `Dropped` (post-P0, deferred)

| Item | Reason |
|------|--------|
| InvestmentOS `verdict`/`can_trade` on Today | No existing consumer without orphan UI mount |
| Decision `why_now`/`why_not`, `uncertainty`, `alternative_actions` | No pre-0240c3f Today consumer |
| Pulse indices/macro/full report on Home | Canonical consumer = Market Pulse tab |
| `learning` on Today dock | Canonical consumer = You/Trust |
| Proof overlay body (if still empty live) | Needs separate render investigation — not data pass-through |
| Equity DecisionArtifact when session closed | Engine attach gate (`star AND session_open`) — engine-layer, not UI |

---

## Files changed (P0)

- `ui/components/dashboard_pipeline.py` — shared loader→DTO helpers
- `ui/components/home_dashboard.py` — pick decision, why/mentor, confidence, pass-through
- `ui/components/today_intelligence.py` — full cache→DTO wiring
- `tests/test_data_flow_restoration.py` — pipeline contracts
