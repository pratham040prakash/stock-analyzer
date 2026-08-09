# APEX — Tech Stack

**Status:** Production locked  
**Last updated:** 2026-08-09

---

## Frontend

- React 19
- Next.js
- TypeScript
- Tailwind
- Framer Motion

---

## Backend (production)

- Next.js Route Handlers (`apex-ui/app/api/`)
- Supabase (Postgres, auth, RLS)
- Zerodha Kite (broker sync via server routes)

## Backend (future / intelligence)

- Python `analyzer/` — Alpha AI, context/evidence/decision engines (not the Vercel UI shell)
- FastAPI — optional later if Python services split from Next.js

---

## AI

- OpenAI (via existing analyzer paths when integrated)
- Alpha AI reports (`analyzer/alpha_ai_report.py`) — premium depth, future API bridge

---

## Deploy

- **Vercel** — `apex-ui/` root for production
- **Supabase** — auth, profiles, session storage
- Cron via `vercel.json` where configured

**Not production UI:** Streamlit (`ui/`, `app.py`) — legacy local tooling only.

**Change policy:** Stack changes require Founder + ADR for structural shifts.
