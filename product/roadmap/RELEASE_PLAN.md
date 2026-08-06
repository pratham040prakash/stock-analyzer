# RELEASE_PLAN

| Field | Value |
|-------|-------|
| **Version** | 2.0 |
| **Status** | **Shipped — GA** |
| **Owner** | Product |
| **Last Updated** | 2026-08-06 |

---

## Release Train

| Version | Type | Tag | Status | Date |
|---------|------|-----|--------|------|
| APEX V1 | Major (APS) | — | ✅ Shipped | 2026-08 |
| APEX V2 RC | Major (Experience) | `v2.0.0-rc1` | ✅ Shipped | 2026-08-06 |
| **APEX V2 GA** | Major | **`v2.0.0`** | ✅ **General Availability** | 2026-08-06 |
| APEX V2.1+ | Minor | `v2.1.x` | Planned | TBD |

---

## v2.0.0 GA Cut Line

**Includes:** APS-001–006, V2-001–004, RC-001, V2.1-T001

**Regression gate:** 54 / 54 tests  
**Full suite:** 687 / 687 tests — **0 known failures**

**Release notes:** [product/releases/v2.0.0.md](../releases/v2.0.0.md)

**Documentation freeze:** [docs/apex/APEX-014_V2_Architecture_and_Release.md](../../docs/apex/APEX-014_V2_Architecture_and_Release.md) — FROZEN (v2.0.0 GA)

**Review archive:** [docs/apex/archive/v2.0.0-ga/ENGINEERING_REVIEW_SUMMARY.md](../../docs/apex/archive/v2.0.0-ga/ENGINEERING_REVIEW_SUMMARY.md)

---

## GA Exit Criteria — Closed

- [x] Obsolete static tests updated or retired (V2.1-T001)
- [x] Review Depth drift guard maintained (RC-001)
- [x] Full suite clean (687 / 687)
- [ ] Manual QA sign-off — operational backlog
- [ ] Session ribbon product decision — backlog
