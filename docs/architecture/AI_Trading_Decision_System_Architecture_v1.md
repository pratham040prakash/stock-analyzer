# AI Trading Decision System — Product Architecture v1.0

**Document type:** Final product design artifact — foundation for next-generation development  
**Version:** 1.0  
**Date:** 2026-07-16  
**Status:** Canonical blueprint — **no implementation in this document**  
**Authors:** CPO · Chief UX · Principal Architect (design intent)  
**Audience:** Product, design, engineering, leadership  
**Supersedes:** Dashboard-first product identity (Stock Analyzer, Investment OS)  
**Companion docs:** `AI_Trading_Decision_System_UX.md` (presentation layer), `WOW_Experience_Redesign.md` (experience north star)

---

## How to use this document

This is the **constitution and blueprint** for the AI Trading Decision System for the next several years. It defines:

- **What** the product is and is not  
- **Why** it exists  
- **How** decisions flow from raw reality to user-facing recommendation  
- **Where** every screen gets its truth (one object: `TradingDecision`)  
- **When** each lifecycle phase applies  
- **Who** we build for  

Engineering may refactor internals. UX may evolve visuals. **TradingDecision and the decision pipeline are invariant** unless this document is explicitly revised.

---

# 1. Vision

## 1.1 Statement

> **An AI Trading Partner that absorbs market complexity, understands your real portfolio, and tells you — calmly and clearly — the single smartest thing to do right now.**

## 1.2 Long-term north star

The application evolves from **decision advisor** → **decision partner** → **guarded autonomous co-pilot**:

| Era | Capability | User relationship |
|-----|------------|-------------------|
| **v1 (now)** | Recommends; user executes on Zerodha | Trusted mentor |
| **v2** | Monitors open trades; nudges at review times | Active partner |
| **v3** | Pre-staged orders with human confirm | Co-pilot |
| **v4+** | Policy-bound autonomous execution (opt-in) | AI trading partner |

v1 architecture **must not block** v4, but v1 **must not pretend** to be autonomous.

## 1.3 Strategic bet

Retail traders fail not from lack of data but from **decision fatigue**, **portfolio blindness**, and **inconsistent risk discipline**. We win by being the system that **thinks once, clearly, on their behalf** — and proves it was right over time.

## 1.4 What success looks like in 3 years

- User opens app → knows what to do in **< 20 seconds** — **90% of trading days**
- **Trust score** (user-reported) correlates with continued use after first loss week
- **Hit rate** on high-conviction calls is trackable and published internally
- Zerodha portfolio is connected for **> 80%** of active users
- Product is described by users as *"my trading brain"* — never as *"a screener"*

---

# 2. Mission

**Help traders make better trading decisions so they can grow their wealth while protecting capital.**

### Mission decomposition

| Pillar | Meaning | Measurable proxy |
|--------|---------|------------------|
| **Better decisions** | Fewer impulsive trades; better timing | Hit rate on high-conviction calls |
| **Grow wealth** | Compound via edge + discipline | User P&L vs baseline (self-reported + broker) |
| **Protect capital** | Survive bad days/weeks | Max drawdown guidance adherence |
| **Reduce thinking** | Cognitive load ↓ | Time-to-decision < 20s |

---

# 3. Product Promise

When the user opens the application every morning, within **20 seconds** they know:

| # | Question | Valid answer format |
|---|----------|-------------------|
| 1 | **Should I trade today?** | Yes / Wait / No — one word headline |
| 2 | **If yes, what should I trade?** | One instrument (or "nothing worth trading") |
| 3 | **Exactly how should I trade it?** | If/then trigger · entry · stop · target · size |
| 4 | **Why is this the best decision?** | ≤ 3 bullets in plain English (optional expand) |
| 5 | **Can I safely close the application now?** | Explicit release: "You're done" / "Come back at X" |

If there is nothing worth doing, the application **must confidently say so** — and **must not** manufacture engagement.

---

# 4. Product Philosophy

## 4.1 Core identity

| This product is NOT | This product IS |
|---------------------|-----------------|
| A dashboard | A decision surface |
| A stock screener | A conviction filter (0–2 ideas/day) |
| A reporting tool | A forward-looking recommendation engine |
| An analytics platform | A clarity engine |
| A chart viewer | A mentor that uses charts only when needed |

## 4.2 The supreme principle

> **The application must THINK. The user should not.**

The system ingests:

- Today's market (session, regime, macro, news, global spillover)
- User's Zerodha portfolio (holdings, sectors, P&L, cash)
- Available capital and margin
- Existing positions and open trades
- Risk limits and loss streaks
- Trading history and learning history
- Sector exposure and correlation
- User behaviour patterns

It returns: **one primary recommendation** per active decision context.

## 4.3 Complexity absorption rule

For every input dimension, the user sees **at most one synthesized sentence** in the default view. Details are opt-in.

## 4.4 Inaction is a first-class output

`WAIT`, `PASS`, `HOLD`, and **"close the app"** are successful outcomes — not empty states.

## 4.5 Portfolio-aware by default

**Never recommend a trade in isolation.** Every trade recommendation passes through **Portfolio Impact Analysis** — even if the answer is "you're already exposed."

## 4.6 Accountability builds trust

Every decision is recorded, scored against reality, and fed back into future decisions — without exposing "learning engine" language to users.

---

# 5. Product Constitution

Immutable rules. Changes require explicit product architecture revision.

### Article I — Single source of truth

**Every recommendation shown to the user MUST originate from a `TradingDecision` object.** No page, component, or script may invent an independent buy/sell/wait verdict.

### Article II — One primary recommendation

Each screen shows **one** primary recommendation. Secondary alternatives exist in `TradingDecision` but are collapsed by default.

### Article III — Recommendation before explanation

UI order is invariant: **Verdict → Reason → Plan → Action → Evidence (optional)**.

### Article IV — No engine exposure

Users never see: engine names, packet IDs, module keys, calibration metrics, or architecture diagrams in default UI.

### Article V — Zerodha truth for money

P&L, fills, holdings, and order state: **Zerodha is authoritative**. The system advises; the broker settles.

### Article VI — Capital protection precedence

When risk and reward conflict, **risk wins** unless user has explicitly overridden in Settings (with warning).

### Article VII — Immutable decision record

Once published to the user, a `TradingDecision` is **append-only**. Revisions create a new decision with `supersedes_id` — never silent mutation.

### Article VIII — Release permission

Every session must end with either an **action** or explicit **permission to stop**.

### Article IX — Human execution (v1)

v1 never places orders without explicit human action in Zerodha.

### Article X — Honest uncertainty

When conviction is low, the system says so and recommends smaller size or waiting — never false confidence.

---

# 6. User Personas

## 6.1 Primary — Active MIS equity trader (Pratham archetype)

| Attribute | Detail |
|-----------|--------|
| **Goal** | Consistent daily income without blowing up |
| **Broker** | Zerodha Kite |
| **Session** | 9:15–15:30 IST; peaks 9:45–11:30 |
| **Pain** | Too many scanners; unclear sizing; revenge trading |
| **Success** | Opens app → one plan → executes → closes |
| **Decision frequency** | 1–2 trades/day max |

## 6.2 Secondary — Swing / positional holder

| Attribute | Detail |
|-----------|--------|
| **Goal** | Grow ₹10 Cr corpus; trim losers; add on dips |
| **Horizon** | Days to years |
| **Pain** | Portfolio drift; when to add/trim |
| **Primary screens** | Morning Brief (hold/trim) · Portfolio · Ask AI |

## 6.3 Secondary — Options intraday trader

| Attribute | Detail |
|-----------|--------|
| **Goal** | Index/single-stock options with defined risk |
| **Pain** | Theta, ORB timing, premium richness |
| **Primary screens** | Morning Brief · Trade Plan (options leg) |

## 6.4 Tertiary — Long-term investor (research mode)

| Attribute | Detail |
|-----------|--------|
| **Goal** | Quality businesses; 3-year view |
| **Pain** | Valuation timing |
| **Primary screens** | Ask AI (deep) · Portfolio |

## 6.5 Anti-persona — Data tourist

Wants 50 scanners, heatmaps, and charts without acting. **We do not optimize for this user.** Advanced tools exist but are not the product.

---

# 7. User Decision Journey

## 7.1 Lifecycle phases

```
┌─────────────┐
│ Before      │  Prior night: picks saved, briefing staged
│ Market      │
└──────┬──────┘
       ▼
┌─────────────┐
│ Market Open │  Opening range · WAIT rules · context refresh
└──────┬──────┘
       ▼
┌─────────────┐
│ Trade       │  TradingDecision published → Morning Brief
│ Planning    │
└──────┬──────┘
       ▼
┌─────────────┐
│ Trade       │  User executes on Zerodha (external)
│ Execution   │
└──────┬──────┘
       ▼
┌─────────────┐
│ Monitoring  │  Review time triggers · invalidation checks
└──────┬──────┘
       ▼
┌─────────────┐
│ Exit        │  Stop/target hit · time stop · manual exit
└──────┬──────┘
       ▼
┌─────────────┐
│ End of Day  │  Score decisions · journal · learning ingest
│ Review      │
└──────┬──────┘
       ▼
┌─────────────┐
│ Weekend     │  Weekly trust score · behaviour review
│ Review      │
└──────┬──────┘
       ▼
┌─────────────┐
│ Monthly     │  Performance vs benchmark · risk adherence
│ Performance │
└─────────────┘
```

## 7.2 Phase specifications

### Before market (prior day 15:30 – today 9:00)

| Activity | System behaviour | User sees |
|----------|------------------|-----------|
| Post-close scan | Generate candidate setups for tomorrow | Nothing required (autopilot) |
| Staging | Create draft `TradingDecision` (status: `STAGED`) | Optional: "Tomorrow's watchlist ready" |
| Pre-market refresh | Update macro/global; validate picks still valid | Morning Brief (pre-open variant) |

### Market open (9:15–9:45)

| Activity | System behaviour | User sees |
|----------|------------------|-----------|
| Opening range | Observe; suppress ACT unless exceptional | "Wait until 9:45" |
| Context refresh | Recompute `TradingDecision` | Updated Morning Brief |

### Trade planning (9:45+)

| Activity | System behaviour | User sees |
|----------|------------------|-----------|
| Publish decision | `TradingDecision` status → `ACTIVE` | Morning Brief headline |
| Drill-down | Trade Plan = execution view of same decision | Entry/stop/size |

### Trade execution

| Activity | System behaviour | User sees |
|----------|------------------|-----------|
| Human order | User trades on Kite | Optional: "Log trade" |
| Link trade | Associate Zerodha order ID if available | Confirmation |

### Monitoring

| Activity | System behaviour | User sees |
|----------|------------------|-----------|
| Review time | Trigger at `review_time` | Push/Telegram: "Check RELIANCE" |
| Invalidation | Price violates condition | "Setup invalidated — stand down" |

### Exit

| Activity | System behaviour | User sees |
|----------|------------------|-----------|
| Stop/target | Broker truth detects fill | Results update |
| Time stop | Session hard stop (e.g. 15:10 MIS) | "Exit before close" |

### End of day (15:30+)

| Activity | System behaviour | User sees |
|----------|------------------|-----------|
| Score | Compare plan vs session OHLC | Results: hit/stop/miss |
| Learn | Ingest outcome into behaviour model | Nothing (internal) |

### Weekend review

| User question | Answer source |
|---------------|---------------|
| Can I trust this system? | `Decision History` aggregate |

### Monthly performance

| User question | Answer source |
|---------------|---------------|
| Am I growing wealth safely? | P&L + risk adherence + decision quality |

---

# 8. TradingDecision Domain Model

## 8.1 Purpose

`TradingDecision` is the **canonical domain object** — the single source of truth for all recommendations. Every screen is a **view** over one or more `TradingDecision` instances.

### Relationship to existing `DecisionArtifact`

Today the codebase has `DecisionArtifact` (decision engine). **Migration path:**

- `TradingDecision` **wraps and extends** `DecisionArtifact` — it does not duplicate verdict logic.
- `DecisionArtifact` remains the verdict authority internally.
- `TradingDecision` adds: portfolio impact, execution plan, NL summary, lifecycle state, broker actions, and view-specific projections.
- **Rule:** UI reads `TradingDecision` only — never raw engine outputs.

## 8.2 Entity diagram (conceptual)

```
TradingDecision
├── Identity & lifecycle
├── Classification (type, priority, confidence)
├── Context bundle (market, portfolio, risk, capital, behaviour)
├── Instrument & levels
├── Risk/reward & sizing
├── Reasoning & evidence (user-safe)
├── Execution & post-trade plans
├── Broker integration
├── Natural language projections
└── Learning & outcome (filled post-hoc)
```

## 8.3 Full schema

### 8.3.1 Identity & lifecycle

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `decision_id` | `UUID` | ✓ | Immutable identifier |
| `decision_version` | `string` | ✓ | Schema version (e.g. `TD-1.0`) |
| `timestamp` | `ISO8601` | ✓ | When decision was computed |
| `valid_from` | `ISO8601` | ✓ | When recommendation becomes actionable |
| `valid_until` | `ISO8601` | ○ | Expiry (session end, invalidation) |
| `status` | `enum` | ✓ | `STAGED` · `ACTIVE` · `SUPERSEDED` · `INVALIDATED` · `COMPLETED` · `EXPIRED` |
| `supersedes_id` | `UUID` | ○ | Prior decision this replaces |
| `session_date` | `date` | ✓ | Trading session (IST) |
| `user_id` | `string` | ○ | Zerodha user / profile key |

### 8.3.2 Classification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `decision_type` | `enum` | ✓ | See §8.4 |
| `priority` | `enum` | ✓ | `PRIMARY` · `SECONDARY` · `WATCH_ONLY` · `INFORMATIONAL` |
| `conviction` | `enum` | ✓ | `HIGH` · `MEDIUM` · `LOW` |
| `conviction_numeric` | `float` | ○ | Internal 0–100 — **not shown in default UI** |
| `scope` | `enum` | ✓ | `SESSION` · `SWING` · `POSITIONAL` · `PORTFOLIO` · `INSTRUMENT` |

### 8.3.3 Market context (embedded)

| Field | Type | Description |
|-------|------|-------------|
| `market_context.session` | `enum` | `PRE_OPEN` · `OPEN` · `CLOSED` · `HOLIDAY` |
| `market_context.phase` | `string` | e.g. opening hour, mid-day, last hour |
| `market_context.bias` | `enum` | `BULLISH` · `BEARISH` · `NEUTRAL` · `CHOPPY` |
| `market_context.timing_rule` | `string` | NL: "Wait until 9:45 AM" |
| `market_context.macro_note` | `string` | One sentence macro |
| `market_context.news_note` | `string` | One sentence news catalyst if any |
| `market_context.global_note` | `string` | One sentence global spillover |
| `market_context.trading_allowed` | `bool` | Master gate |

### 8.3.4 Portfolio context (embedded)

| Field | Type | Description |
|-------|------|-------------|
| `portfolio_context.connected` | `bool` | Zerodha sync active |
| `portfolio_context.holdings_count` | `int` | |
| `portfolio_context.total_value_inr` | `float` | |
| `portfolio_context.unrealized_pnl_inr` | `float` | |
| `portfolio_context.cash_available_inr` | `float` | |
| `portfolio_context.sector_exposure` | `map<sector, pct>` | |
| `portfolio_context.duplicate_exposure` | `bool` | True if recommended symbol already held |
| `portfolio_context.correlation_warning` | `string` | NL warning if correlated to existing book |
| `portfolio_context.portfolio_health` | `enum` | `HEALTHY` · `NEEDS_REVIEW` · `HIGH_RISK` |
| `portfolio_context.impact_summary` | `string` | NL: "Adds 5% IT exposure — acceptable" |

### 8.3.5 Risk context (embedded)

| Field | Type | Description |
|-------|------|-------------|
| `risk_context.daily_loss_cap_inr` | `float` | |
| `risk_context.daily_loss_used_inr` | `float` | |
| `risk_context.loss_streak_days` | `int` | |
| `risk_context.max_trades_today` | `int` | |
| `risk_context.trades_taken_today` | `int` | |
| `risk_context.risk_reward_ratio` | `float` | |
| `risk_context.behaviour_flags` | `list<string>` | Internal codes |
| `risk_context.behaviour_warning` | `string` | NL: "Three losing days — sit out" |
| `risk_context.block_reason` | `string` | If trade blocked |

### 8.3.6 Capital context (embedded)

| Field | Type | Description |
|-------|------|-------------|
| `capital_context.trading_capital_inr` | `float` | |
| `capital_context.allocated_inr` | `float` | For this decision |
| `capital_context.risk_per_trade_inr` | `float` | |
| `capital_context.margin_available_inr` | `float` | From Kite if available |
| `capital_context.allocation_pct` | `float` | % of capital at risk |

### 8.3.7 Instrument

| Field | Type | Description |
|-------|------|-------------|
| `instrument.symbol` | `string` | NSE symbol |
| `instrument.exchange` | `string` | NSE/BSE |
| `instrument.asset_class` | `enum` | `EQUITY` · `INDEX_OPTION` · `STOCK_OPTION` |
| `instrument.side` | `enum` | `LONG` · `SHORT` · `BUY_CE` · `BUY_PE` · `SELL` (exit) |
| `instrument.alternative` | `Instrument?` | Second-choice instrument |
| `instrument.invalidation_price` | `float` | Setup dies below/above this |

### 8.3.8 Levels & sizing

| Field | Type | Description |
|-------|------|-------------|
| `entry.type` | `enum` | `MARKET` · `LIMIT` · `TRIGGER` · `RANGE` |
| `entry.price` | `float` | |
| `entry.condition` | `string` | NL: "If breaks ₹2,850 after 9:45" |
| `stop_loss.price` | `float` | |
| `stop_loss.type` | `enum` | `HARD` · `TRAILING` · `TIME` |
| `target.price` | `float` | |
| `target.type` | `enum` | `FIXED` · `SCALE_OUT` |
| `quantity.shares` | `int` | |
| `quantity.lots` | `int` | Options |
| `quantity.rationale` | `string` | NL sizing explanation |

### 8.3.9 Risk / reward

| Field | Type | Description |
|-------|------|-------------|
| `expected_risk_inr` | `float` | |
| `expected_reward_inr` | `float` | |
| `expected_outcome` | `enum` | `ASYMMETRIC_WIN` · `BALANCED` · `UNFAVORABLE` |
| `time_horizon` | `enum` | `INTRADAY` · `SWING` · `POSITIONAL` |
| `review_time` | `ISO8601` | When to re-check |
| `time_stop` | `ISO8601` | Must exit by |

### 8.3.10 Reasoning (user-safe)

| Field | Type | Description |
|-------|------|-------------|
| `reasoning.summary` | `string` | ≤ 2 sentences |
| `reasoning.why_now` | `string` | |
| `reasoning.why_not` | `string` | What we're avoiding |
| `reasoning.supporting_points` | `list<string>` | Max 6 bullets (user language) |
| `reasoning.behaviour_warnings` | `list<string>` | Max 3 |
| `reasoning.historical_analog` | `string` | "Similar setup last Tuesday worked" |
| `reasoning.evidence_refs` | `list<UUID>` | Internal IDs — **not shown to user** |

### 8.3.11 Execution plan

| Field | Type | Description |
|-------|------|-------------|
| `execution_plan.steps` | `list<string>` | Ordered NL steps |
| `execution_plan.pre_conditions` | `list<string>` | |
| `execution_plan.post_entry` | `list<string>` | Trail stop, scale out rules |
| `execution_plan.broker_order_type` | `string` | MIS/CNC/NRML suggestion |
| `execution_plan.product` | `enum` | `MIS` · `CNC` · `NRML` |

### 8.3.12 Post-trade plan

| Field | Type | Description |
|-------|------|-------------|
| `post_trade_plan.stop_management` | `string` | |
| `post_trade_plan.target_management` | `string` | |
| `post_trade_plan.exit_rules` | `list<string>` | |
| `post_trade_plan.eod_action` | `string` | Square-off MIS etc. |

### 8.3.13 Broker actions

| Field | Type | Description |
|-------|------|-------------|
| `broker_actions.suggested` | `list<enum>` | `CONNECT` · `SYNC` · `PLACE_ORDER` · `EXIT_POSITION` · `REDUCE` · `NONE` |
| `broker_actions.deep_link` | `string` | Kite URL if applicable |
| `broker_actions.existing_orders` | `list<OrderRef>` | Conflicts |

### 8.3.14 Natural language projections (precomputed)

| Field | Type | Description |
|-------|------|-------------|
| `nl.morning_brief` | `string` | Full Morning Brief text |
| `nl.headline` | `string` | 6–12 words |
| `nl.release_statement` | `string` | "You're done" / "Come back at 3:30" |
| `nl.primary_cta` | `string` | Button label |
| `nl.secondary_cta` | `string` | |

### 8.3.15 Learning & outcome (post-hoc)

| Field | Type | Description |
|-------|------|-------------|
| `outcome.status` | `enum` | `PENDING` · `TARGET` · `STOP` · `SCRATCH` · `INVALIDATED` · `EXPIRED` |
| `outcome.realized_pnl_inr` | `float` | From broker truth |
| `outcome.max_favorable_excursion` | `float` | |
| `outcome.max_adverse_excursion` | `float` | |
| `outcome.scored_at` | `ISO8601` | |
| `learning_feedback.tags` | `list<string>` | Internal |
| `learning_feedback.user_notes` | `string` | Optional journal |

## 8.4 Decision type enum

| `decision_type` | User headline | Typical scope |
|-----------------|---------------|---------------|
| `TRADE` | "Trade today" | Session |
| `WAIT` | "Wait" | Session |
| `NO_TRADE` | "Don't trade today" | Session |
| `REDUCE` | "Cut back exposure" | Portfolio |
| `HOLD` | "Hold — no changes" | Portfolio |
| `EXIT` | "Exit [symbol]" | Position |
| `ADD` | "Add to [symbol]" | Position |
| `TRIM` | "Trim [symbol]" | Position |
| `WATCH` | "Watch [symbol]" | Instrument |
| `BUY` | "Buy [symbol]" | Instrument (Ask AI) |
| `SELL` | "Sell [symbol]" | Instrument |
| `STAY_OUT` | "Stay out of [symbol]" | Instrument |

## 8.5 Priority rules (which decision becomes PRIMARY)

```
1. Risk block (loss cap, streak) → NO_TRADE primary
2. Portfolio HIGH_RISK → REDUCE or HOLD primary
3. Session NO_TRADE gate → WAIT primary
4. High-conviction TRADE with portfolio clearance → TRADE primary
5. Else → WAIT with WATCH_ONLY secondary
```

Only **one** `PRIMARY` decision per session per user at a time.

## 8.6 Aggregates

| Aggregate | Contains |
|-----------|----------|
| `SessionDecisionBundle` | One PRIMARY + up to 2 SECONDARY + WATCH list |
| `PortfolioDecisionSet` | Per-holding decisions for Portfolio view |
| `InstrumentDecision` | Single-symbol decision for Ask AI |

---

# 9. Decision Lifecycle

## 9.1 Pipeline (canonical)

```
Market data ─────┐
Global/macro ────┤
News/events ─────┤
                 ▼
            ┌─────────┐
            │ CONTEXT │  Session, regime, restrictions, timing
            └────┬────┘
                 ▼
            ┌───────────┐
            │ PORTFOLIO │  Holdings, sectors, cash, correlation
            └────┬──────┘
                 ▼
            ┌─────────┐
            │  RISK   │  Limits, streak, R:R gates, behaviour
            └────┬────┘
                 ▼
            ┌──────────┐
            │ CAPITAL  │  Size, allocation, margin
            └────┬─────┘
                 ▼
            ┌────────────┐
            │ BEHAVIOUR  │  Loss chasing, overtrading patterns
            └────┬───────┘
                 ▼
            ┌─────────────┐
            │ SYNTHESIS   │  Merge → single verdict (internal)
            └────┬────────┘
                 ▼
         ┌───────────────────┐
         │  TradingDecision   │  ← SINGLE SOURCE OF TRUTH
         └─────────┬─────────┘
                   │
     ┌─────────────┼─────────────┬──────────────┐
     ▼             ▼             ▼              ▼
Morning Brief  Trade Plan   Portfolio      Ask AI
     │             │             │              │
     └─────────────┴─────────────┴──────────────┘
                   ▼
            ┌─────────────┐
            │  EXECUTION  │  Human on Zerodha (v1)
            └──────┬──────┘
                   ▼
            ┌─────────────┐
            │ MONITORING  │  Review times, invalidation
            └──────┬──────┘
                   ▼
            ┌─────────────┐
            │   REVIEW    │  EOD score
            └──────┬──────┘
                   ▼
            ┌─────────────┐
            │  LEARNING   │  Outcome ingest (internal)
            └─────────────┘
```

## 9.2 Stage contracts

Each stage **inputs** and **outputs** a structured context — never UI strings.

| Stage | Input | Output | Failure mode |
|-------|-------|--------|--------------|
| Context | Market feeds, calendar | `MarketContext` | Degrade to WAIT + "data stale" |
| Portfolio | Zerodha holdings | `PortfolioContext` | Block TRADE if disconnected (configurable) |
| Risk | Prefs + journal | `RiskContext` | Force NO_TRADE |
| Capital | Prefs + margin | `CapitalContext` | Reduce size |
| Behaviour | History | `BehaviourFlags` | Force WAIT |
| Synthesis | All above + candidates | `DecisionArtifact` | WAIT with reason |
| TradingDecision | Artifact + NL render | `TradingDecision` | Must not fail silently |
| Views | TradingDecision | Projected UI DTO | Read-only |

## 9.3 Refresh cadence

| Trigger | Recompute |
|---------|-----------|
| App open | Full pipeline |
| 9:15, 9:45, 11:30, 14:00, 15:00 IST | Context + decision refresh |
| Zerodha sync | Portfolio stage |
| User asks symbol | Instrument decision only |
| Invalidation price hit | Status → INVALIDATED + new WAIT |

## 9.4 Immutability & supersession

- Published decisions are **immutable**.
- Material change (invalidation, regime flip) → new `decision_id`, `supersedes_id` set.
- UI shows: "Updated recommendation (10:32 AM)" — not silent change.

---

# 10. Information Architecture

## 10.1 Principle: decisions, not pages

Every surface is a **view** over `TradingDecision`:

| User-facing name | View type | Decision filter |
|------------------|-----------|-----------------|
| **Morning Brief** | Decision Summary | `PRIMARY` session decision |
| **Trade Plan** | Execution View | `PRIMARY` where `decision_type` ∈ {TRADE, WATCH} |
| **Portfolio** | Portfolio Impact | Per-holding + portfolio-level |
| **Ask AI** | Decision Explorer | `scope=INSTRUMENT` for queried symbol |
| **Results** | Decision History | Completed decisions, outcomes |
| **Settings** | System health | No decision (configuration) |

## 10.2 Navigation (v1)

```
┌────────────────────────────────────────────────────────┐
│  AI Trading Decision System              [Ask] [Settings]│
├────────────────────────────────────────────────────────┤
│  Morning Brief │ Trade Plan │ Portfolio │ Results      │
└────────────────────────────────────────────────────────┘
```

**Ask AI** is global overlay — not a competing tab with its own truth.

## 10.3 View projection layer

```
TradingDecision
      │
      ▼
DecisionViewService (read-only projections)
      │
      ├── toMorningBrief()   → MorningBriefDTO
      ├── toTradePlan()      → TradePlanDTO
      ├── toPortfolioBrief() → PortfolioBriefDTO
      ├── toInstrumentView() → InstrumentDecisionDTO
      └── toHistoryRow()     → DecisionHistoryDTO
```

**Engineering rule:** UI components consume DTOs only — never assemble verdicts.

## 10.4 Demoted capabilities (not decision views)

| Capability | Access |
|------------|--------|
| Market scanner | Settings → Advanced |
| Full chart grid | Trade Plan → one chart link |
| Screener | Ask AI → "Find stocks like…" |
| Backtest | Settings → Advanced |
| Education (Varsity) | Contextual links in reasoning |

---

# 11. Screen Philosophy

Each screen answers **exactly one question** (see §10). Shared rules:

1. **Starts with recommendation** — not logo, not metrics
2. **Ends with action or release**
3. **Max one screen scroll** for default state on mobile
4. **No tabs within tabs** on Morning Brief
5. **Evidence collapsed** by default everywhere

| Screen | Question | If nothing to say |
|--------|----------|-------------------|
| Morning Brief | Smartest thing today? | "Nothing requires your attention. Close the app." |
| Trade Plan | How to execute? | "No active trade plan today." |
| Portfolio | What to change? | "Hold everything. No changes." |
| Ask AI | Buy/hold/reduce/sell? | "Insufficient data — connect broker." |
| Results | Can I trust system? | "Not enough history yet — check back Friday." |

---

# 12. UX Principles

| # | Principle | Test |
|---|-----------|------|
| 1 | **One recommendation** | Can user state it in one sentence? |
| 2 | **One memory** | One headline sticks after leaving |
| 3 | **One action** | Exactly one primary button |
| 4 | **One conclusion** | Release or execute — never ambiguous |
| 5 | **Recommendation first** | First 32px text is the verdict |
| 6 | **Explanation second** | Reason follows headline |
| 7 | **Evidence optional** | Collapsed; never required reading |
| 8 | **Charts support** | Chart appears only after verdict |
| 9 | **20-second Morning Brief** | Word count ≤ 80 default visible |
| 10 | **Think, don't scroll** | WAIT days = zero scroll |

---

# 13. Design Language

## 13.1 Visual personality

- **Calm** — no flashing alerts
- **Confident** — large verdict typography
- **Minimal** — white/black space dominant
- **Warm** — personal greeting, human sentences
- **Not** — Bloomberg green-on-black, not neon crypto, not enterprise SaaS

## 13.2 Typography hierarchy

| Level | Size | Use |
|-------|------|-----|
| L0 Verdict | 32px bold | TRADE / WAIT / HOLD |
| L1 Reason | 18px regular | Why sentence |
| L2 Detail | 16px | Plan levels |
| L3 Label | 12px caps | "ONE THING TO WATCH" |
| L4 Muted | 14px 70% | Footer, reading time |

## 13.3 Color semantics

| Verdict | Color | Hex |
|---------|-------|-----|
| Trade / Buy | Green | `#00C853` |
| Wait / Watch | Amber | `#FFD600` |
| No trade / Sell | Red | `#FF5252` |
| Hold / Cautious | Orange | `#FF9800` |
| Neutral | White/Gray | theme default |

## 13.4 Layout

- Max content width: **680px** (reading comfort)
- Single column default
- No metric tile grids in default view
- No dataframe tables above fold

## 13.5 Components (canonical)

| Component | Purpose |
|-----------|---------|
| `VerdictHeadline` | L0 verdict |
| `MentorParagraph` | NL reasoning |
| `IfThenPlan` | Conditional entry |
| `LevelStrip` | Entry/stop/target inline |
| `ReleaseButton` | "You're done today" |
| `PrimaryAction` | One CTA |
| `WhyExpand` | Evidence bullets |
| `ReadingTime` | "20 sec" |

---

# 14. Tone of Voice

## 14.1 Persona

**Calm, experienced professional trader** — conservative bias, capital-first, never hype.

## 14.2 Rules

| Rule | Example |
|------|---------|
| Write like speech | "I'd wait until after 9:45." |
| Use if/then | "If RELIANCE breaks ₹2,850, buy." |
| Name the user | "Good morning, Pratham." |
| Admit uncertainty | "Low conviction — half size or skip." |
| Admit mistakes | "We were wrong on INFY yesterday." |
| Release explicitly | "Nothing requires your attention today." |

## 14.3 Banned vocabulary (UI)

`Context Engine` · `Evidence Packet` · `Risk Module` · `Market Regime` · `Confidence Engine` · `Synthesis` · `Calibration` · `Investment OS` · `Decision Engine` · `Broker Truth` · `Combined Score` · `snapshot_id`

## 14.4 Preferred vocabulary

| Concept | User hears |
|---------|------------|
| High conviction | "We're confident" |
| Sector overweight | "You already have enough banking exposure" |
| Loss streak | "Three losing days in a row" |
| R:R | "Reward is 2× your risk" |
| EOD | "After market close" |

---

# 15. Recommendation Framework

## 15.1 Structure (invariant)

Every recommendation follows:

```
HEADLINE     → 6–12 words
REASON       → 1–2 sentences
PLAN         → if/then + levels + size (if acting)
ACTION       → one primary button
RELEASE      → when to stop engaging
WHY (opt)    → ≤ 3 bullets
```

## 15.2 Recommendation quality bar

A recommendation ships only if:

| Criterion | Required |
|-----------|----------|
| Actionable or explicit release | ✓ |
| Portfolio-checked | ✓ |
| Risk-sized | ✓ |
| Invalidation defined | ✓ (for TRADE) |
| Plain language summary | ✓ |
| Conviction stated | ✓ |
| Review time set | ✓ (for TRADE) |

## 15.3 Anti-patterns (reject at synthesis)

- "Market is bullish" without action
- "Consider RELIANCE" without trigger price
- Two PRIMARY trade recommendations
- Trade that duplicates 20% existing position without warning
- ACT recommendation when `loss_streak >= threshold`

---

# 16. Portfolio Intelligence Framework

## 16.1 Purpose

Ensure every trade recommendation is evaluated against **the whole book** — not a blank slate.

## 16.2 Analysis dimensions

| Dimension | Question | Output |
|-----------|----------|--------|
| **Duplicate exposure** | Already holding symbol? | ADD vs TRADE warning |
| **Sector concentration** | Adds to overweight sector? | Block or reduce size |
| **Correlation** | Correlated to existing holdings? | "Pick one" message |
| **Cash headroom** | Can afford size? | Cap quantity |
| **Open risk** | Unrealized loss today? | Reduce aggression |
| **Position count** | Too many open trades? | WAIT |
| **Style fit** | MIS pick for CNC holder? | Product mismatch warning |

## 16.3 Portfolio health states

| State | Criteria (examples) | User message |
|-------|---------------------|--------------|
| `HEALTHY` | Diversified; no sector > 35%; drawdown < threshold | "Your portfolio looks healthy." |
| `NEEDS_REVIEW` | One laggard > 8% loss; sector 35–50% | "One position needs review." |
| `HIGH_RISK` | Sector > 50%; loss streak; margin stress | "Reduce risk before adding." |

## 16.4 Per-holding decisions

Each holding generates a `TradingDecision` with `scope=PORTFOLIO`:

- `HOLD` — default when healthy
- `TRIM` — underwater + overweight
- `ADD` — winner + room in sector
- `EXIT` — thesis broken

Portfolio screen PRIMARY = worst holding needing action, or `HOLD ALL` if none.

---

# 17. Risk Intelligence Framework

## 17.1 Risk hierarchy

```
1. Daily loss cap (hard stop)
2. Loss streak pause
3. Max trades per day
4. Per-trade risk ₹
5. Minimum R:R
6. Session timing gates
7. Behaviour warnings (soft)
```

Higher layers **override** lower layers.

## 17.2 Risk outputs

| Output | Field |
|--------|-------|
| Block trade | `risk_context.block_reason` |
| Reduce size | `quantity` reduced + `reasoning` |
| Force WAIT | `decision_type = WAIT` |
| Behaviour warning | `reasoning.behaviour_warnings` |

## 17.3 User-configurable (Settings)

- Max daily loss ₹
- Max risk % per trade
- Max trades/day
- Loss streak pause threshold
- Min R:R
- Opening observe until (default 9:45)

---

# 18. Behaviour Intelligence Framework

## 18.1 Purpose

Detect **process failures** — revenge trading, overtrading, ignoring stops — and intervene via decision, not lecture.

## 18.2 Signals

| Signal | Detection | Decision impact |
|--------|-----------|-----------------|
| Loss streak | N negative journal days | NO_TRADE |
| Increasing size after loss | Size > 1.5× average after red day | Reduce + warning |
| Overtrading | Trades > max before noon | WAIT afternoon |
| Ignoring stops | Historical stop violations | Lower conviction |
| Chasing | Entry far above planned | WATCH not TRADE |

## 18.3 User-facing tone

Never: "Behaviour model detected revenge trading."  
Always: "Yesterday was rough — best to sit out the first hour today."

---

# 19. Zerodha Integration Philosophy

## 19.1 Principles

1. **Connect early** — portfolio-aware decisions require broker
2. **Sync often** — holdings, cash, positions at session start + periodic
3. **Never compete with Kite** — we advise; Kite executes
4. **Truth for outcomes** — fills and P&L from broker, not estimates
5. **Deep link, don't duplicate** — order placement in Kite

## 19.2 Required data

| Data | Use |
|------|-----|
| Holdings | Portfolio context, duplicate check |
| Positions | Open MIS tracking |
| Margins | Capital context |
| Orders | Conflict detection |
| Profile | Personalization |
| P&L | Results scoring |

## 19.3 Degraded mode

When disconnected:

- Morning Brief shows **CONNECT** primary action
- Trade recommendations carry `conviction` cap at MEDIUM
- Portfolio view uses last-synced data with **stale timestamp warning**

## 19.4 Future (v2+)

- Read open orders for conflict
- Detect fills for automatic outcome scoring
- Optional order staging (not v1)

---

# 20. Morning Brief Specification

## 20.1 Question

**What is the smartest thing I should do today?**

## 20.2 Data source

```python
# Conceptual — not implementation
brief = DecisionViewService.toMorningBrief(
    bundle.primary_decision  # TradingDecision
)
```

## 20.3 Content template

```
{greeting}

{headline}                                    # L0: WAIT day / Trade day / etc.

{reason_sentence}                             # L1

{portfolio_sentence}                          # L1

{watch_section?}                              # Only if WATCH or TRADE
  {symbol}
  {if_then_plan}

{release_statement}                           # "You're done" / "Open trade plan"

[Primary CTA]
[Secondary CTA?]

▸ See why we think this
Estimated reading time: {n} sec
```

## 20.4 Example variants

### WAIT (zero scroll)

> Good morning, Pratham.  
> **Today is a wait day.**  
> I'd wait until after 9:45 — the opening range is still forming.  
> Your portfolio looks healthy.  
> RELIANCE is the only name worth watching. If it breaks ₹2,850 after 9:45, consider it. Otherwise, you're done for today.  
> **[You're done for today]**

### TRADE

> Good morning, Pratham.  
> **Today is a trade day.**  
> One high-conviction setup — stay within your ₹2,000 risk budget.  
> Your portfolio looks healthy.  
> **RELIANCE · Long** — enter above ₹2,850, stop ₹2,820, target ₹2,920.  
> **[Open trade plan]**

### NO_TRADE (loss streak)

> Good morning, Pratham.  
> **Not a day to trade.**  
> Three losing days in a row — protect capital and sit out.  
> Your portfolio needs no changes.  
> **[You're done for today]**

## 20.5 Acceptance criteria

- [ ] ≤ 80 words visible before expand
- [ ] Answers all 5 product promise questions
- [ ] One primary CTA
- [ ] Reading time displayed
- [ ] iPhone SE — no scroll on WAIT day

---

# 21. Trade Plan Specification

## 21.1 Question

**Exactly how should I execute today's recommendation?**

## 21.2 Data source

`DecisionViewService.toTradePlan(primary_decision)` where `decision_type` ∈ {`TRADE`, `WATCH`}

## 21.3 Content

| Section | Content |
|---------|---------|
| Header | Date · session status |
| Plan card | Symbol · side · conviction |
| Levels | Entry condition · stop · target |
| Size | Shares · risk ₹ |
| Timing | Safe entry window |
| Options leg | Only if options decision attached |
| Actions | Review setup · Log trade |
| Footer | Back to Morning Brief |

## 21.4 Empty state

> No active trade plan today.  
> The smartest thing you can do is wait.  
> **[Back to Morning Brief]**

## 21.5 End action

- **Log trade** → Results
- **Back to Morning Brief** → always available

---

# 22. Portfolio Specification

## 22.1 Question

**What should I change in my current portfolio?**

## 22.2 Data source

`PortfolioDecisionSet` — aggregate of per-holding `TradingDecision` + one portfolio-level decision

## 22.3 Content

| Section | Content |
|---------|---------|
| Banner | HOLD ALL / TRIM X / REVIEW X |
| One-liner | P&L · positions · sector note |
| Primary CTA | No changes needed / Review symbol |
| Collapsed | Holdings table with per-row action |
| Collapsed | Sector breakdown |
| Broker status | Connected · synced time |

## 22.4 Holdings row format

| Symbol | Today's action | One-line why |
|--------|----------------|--------------|
| INFY | Trim | Down 8%; overweight IT |
| TCS | Hold | Within plan |

## 22.5 End action

**No changes needed** OR **Review [symbol]** → Ask AI

---

# 23. Ask AI Specification

## 23.1 Question

**Should I buy, hold, reduce, or sell this stock?**

## 23.2 Entry

Global search overlay → symbol → instrument `TradingDecision`

## 23.3 Fast answer (default)

```
{SYMBOL} — {BUY|HOLD|WAIT|SELL|REDUCE}

{reason_sentence}

Entry zone · Stop · Target
Conviction: High/Medium/Low

[Add to today's watch]  [Full analysis]
▸ Why this call
```

## 23.4 Full analysis (deep)

Long-horizon business quality report — sections renamed for humans:

- The bottom line
- Should you buy?
- How to enter
- What could go wrong
- The business (collapsed sections)

## 23.5 End action

- **Add to watch** → attaches as SECONDARY to session bundle
- **Open trade plan** → if ACT day + high conviction
- **Compare** → Compare mode

---

# 24. Results Specification

## 24.1 Question

**Can I trust the system?**

## 24.2 Data source

`Decision History` — completed `TradingDecision` with `outcome` populated

## 24.3 Content

| Section | Content |
|---------|---------|
| Headline | "Last 7 days: X of Y correct" |
| Tiles | Wins · Losses · Rate |
| Yesterday | Best/worst call one-liners |
| CTA | Score yesterday (if pending) / You're up to date |
| Collapsed | Full history table |
| Collapsed | Export |

## 24.4 Trust framing

Never lead with calibration curves. Lead with **plain hit rate** and **honest misses**.

> "We called RELIANCE right. We missed INFY — stopped out."

## 24.5 End action

- Pending: **Score yesterday's picks**
- Up to date: **Back to Morning Brief**

---

# 25. Future Autonomous Trading Vision

## 25.1 Phased autonomy

| Phase | System | Human |
|-------|--------|-------|
| **v1** | Recommends | Executes all orders |
| **v2** | Alerts at review times | Executes |
| **v3** | Pre-fills order ticket in Kite | One-tap confirm |
| **v4** | Policy-bound auto-exec (MIS only, max ₹ risk) | Opt-in + kill switch |

## 25.2 Guardrails for autonomy

- Daily loss cap hard stop
- Max position size
- Allowed instruments whitelist
- Session window only
- Instant kill switch in Settings
- Full audit log of every auto action

## 25.3 AI Trading Partner definition

> A system that knows your book, remembers your mistakes, watches your trades, and acts **only within rules you set** — with full transparency after the fact.

## 25.4 What we will NOT auto-do (ever without explicit opt-in)

- Short selling without confirmation
- Options selling (uncovered)
- CNC sells of held stock
- Trades exceeding daily loss cap
- Trades outside session hours

---

# 26. Phase-wise Implementation Roadmap

## Phase 0 — Constitution (Month 1)

| Deliverable | Owner |
|-------------|-------|
| `TradingDecision` schema in code (dataclass) | Backend |
| `DecisionViewService` projections | Backend |
| Migrate `DecisionArtifact` → `TradingDecision` wrapper | Backend |
| Feature flag `TD_SYSTEM=1` | Eng |
| Ban independent verdicts in UI (lint) | Eng |

**Exit:** One PRIMARY decision drives Morning Brief.

## Phase 1 — Morning Brief (Month 2)

| Deliverable | Owner |
|-------------|-------|
| NL renderer for `nl.morning_brief` | Backend |
| Morning Brief UI (narrative, not cards) | Frontend |
| All WAIT/TRADE/NO_TRADE states | Product QA |
| 20-second acceptance test | UX |

**Exit:** Product promise Q1–Q5 answered above fold.

## Phase 2 — Trade Plan + Results (Month 3)

| Deliverable | Owner |
|-------------|-------|
| Trade Plan projection | Backend + FE |
| Outcome scoring → `outcome` fields | Backend |
| Results trust headline | Frontend |

## Phase 3 — Portfolio intelligence (Month 4)

| Deliverable | Owner |
|-------------|-------|
| Per-holding decisions | Backend |
| Portfolio Brief projection | Backend + FE |
| Merge Daily Advisor | Frontend |
| Sector/correlation warnings in NL | Backend |

## Phase 4 — Ask AI unification (Month 5)

| Deliverable | Owner |
|-------------|-------|
| Instrument decision pipeline | Backend |
| Single search → fast/deep | Frontend |
| Remove duplicate Single Stock / Alpha tabs | IA |

## Phase 5 — IA surgery (Month 6)

| Deliverable | Owner |
|-------------|-------|
| 5-tab nav | Frontend |
| Settings page | Frontend |
| Demote scanners/charts | IA |
| Sidebar removal | Frontend |

## Phase 6 — Behaviour + monitoring (Month 7–8)

| Deliverable | Owner |
|-------------|-------|
| Behaviour stage in pipeline | Backend |
| Review time notifications | Backend + Telegram |
| Invalidation refresh | Backend |

## Phase 7 — Partner features (Month 9–12)

| Deliverable | Owner |
|-------------|-------|
| Kite deep links | Frontend |
| Auto outcome from fills | Backend |
| v2 monitoring dashboard (minimal) | Product |

---

# 27. What NOT to Build

| Do not build | Why |
|--------------|-----|
| Multi-stock dashboard home | Violates one recommendation |
| Confidence % in headlines | False precision |
| Separate verdict per page | Violates Article I |
| 200-stock live chart grid as default | Chart viewer identity |
| Market Pulse as daily destination | Screener identity |
| Health score rings / gamification | Dashboard theatre |
| "Explore features" engagement | Violates release principle |
| AI chat freeform without decision object | Unbounded, unaccountable |
| Auto-trade in v1 | Constitution Article IX |
| Synthetic portfolio advice without broker | Violates Zerodha philosophy |
| Multiple PRIMARY trades without explicit user request | Violates quality bar |
| Engine names in UI | Violates Article IV |
| Silent recommendation changes | Violates Article VII |

---

# 28. Product Review Checklist

Before any release, product signs off:

- [ ] Does every screen answer exactly one question?
- [ ] Does every recommendation originate from `TradingDecision`?
- [ ] Is there exactly one PRIMARY recommendation per session?
- [ ] Can user finish Morning Brief in < 20 seconds?
- [ ] Are all 5 product promise questions answered on Morning Brief?
- [ ] Is there a release statement on WAIT/NO_TRADE days?
- [ ] Is portfolio impact checked for every TRADE?
- [ ] Is risk hierarchy respected?
- [ ] Are behaviour warnings shown when triggered?
- [ ] Is Zerodha stale state handled honestly?
- [ ] No banned vocabulary in default UI?
- [ ] Every screen ends with action or release?
- [ ] Would a calm trader write this copy?

---

# 29. UX Review Checklist

- [ ] Verdict is first visible element (L0)
- [ ] ≤ 80 words above fold on Morning Brief
- [ ] Zero scroll WAIT day on mobile
- [ ] One primary button per screen
- [ ] Evidence collapsed by default
- [ ] No metric tile grid default
- [ ] No dataframe above fold
- [ ] Charts only in expand/link
- [ ] Reading time on Morning Brief
- [ ] Personal greeting when name available
- [ ] Conviction = High/Med/Low only (default)
- [ ] Footer disclaimer only (not header)
- [ ] 680px max width maintained
- [ ] Verdict colors consistent

---

# 30. Engineering Guardrails

## 30.1 Architecture rules

| Rule | Enforcement |
|------|-------------|
| UI reads `TradingDecision` DTOs only | Code review + lint |
| No verdict logic in `ui/` | CI grep |
| `DecisionArtifact` → `TradingDecision` mapping in one module | `analyzer/trading_decision/` |
| Projections are pure functions | Unit tests |
| Decisions immutable after publish | DB append-only |
| Supersession explicit | `supersedes_id` required |

## 30.2 Module boundaries (proposed)

```
analyzer/
  trading_decision/
    model.py          # TradingDecision dataclass
    factory.py        # Builds from pipeline stages
    projections.py    # DecisionViewService
    nl_renderer.py    # Natural language generation
    history.py        # Outcome + learning
  decision_engine/    # Existing — verdict authority
  context_engine/     # Existing — market context
  portfolio_live/     # Existing — Zerodha
  ...

ui/
  views/
    morning_brief.py  # DTO only
    trade_plan.py
    portfolio_brief.py
    ask_ai.py
    results.py
```

## 30.3 API contract (internal)

```python
# Conceptual service — not implementation code

class TradingDecisionService:
    def get_session_bundle(user_id, session_date) -> SessionDecisionBundle: ...
    def get_primary_decision(user_id, session_date) -> TradingDecision: ...
    def get_instrument_decision(symbol, user_id) -> TradingDecision: ...
    def get_portfolio_decisions(user_id) -> PortfolioDecisionSet: ...
    def get_history(user_id, days) -> list[TradingDecision]: ...
    def refresh(force: bool = False) -> SessionDecisionBundle: ...
```

## 30.4 Performance budgets

| Operation | Budget |
|-----------|--------|
| Morning Brief load | < 2s P95 |
| Ask AI fast | < 3s P95 |
| Full pipeline refresh | < 5s P95 |
| NL render | < 100ms |

## 30.5 Testing requirements

| Test type | Coverage |
|-----------|----------|
| Unit | Projections, NL templates, priority rules |
| Integration | Pipeline → TradingDecision → DTO |
| Golden | Morning Brief copy for 10 scenarios |
| UX acceptance | 20-second test with real users |
| Regression | No independent verdicts in UI |

## 30.6 Copy lint (CI)

Fail build if banned words appear in `ui/views/` default strings.

## 30.7 Feature flags

| Flag | Purpose |
|------|---------|
| `TD_SYSTEM=1` | Enable TradingDecision-driven UI |
| `TD_NL_RENDERER=v2` | A/B copy improvements |
| `TD_BEHAVIOUR=1` | Behaviour stage enabled |

---

# Appendix A — Challenged assumptions

| Assumption | Challenge | Resolution |
|------------|-----------|------------|
| More tabs = more value | Users bounce | 5 decision views |
| Show confidence % | False precision | High/Med/Low |
| Each page computes its own advice | Contradictions | TradingDecision SSoT |
| Charts sell the product | Decision fatigue | Verdict first |
| Users want scanners | They want conviction | Demote scanners |
| Learning = show calibration | Trust = hit rate | Plain language results |
| Investment OS sounds premium | Sounds like software | AI Trading Decision System |
| Home = dashboard | Home = letter | Morning Brief narrative |

---

# Appendix B — Glossary (internal only)

| Term | Meaning |
|------|---------|
| `TradingDecision` | Canonical recommendation object |
| `SessionDecisionBundle` | Today's decision set |
| `DecisionViewService` | Read-only UI projections |
| `PRIMARY` | The one recommendation user must remember |
| `Release statement` | Permission to close app |
| `NL renderer` | Template + data → mentor copy |

---

# Appendix C — Document lineage

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-16 | Initial canonical architecture |

---

*AI Trading Decision System — Product Architecture v1.0*  
*The application must THINK. The user should not.*  
*This document is the foundation for the next several years of development.*
