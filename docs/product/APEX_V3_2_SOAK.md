# APEX V3 — v3.2.0 Soak Checklist

**Document ID:** APEX-V3-2-SOAK  
**Version:** 1.0  
**Status:** ACTIVE  
**Date:** 2026-08-11  
**Parent:** [APEX_V3_TRANSFORMATION_ROADMAP.md](./APEX_V3_TRANSFORMATION_ROADMAP.md) · [APEX_V3_1_SOAK.md](./APEX_V3_1_SOAK.md)

---

## Purpose

Validate **Phase T3 monetization** (T3-1 → T3-3) on production before tagging **`v3.2.0`**. Free tier must remain fully usable; premium paths are additive.

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

## Prod database migrations (required)

Apply in Supabase SQL Editor (once each):

1. `supabase/migrations/operating_profile.sql`
2. `supabase/migrations/premium_subscriptions.sql`
3. `supabase/migrations/premium_trial_offers.sql`

Confirm on prod:

```bash
npm run verify:prod
```

Look for `/api/health` → `migrations`:

- `operating_profile`: **ready**
- `premium_subscriptions`: **ready**
- `premium_trial_offers`: **ready**

---

## Prod manual soak (48h recommended)

### Free tier regression

- [ ] Today **Wait · Trade · Pause** unchanged
- [ ] Portfolio, Research, Review, You all load signed-in
- [ ] Free user can complete discipline commit without paying
- [ ] No paywall blocks Today verdict or broker connect

### Premium packaging (T3-1)

- [ ] You → **Open settings** → Settings loads
- [ ] Free user sees locked export + digest gates with ROI copy
- [ ] `GET /api/thesis/export` → **403** (free)
- [ ] `POST /api/review/digest` → **403** (free)
- [ ] Invite code activation still works (`APEX_PREMIUM_ACCESS_CODES`)

### Razorpay billing (T3-2) — when enabled

- [ ] `APEX_RAZORPAY_ENABLED=true` + keys in Vercel
- [ ] Settings shows **Subscribe with Razorpay**
- [ ] Test checkout → premium unlocks via billing sync
- [ ] Webhook (when registered) updates subscription status
- [ ] Cancelled subscription revokes paid premium

### Trial funnel (T3-3)

- [ ] Fresh free user: first **WAIT** receipt → trial offer on Today + You
- [ ] **Start 7-day trial** unlocks premium immediately
- [ ] **Not now** dismisses offer (no repeat prompt)
- [ ] `/api/subscription/tier` returns `trial.status` field

### Trust + Review regression (T2)

- [ ] CDQS + override discipline on `/app/trust`
- [ ] Discipline digest strip on Review weekly
- [ ] Cron digest skips non-premium users

---

## Tag criteria

All pre-tag gates green · all three monetization migrations **ready** · 48h soak signed · no P0 regressions.

```bash
git tag v3.2.0 && git push origin v3.2.0
```

---

## Rollback

Revert deploy to prior tag (`v3.1.0` or `v3.0.0-rc1`). Premium gates and trial are additive — free tier stays functional.

---

## Post-tag ops (optional)

| Env | Purpose |
|-----|---------|
| `APEX_RAZORPAY_*` | Paid subscriptions |
| `APEX_PREMIUM_TRIAL_DAYS` | Trial length (default 7) |
| `APEX_PREMIUM_ACCESS_CODES` | Beta invites without payment |
| `APEX_REVIEW_DIGEST_ENABLED` | Weekly digest cron |

Webhook URL (when ready): `https://apex-ten-kappa.vercel.app/api/subscription/webhook/razorpay`
