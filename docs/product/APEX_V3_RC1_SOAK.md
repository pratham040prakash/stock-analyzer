# APEX V3 — v3.0.0-rc1 Soak Checklist

**Document ID:** APEX-V3-RC1-SOAK  
**Version:** 1.1  
**Status:** ACTIVE  
**Date:** 2026-08-11  
**Parent:** [APEX_V3_ROADMAP.md](./APEX_V3_ROADMAP.md) · [APEX_V3_TRANSFORMATION_ROADMAP.md](./APEX_V3_TRANSFORMATION_ROADMAP.md)

---

## Purpose

Validate Phase T0 (surface architecture) and Phase T1 (rc1 readiness) on production before tagging `v3.0.0-rc1`. Soak focuses on **Wait · Trade · Pause**, capital dams, onboarding, broker UX, and ops gates — not new feature work.

---

## Pre-tag gates (local / CI)

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

### Today — Phase T0 (Sprints Z1–Z3)

- [ ] Hero shows only **Wait**, **Trade**, or **Pause** — not ACT/TRIM/EXPLORE
- [ ] **Pause** day has no buy button; copy explains why (loss streak / daily dam)
- [ ] **Operating manual strip** visible: Core / Tactical / Not intraday
- [ ] **Capital dams strip** shows daily max loss before any trade CTA
- [ ] Sacred core holdings → no Today buy suggestion
- [ ] **Details** accordion collapses portfolio / monitor / depth below fold
- [ ] Wait or Pause → primary CTA feels like “You’re done for today”
- [ ] New user **cannot reach Today** without investment style + intraday ack
- [ ] **How APEX works** linked from strip (`/app/you/how-it-works`) — see [APEX_V3_CANONICAL_IA.md](./APEX_V3_CANONICAL_IA.md)

### Portfolio / Review — Phase T1a

- [ ] **Sector cap strip** warns when top sector exceeds ~30%
- [ ] **Review weekly** shows planned vs actual summary at top

### Broker (Sprint W)

- [ ] Single-share trim shows **full exit or hold** — not misleading partial %
- [ ] **Hold position — skip trim** records WAIT streak
- [ ] Zerodha funds / P&L refresh without “Syncing Zerodha funds…” flash
- [ ] Breakout setups show **wait-for-breakout** copy until entry confirmed
- [ ] No conflicting “Session expired” + “Zerodha connected” banners

### Auth & cron (Sprint X)

- [ ] `/api/cron/review-digest` returns **401** without `Authorization: Bearer $CRON_SECRET`
- [ ] Protected API routes return JSON error envelope when unauthenticated
- [ ] GitHub `apex-prod-verify` workflow green with `APEX_VERIFY_COOKIE`

### Operating profile (T1 ops)

- [ ] `GET /api/health` → `migrations.operating_profile` is **`ready`** (not `pending`)
- [ ] Onboarding Step 3 saves to server (not only localStorage)
- [ ] Users who saved locally during 503 auto-sync profile on next visit

### Review digest (optional)

- [ ] `APEX_REVIEW_DIGEST_ENABLED=true` on Vercel
- [ ] Telegram or webhook receives test digest after cron trigger
- [ ] No PII in digest payload beyond user-owned portfolio summary

### Database

- [ ] All migrations applied via `npm run db:migrate:checklist` (includes `operating_profile.sql`)
- [ ] RLS policies idempotent (re-run safe)

---

## Founder T0 gate (required before rc1 tag)

- [ ] *“I knew what to do without stock knowledge”*
- [ ] Most sessions end in Wait or Pause without guilt
- [ ] `npm run build` + `validate:capital` green

---

## Tag procedure

Only after all gates, soak items, and founder T0 gate pass:

```bash
git tag -a v3.0.0-rc1 -m "APEX V3 release candidate 1 — Phase T0 surface + T1 rc1"
git push origin v3.0.0-rc1
```

---

## Rollback

- Revert Vercel deployment to prior production build
- Disable digest cron in `vercel.json` or unset `APEX_REVIEW_DIGEST_ENABLED`
- Do not delete migration tables; rc1 is forward-only

---

## Sign-off

| Role | Name | Date | Notes |
|------|------|------|-------|
| Engineering | | | verify:prod + build |
| Product | | | soak checklist + T0 gate |
| Ops | | | migrations + env |
