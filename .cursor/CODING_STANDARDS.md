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

## Repository note (current production)

This workspace (`stock-analyzer`) is **Python + Streamlit** until Sprint 1 migration. Python standards until then: PEP 8, type hints on decision-path public APIs, tests in `tests/`, business logic in `analyzer/` not `ui/`.

See `.cursor/TECH_STACK.md` for target vs current stack.

---

## Self-review before merge

- [ ] File size limits respected?
- [ ] Types + lint clean?
- [ ] No duplicated business logic?
- [ ] Tests for behaviour changes?
- [ ] Trust and clarity improved?
