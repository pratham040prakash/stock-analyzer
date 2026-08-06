# APEX Performance Review Prompt

Targets: cold <2s · warm <500ms · interaction <100ms · 60 FPS motion

## Scope

Route / feature / bundle:

## Measurements

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| | | | |

## Checklist

- [ ] Lazy load non-critical modules
- [ ] Cache with clear invalidation (no stale truth)
- [ ] Avoid duplicate fetches / N+1 domain loads
- [ ] Memoize expensive projections
- [ ] Streamlit rerenders minimized

## Risks

Stale UI vs fresh truth — document trade-off explicitly.
