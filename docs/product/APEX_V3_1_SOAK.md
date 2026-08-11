# APEX V3 — v3.1.0 Soak Checklist

**Document ID:** APEX-V3-1-SOAK  
**Version:** 1.0  
**Status:** ACTIVE  
**Date:** 2026-08-11  
**Parent:** [APEX_V3_TRANSFORMATION_ROADMAP.md](./APEX_V3_TRANSFORMATION_ROADMAP.md) · [APEX_V3_RC1_SOAK.md](./APEX_V3_RC1_SOAK.md)

---

## Purpose

Validate Phase T2 (Trust + discipline loop) and Sprint T3-1 (premium packaging) on production before tagging **`v3.1.0`**. Assumes **`v3.0.0-rc1`** soak passed or is in progress.

---

## Pre-tag gates (local / CI)

| Gate | Command | Pass criteria |
|------|---------|---------------|
| Capital self-checks | `npm run validate:capital` | Exit 0 (includes `runPremiumCopySelfCheck`) |
| RC module checklist | `npm run rc:checklist -- --verify` | Exit 0 |
| Build | `npm run build` | Exit 0 |
| E2E smoke | `npm run test:e2e:smoke` | All pass |
| E2E authed | `APEX_E2E_COOKIE=… npm run test:e2e:authed` | All pass (thesis export accepts 403 or 200) |
| Prod verify | `npm run verify:prod` | Critical checks pass |

---

## Prod manual soak (48h recommended)

### Trust — Phase T2 (T2-1 → T2-6)

- [ ] `/app/trust` shows **CDQS** score + interpretation
- [ ] **Last broker-verified close** visible when outcome data exists
- [ ] **Override discipline (14 days)** headline + count
- [ ] Free tier shows **CDQS trend history** premium gate (not blank error)
- [ ] `/api/you/snapshot` returns `cdqs_*` and `override_*` fields

### Review discipline digest — T2c

- [ ] Review weekly tab shows **discipline digest strip** (plan follow-through line)
- [ ] Mobile: verdict + nav usable at 375px width (safe-area, touch targets)

### Premium packaging — T3-1

- [ ] Free user on **Settings** sees `PremiumValueCard` + locked export/digest gates
- [ ] `GET /api/thesis/export` → **403** with Premium message (free tier)
- [ ] `POST /api/review/digest` → **403** with Premium message (free tier)
- [ ] `GET /api/review/digest` → **200** preview still works (discipline line in JSON)
- [ ] Premium user (activation or allow-list) can export investment book
- [ ] Cron digest skips free-tier users (`runReviewDigestCron` premium filter)

### Auto-trade gate — T2a

- [ ] `APEX_AUTO_TRADE_ENABLED` unset/false → no auto execution paths fire
- [ ] Env documented in Vercel + README

### Regression (T0/T1)

- [ ] Today still **Wait · Trade · Pause** only
- [ ] Operating profile migration **`ready`** on `/api/health`
- [ ] Sector cap + planned vs actual on Review unchanged

---

## Tag criteria

All pre-tag gates green · 48h soak checklist signed · no P0 broker/auth regressions.

```bash
git tag v3.1.0 && git push origin v3.1.0
```

---

## Rollback

Revert to `v3.0.0-rc1` tag. Premium gates are additive — free tier remains functional without export/digest send.
