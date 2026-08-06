# APEX Code Review Prompt

Review as Principal Engineer + UX Engineer. Do not approve hype or scope creep.

## Scope

**PR / diff:**  
**Feature ID:**  

## Checklist

### Product & trust
- [ ] Answers before analysis
- [ ] Explains recommendations; no pressure to act
- [ ] One primary question per screen

### Architecture
- [ ] Single source of truth preserved
- [ ] No business logic in UI components
- [ ] No duplicated loaders or verdict logic

### Engineering
- [ ] Tests for behaviour and regressions
- [ ] Error/loading/empty paths
- [ ] No hardcoded secrets or magic numbers

### Accessibility & UX
- [ ] Keyboard / screen reader viable
- [ ] Not color-only meaning
- [ ] Calm, professional copy

## Verdict

Approve / Request changes / Block

**Findings (severity: P0 / P1 / P2):**
