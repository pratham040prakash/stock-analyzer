# RELEASE_PLAN

| Field | Value |
|-------|-------|
| **Version** | 2.0 |
| **Status** | Approved — RC cut complete |
| **Owner** | Product |
| **Last Updated** | 2026-08-06 |

---

## Release Train

| Version | Type | Tag | Status | Date |
|---------|------|-----|--------|------|
| APEX V1 | Major (APS) | — | ✅ Shipped | 2026-08 |
| APEX V2 | Major (Experience) | `v2.0.0-rc1` | ✅ **Release Candidate** | 2026-08-06 |
| APEX V2 GA | Major | `v2.0.0` | Planned | TBD |

---

## v2.0.0-rc1 Cut Line

**Includes:** APS-001–006, V2-001–004, RC-001

**Regression gate:** 54 / 54 tests

**Release notes:** [product/releases/v2.0.0-rc1.md](../releases/v2.0.0-rc1.md)

**Documentation freeze:** [docs/apex/APEX-014_V2_Architecture_and_Release.md](../../docs/apex/APEX-014_V2_Architecture_and_Release.md) — APPROVED — FROZEN

---

## GA Exit Criteria (V2 → v2.0.0)

- [ ] Manual QA sign-off on Today + Review journeys
- [ ] Obsolete static tests updated or retired
- [ ] Optional full-suite infra deps documented in CI
- [ ] Session ribbon product decision (wire or remove)
- [ ] Review Depth drift guard maintained (single compositor)
