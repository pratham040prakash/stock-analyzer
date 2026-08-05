# APEX-000 — Company Constitution

**Document ID:** APEX-000  
**Version:** 0.1  
**Status:** DRAFT — pending Founder + CTO approval  
**Date:** 2026-08-05  
**Owner:** Pratham Prakash (Founder & CEO)  
**Author:** Cursor AI (Engineering Team)  
**Reviewers:** ChatGPT (CTO) — pending  
**Supersedes:** None (consolidates `docs/design/Product_Constitution_LOCKED.md`, `docs/architecture/08_Final_Investment_OS_Architecture.md` principles)  
**References:** None — this is the root document

---

## Authority

This is the **highest-level document** in APEX. All other documents — APEX-001 through APEX-998, ADRs, RFCs, ETS specs, and the Engineering Handbook (APEX-999) — must align with this constitution.

If any document conflicts with APEX-000, **this document wins** unless explicitly amended through Founder + CTO approval.

---

## Governance & Roles

### Role definitions

| Role | Name / System | Scope |
|------|---------------|-------|
| **Founder & CEO** | Pratham Prakash | Vision, business strategy, customer validation, roadmap, final business decisions, release approval |
| **CTO & Chief Product Architect** | ChatGPT | Architecture, engineering standards, AI architecture, technical strategy, all RFC/ADR/ETS review, code review |
| **Engineering Team** | Cursor AI | Implementation, testing, documentation drafts, approved refactoring — under CTO and Founder authority |

### Decision Authority Matrix

| Domain | Owner | Changes require |
|--------|-------|-------------------|
| Business strategy | Founder | Founder approval |
| Product vision | Founder + CTO | Founder + CTO approval |
| Architecture | CTO | CTO approval + ADR |
| Engineering standards | CTO | CTO approval |
| Design system | CTO | CTO approval |
| Technology stack | CTO | CTO approval + ADR |
| Repository structure | CTO | CTO approval |
| Implementation | Cursor | Approved ETS; CTO code review |
| Testing | Cursor | CI green |
| Documentation | Cursor | CTO review (APEX/ADR/RFC/ETS) |
| Code reviews | CTO | CTO sign-off |
| Release approval | Founder + CTO | Both |
| Major refactoring | — | **Founder + CTO** |
| Architecture changes | — | **CTO + ADR** |
| Business logic changes | — | **Founder** |

Engineering (Cursor) **must not** change product direction, change architecture without approval, delete working business logic without approval, or make business decisions. When requirements are ambiguous: state assumptions, present alternatives and trade-offs, recommend, then **wait for approval**.

---

## 1. Mission

Help investors consistently make **better decisions** that improve **long-term, risk-adjusted returns**.

APEX is not a prediction engine, a tip service, or a charting tool. It is a **decision operating system** that runs a disciplined investment process every day.

---

## 2. Vision

Become the **trusted AI Investment Operating System** for individual investors — starting with Indian markets — where users pay for **discipline, explainability, and improvement**, not for hot tips or guaranteed returns.

**One sentence:** APEX turns investing from reactive guessing into a repeatable, auditable, self-improving decision process.

**Horizon:** Enable any investor — from ₹9,000 MIS pool to ₹9 crore portfolio — to operate with institutional-grade process integrity.

---

## 3. Core Values

| Value | Meaning | Violation example |
|-------|---------|-------------------|
| **Truth over narrative** | Broker-verified outcomes beat model predictions | Learning loop tuned on coach proxy P&L |
| **Preservation before growth** | Capital protection is the first optimization | Aggressive default-to-trade UX |
| **Explainability** | Every recommendation traceable to evidence | Black-box scores without provenance |
| **Intellectual honesty** | Label FACT · ASSUMPTION · ESTIMATE · OPINION | Invented metrics or certainty claims |
| **Default to WAIT** | Inaction is a valid, often optimal decision | Activity-biased nudges to increase churn |
| **Continuous learning** | Pain + reflection = progress | Static thresholds never updated from outcomes |
| **Simplicity** | One clear answer beats ten dashboards | Feature sprawl without decision impact |

---

## 4. Product Philosophy

### 4.1 Primary user question

> **"What should I do with my money today, and why?"**

Every feature, surface, and engineering decision must support answering this question. If it does not, do not build it.

### 4.2 Product identity

| Concept | Name |
|---------|------|
| Repository | `stock-analyzer` (during migration) |
| Legacy product | Stock Analyzer V2 |
| Current product | **APEX** — AI Investment Operating System |

### 4.3 Six partner surfaces (non-negotiable)

No seventh surface. No alternate navigation shell. No additional product modes.

| Surface | Purpose | Answers |
|---------|---------|---------|
| **Today** | Command center | Should I trade? What deserves attention? What blocks me? |
| **Trades** | Execution | Entry · Stop · Target · Risk · Timing |
| **You** | Relationship | Trader state · behaviour · one portfolio action · one improvement |
| **Ask** | One-shot doubt | One question · one answer · no threads |
| **Trust** | Accountability | Honest track record · not vanity analytics |
| **Proof** | Evidence | AI-annotated evidence · not a charting workspace |

**Today is the product.** All other surfaces support Today.

### 4.4 Depth philosophy

Depth lives in **Proof** and **Ask** overlays — not in additional tabs, dashboards, or report pages. Legacy feature tabs exist during migration only and must retire into surfaces.

### 4.5 Product gate

Before any feature ships, answer:

> *Does this help the user make a better investment decision?*

If **no** → do not build.

---

## 5. Engineering Philosophy

| Principle | Application |
|-----------|-------------|
| **Architecture first** | Structure before features; boundaries before modules |
| **Product first** | Engineering serves decision quality, not engineering elegance |
| **User first** | Time-to-clarity beats time-to-data |
| **Security first** | No hosted deploy without auth, secrets hardening, and data protection |
| **Evolutionary migration** | Never greenfield; never rewrite working business logic without justification |
| **Documentation first** | If it is not documented, it is not done |
| **Testability first** | Decision pipelines must be verifiable without UI |
| **Simplicity first** | Prefer 6 boundaries over 16 domains until scale demands otherwise |

### Repository strategy

```
Legacy V2 → Architecture Audit → New Architecture → Module Migration → Legacy Retirement
```

Never delete large code sections before understanding their purpose.

---

## 6. AI Philosophy

### 6.1 What AI is in APEX

AI is a **decision support layer** — not an oracle, not an autonomous trader, not a return guarantee.

AI synthesizes evidence, surfaces conflicts, explains reasoning, and learns from verified outcomes. The **user always decides**.

### 6.2 Three laws of AI in APEX

1. **No invented certainty.** Every output carries an uncertainty band. Never speak in guarantees.
2. **Broker truth beats model truth.** Learning uses what happened to the user's money, not what the coach hoped.
3. **Facts before narrative.** LLM synthesis (when used) operates on structured evidence only — never invent numbers.

### 6.3 AI boundaries

| AI may | AI may not |
|--------|------------|
| Assemble and label evidence | Execute trades autonomously |
| Synthesize narrative from facts | Invent financial metrics |
| Detect conflicts in evidence | Override risk gates or capital constraints |
| Propose scenarios with probabilities | Claim prediction accuracy |
| Learn from broker-verified outcomes | Optimize for activity or engagement |

### 6.4 Four-engine model

All AI and analytical output flows through:

```
Context Engine → Evidence Engine → Decision Engine
                                        ↑
                              Broker Truth (ground truth)
```

Only the **Decision Engine** issues verdicts: ACT · WAIT · PASS · REDUCE · DEFENSIVE.

---

## 7. Design Philosophy

| Principle | Rule |
|-----------|------|
| **Verdict is hero** | Today leads with the decision, not data |
| **Prose over dashboards** | Supporting intelligence is narrative, not metric grids |
| **Progressive disclosure** | Proof and Ask provide depth on demand |
| **Calm over excitement** | No FOMO patterns, no urgency manipulation |
| **Trust through honesty** | Trust surface shows failures, not just wins |
| **One action per surface** | You gives one portfolio action; Ask gives one answer |

Visual design follows [APEX-007 Design System](./APEX-007_Design_System.md) when approved. Until then, `docs/design/Phase_*` specs apply.

---

## 8. Decision Framework

Governance roles and the Decision Authority Matrix are defined in **Governance & Roles** above. This section defines *how* decisions are evaluated and processed.

### 8.1 Decision process by type

| Type | Process | Approver |
|------|---------|----------|
| Strategic (vision, roadmap, pricing, SaaS model) | RFC optional → Founder decision | Founder (+ CTO consult) |
| Architecture (boundaries, stack, security design) | RFC optional → **ADR required** → ETS | CTO |
| Product (surfaces, features, UX flows) | Product gate (§4.5) → ETS | Founder (+ CTO if architectural) |
| Business logic (scoring rules, thresholds, verdict logic) | Impact doc → ETS | **Founder** |
| Engineering (module refactor, tests, perf within bounds) | ETS → implement → code review | Cursor → CTO review |
| Major refactoring | RFC → ADR → ETS | **Founder + CTO** |

Standard flow: **RFC (optional) → ADR (if architectural) → ETS (implementation) → Code Review (CTO) → Release (Founder + CTO)**.

### 8.2 Escalation rules

- Cursor **must escalate** when: requirements ambiguous, architecture impact unclear, business logic affected, major dependency proposed, or working logic deletion proposed.
- CTO **must challenge** when: decision violates APEX-000 non-negotiables, increases complexity without decision-quality benefit, or bypasses four-engine pipeline.
- Founder **must decide** when: business strategy, product direction, business logic, or release timing in dispute.

### 8.3 Decision evaluation matrix

Score each proposed initiative:

| Criterion | Weight | Question |
|-----------|--------|----------|
| Decision quality impact | 30% | Does this improve the user's investment decisions? |
| Trust impact | 25% | Does this increase or decrease user confidence in APEX? |
| Engineering cost | 20% | What is the implementation and maintenance cost? |
| Risk reduction | 15% | Does this reduce critical technical or product risk? |
| Revenue enablement | 10% | Does this unlock a commercial path? |

Reject initiatives that score high on engineering elegance but low on decision quality impact.

---

## 9. Quality Standards

### 9.1 Product quality

| Standard | Threshold |
|----------|-----------|
| Morning readiness | Grade B or higher (CPO assessment) |
| Verdict consistency | Single DecisionArtifact per symbol per session |
| Evidence traceability | 100% of ACT verdicts have EvidencePacket |
| Broker learning coverage | ≥90% of scored outcomes broker-verified |
| Recommendation trust | User can explain *why* for every ACT verdict |

### 9.2 Engineering quality

| Standard | Threshold |
|----------|-----------|
| Test pass rate | 100% in CI |
| Architecture compliance | ≥96/100 against four-engine model |
| Critical security debt | Zero before hosted multi-user deploy |
| Documentation coverage | Every domain boundary documented in APEX catalog |
| New code test coverage | ≥1 test per public function in decision path |

### 9.3 AI quality

| Standard | Threshold |
|----------|-----------|
| Hallucination rate | Zero invented financial metrics |
| Label compliance | 100% of claims labeled FACT/ASSUMPTION/ESTIMATE/OPINION |
| LLM opt-in | LLM narrative disabled by default; env-gated |
| Conflict detection | Evidence Engine flags contradictions before verdict |

---

## 10. Non-Negotiable Rules

These rules cannot be waived without Founder + CTO written amendment to this document.

| # | Rule |
|---|------|
| N1 | Default action is **WAIT** — trade only when context, thesis, evidence, risk, and execution align |
| N2 | **Broker truth beats model truth** in all learning loops |
| N3 | **No invented certainty** — no guaranteed returns, no prediction claims |
| N4 | **Decision Engine is sole verdict authority** — no parallel recommendation paths |
| N5 | **Six surfaces only** — no seventh navigation paradigm |
| N6 | **Evolutionary migration** — no greenfield rewrite of working domain logic |
| N7 | **No hosted multi-user deploy** until C1–C3 security debt resolved |
| N8 | **Every feature passes the product gate** (§4.5) |
| N9 | **Documentation before implementation** for architectural changes |
| N10 | **Repository name stays `stock-analyzer`** until explicit migration decision |

---

## 11. Long-Term Vision

### Phase horizon

| Phase | State | Trigger |
|-------|-------|---------|
| **Now — Sprint 0** | Documentation & architecture baseline | Current |
| **Phase 1** | Six-surface UX; DecisionArtifact end-to-end | Sprint 0 approved |
| **Phase 2** | Six-boundary package architecture | Phase 1 complete |
| **Phase 3** | Platform readiness (auth, API, licensed data) | SaaS decision |
| **Phase 4** | Scale (multi-broker, plugin registry, mobile) | User demand |
| **Phase 5** | APEX commercial SaaS | Founder launch decision |

### What APEX becomes

A platform where:

- Individual investors operate with institutional-grade process
- Every decision is evidence-backed, risk-gated, and auditable
- The system learns from real money outcomes, not simulations
- Users compound wealth through discipline, not activity
- Engineering scales through boundaries, not hero modules

### What APEX does not become

- A social trading platform
- An autonomous trading bot
- A financial data terminal
- A get-rich-quick recommendation engine
- A feature-bloated dashboard product

---

## 12. North Star Metric

**Calibrated Decision Quality Score (CDQS)**

Composite metric measuring whether APEX recommendations, when acted upon, produce outcomes aligned with stated confidence and risk parameters — verified against broker P&L.

```
CDQS = (Broker-verified outcomes matching confidence band) / (Total ACT verdicts acted upon)
```

| CDQS Range | Interpretation |
|------------|----------------|
| ≥ 0.80 | System is trustworthy at stated confidence levels |
| 0.60 – 0.79 | Calibration needed; threshold tuning active |
| < 0.60 | Trust failure; halt new feature work; fix learning loop |

CDQS is reported on the **Trust** surface. It is the single metric that validates whether APEX fulfills its mission.

Secondary metrics: Time to First Value, Decision Latency, User Confidence (qualitative), Developer Onboarding Time.

---

## Amendment Process

1. Author proposes amendment via RFC
2. CTO reviews technical and product alignment
3. Founder approves business-impacting changes
4. APEX-000 version incremented (e.g. 0.1 → 1.0)
5. All dependent documents reviewed for alignment within 30 days

---

*Repository: stock-analyzer · Product: APEX · Document: APEX-000 · Root authority*
