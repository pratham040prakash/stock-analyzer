# APEX — Coding Standards

**Status:** Architecture Frozen (Sprint 1)  
**Last updated:** 2026-08-06  
**Authority:** [.cursor/MASTER_PROMPT.md](./MASTER_PROMPT.md) · [DECISION_LOG.md](./DECISION_LOG.md)

---

## Size limits

| Unit | Max lines |
|------|-----------|
| **Any file** | 400 |
| **Hooks** | 150 |
| **Components** | 250 |

Split before exceeding limits. No exceptions without CTO approval.

---

## Type safety

- **Strong typing only** — no `any`, no untyped public APIs
- **100% TypeScript clean** — `tsc` passes with zero errors
- **100% ESLint clean** — zero warnings, zero errors

---

## Architecture

- **No duplicated business logic** — single source of truth in services / use cases
- Business logic in backend services and domain layer — not in UI components
- Presentation in components; data and decisions in services

---

## Product alignment

Every feature must satisfy [MASTER_PROMPT.md](./MASTER_PROMPT.md):

- Answer before analysis
- Recommendation Card structure is universal (Decision 002)
- No engagement hacks · no pressure to act

---

## Repository note (production)

**Ship from `apex-ui/` only** (Next.js + TypeScript on Vercel).

- Business logic: `apex-ui/lib/`, `apex-ui/services/` — not in React components
- API routes: `apex-ui/app/api/` — auth, broker sync, decision
- Capital/decision rules: `apex-ui/lib/dailyLoop/` — single source for Today
- Prebuild gate: `npm run build` runs `scripts/validate-capital.ts`

**Legacy Python (`analyzer/`, `ui/`):** reference for Alpha AI and future API bridges; not the production UI path.

See `.cursor/TECH_STACK.md` for full stack.

---

## Self-review before merge

- [ ] File size limits respected?
- [ ] Types + lint clean?
- [ ] No duplicated business logic?
- [ ] Tests for behaviour changes?
- [ ] Trust and clarity improved?
