# APEX Context

## Mission

Help investors make better decisions.

## North Star

Become the world's most trusted investment decision platform.

## Current Sprint

Sprint 1

## Current Milestone

Daily Decision Experience

## Current Feature

APS-001 Today's Brief

## Current Architecture

Next.js (App Router)  
React 19  
TypeScript  
Tailwind  
Supabase (auth + Postgres)  
Vercel (hosting)  

**Status:** Production stack locked — `apex-ui/` on Vercel

## Next Task

UX-001 — One canonical Today surface (`ETS-003`)

---

## Repository note

**Production:** Daily Decision Experience ships from **`apex-ui/`** — deployed on **Vercel**. User-facing product work happens here only.

**Legacy (reference, not production UI):** `analyzer/` + `ui/` Streamlit — domain logic and Alpha AI; may feed APIs later. Do not treat Streamlit as the shipping surface.

Canonical product/engineering docs: `docs/apex/` (interpret through Vercel/`apex-ui` reality).
