# APEX V3 — Canonical Information Architecture

**Document ID:** APEX-V3-CANONICAL-IA  
**Version:** 1.0  
**Status:** ACTIVE — canonical for `v3.0.0-rc1` and GA  
**Date:** 2026-08-11  
**Owner:** Product · CTO  
**Parent:** [APEX-000](../apex/APEX-000_Company_Constitution.md) · [APEX_V3_TRANSFORMATION_ROADMAP.md](./APEX_V3_TRANSFORMATION_ROADMAP.md)  
**Code reference:** `apex-ui/components/nav/ApexSurfaceNav.tsx`

---

## Purpose

Single source of truth for **V3 navigation**, **Today hero language**, and **engine vs surface verdict mapping**. Resolves drift between the legacy six-surface constitution (Today · Trades · You · Ask · Trust · Proof) and the shipped V3 shell.

When APEX-000 §4.3 conflicts with this document for V3 product behavior, **this document wins for navigation and Today UX** until APEX-000 is formally amended to v1.0.

---

## Primary navigation (five surfaces)

No sixth primary tab. No alternate product modes.

| Surface | Route | Answers |
|---------|-------|---------|
| **Today** | `/app` | Should I act today? Wait · Trade · Pause — with capital dams visible first |
| **Portfolio** | `/app/portfolio` | What do I own? Is concentration healthy? |
| **Research** | `/app/research` | Should I study this symbol? (depth workspace) |
| **Review** | `/app/review` | Did I follow the plan? Receipts · weekly · monthly |
| **You** | `/app/you` | Who am I as an investor? Settings · trust · operating manual |

**Today is the product.** All other surfaces support Today.

---

## Legacy six-surface → V3 mapping

| Legacy surface (APEX-000) | V3 location | Notes |
|---------------------------|-------------|-------|
| Today | **Today** (`/app`) | Hero = Wait · Trade · Pause |
| Trades | **Today** execution panel | Trade days only; no separate Trades tab |
| Proof | Receipt overlay + Review receipts | `?receipt=` on Today; Review tab |
| Trust | **You** + `/app/trust` | Trust score, outcome loop; not primary nav |
| Ask | One-shot overlay on Today | `/api/ask/answer`; no Ask tab |
| You | **You** (`/app/you`) | Relationship + settings |

Redirects preserve bookmarks: `/app/journal` → Review receipts; `/app/explore` → Research.

---

## Today hero — user-facing verdict

Investors with zero market jargon see **one of three words**:

| Hero | Meaning | Primary CTA |
|------|---------|-------------|
| **Wait** | No confirmed entry; inaction is success | “You’re done for today” |
| **Trade** | Entry confirmed + capital dams allow action | Execute / trim per plan |
| **Pause** | Loss streak or daily loss dam hit | No buy; explain why |

Implementation: `lib/dailyLoop/dailyVerdict.ts` → `VerdictCanvas.tsx`.

### Above-the-fold order (Phase T0)

1. Operating manual strip (Core / Tactical / Not intraday)
2. Capital dams strip (daily max loss, tactical scope)
3. Sector cap strip (compact, when relevant)
4. Verdict canvas (Wait · Trade · Pause)
5. Execution panel (Trade days only)
6. **Details** accordion — portfolio, monitor, depth

---

## Engine verdicts (internal)

The **Decision Engine** still emits structured verdicts for receipts, APIs, and learning loops. These are **not** shown as the Today hero.

| Engine layer | Values | Where used |
|--------------|--------|------------|
| Decision action | ACT · WAIT · PASS · REDUCE · DEFENSIVE | `DecisionArtifact`, receipts, history |
| Execution kind | BUY · TRIM · EXPLORE · HOLD · … | `todaySurface.ts`, execution panel |
| Daily projection | `wait` · `trade` · `pause` | Today hero only |

Mapping lives in `resolveDailyVerdict()` and `projectVerdict.ts`. Do not add parallel hero vocabulary.

---

## Capital architecture on surface

Visible on Today before any trade button:

| Dam | Source | User-visible effect |
|-----|--------|---------------------|
| Sacred core | `allocationPolicy.ts` | Core symbols → no Today buy |
| Tactical pool | Brief / funds | “Today applies to ₹X tactical only” |
| Daily max loss | `riskControl.ts` | Hit → Pause |
| Sector cap | `sectorCapPolicy.ts` | Warn when top sector > ~30% |

---

## Onboarding gate

Users cannot reach Today until:

1. Financial profile complete  
2. Zerodha connected (or demo path)  
3. **Operating profile** saved — investment style + intraday acknowledgment  

Help: `/app/you/how-it-works` (linked from operating manual strip).

Storage: `operating_profiles` table; local fallback when migration pending (`syncToServer.ts`).

---

## Depth philosophy (unchanged)

Depth lives in **Research**, **Review**, **Ask overlay**, and **Proof receipts** — not in extra primary tabs.

---

## Non-goals (V3 rc1)

- Seventh primary nav item  
- Intraday trading on Today (use Kite separately)  
- Auto-execute default on  
- ACT/TRIM/EXPLORE as hero labels  

---

## Amendment log

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-08-11 | Initial canonical IA after Phase T0 ship (Sprints Z1–Z3, T1a–T1b) |

---

*Repository: stock-analyzer · Product: APEX · Document: APEX-V3-CANONICAL-IA*
