# Security Baseline v1 — APEX Engineering

**Document ID:** SEC-BASELINE-v1  
**Version:** 1.0  
**Status:** Approved (ETS-002.1 Commit A-3)  
**Date:** 2026-08-05  
**Owner:** ChatGPT (CTO)  
**Author:** Cursor AI (Engineering)  
**References:** [ETS-002.1](../ets/ETS-002.1_Broker_Auth_Session.md), [APEX-999](../APEX-999_Engineering_Handbook.md)

---

## Purpose

First permanent security baseline for APEX. Establishes audit methodology and documents credential/logging exposure findings. P0/P1 items fixed in Commit A-3; P2/P3 tracked as backlog.

---

## Stage 1 — Security Audit Findings

| ID | Severity | Location | Description | Risk | Recommendation | Status |
|----|----------|----------|-------------|------|----------------|--------|
| SEC-001 | **P0** | `ui/components/kite_auth.py:167-168` | `print(api_key)` and `print(api_secret)` during OAuth exchange | Full Zerodha app credentials in terminal/log capture | Remove immediately | **Fixed A-3** |
| SEC-002 | **P0** | `ui/components/kite_auth.py:166` | `print("request_token", request_token)` — full one-time token | Token replay if stdout captured | Remove immediately | **Fixed A-3** |
| SEC-003 | **P0** | `analyzer/zerodha.py:328` | `print("AFTER generate_session", data)` — full Kite session dict | Access token + user metadata in stdout | Remove immediately | **Fixed A-3** |
| SEC-004 | **P0** | `ui/components/kite_auth.py:66-67` | `print(qp_token/ctx_token)` with full repr | Request token in stdout | Remove immediately | **Fixed A-3** |
| SEC-005 | **P0** | `ui/components/kite_auth.py:265` | `print(request_token=…)` full repr | Request token in stdout | Remove immediately | **Fixed A-3** |
| SEC-006 | **P1** | `app.py:212` | `print(dict(st.query_params))` on every app start | OAuth `request_token` in URL params leaked to stdout | Remove; use masked startup_trace | **Fixed A-3** |
| SEC-007 | **P1** | `ui/components/kite_auth.py:256-257` | Prints full `st.query_params` and `st.context.url` | OAuth callback URL with token in stdout | Remove | **Fixed A-3** |
| SEC-008 | **P1** | `ui/components/kite_auth.py:259-261` | `oauth_log` with unmasked `context.url[:120]` | Request token persisted to `data/broker/oauth.log` | Mask URL before log | **Fixed A-3** |
| SEC-009 | **P1** | `ui/components/kite_auth.py:269-272` | Debug print of full `context_url` when no token | URL may still contain stale token params | Remove | **Fixed A-3** |
| SEC-010 | **P1** | `ui/broker/oauth_log.py:63` | `oauth_log_exception` logged raw `str(exc)` | Exception text may echo API payloads | Sanitize before write | **Fixed A-3** |
| SEC-011 | **P1** | `ui/broker/oauth_log.py:71-77` | `startup_trace` detail not sanitized | Startup logs may capture URL/token fragments | Sanitize detail strings | **Fixed A-3** |
| SEC-012 | **P2** | `analyzer/zerodha.py` + `.env` | Plaintext `ZERODHA_API_*` / `ZERODHA_ACCESS_TOKEN` in `.env` | Local disk exposure if machine compromised | Keychain store (ETS-002.1 Phase B) | Backlog |
| SEC-013 | **P2** | `st.session_state` | `kite_access_token`, `kite_token_exchanged` in memory | Expected for Streamlit; XSS would expose | CSP + secure store Phase B | Backlog |
| SEC-014 | **P2** | `data/broker/oauth.log` | OAuth file logs on disk | Local forensics surface | Encrypt/rotate; redaction policy | Backlog |
| SEC-015 | **P2** | `ui/components/kite_connect.py:149` | Manual `request_token` paste in UI | User error; token in browser memory | Unified wizard (Phase B) | Backlog |
| SEC-016 | **P2** | `cli.py:348` | `print(f"Error: {exc}")` on token exchange failure | May leak Kite error details | Sanitize CLI errors | Backlog |
| SEC-017 | **P2** | OAuth redirect URL | `request_token` in browser history until cleared | Known OAuth pattern; mitigated by `_clear_oauth_query_params` | Monitor; already cleared pre-rerun | Accepted |
| SEC-018 | **P3** | `ui/components/kite_auth.py:119,254-255,277` | Non-secret debug prints (`APP START`, etc.) | Log noise; no credential leak | Remove in hygiene pass | Backlog |
| SEC-019 | **P3** | `tmp/fetch_recording_sizes.py` | `TOKEN_HELPDESK` bearer usage | Non-APEX tooling; out of product scope | Keep out of APEX deploy | N/A |
| SEC-020 | **P3** | `interaction-investigator/` | Separate app; OpenAI key in `.env` | Not APEX production surface | Separate baseline if shipped | N/A |

---

## Stage 2 — Fixes Applied (Commit A-3)

| File | Change |
|------|--------|
| `ui/components/kite_auth.py` | Removed all P0/P1 credential and URL `print()` calls; masked URL in `oauth_log` |
| `analyzer/zerodha.py` | Removed session dict `print()` from `exchange_request_token` |
| `app.py` | Removed `print(dict(st.query_params))` |
| `ui/broker/oauth_log.py` | Added `sanitize_log_detail`, `mask_oauth_url`; applied to oauth/startup/exception logs |
| `tests/test_security_baseline.py` | Sanitization + static source hygiene tests |
| `docs/apex/security/Security_Baseline_v1.md` | This document |

**Not changed:** OAuth flow, UI, startup order, credential storage, architecture.

---

## Summary Counts

| Severity | Found | Fixed (A-3) | Backlog |
|----------|-------|-------------|---------|
| P0 | 5 | 5 | 0 |
| P1 | 6 | 6 | 0 |
| P2 | 6 | 0 | 6 |
| P3 | 3 | 0 | 3 |
| **Total** | **20** | **11** | **9** |

---

## Remaining Risks

- Plaintext `.env` credential storage (SEC-012) — Phase B Keychain
- OAuth tokens in `session_state` (SEC-013) — acceptable for local Streamlit until secure store
- Residual debug prints without secrets (SEC-018) — P3 backlog
- Browser history window for `request_token` (SEC-017) — mitigated by early clear + rerun

---

## Rollback Plan

Revert Commit A-3: restores debug prints and unsanitized logging. No data migration impact. Run `tests/test_security_baseline.py` to verify baseline after any revert.

---

## Test Verification

```bash
python3 -m unittest tests.test_security_baseline tests.test_kite_oauth tests.test_broker_session -v
```

---

*Next review: ETS-002.1 Phase B (credential store) or quarterly per APEX-999.*
