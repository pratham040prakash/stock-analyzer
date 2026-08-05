# ADR-001 — Six Deployable Boundaries

**Document ID:** ADR-001  
**Status:** Accepted  
**Date:** 2026-08-05  
**Deciders:** CTO  
**References:** [APEX-001 §Decision Log D-003](./APEX-001_Sprint0_Engineering_Assessment.md)

## Context

Doc 05 proposed 16 bounded domains. Architecture critique (doc 07) argued this exceeds current change velocity for a single-trader Streamlit product.

## Decision

Adopt **6 deployable boundaries**: Intelligence, Context, Decision, Execution, Learning, Platform.

## Consequences

- Migration reduced from ~52 steps / 20 weeks to ~18 steps / 8–10 weeks
- Less granular ownership until team scale warrants re-split
- Revisit 16-domain model when independent release cycles exist

## Alternatives Rejected

16 domains — over-engineered for current scale (see APEX-001 R-002).
