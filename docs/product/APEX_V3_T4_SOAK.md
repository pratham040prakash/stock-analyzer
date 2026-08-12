# APEX V3 — Phase T4 Soak Checklist

**Document ID:** APEX-V3-T4-SOAK  
**Version:** 1.0  
**Status:** ACTIVE  
**Date:** 2026-08-12  
**Parent:** [APEX_V3_TRANSFORMATION_ROADMAP.md](./APEX_V3_TRANSFORMATION_ROADMAP.md) · [APEX_V3_2_SOAK.md](./APEX_V3_2_SOAK.md)

---

## Purpose

Validate **Phase T4 distribution** (T4a → T4e) on production before treating the phase as closed. All T4 features are **additive** — free Today discipline must stay unchanged.

---

## Pre-soak gates (local / CI)

| Gate | Command | Pass criteria |
|------|---------|---------------|
| Capital self-checks | `npm run validate:capital` | Exit 0 |
| RC module checklist | `npm run rc:checklist -- --verify` | Exit 0 |
| Build | `npm run build` | Exit 0 |
| E2E smoke | `npm run test:e2e:smoke` | All pass |
| E2E authed | `APEX_E2E_COOKIE=… npm run test:e2e:authed` | All pass |
| Prod verify | `npm run verify:prod` | Critical checks pass |

---

## Prod manual soak (48h recommended)

### T4a — Wait day brand (public)

- [ ] Landing `/` shows **Most days, Wait is the win.**
- [ ] OpenGraph / meta description present (view page source or share debugger)
- [ ] `/app/you/how-it-works` includes Wait day brand card

### T4b — Kite connect discipline

- [ ] Connect Zerodha card uses discipline copy (not generic broker text)
- [ ] Post-OAuth welcome shows Kite connect discipline card once

### T4c — Advisor B2B pilot (env-gated)

- [ ] Without `APEX_ADVISOR_PILOT_ENABLED`: Review weekly has **no** advisor pack panel
- [ ] With `APEX_ADVISOR_PILOT_ENABLED=true`: panel appears on Review → Weekly + Settings
- [ ] Download advisor pack produces `.md` with weekly discipline + receipts
- [ ] `GET /api/review/advisor-pack` → `{ enabled, seats, pack }` when authed

### T4d — Spouse review invite (on by default)

- [ ] Review → Weekly shows partner invite panel (copy + draft email)
- [ ] Copy message includes anti-leaderboard line (no referral codes)
- [ ] `APEX_SPOUSE_REVIEW_INVITE_ENABLED=false` hides panel
- [ ] `GET /api/review/spouse-invite` → `{ enabled, invite }` when authed

### T4e — ESOP review persona (on by default)

- [ ] How it works includes **Corporate ESOP holders** card
- [ ] Review → Weekly: ESOP panel — copy summary + download `.md`
- [ ] Brief mentions weekly + quarterly review cadence (not stock tips)
- [ ] `APEX_ESOP_REVIEW_PERSONA_ENABLED=false` hides panel

### Regression (T0–T3)

- [ ] Today **Wait · Trade · Pause** unchanged during live Kite poll (no screen flash)
- [ ] Free tier still usable without paying
- [ ] v3.2 monetization migrations still **ready** on `/api/health`

---

## Phase close criteria

All pre-soak gates green · 48h manual soak signed · no P0 regressions on Today or broker connect.

**T4-6** (15k–25k paying users / ₹8–15 Cr ARR) is a **business milestone**, not a deploy gate — track separately in ops.

---

## Optional env (T4)

| Env | Feature |
|-----|---------|
| `APEX_ADVISOR_PILOT_ENABLED=true` | Advisor review pack |
| `APEX_ADVISOR_PILOT_SEATS=1` | Seat count in pack |
| `APEX_SPOUSE_REVIEW_INVITE_ENABLED=false` | Hide spouse invite |
| `APEX_ESOP_REVIEW_PERSONA_ENABLED=false` | Hide ESOP persona |

---

## Rollback

Revert deploy to prior commit. T4 panels are env-gated or inert when disabled — free tier unaffected.
