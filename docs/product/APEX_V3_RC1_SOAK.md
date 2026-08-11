# APEX V3 — v3.0.0-rc1 Soak Checklist

**Document ID:** APEX-V3-RC1-SOAK  
**Version:** 1.0  
**Status:** ACTIVE  
**Date:** 2026-08-11  
**Parent:** [APEX_V3_ROADMAP.md](./APEX_V3_ROADMAP.md)

---

## Purpose

Validate Sprints W–Y on production before tagging `v3.0.0-rc1`. Soak focuses on broker UX, silent data refresh, auth gates, and review digest cron — not new feature work.

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

### Today / broker (Sprint W)

- [ ] Single-share trim shows **full exit or hold** — not misleading partial %
- [ ] **Hold position — skip trim** records WAIT streak and shows “holding position today”
- [ ] Zerodha funds / P&L refresh without “Syncing Zerodha funds…” flash
- [ ] Breakout setups show **wait-for-breakout** copy until entry confirmed

### Auth & cron (Sprint X)

- [ ] `/api/cron/review-digest` returns **401** without `Authorization: Bearer $CRON_SECRET`
- [ ] Protected API routes return JSON error envelope when unauthenticated
- [ ] GitHub `apex-prod-verify` workflow green with `APEX_VERIFY_COOKIE`

### Review digest (optional)

- [ ] `APEX_REVIEW_DIGEST_ENABLED=true` on Vercel
- [ ] Telegram or webhook receives test digest after cron trigger
- [ ] No PII in digest payload beyond user-owned portfolio summary

### Database

- [ ] All migrations applied via `npm run db:migrate:checklist`
- [ ] RLS policies idempotent (re-run safe)

---

## Tag procedure

Only after all gates and soak items pass:

```bash
git tag -a v3.0.0-rc1 -m "APEX V3 release candidate 1 — Sprints W–Y"
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
| Product | | | soak checklist |
| Ops | | | migrations + env |
