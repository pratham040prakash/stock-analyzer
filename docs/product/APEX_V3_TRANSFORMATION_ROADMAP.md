# APEX V3 — Transformation Roadmap (Architecture → Surface → ₹100 Cr)

**Document ID:** APEX-V3-TRANSFORMATION-ROADMAP  
**Version:** 1.0  
**Status:** ACTIVE — execution track after Sprints W–Y  
**Date:** 2026-08-11  
**Owner:** Product · CTO  
**Parent:** [APEX_V3_ROADMAP.md](./APEX_V3_ROADMAP.md) · [APEX-000](../apex/APEX-000_Company_Constitution.md) · [08 Final IOS](../architecture/08_Final_Investment_OS_Architecture.md)  
**Baseline code:** `main` @ Sprints W–Y (`7f1e8a6+`)

---

## Executive summary

**V3 feature pillars are shipped** (Portfolio, Research, Review, You, receipts, thesis, discipline).  
**The product fails user #1** (founder, zero stock knowledge) because the **architecture is not visible on Today**.

This roadmap is the **only active execution track** until:

1. Today shows **Wait · Trade · Pause** in plain language  
2. Capital **dams** (sacred core, tactical pool, daily loss) appear **before** buttons  
3. Founder signs off: *“I knew what to do without stock knowledge”*

**North star (company):** Discipline infrastructure for Zerodha-connected investors — broker-verified receipts, calm daily verdict, review rituals.  
**North star (user):** Preserve capital first; compound over years; most days = **Wait**.  
**Valuation path (ESTIMATE):** ~15k–25k paying users × ₹4k–5k/yr → ₹8–15 Cr ARR → ₹80–120 Cr at 10× — **only if retention proves trust**, not tips.

---

## Diagnosis (architecture vs UI)

| Layer | Status | Evidence |
|-------|--------|----------|
| **Architecture (engine)** | ~70% aligned | `capitalDecision.ts`, broker sync, receipts, review, `riskControl.ts`, `allocationPolicy.ts` |
| **Surface (Today UX)** | ~20% aligned | ACT/WAIT/TRIM/EXPLORE; dense `HomeDecisionScreen`; no Pause hero; no operating manual |
| **Loss attribution** | UI first | User built OS but cannot follow screen — beginner persona failed |

**Rule:** Do not add nav/features until Phase T0 exit criteria pass.

---

## Phase map (2026 Q3 → 2028)

```text
2026 Aug–Sep     2026 Oct–Dec        2027 H1             2027 H2             2028+
     │                │                   │                   │                  │
     ▼                ▼                   ▼                   ▼                  ▼
  Phase T0         Phase T1            Phase T2            Phase T3           Phase T4
  Surface the      Operating           Trust &             Monetization       Scale to
  architecture     manual + rc1        CDQS + premium      + GTM              ₹100 Cr path
  (6 weeks)        GA                  (retention)         (15k paying)
```

| Phase | Tag target | Theme |
|-------|------------|--------|
| **T0** | — | Wait · Trade · Pause + minimal Today |
| **T1** | `v3.0.0-rc1` → `v3.0.0` | Onboarding, sector caps, soak, GA |
| **T2** | `v3.1.0` | CDQS, outcome loop, mobile, hide auto-trade |
| **T3** | `v3.2.0` | Premium launch, digest, thesis export |
| **T4** | — | Distribution, B2B RIA pilot, 15k+ paying |

---

## Severity legend

| Level | Meaning | Gate |
|-------|---------|------|
| **S0** | Trust / wrong action / money at risk | Blocks all feature work |
| **S1** | Architecture not visible; beginner lost | Blocks rc1 |
| **S2** | Ops, polish, monetization prep | After S0–S1 |
| **S3** | v3.1+ maintenance | After GA |

---

# Phase T0 — Surface the architecture (Weeks 1–6)

**Theme:** *One verdict. One pool. One horizon. Plain language.*

**Reuses:** `lib/dailyLoop/capitalDecision.ts`, `todaySurface.ts`, `projectVerdict.ts`, `VerdictCanvas.tsx`, `disciplineStreak*`, `riskControl.ts`, `allocationPolicy.ts`, `apexVoice.ts`

### Sprint Z1 (Week 1–2) — S0 verdict projection

| ID | Deliverable | Severity | Implementation notes |
|----|-------------|----------|-------------------|
| **Z1-1** | `resolveDailyVerdict()` → `wait \| trade \| pause` | S0 | New `lib/dailyLoop/dailyVerdict.ts`; maps BUY+confirmed→trade, loss streak/dam→pause, else wait |
| **Z1-2** | Replace hero ACT/WAIT/TRIM/EXPLORE with Wait/Trade/Pause | S0 | `VerdictCanvas.tsx`, `resolveVerdictWord()` deprecation path |
| **Z1-3** | Title case mentor copy (not all-caps) | S0 | Phase 1 canvas spec; `apexVoice.ts` |
| **Z1-4** | **Pause** locks Trade CTAs | S0 | `HomeDecisionScreen`, `TodayExecutionPanel` |
| **Z1-5** | Entry confirmed gates **Trade** | S0 | Wire `ExecutionPlanCard` / entry timing to verdict |
| **Z1-6** | Self-checks + unit tests for verdict map | S0 | `validate-capital.ts` |

**Exit:** Hero shows only Wait | Trade | Pause; Pause day has no buy button.

### Sprint Z2 (Week 3–4) — S0 capital dams on surface

| ID | Deliverable | Severity | Implementation notes |
|----|-------------|----------|-------------------|
| **Z2-1** | `OperatingManualStrip` on Today | S0 | Plan pill: Core / Tactical / Not intraday |
| **Z2-2** | Sacred core gating | S0 | `classifyBucket()` — core symbols → no Today buy |
| **Z2-3** | Daily max loss visible before trade | S0 | Surface `riskControl.ts` limits on hero; hit → Pause |
| **Z2-4** | Tactical pool scope line | S0 | “Today applies to ₹X tactical only” from brief/cash |
| **Z2-5** | Collapse Today panels → **Details** accordion | S0 | `HomeDecisionScreen` — verdict + 1 CTA + Details |
| **Z2-6** | **“You’re done for today”** on Wait/Pause | S0 | Primary CTA Phase 1 spec |

**Exit:** Founder can state pool + horizon + verdict in one sentence after 10s on Today.

### Sprint Z3 (Week 5–6) — S1 onboarding + docs

| ID | Deliverable | Severity | Implementation notes |
|----|-------------|----------|-------------------|
| **Z3-1** | `OperatingProfile` schema + migration | S1 | `operating_profile.sql`; style: long_term_only \| core_plus_tactical \| tactical_only |
| **Z3-2** | Onboarding step after profile | S1 | Extend `firstRun.ts`, `InvestmentStyleSetup.tsx` |
| **Z3-3** | Intraday acknowledgment checkbox | S1 | Required before Today |
| **Z3-4** | Static **How APEX works** help page | S1 | Long-term / swing / not intraday playbooks |
| **Z3-5** | Rename intent in UI (not API) | S1 | grow→Deploy tactical; protect→Protect capital; explore→Stay in cash |
| **Z3-6** | ETS-004 Operating Manual spec | S1 | Copy deck ≤20 strings |

**Exit:** New user cannot reach Today without investment style; help page linked from strip.

**Phase T0 gate (founder sign-off):**

- [ ] I knew what to do without stock knowledge  
- [ ] Most sessions end in Wait or Pause without guilt  
- [ ] `npm run build` + `validate-capital` green  

---

# Phase T1 — RC1, soak, GA (Weeks 7–10)

**Theme:** *Ship trust, not features.*

| ID | Deliverable | Severity | Notes |
|----|-------------|----------|-------|
| **T1-1** | Sector cap strip on Portfolio (+ optional Today) | S1 | Top sector vs `sectorCapPct` default 30% |
| **T1-2** | Planned vs actual reconcile prominence | S1 | Review tab; `plannedVsActual.ts` |
| **T1-3** | Supabase migrations applied on prod | S2 | `npm run db:migrate:checklist` |
| **T1-4** | `verify:prod` + e2e green | S2 | See [APEX_V3_RC1_SOAK.md](./APEX_V3_RC1_SOAK.md) |
| **T1-5** | Alpha worker + Kite proxy live | S2 | `verify:deploy` |
| **T1-6** | 48h prod soak | S2 | Manual checklist |
| **T1-7** | Tag **`v3.0.0-rc1`** | S2 | After T0 gate + soak |
| **T1-8** | Tag **`v3.0.0`** GA | S2 | Roadmap v1.0 freeze; engineering review archive |
| **T1-9** | Amend APEX-000 vs V3 IA | S2 | Single canonical nav + verdict doc | **✅ Shipped** — [APEX_V3_CANONICAL_IA.md](./APEX_V3_CANONICAL_IA.md) + APEX-000 v0.2 |

**Non-goals:** New pages, Alpha portfolio drill-down, auto-trade expansion.

---

# Phase T2 — Trust & retention (Months 3–6)

**Theme:** *Prove discipline, not returns.*

| ID | Deliverable | Outcome |
|----|-------------|---------|
| **T2-1** | **CDQS** on Trust surface | Constitution north star visible | **✅ Shipped** — `services/trust/cdqs.ts`, Trust canvas |
| **T2-2** | Broker-verified outcome loop UI | `trustOutcome.ts`, `outcomeEngine.ts` → user-facing | **✅ Shipped** — Trust canvas last close + scores |
| **T2-3** | Override tracking | Traded when Wait shown → metric ↓ over time | **✅ Shipped** — 14d override strip on Trust |
| **T2-4** | Hide / gate **autoExecute** default off | Constitution alignment | **✅ Shipped** — `APEX_AUTO_TRADE_ENABLED` env gate (default off) |
| **T2-5** | Mobile-first Today polish | India usage | **✅ Shipped** — safe-area shell, touch nav, responsive verdict |
| **T2-6** | Weekly digest discipline summary | “4/5 days followed plan” | **✅ Shipped** — digest line + Review weekly strip |
| **T2-7** | Tag **`v3.1.0`** | Trust release |

**Metrics gate (90 days post-GA):**

| Metric | Target |
|--------|--------|
| D7 retention | >40% |
| D30 retention | >25% |
| Sessions ending Wait/Pause | >70% |
| “Confused” support / founder feedback | ↓ 50% vs baseline |
| NPS | >40 |

---

# Phase T3 — Monetization (Months 6–12)

**Theme:** *Pay for ritual + depth, not tips.*

| Tier | Free | Premium (ESTIMATE ₹299–499/mo or ₹3,999–4,999/yr) |
|------|------|-----------------------------------------------------|
| Today Wait/Trade/Pause | ✅ | ✅ |
| Portfolio overview | ✅ | ✅ |
| Review weekly | ✅ | ✅ |
| Margin deploy mode | — | ✅ (`CapitalModeToggle`) |
| Review digest (TG/email) | — | ✅ |
| Thesis export / investment book | — | ✅ |
| Monthly/quarterly doctor alerts | Basic | Full drift |
| Alpha AI deep research | — | ✅ (hosted worker) |
| Trust CDQS history | — | ✅ |

| ID | Deliverable |
|----|-------------|
| **T3-1** | Premium packaging + paywall copy tied to ROI | ✅ Shipped (T3a) |
| **T3-2** | Razorpay / subscription flow hardening | ✅ Shipped (T3b) |
| **T3-3** | Conversion funnel: free → first WAIT receipt → premium trial | ✅ Shipped (T3c) |
| **T3-4** | Tag **`v3.2.0`** | ✅ Release prep shipped (T3d) — tag after soak |

**Target:** 1,000 paying users · validate willingness to pay for **discipline**, not alpha.

---

# Phase T4 — Scale toward ₹100 Cr (Year 2)

**Theme:** *Distribution + B2B + retention at scale.*

| ID | Channel | Deliverable |
|----|---------|-------------|
| **T4-1** | Content GTM | “Wait day” brand; anti-FOMO | ✅ Shipped (T4a) |
| **T4-2** | Zerodha-adjacent audience | After Kite connect → APEX discipline | ✅ Shipped (T4b) |
| **T4-3** | RIA / advisor B2B pilot | Receipts + review seats | ✅ Shipped (T4c) |
| **T4-4** | Referral | Spouse Review invite (not leaderboard) | ✅ Shipped (T4d) |
| **T4-5** | Corporate ESOP | Long-term + review persona |
| **T4-6** | 15k–25k paying users | ₹8–15 Cr ARR path |

**Valuation narrative (ESTIMATE):** Retention SaaS on broker-connected cohort + trust moat (receipts, broker truth).

---

## What is built vs what this roadmap adds

### Already shipped (do not rebuild)

- Portfolio command center, holdings, allocation policy UI  
- Research workbench, thesis CRUD, new capital workflow  
- Review weekly / monthly / quarterly, digest cron scaffold  
- Receipts, discipline streak, broker reconcile  
- Ask overlay, Trust/Proof depth, You snapshot  
- Zerodha sync, execute path, risk at order time  
- W–Y: hold/skip trim, silent P&L, verify-prod, rc-checklist  

### Not shipped (this roadmap)

- Wait · Trade · Pause hero  
- Pause as system state on Today  
- Sacred core **gating** (not just copy)  
- Daily loss dam **before** buttons  
- Operating profile onboarding  
- Minimal Today canvas  
- CDQS productized  
- Premium ROI story + scale GTM  

---

## Explicit exclusions (all phases)

- Intraday trading product  
- Social / copy trading / leaderboards  
- Guaranteed returns marketing  
- Chat threads (Ask stays one-shot)  
- New nav pages before T0 gate  
- Default-on auto-trading  

---

## Release train (updated)

| Tag | When | Criteria |
|-----|------|----------|
| `7f1e8a6` | 2026-08-11 ✅ | Sprints W–Y |
| **`v3.0.0-rc1`** | After T0 + T1 soak | Founder sign-off + verify:prod |
| **`v3.0.0`** | +2–4 weeks | GA docs freeze |
| **`v3.1.0`** | +3–6 months | CDQS + retention metrics |
| **`v3.2.0`** | +6–12 months | Premium + 1k paying |
| **₹100 Cr conversation** | Year 2+ | 15k+ paying, <30% annual churn |

---

## Sprint calendar (next 10 weeks)

| Week | Sprint | Focus |
|------|--------|--------|
| 1–2 | **Z1** | `dailyVerdict.ts`, VerdictCanvas, Pause lock |
| 3–4 | **Z2** | Operating strip, gating, collapse Today |
| 5–6 | **Z3** | Onboarding, help page, ETS-004 |
| 7–8 | **T1-a** | Sector cap, reconcile, prod migrations |
| 9–10 | **T1-b** | Soak, rc1 tag, GA prep |

---

## Ownership

| Role | Responsibility |
|------|----------------|
| **Founder / CEO** | T0 gate sign-off; dogfood daily; GTM narrative |
| **CTO** | Verdict projection design; constitution amendments; quality bar |
| **Engineering** | Z1–Z3 implementation; no scope outside roadmap without approval |
| **Product** | Copy deck; ETS-004; soak checklist updates |

---

## References

- [APEX_V3_RC1_SOAK.md](./APEX_V3_RC1_SOAK.md)  
- [APEX_UX_MANIFESTO.md](./APEX_UX_MANIFESTO.md)  
- [Phase 1 Verdict Canvas](../design/Phase_1_Verdict_Canvas_Spec.md)  
- Code index: `apex-ui/lib/dailyLoop/`, `components/HomeDecisionScreen.tsx`, `services/risk/riskControl.ts`

---

## Amendment log

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-08-11 | Initial transformation track post W–Y; T0–T4; ₹100 Cr path |
