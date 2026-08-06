# APEX Release Checklist

## Pre-release

- [ ] `git rev-parse --short HEAD` recorded
- [ ] CI green (`requirements-lock.txt` install + tests)
- [ ] Streamlit Cloud Python version compatible with lockfile
- [ ] No P0 open (production startup, NameError, dependency unsatisfiable)

## Deploy

- [ ] Push to `main`
- [ ] Reboot Streamlit Cloud app
- [ ] Verify Today Brief loads (connected + offline broker)

## Post-release

- [ ] Snapshot recording works (E0 ledger)
- [ ] Rollback commit identified
- [ ] Release notes: user-visible trust/decision changes only

## Rollback

```bash
git revert <commit>
# push + reboot Cloud
```
