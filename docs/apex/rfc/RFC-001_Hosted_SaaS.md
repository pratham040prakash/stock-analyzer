# RFC-001 — Hosted Multi-Tenant SaaS Deployment

**Document ID:** RFC-001  
**Status:** Open  
**Date:** 2026-08-05  
**Author:** Principal Engineering  
**Owner:** Founder  
**References:** [APEX-001 OQ1](./APEX-001_Sprint0_Engineering_Assessment.md)

## Summary

Evaluate whether APEX targets hosted multi-tenant SaaS or remains local-first indefinitely.

## Options

1. **Local-first indefinitely** — security debt C1–C3 waived with risk acceptance
2. **Hosted single-tenant** — auth + secrets hardening; one user per instance
3. **Multi-tenant SaaS** — auth, RLS, Postgres, licensed data, billing

## Blocking Questions

- Revenue model and pricing
- Target user count in 12 months
- Budget for licensed NSE data (required for cloud options)

## Decision Required By

Sprint 0 exit — determines Phase 3 scope

## Recommendation

Defer multi-tenant until Phase 1 product unification complete and CDQS measurable locally.
