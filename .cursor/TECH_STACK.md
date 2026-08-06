# APEX — Tech Stack

**Status:** Architecture Frozen (Sprint 1)  
**Last updated:** 2026-08-06

---

## Frontend

- React 19
- Next.js
- TypeScript
- Tailwind
- Framer Motion

---

## Backend

- FastAPI
- Python
- SQLAlchemy
- Postgres
- Redis

---

## AI

- OpenAI
- LangGraph
- LlamaIndex
- Vector DB

---

## Repository note (current production)

This workspace (`stock-analyzer`) still runs the Daily Decision Experience on **Streamlit + Python** with pinned deps in `requirements-lock.txt`. Use the stack above for Sprint 1 target architecture; see `.github/workflows/ci.yml` and `requirements-lock.txt` for deploy reality until migration.

**Change policy:** Stack changes require CTO approval + ADR.
