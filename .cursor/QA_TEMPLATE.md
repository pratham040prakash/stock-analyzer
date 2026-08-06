# APEX QA Prompt

Validate trust and decision quality, not vanity engagement.

## Test plan

| Scenario | Steps | Expected | Priority |
|----------|-------|----------|----------|
| Happy path | | | P0 |
| Offline / stale data | | | P0 |
| Broker disconnected | | | P0 |
| Error recovery | | | P1 |
| Accessibility (keyboard) | | | P1 |

## Regression

- Unit: `python -m unittest discover -s tests -p "test_*.py"`
- Manual: Today Brief loads, explanation opens, no NameError on render

## Sign-off

- [ ] P0 scenarios pass
- [ ] No new duplicate truth paths
- [ ] Performance acceptable (warm <500ms target where measurable)
