# APEX V3 — Release Index

**Document ID:** APEX-V3-RELEASE-INDEX  
**Version:** 1.0  
**Status:** ACTIVE  
**Date:** 2026-08-12  
**Parent:** [APEX_V3_TRANSFORMATION_ROADMAP.md](./APEX_V3_TRANSFORMATION_ROADMAP.md)

---

## Tag order (recommended)

| Tag | Soak doc | Phase |
|-----|----------|-------|
| `v3.0.0-rc1` | [APEX_V3_RC1_SOAK.md](./APEX_V3_RC1_SOAK.md) | T0 + T1 |
| `v3.0.0` | RC1 soak + GA sign-off | T1 GA |
| `v3.1.0` | [APEX_V3_1_SOAK.md](./APEX_V3_1_SOAK.md) | T2 trust |
| `v3.2.0` | [APEX_V3_2_SOAK.md](./APEX_V3_2_SOAK.md) | T3 monetization |
| — | [APEX_V3_T4_SOAK.md](./APEX_V3_T4_SOAK.md) | T4 distribution (no tag required) |

---

## Pre-tag commands (every release)

```bash
cd apex-ui
npm run validate:capital
npm run rc:checklist -- --verify
npm run build
npm run test:e2e:smoke
APEX_E2E_COOKIE=… npm run test:e2e:authed
APEX_VERIFY_BASE_URL=https://apex-ten-kappa.vercel.app npm run verify:prod
```

---

## Prod migrations checklist

Apply once in Supabase SQL Editor:

1. `operating_profile.sql`
2. `premium_subscriptions.sql`
3. `premium_trial_offers.sql`

Confirm via `GET /api/health` → `migrations.*` all **`ready`**.

---

## Scale milestone (T4-6)

Business target: **15k–25k paying users** · **₹8–15 Cr ARR** (ESTIMATE).

Ops signal (when service role configured): `GET /api/health` → `scale_path` counts.

Not a deploy gate — track in ops, not CI.
