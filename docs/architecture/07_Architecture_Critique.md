# 07 — Architecture Critique (Second-Level Review)

**Reviewer role:** Chief Software Architect — self-review  
**Date:** 2026-07-15  
**Scope:** Critique of documents 01–06 only (not application code)  
**Posture:** Adversarial. Assume the architecture is wrong until proven necessary.

---

## Executive verdict

The proposed target architecture (doc 05) and migration plan (doc 06) are **directionally sound for a commercial Indian investing SaaS at 10k–100k users**, but **over-engineered for the actual product today** (single trader, ₹9k MIS pool, Streamlit monolith, Mac autopilot).

The audit (docs 01–03) correctly identified pain. The target design **over-corrects** by importing institutional vocabulary (16 domains, Evidence Engine, event bus, plugin registry) **before** fixing the one failure that invalidates everything else: **broker-verified truth in the learning loop**.

**Revised recommendation:** Adopt a **simplified target** — **6 deployable boundaries**, not 16 — and cut the migration from **52 steps / 20 weeks** to **~18 high-value steps / 8–10 weeks**. Defer institutional patterns until dogfood metrics justify them.

---

## 1. Ten-question gate (applied to major recommendations)

Each row scores: ✅ Yes · ⚠️ Partial · ❌ No

| Recommendation | Necessary? | Trading decisions? | Explainability? | Less maintenance? | Scalability? | Less complexity? | Simplify? | Hedge fund? | Bloomberg? | 1M users? |
|----------------|------------|---------------------|-----------------|-------------------|--------------|------------------|-----------|-------------|------------|-----------|
| **16 bounded domains** | ⚠️ | ❌ | ⚠️ | ⚠️ | ✅ | ❌ | ✅ **Merge to 6** | ❌ | ❌ | ⚠️ |
| **Evidence Engine (separate domain)** | ⚠️ | ⚠️ | ✅ | ❌ | ✅ | ❌ | ✅ **Inline first** | ⚠️ | ✅ | ✅ |
| **Strategy plugin registry** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ⚠️ | ✅ |
| **Unified journal facade** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ⚠️ | ✅ |
| **Broker P&L as learning primary** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| **In-process event bus** | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ✅ **Defer** | ⚠️ | ✅ | ✅ |
| **Split zerodha into 3 modules** | ⚠️ | ❌ | ❌ | ✅ | ⚠️ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| **8 Intelligence domain facades** | ❌ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ✅ **One Intelligence pkg** | ❌ | ❌ | ⚠️ |
| **52-step strangler migration** | ⚠️ | ❌ | ❌ | ❌ | ⚠️ | ❌ | ✅ **~18 steps** | ❌ | ❌ | ⚠️ |
| **Delete `analyzer/` package (M52)** | ❌ | ❌ | ❌ | ⚠️ | ⚠️ | ❌ | ✅ **Keep alias tree** | ❌ | ❌ | ❌ |
| **FastAPI + Postgres (Phase 4)** | ⚠️ | ❌ | ❌ | ⚠️ | ✅ | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| **Streamlit long-term shell** | ✅ | ⚠️ | ⚠️ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Risk Intelligence domain** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ |
| **Notification Engine domain** | ⚠️ | ⚠️ | ❌ | ✅ | ✅ | ❌ | ✅ **Subfolder** | ⚠️ | ⚠️ | ✅ |
| **AI Layer domain** | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ❌ | ✅ **Guardrails only** | ⚠️ | ✅ | ✅ |
| **Research vs Fundamental split** | ⚠️ | ⚠️ | ✅ | ❌ | ⚠️ | ❌ | ✅ **Merge for MVP** | ✅ | ✅ | ✅ |

**Pattern:** Anything that improves **packaging hygiene** scores high on maintenance/scalability but **fails complexity and hedge-fund pragmatism** unless tied to a trading or explainability outcome.

---

## 2. Weak architecture decisions

### W1. Domain count driven by taxonomy, not by change velocity

**Decision:** 16 domains because the Investment OS has seven questions plus platform layers.

**Problem:** Seven user questions ≠ seven deployable microservices. Market AI and Sector AI both read macro/pulse — splitting **Market Intelligence** and **Macro Analysis** creates **coordination tax** without independent release cycles.

**Evidence from audit:** `investment_os.py` already composes both in one call. No team owns "Macro" separately.

**Fix:** Collapse to **6 boundaries** (see §9).

---

### W2. Recommendation Engine at risk of becoming the new god module

**Decision:** `recommendation_engine` owns OS, synthesis, watchlist builder, nightly prep, MIS advisory.

**Problem:** Doc 05 moves **five orchestration hubs** into one domain — recreating `market_pulse_scan` / `alpha_ai_report` hub anti-pattern under a new name.

**Ten-question fail:** Hedge funds separate **research**, **portfolio construction**, and **execution** — they do not merge them into "Recommendation Engine."

**Fix:** Recommendation Engine **aggregates votes only**. Watchlist construction stays **Prep Pipeline**. MIS gating stays **Risk + Session policy**.

---

### W3. Evidence Engine as a separate domain before journal truth

**Decision:** Wave 7 builds Evidence Engine; Wave 4 builds journal facade.

**Problem:** Explainability without **verified outcomes** produces elegant fiction. Evidence IDs on wrong coach scores **increase false confidence**.

**Priority inversion:** Doc 03 lists C5 (P&L truth gap) as **Critical** but doc 06 schedules Evidence Engine **after** 34 other steps.

**Fix:** Phase 0 = journal truth + module failure tags. Evidence = **structured fields on existing votes** (no new store) until 90 broker-logged sessions.

---

### W4. Event bus for a single-process Streamlit app

**Decision:** `shared/events/bus.py` to break import cycles (M08, M22).

**Problem:** In-process pub/sub adds **indirection** without concurrency benefits. Python function calls already work. Cycles are better fixed by **dependency inversion on 3 hot edges**, not events.

**Bloomberg test:** B-PIPE uses streaming infrastructure because **millions of ticks/sec** matter. You have **one user** and **5-second** options polling.

**Fix:** Delete event bus from near-term plan. Fix cycles: `watchlist_learning` reads gates via **injected parameters** at prep time, not pull from history at import time.

---

### W5. 52 migration steps optimizes for architectural purity over shipping

**Decision:** Strangler with physical moves for every intelligence domain (M26–M34).

**Problem:** Each facade step (M26–M34) adds **shim + re-export + tests** with **zero user value**. Solo developer spends **~6 weeks** on package moves while trading decisions unchanged.

**Maintenance:** During migration, developers must know **both** `analyzer.foo` and `domains.foo` — **higher** complexity, not lower.

**Fix:** Stop at **~18 steps** that change behavior or break cycles. Keep `analyzer/` as permanent **compat layer** until team > 2 engineers.

---

### W6. "Institutional-grade" label on retail MIS copilot

**Decision:** Target doc title and principles mirror sell-side research platforms.

**Problem:** User context (doc 01 audit, prefs): beginner, equity-only, ₹9k, one trade/day. Institutional stack implies **compliance, OMS, allocations, prime brokerage** — none appear in docs 01–06.

**Risk:** Team builds Bloomberg-shaped architecture for a product that competes with **discipline + journaling**, not with Refinitiv.

**Fix:** Rename target to **"Professional Retail Investment OS"** — institutional *explainability*, not institutional *infrastructure*.

---

### W7. Scalability story conflates code modularity with operational scale

**Decision:** Doc 04 rates scalability 9.5/10 on "code shape"; doc 05 adds API/workers/Postgres.

**Problem:** At **1M users**, Streamlit is non-starter. Modular Python packages do not help if **every user hits NSE scrape** and **Kite token per user**. Scalability bottleneck is **data licensing + per-tenant broker OAuth + job queue**, not domain folders.

**Fix:** Document explicit **scale tiers** (see §12).

---

## 3. Over-engineering

| Item | Why over-engineered | Simpler alternative |
|------|---------------------|---------------------|
| 16 domains | No independent teams or deploy cadence | 6 packages |
| `contracts/ports.py` for all domains | Python duck-typing works; team size = 1 | Protocols only at Data + Journal boundaries |
| Evidence store + evidence IDs (M35–M37) | No audit/regulatory requirement yet | Extend `StrategyVote.detail` + `source` field |
| 8 intelligence facades (Wave 6) | Thin wrappers over existing modules | Single `intelligence/` subpackage with modules |
| `apps/streamlit/` move (M51) | Import path churn | Keep `ui/` until real second app exists |
| AI Layer as platform | One LLM client + prompts | `platform/llm.py` — not a "layer" |
| Notification Engine domain | Telegram + formatters | `shared/notifications/` |
| Macro vs Market split | Same consumer (OS), same data sources | `market_context` module inside Intelligence |
| Research Intelligence 15-section split (M50) | Premature before report snapshot tests | Golden-file test first, split later |
| Plugin registry + JSON gates | Two extension mechanisms | Registry only; gates become plugin metadata |

---

## 4. Under-engineering

| Gap | Why it matters | In docs 01–06? |
|-----|----------------|----------------|
| **Broker reconciliation** | Learning without fill/slippage vs plan is toy | Mentioned (C5) but **no domain** |
| **Execution / OMS boundary** | OS says "enter at X" but never sees actual order | Missing |
| **Plan adherence scoring** | Review AI cannot say "you entered 12 min early" | Missing |
| **Licensed market data architecture** | 1M users cannot scrape NSE | Deferred to Phase 3 POC only |
| **Multi-tenant data model** | user_id on every row — not designed | Missing |
| **Secrets management** | Keychain/Vault — only "Phase 3" handwave | Under-specified |
| **Backtest in OS loop** | Strategy plugins need proof before live vote | Plugin backtest in Phase 2 but not OS-integrated |
| **Corporate actions / adjustments** | Splits, dividends break cost basis | Missing |
| **India tax / STCG context** | Retail wealth path needs tax-aware holds | Missing |
| **Model governance** | LLM prompt/version rollback | Missing |
| **Disaster recovery** | journal.db is single point of failure | Missing |
| **Rate limiting / cost caps** | LLM + NSE + Kite quotas at scale | Missing |
| **Compliance audit trail** | Who changed gates, when, why | Missing |
| **Feature store** | ML-ready learning mentioned, not designed | Missing |

**Critical under-engineering:** The architecture fixes **folder layout** more aggressively than **truth pipeline** (broker → journal → learning → gates).

---

## 5. Unnecessary abstractions

| Abstraction | Verdict |
|-------------|---------|
| `UniversePulsePort` vs function `get_pulse()` | Unnecessary until second implementation |
| Separate `Sentiment Analysis` domain for 2 modules | Namespace only |
| `RepositoryPort` in Data Layer | ORM/SQLite already implicit |
| `MLModelPort` in AI Layer (future) | YAGNI — no ML in production |
| `TemplatePort` in Notification | Functions suffice |
| `apps/workers/` before extracting hooks | `analyzer/schedulers/` rename enough |
| Deleting entire `analyzer/` tree | **Harmful** — breaks scripts, muscle memory, 76 tests' import paths |

**Rule:** Add abstraction when **second implementation exists** or **cycle must break** — not when diagram looks clean.

---

## 6. Missing abstractions (actually needed)

| Abstraction | Why necessary |
|-------------|---------------|
| **`BrokerTruthPort`** | Single interface: plan vs fill vs P&L from Zerodha Console/Kite |
| **`TradeRecord` canonical model** | One struct across journal, learning, review |
| **`GateConfig` versioned artifact** | Learned gates with version, diff, rollback |
| **`MarketDataProvider` Protocol** | Kite / Yahoo / licensed — already half-built |
| **`StrategyPlugin` Protocol** | Real OCP win — doc 05 correct here |
| **`RecommendationContext`** | Explicit inputs to OS (regime, starred, prefs, gates) |
| **`HealthStatus` per provider** | NSE 403, Kite token expiry — operational necessity |
| **`TenantContext`** | Required before user #2 |

---

## 7. Missing business capabilities

Capabilities a **paid Indian investing OS** needs but docs 01–06 do not architect:

| Capability | User/business impact |
|------------|-------------------|
| **Broker-synced trade import** | Eliminates manual P&L logging friction |
| **Discipline scorecard** | Plan adherence % — sellable metric |
| **Subscription tiers** | Equity-only free vs options pro — no billing domain |
| **Paper trading mode** | Dogfood strategies without capital risk |
| **Wealth track (SIP) vs MIS track** | User has both; OS treats MIS only |
| **Regulatory disclaimers as first-class** | SEBI-style "not advice" — versioned |
| **Onboarding for beginner mode** | Architecture ignores `beginner_mode` flag |
| **Coach vs broker reconciliation UI** | Trust recovery after Jul 13-type incidents |
| **Export for CA/tax** | India retail need; only SIP export exists |
| **Offline / market-closed mode** | Home already special-cases; not in target domains |

---

## 8. Missing AI capabilities

| Capability | Current docs | Gap |
|------------|--------------|-----|
| **Grounded generation** | AI Layer cites evidence IDs | No retrieval architecture (RAG over what corpus?) |
| **Hallucination guards on numbers** | guardrails.py stub | No allowlist of numeric fields from Data Layer |
| **Prompt versioning** | alpha_ai_prompts | No rollback / A-B |
| **Per-user calibration** | confidence_calibration | Not in target Learning Engine API |
| **Explainable score decomposition** | synthesis pillars | No SHAP-style attribution — OK for MVP |
| **NL copilot** | Mentioned in user vision | **Absent** from docs 01–06 target |
| **Module failure attribution** | Review AI | Not in Evidence or Learning domain specs |
| **Cost/latency budget** | Missing | Alpha AI can burn tokens unbounded |

**Verdict:** "AI Layer" is **LLM wrapper**, not **AI system architecture**. Acceptable for Phase 1; misleading name for institutional claim.

---

## 9. Missing data capabilities

| Capability | Gap |
|------------|-----|
| **Licensed NSE/BSE tick history** | Critical for SaaS; still optional POC |
| **Point-in-time correctness** | Backtest/Learning can leak future data — not addressed |
| **Symbol master / corporate actions** | NSE symbol changes, splits |
| **Data lineage** | Evidence Engine wants this but no lineage design |
| **Cache invalidation policy** | pulse_cache TTL ad hoc |
| **Per-tenant data isolation** | 1M users impossible without |
| **FII/DII / bulk deals freshness** | Macro domain lists but no SLA |
| **Options chain snapshots time series** | IV rank history mentioned in UPGRADE, not in domain arch |
| **Failover when NSE 403** | health banner exists; no graceful degradation architecture |

**Bloomberg test:** Bloomberg is a **data company** first. Your architecture is **application-first** with data as adapter — honest for retail, not Bloomberg-shaped.

---

## 10. Missing portfolio capabilities

| Capability | Gap |
|------------|-----|
| **Position-aware recommendations** | Alpha portfolio mode exists; OS ignores holdings |
| **Correlation / beta to Nifty** | portfolio_risk partial |
| **MIS vs delivery vs SIP buckets** | Single capital number in prefs |
| **Rebalance suggestions** | Research mentions; OS doesn't |
| **Concentration vs starred MIS pick** | Sector warn on watchlist only |
| **Cash / margin availability** | Kite margins in zerodha; not in Risk domain |
| **Wealth plan integration** | wealth_plan dead; not in Portfolio Intelligence path |
| **Multi-broker** | Zerodha-only implicit |

**Trading decision impact:** Stock AI ranks watchlist picks, not **portfolio-optimal** picks — OK for MIS beginner, under-engineered for "institutional OS" claim.

---

## 11. Missing learning capabilities

| Capability | Gap |
|------------|-----|
| **Broker-primary labels** | Still coach-secondary in target Learning API |
| **Module-level attribution** | Which OS module failed — in Phase 0 text, not domain model |
| **User-specific vs global gates** | All learning is global JSON — wrong at 1M users |
| **Exploration vs exploitation** | No bandit/thompson for strategy selection |
| **Minimum sample enforcement** | MIN_SAMPLES in code; not in architecture governance |
| **Rollback of bad tuning** | gates versioned in missing abstraction |
| **Counterfactual logging** | "Skipped trade" not learned from |
| **Regime-conditional performance** | Insights text only; no stratified models |

**Verdict:** Learning Engine architecture is **batch EOD tuner**, not **learning system**. Fine for v1; oversold as "self-learning AI."

---

## 12. Missing risk capabilities

| Capability | Gap |
|------------|-----|
| **Pre-trade risk** | Position size exists |
| **Intra-trade risk** | No monitor while position open |
| **Portfolio heat / aggregate MIS exposure** | Single trade focus |
| **Margin call / leverage** | Options need; not architected |
| **Tail / gap risk** | Gap open through stop — MIS reality |
| **Behavioral circuit breakers** | Loss streak exists; not tied to broker P&L |
| **Kill switch** | No "stop all coaching after 3 broker losses" |
| **Scenario stress** | Alpha Monte Carlo separate; Risk domain doesn't consume |
| **Regulatory position limits** | Retail not relevant; SME OI limits absent for options |

**Hedge fund test:** Risk is **first-class real-time system** with limits server — yours is **pre-trade calculator** — appropriate for retail MIS if labeled honestly.

---

## 13. Missing observability

Docs mention `structured_log.py` and Phase 3 Sentry — **no observability architecture**:

| Missing | Why |
|---------|-----|
| **Structured domain events** | Can't debug wrong verdict |
| **Provider latency metrics** | NSE/Kite slowness invisible |
| **Verdict → outcome join** | Can't prove OS calibration |
| **Alerting on learning failures** | EOD silent fail in background hook |
| **User journey funnel** | Scan → star → trade → log drop-off |
| **SLOs** | Home load <2s claimed; not measured |
| **Audit log** | Gate changes untracked |
| **Coach vs broker divergence metric** | Trust KPI — should be dashboard #1 |

**At 1M users:** Need distributed tracing, per-tenant metrics, cost attribution — **none designed**.

---

## 14. Missing testing strategy

Docs say "tests must pass each step" — **not a test architecture**:

| Gap | Recommendation |
|-----|----------------|
| No **golden-file** tests for OS verdict | Snapshot 5 fixtures |
| No **contract tests** between domains | Only implied |
| No **property tests** for position sizing | Money-critical |
| No **synthetic market replay** | Intraday regression |
| No **chaos tests** for NSE 403 / Kite down | Resilience |
| No **migration shim tests** | Import both paths |
| No **LLM eval harness** | Alpha AI regression |
| No **dogfood acceptance tests** | "30 sessions" manual |

**Missing principle:** **Risk Intelligence and Learning Engine require higher test tier** than Sentiment — not distinguished in docs.

---

## 15. Missing deployment strategy

| Gap | Impact |
|-----|--------|
| **Single deployment unit undefined** | Streamlit + launchd + scripts — 3 deploy surfaces |
| **Environment matrix** | local Mac vs Streamlit Cloud vs future Fly — configs differ |
| **Secrets per environment** | .env antipattern not replaced in target |
| **DB migration strategy** | SQLite → Postgres path absent |
| **Blue/green or canary** | Strategy registry flag mentioned; no deploy pairing |
| **Background job ownership** | app.py hooks vs launchd — duplicate EOD risk |
| **Multi-region** | 1M India users — single region OK; not stated |
| **CDN / static assets** | Minor for Streamlit |
| **Compliance data residency** | India user data — not addressed |

**At 1M users:** Need **API tier + worker tier + Postgres + Redis + object storage** — doc 05 lists names but **no capacity model, no job topology, no Streamlit deprecation trigger**.

---

## 16. Would a hedge fund build it this way?

**No** — for infrastructure. **Yes** — for a **research note template**.

| Hedge fund reality | Your target arch |
|--------------------|------------------|
| OMS/EMS separate from research | Merged into Recommendation Engine |
| Central security master | Symbol handling scattered |
| Real-time risk server | Pre-trade function |
| Proprietary data lake | File cache + SQLite |
| Quant pod owns strategies as code in repo | Plugin registry ✅ (good) |
| Backtest cluster | Single-machine walk-forward |
| Compliance archives every model change | Missing |

**Take:** Adopt **hedge fund discipline** (evidence labels, risk limits, journal truth, plugin versioning) — not **hedge fund topology**.

---

## 17. Would Bloomberg build it this way?

**No.** Bloomberg is:

1. **Data terminal** with entitlements — you are **decision coach**
2. **Normalized symbology** — you use Yahoo/NSE strings
3. **No Streamlit** — thick client / B-PIPE / API
4. **Entitlement per field** — you have no field-level licensing model

**What to steal from Bloomberg:**

- FACT / ESTIMATE / OPINION labeling ✅ (already in rules)
- **Field provenance** on every number
- **Consistent symbology layer**
- **Health indicators** when data stale

**Do not steal:** 16 product domains mirroring Bloomberg functions (EQSR, PORT, etc.) — overkill.

---

## 18. Would this make sense at one million users?

| Component | 1M-user viability |
|-----------|-----------------|
| Streamlit UI | ❌ Replace with web app + API |
| 16 Python domains | ✅ Fine as monorepo modules |
| SQLite journal | ❌ Postgres + tenant_id |
| JSON learned gates | ❌ Per-tenant + version table |
| NSE scrape | ❌ Licensed feed + legal |
| Per-user Kite OAuth | ✅ Required architecture missing |
| In-process event bus | ❌ Redis/Kafka job queue |
| Single pulse cache key | ❌ Sharded cache per tenant |
| 5s options poll | ❌ WebSocket fanout service |
| Mac launchd autopilot | ❌ Cloud scheduler per user TZ |
| Evidence store on disk | ❌ Object store + OLAP |

**Scale conclusion:** Domain modularity **helps** at 1M only **after** replacing runtime shell (Streamlit), storage, and data licensing. **Folder structure alone does not scale.**

**Minimum 1M-user additions not in docs 01–06:**

```text
API Gateway (auth, rate limit)
Tenant service
Job queue (prep, EOD, learning per tenant)
Market data entitlement service
Broker connection pool (OAuth refresh workers)
Observability stack
Postgres + read replicas
```

---

## 19. Simplified target architecture (recommended revision)

Replace 16 domains with **6 deployable boundaries**:

```text
shared/           # clock, prefs, config, logging
platform/
  data/           # providers, cache, broker adapters
  llm/            # LLM + guardrails (not "AI Layer")
intelligence/     # market, macro, ta, fa, sentiment, options (modules, not domains)
engines/
  decision/       # OS + synthesis + prep pipeline
  risk/           # sizing, circuit breakers, validation
  learning/       # journal + EOD + gates (BrokerTruthPort)
  notify/         # telegram
apps/
  streamlit/      # ui + app.py
  workers/        # schedulers only
analyzer/         # permanent compat shims (optional forever)
```

**Merge:**

- Market + Macro → `intelligence/market_context.py`
- Research + Fundamental → `intelligence/research.py` (until team grows)
- Evidence → fields on `StrategyVote` + `TradeRecord`, not domain
- Notification → `engines/notify/`

**Keep separate (high value):**

- `engines/decision/` (OS)
- `engines/learning/` (truth pipeline)
- `engines/risk/`
- `platform/data/`
- Strategy plugins inside `intelligence/ta/plugins/`

---

## 20. Revised migration plan (critique of doc 06)

| Doc 06 choice | Critique | Revised |
|---------------|----------|---------|
| 52 steps | Too many package moves | **18 steps** max |
| M26–M34 intelligence facades | Zero user value | **Skip** — use `intelligence/` subfolder in one step |
| M08 event bus | YAGNI | **Remove** |
| M35–M37 Evidence Engine | Premature | **Merge** into M05 synthesis vote metadata |
| M51 ui move | High churn | **Defer** until second client |
| M52 delete analyzer | High risk, low reward | **Never require** — compat shims OK |
| Wave order | Evidence before truth | **Wave 0:** journal truth + module tags |

### Revised 18-step critical path

| Step | Purpose |
|------|---------|
| R01 | `BrokerTruthPort` + canonical `TradeRecord` model (doc only → then code) |
| R02 | Journal facade — unified API |
| R03 | Require broker P&L for Review AI |
| R04 | OS module failure tags on trade log |
| R05 | Import-cycle CI (M03) |
| R06 | `platform/data/api.py` facade |
| R07 | Split zerodha auth (only) — security win |
| R08 | Learning facade + single EOD entry |
| R09 | Risk facade wired to OS |
| R10 | Strategy plugin registry + 3 plugins |
| R11 | Synthesis uses registry (flag) |
| R12 | Break watchlist↔learning cycle (inject gates) |
| R13 | `engines/decision/` — move investment_os + synthesis |
| R14 | `engines/learning/` — move journal + tuners |
| R15 | `intelligence/` subpackage (no per-domain facades) |
| R16 | app_hooks extraction |
| R17 | Coach vs broker divergence metric + log |
| R18 | Golden-file OS verdict tests |

**Defer:** Evidence store, event bus, 8 intelligence domains, ui→apps move, analyzer deletion, Postgres, FastAPI.

---

## 21. What the original architecture got right

| Decision | Keep |
|----------|------|
| Investment OS seven-question model | ✅ Core product |
| Recommendation as canonical daily driver | ✅ With narrower scope |
| Unified journal | ✅ #1 priority |
| Strategy plugin registry | ✅ Best OCP win |
| Data Layer / MarketDataPort | ✅ Before licensed data swap |
| Strangler migration concept | ✅ But fewer steps |
| Broker P&L truth emphasis | ✅ Must be Wave 0 not text |
| Risk as separate concern | ✅ |
| FACT/ASSUMPTION labeling | ✅ Inline first |
| Tests gate each step | ✅ Add golden files |
| Feature flags for registry | ✅ |
| Honest gap vs Bloomberg | ✅ From UPGRADE.md |

---

## 22. Architecture decision records (ADR) to add

| ADR | Decision |
|-----|----------|
| ADR-001 | Six boundaries, not sixteen, until team > 3 |
| ADR-002 | Streamlit remains shell until 1k paid users |
| ADR-003 | Broker truth primary for all learning |
| ADR-004 | No event bus until multi-process workers |
| ADR-005 | `analyzer/` compat layer indefinite |
| ADR-006 | Evidence inline on votes; store at 10k users |
| ADR-007 | Licensed data before options SaaS tier |
| ADR-008 | Scale tier triggers (users, jobs/sec) documented |

---

## 23. Final scorecard (architecture quality)

| Dimension | Docs 01–06 score | After critique adjustment |
|-----------|------------------|---------------------------|
| As-is audit accuracy | 9/10 | — |
| Target domain model | 7/10 | **6/10** — over-segmented |
| Migration plan safety | 8/10 | **6/10** — too long |
| Trading decision focus | 6/10 | Must raise to **9/10** via R01–R04 |
| Explainability design | 7/10 | **8/10** if inline evidence |
| Scalability honesty | 5/10 | **8/10** with tier model |
| Complexity control | 4/10 | **7/10** with 6-boundary model |
| Institutional honesty | 5/10 | **8/10** relabel retail-professional |
| 1M-user readiness | 3/10 | **6/10** with explicit runtime replacement path |

---

## 24. Chief Architect ruling

1. **Approve** the problem diagnosis (docs 01–03).  
2. **Revise** the target topology from 16 domains → **6 boundaries** (§19).  
3. **Reorder** migration: **truth pipeline first**, packaging second.  
4. **Reject** near-term: event bus, Evidence domain, 8 intelligence facades, analyzer deletion.  
5. **Add** missing specs: BrokerTruthPort, testing tiers, deployment tiers, observability KPIs.  
6. **Rename** "institutional-grade" → **"professional retail OS"** until broker reconciliation and licensed data exist.

**Next document (if requested):** `08_Revised_Target_Architecture.md` — single source of truth replacing the over-scoped portions of doc 05 and doc 06.

---

## Related documents

- [01_Project_Architecture.md](./01_Project_Architecture.md) — As-is (still valid)
- [05_Target_OS_Architecture.md](./05_Target_OS_Architecture.md) — **Superseded in part** by §19–§20 of this critique
- [06_Migration_Plan.md](./06_Migration_Plan.md) — **Superseded in part** by revised 18-step path
- [03_Technical_Debt.md](./03_Technical_Debt.md) — C5 remains **#1 architectural priority**
- [04_Improvement_Plan.md](./04_Improvement_Plan.md) — Phase 0 aligned; Phase 1 scope should shrink

---

*This critique applies the same rigor to the architecture documents that those documents applied to the codebase. The goal is a system that improves **trading decisions** and **explainability**, not a folder tree that impresses an architecture review.*
