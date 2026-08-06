# APEX — Git Workflow

**Last updated:** 2026-08-06  
**Default branch:** `main`

---

## Branches

| Branch | Purpose |
|--------|---------|
| **`main`** | Production-ready · deployable |
| **`develop`** | Integration branch for Sprint work |
| **`feature/*`** | New features (e.g. `feature/ux-001-today-brief`) |
| **`bugfix/*`** | Non-production hotfixes and defect fixes |
| **`release/*`** | Release stabilization (e.g. `release/sprint-1`) |

---

## Flow

```
feature/*  ──→  develop  ──→  release/*  ──→  main
bugfix/*   ──→  develop  (or main for P0 production)
```

- Branch from **`develop`** for normal feature work
- **`bugfix/*`** → `develop`; P0 production may go **`bugfix/*`** → `main` with CTO approval
- **`release/*`** cut from `develop` when milestone is feature-complete
- Merge to **`main`** only after review + tests + release checklist

---

## Commits

- One logical change per commit · explain **why**
- Do not commit: `tmp/` · `.env` · secrets
- Never force-push `main`

---

## Before merge

- [ ] Lint / types clean (see `CODING_STANDARDS.md`)
- [ ] Tests pass
- [ ] No duplicated business logic
- [ ] PR reviewed (`.cursor/REVIEW_TEMPLATE.md`)

---

## Deploy

Production deploys from **`main`**. Reboot hosted app after dependency or startup-path changes.

---

## Agent rules

- Never update `git config`
- Never commit unless user asks
- Never force-push `main`
- Use `gh` for GitHub when requested

---

## References

- Release: `.cursor/RELEASE_TEMPLATE.md`
- Decisions: `.cursor/DECISION_LOG.md`
