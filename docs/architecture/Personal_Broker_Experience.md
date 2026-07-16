# Personal Broker Experience — Zerodha Kite for a Single-User Desktop OS

**Role:** Chief Product Officer  
**Product type:** Personal desktop Investment Operating System — **not SaaS**  
**User model:** Exactly one investor (you), one machine, one Kite account  
**Constraints:** Do **not** redesign Broker Truth · Do **not** redesign OAuth mechanics (`request_token` → `access_token` exchange stays as-is)  
**Scope:** Personal-user experience only — startup, storage, UI, reconnect  
**Date:** 2026-07-16  
**Related:** [20_Product_Information_Architecture.md](./20_Product_Information_Architecture.md) · `ui/components/kite_auth.py` · `analyzer/zerodha.py`

---

## Executive Summary

Today the app treats Kite like a **developer integration**: API key forms in the sidebar, manual `request_token` fallback, setup wizards, and OAuth that **skips Home**. That is correct for a multi-tenant SaaS demo; it is wrong for a **personal desktop OS**.

**Target experience:** Like a premium trading terminal on your Mac — open the app, see **Broker Connected**, portfolio already synced, today's P&L on Home. Login again only when Zerodha's session expires (~daily, ~6 AM IST), via one **Login with Zerodha** click — never re-enter API key/secret.

| Today (developer) | Target (personal desktop) |
|-------------------|---------------------------|
| Sidebar API key form | **One-time** first-run setup only |
| OAuth skipped on Home | OAuth on **every** page load |
| Portfolio asks to connect | Portfolio **never** asks for credentials |
| Manual sync buttons | **Automatic** sync on startup |
| Token paste fallback exposed | Hidden in Settings › Advanced (emergency only) |

---

## Design Principles

1. **Configure once, forget forever** — API Key + Secret saved locally at first run; never shown again unless user opens Settings › Broker › Reconfigure.  
2. **Session token is daily, login is one click** — Zerodha does not offer long-lived refresh tokens for retail Connect; “refresh” means **automatic redirect to login**, not silent background renewal.  
3. **Broker bootstrap before UI** — Every app start runs a broker gate: load creds → verify token → sync or re-login.  
4. **Portfolio is read-only truth** — No forms, no “connect Kite” CTAs; only data and actions on holdings.  
5. **Home shows broker pulse** — Connected status, last sync, portfolio value, today's P&L — zero clicks.  
6. **Local-only secrets** — `.env` + `data/broker/` metadata on disk; no cloud secrets UI, no profile name field for “shared app”.

---

## Local Configuration Model

### One-time secrets (never re-prompted)

| Key | Storage | When written |
|-----|---------|--------------|
| `ZERODHA_API_KEY` | `~/.env` or project `.env` | First-run wizard only |
| `ZERODHA_API_SECRET` | same | First-run wizard only |
| `KITE_REDIRECT_URL` | same (optional) | Default `http://127.0.0.1:8502` from `run_app.sh` |

**Existing backend:** `save_zerodha_api_credentials_to_env()` in `analyzer/zerodha.py` — reuse unchanged.

### Session token (daily)

| Key | Storage | When written |
|-----|---------|--------------|
| `ZERODHA_ACCESS_TOKEN` | `.env` | After each successful OAuth callback |

**Existing backend:** `save_access_token_to_env()`, `exchange_request_token()` — unchanged.

### Broker state (new UI metadata file — display only)

Path: `data/broker/session_state.json` (written by UI layer, not Broker Truth)

```json
{
  "last_sync_at": "2026-07-16T09:12:04+05:30",
  "last_sync_status": "ok",
  "user_id": "AB1234",
  "user_name": "Pratham",
  "token_valid_until_hint": "2026-07-17T06:00:00+05:30",
  "holdings_count": 12,
  "positions_count": 2,
  "portfolio_value_inr": 1842500,
  "today_realized_pnl_inr": 1240,
  "today_unrealized_pnl_inr": 8200,
  "available_cash_inr": 42000
}
```

This file powers **Last Sync** and Home metrics without re-querying Kite on every widget paint. Broker Truth remains authoritative for learning; this is **UI cache**.

---

## Startup Flow

Runs **once per Streamlit session**, at the top of `app.py` **before** any page render — including Home.

```text
┌─────────────────────────────────────────────────────────────────┐
│ APP START                                                        │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. load_app_env() — read .env from project root                  │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. handle_kite_redirect() — if ?request_token= in URL, exchange  │
│    (MUST run on ALL pages, including Home)                       │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. broker_bootstrap() — new UI orchestrator (wraps existing APIs)│
└────────────────────────────┬────────────────────────────────────┘
                             ▼
                    ┌────────┴────────┐
                    ▼                 ▼
            API key missing?    API key present
                    │                 │
                    ▼                 ▼
         first_run_required    hydrate_kite_access_token()
         (block → Settings)           │
                                      ▼
                            verify_token() — kite.profile()
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                    token valid               token invalid / expired
                         │                         │
                         ▼                         ▼
              sync_broker_snapshot()      reconnect_required
              (holdings, positions,       (set session flag;
               margins, LTP)              show login on Home ribbon)
                         │
                         ▼
              write session_state.json
              st.session_state["broker_snapshot"] = ...
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Render page (Home / Portfolio / …) with broker state ready      │
└─────────────────────────────────────────────────────────────────┘
```

### `broker_bootstrap()` responsibilities (UI-only wrapper)

| Step | Existing API | Notes |
|------|--------------|-------|
| Load credentials | `load_env_credentials()` | No UI |
| OAuth callback | `handle_kite_redirect()` | Already implemented |
| Verify session | `kite_connection_status(probe=True)` / `kite.profile()` | Map `expired` → reconnect |
| Sync holdings | `sync_holdings_from_kite()` → `save_portfolio()` | `portfolio_live.py` |
| Sync positions | `fetch_kite_activity_symbols()` + positions net bucket | Extend display in Portfolio |
| Sync funds | `fetch_kite_margins()` | `available.cash` / `net` |
| Refresh LTP | `refresh_holdings_ltp()` | For portfolio value |
| Start stream | `start_kite_ticker_on_app_start()` | Optional, non-blocking |
| Persist UI state | New JSON writer | Last sync timestamp |

### First-run gate

If `ZERODHA_API_KEY` or `ZERODHA_API_SECRET` missing:

- Show **full-screen first-run** (Settings › Broker setup) — **only time** API forms appear.  
- Block Portfolio and Home broker metrics with calm message: *“Complete one-time broker setup.”*  
- Do **not** show sidebar credential expander on every page.

### Remove Home fast-path exception

**Current bug:** `app.py` returns early on `nav_tab == "Home"` and skips `handle_kite_redirect()` and `_hydrate_saved_portfolio()`.

**Required change (UI routing only):** Home uses the same startup pipeline as every other page.

---

## Authentication Lifecycle

### States

```text
                    ┌──────────────────┐
                    │  NOT_CONFIGURED  │  No API key in .env
                    └────────┬─────────┘
                             │ first-run wizard saves key+secret
                             ▼
                    ┌──────────────────┐
                    │    LOGGED_OUT    │  Key present, no valid access_token
                    └────────┬─────────┘
                             │ user clicks Login / auto prompt
                             ▼
                    ┌──────────────────┐
         ┌─────────│    CONNECTED     │─────────┐
         │         └────────┬─────────┘         │
         │ daily ~6AM IST   │ sync success      │ profile() fails
         │ or 403           ▼                   ▼
         │         ┌──────────────────┐  ┌──────────────────┐
         └────────►│  RECONNECT_DUE   │  │     EXPIRED      │
                   └──────────────────┘  └──────────────────┘
```

| State | User sees | System behavior |
|-------|-----------|-----------------|
| **NOT_CONFIGURED** | First-run wizard | No Kite API calls |
| **LOGGED_OUT** | “Sign in to Zerodha” on ribbon | Holdings from last `session_state.json` cache, labeled **stale** |
| **CONNECTED** | Green “Broker Connected” | Live sync; stream LTP |
| **RECONNECT_DUE** | Amber “Session ends ~6 AM — sign in” | Morning of expiry, proactive banner |
| **EXPIRED** | Red “Session expired” + one button | Auto-open login URL on user confirm (or single click) |

### What “never ask again” means

| Credential | Frequency |
|------------|-----------|
| API Key | **Once** (first run or explicit Reconfigure in Settings) |
| API Secret | **Once** (same) |
| Zerodha login (OAuth) | **Daily** when session expires — one click, no paste |

This matches Zerodha Connect constraints without changing OAuth.

---

## Reconnect Flow

When `kite.profile()` fails or `kite_connection_status` returns `expired`:

```text
User opens app (any page)
        │
        ▼
broker_bootstrap() detects EXPIRED
        │
        ▼
Set st.session_state["broker_reconnect"] = True
        │
        ▼
Global ribbon shows:
  "Session expired · Sign in to Zerodha"
  [ Sign in ]  ← link_button to get_kite_login_url()
        │
        ▼
User completes Zerodha login in browser
        │
        ▼
Redirect to http://127.0.0.1:8502/?request_token=...
  (works on Home, Portfolio, any tab)
        │
        ▼
handle_kite_redirect()
  → exchange_request_token()
  → save_access_token_to_env()
  → post_kite_login_sync()
        │
        ▼
broker_bootstrap() runs sync again
        │
        ▼
Redirect user to page they intended (stored in session)
Portfolio renders with fresh data — no credential forms
```

### Premium desktop behavior

- **No modal** asking for `request_token`.  
- **No** “Save API credentials” form on reconnect.  
- **No** sidebar expander for daily login — only a **ribbon button**.  
- After login, **toast**: “Zerodha connected · 12 holdings synced · 09:12 IST” — then dismiss.  
- Optional: remember `last_tab` in session so OAuth return lands on Portfolio if that's where you were.

**Existing code to keep:** `handle_kite_redirect()` in `ui/components/kite_auth.py` — enhance only routing placement, not exchange logic.

---

## Token “Refresh” Flow

**Important:** Kite Connect retail sessions do **not** support opaque refresh tokens. The access token is valid until approximately **6:00 AM IST** the next day.

Therefore “token refresh” in this OS means:

| Mechanism | Supported | UX |
|-----------|-----------|-----|
| Silent background refresh without user | **No** (Zerodha limitation) | — |
| Detect expiry via `profile()` / 403 | **Yes** | Automatic state → EXPIRED |
| Pre-emptive morning banner | **Yes** | RECONNECT_DUE before market open |
| One-click OAuth re-login | **Yes** | `get_kite_login_url()` |
| Auto-exchange on redirect | **Yes** | `handle_kite_redirect()` |
| Persist new token to `.env` | **Yes** | `save_access_token_to_env()` |

### Morning ritual (automated detection)

```text
08:45 AM — user opens app
    → bootstrap runs
    → token from yesterday expired at ~06:00
    → state = EXPIRED
    → ribbon: "Sign in to Zerodha" (primary action)
    → user clicks once → OAuth → back in app
    → sync completes before Portfolio paints
    → Home shows Broker Connected + fresh P&L
```

**No manual token paste.** Emergency manual exchange moves to Settings › Broker › Advanced (collapsed, for outage debugging only).

---

## Sync Flow (holdings · positions · funds)

On every successful `CONNECTED` bootstrap:

| Asset | Source (existing) | Portfolio section |
|-------|-------------------|-------------------|
| **Holdings** | `fetch_holdings_from_kite()` + CNC merge | Holdings |
| **Positions** | `kite.positions()` net/day | Positions |
| **Funds / cash** | `fetch_kite_margins()` equity segment | Overview › Cash |
| **LTP / unrealized** | `refresh_holdings_ltp()` | Overview P&L |
| **Realized today** | `trade_journal` + Broker Truth when available | Overview P&L |
| **Watchlist activity** | `sync_watchlist_from_kite_activity()` | Background (Settings log) |

Sync runs:

1. On startup (CONNECTED)  
2. After OAuth callback  
3. Every 60s during market hours on Portfolio tab (existing 15s fragment can remain)  
4. Manual “Sync now” in Settings › Broker only (not Portfolio)

### Last Sync

Display: `Last sync · 09:12:04 IST · 12 holdings · 2 positions · ₹42k available`

Written to `session_state.json` after each successful bootstrap.

---

## UI Changes

### Global broker ribbon (all pages)

```text
┌────────────────────────────────────────────────────────────────────────┐
│ Investment OS     ● Broker Connected    Last sync 2m ago    ⌘ Jump    │
│                     Reliance Capital · AB1234                          │
└────────────────────────────────────────────────────────────────────────┘
```

| State | Ribbon |
|-------|--------|
| CONNECTED | `● Broker Connected` (green) |
| EXPIRED | `○ Sign in to Zerodha` (amber/red) + button |
| NOT_CONFIGURED | `○ Broker not configured` → Settings |
| Stale cache | `◐ Cached data · 6h ago` (gray) when offline |

**Remove from sidebar:** `render_kite_connect_sidebar()` daily login expander — move to ribbon + Settings.

---

### Home — broker pulse (above fold)

New strip under session ribbon, **no manual action**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ BROKER PULSE                                                           │
├──────────────┬──────────────┬──────────────┬──────────────────────────┤
│ ● Connected  │ Last sync    │ Portfolio    │ Today's P&L              │
│ Zerodha      │ 2m ago       │ ₹18.42 L     │ +₹1,240 realized       │
│              │              │              │ +₹8,200 unrealized       │
└──────────────┴──────────────┴──────────────┴──────────────────────────┘
```

Data source: `st.session_state["broker_snapshot"]` from bootstrap — not a second Kite round-trip.

If EXPIRED: show last cached values with **stale badge** and single **Sign in** — never empty forms.

---

### Portfolio page — never asks for credentials

**Remove entirely from Portfolio:**

- API Key / Secret text inputs  
- “Connect Kite in sidebar” messages  
- `render_kite_connect()` forms  
- Profile name text input (single-user — use fixed `default` profile)  
- Manual request_token exchange UI  

**Portfolio shows only:**

| Section | Content |
|---------|---------|
| Overview | Health, allocation, sector, cash, P&L |
| Holdings | Live table — sync implied |
| Positions | MIS/CNC open positions |
| Briefing | Daily advisor actions |
| Wealth | SIP (non-broker) |

If broker EXPIRED: full-page **graceful gate** — not a form:

```text
┌────────────────────────────────────────────────────────────────────────┐
│  Sign in to Zerodha to refresh your portfolio                          │
│                                                                        │
│  [ Sign in with Zerodha ]                                              │
│                                                                        │
│  Showing cached data from 16 Jul, 08:45 IST                            │
│  (holdings table dimmed below)                                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

### Settings › Broker (one-time + maintenance)

**First run only** — full-screen wizard:

1. Welcome — personal OS, one machine  
2. Paste API Key + Secret (once) → Save to `.env`  
3. Set redirect URL (pre-filled `http://127.0.0.1:8502`)  
4. Sign in with Zerodha → OAuth  
5. Confirm sync — holdings count  
6. Done — never show step 2 again  

**After setup** — Settings › Broker shows:

| Item | Action |
|------|--------|
| Connection status | Connected / Expired |
| Account | Name, user ID |
| Last sync | Timestamp + counts |
| Sync now | Manual refresh |
| Sign in again | OAuth link (daily) |
| Reconfigure API app | **Hidden** behind “Advanced” + confirm dialog |
| Manual request_token | **Advanced only** — developer escape hatch |

---

### What disappears (developer → desktop)

| Remove from daily UX | Keep in Settings › Advanced |
|----------------------|-------------------------------|
| Sidebar “🔗 Zerodha Kite” expander with forms | Manual token exchange |
| `zerodha_setup_help()` wall of text on Portfolio | CLI `scripts/kite_auth.py` docs link |
| Portfolio profile name field | Reconfigure API key |
| Home fast-path skipping OAuth | — |
| “Paste request_token” on connect UI | — |
| Cloud / Streamlit shared-app warnings | Local-only banner |

---

## OAuth Callback — All Pages

**Requirement:** Callback must work regardless of active page.

**Implementation rule (UI only):**

```python
# app.py — top of main(), before any nav_tab branch
handle_kite_redirect()
broker_bootstrap()
# then render Home, Portfolio, etc.
```

**Redirect URL:** Fixed in personal install — `http://127.0.0.1:8502` per `scripts/run_app.sh`. Set once in Kite developer console; store in `.env` as `KITE_REDIRECT_URL`.

**Post-login navigation:** Clear query params; restore `st.session_state.get("nav_tab")` or default Home.

---

## File / Module Mapping (UI changes only)

| New / moved (UI) | Wraps (unchanged backend) |
|------------------|---------------------------|
| `ui/broker/bootstrap.py` | `load_env_credentials`, `sync_holdings_from_kite`, `fetch_kite_margins`, `post_kite_login_sync` |
| `ui/broker/state.py` | Read/write `data/broker/session_state.json` |
| `ui/components/broker_ribbon.py` | `kite_connection_status` |
| `ui/components/broker_pulse.py` | Home metrics from `broker_snapshot` |
| `ui/pages/settings_broker.py` | First-run wizard; replaces scattered forms |
| `app.py` | Unified startup; remove Home exception |

**Unchanged:** `analyzer/zerodha.py`, `ui/components/kite_auth.py` (OAuth exchange), Broker Truth package.

---

## Acceptance Criteria

| # | Criterion |
|---|-----------|
| 1 | API Key + Secret entered **once**; never shown on Portfolio or Home |
| 2 | App startup syncs holdings, positions, funds before Portfolio renders (when token valid) |
| 3 | Portfolio never displays credential forms |
| 4 | Expired token → one-click Zerodha login → auto-return → auto-sync |
| 5 | OAuth `?request_token=` works when landing on Home |
| 6 | All config local (`.env` + `data/broker/`) |
| 7 | Home shows Connected, Last Sync, Portfolio Value, Today's P&L without user action |
| 8 | No manual `request_token` in default UX |

---

## Migration from Current UX

| Phase | Change | Effort |
|-------|--------|--------|
| **1** | Move `handle_kite_redirect()` + `broker_bootstrap()` before Home branch | S |
| **2** | Add `broker_ribbon` + `broker_pulse` components | M |
| **3** | Strip credential UI from `zerodha.py` page / Portfolio | M |
| **4** | First-run wizard in Settings; hide sidebar Kite expander | M |
| **5** | `session_state.json` + stale-cache Portfolio gate | S |
| **6** | Remove profile name field; pin `default` profile | S |

---

## CPO Summary

This is **your** terminal on **your** Mac. Zerodha login is a **daily turnstile**, not a setup chore. API credentials are **infrastructure** configured once, like installing a broker plugin — not a form you see beside every chart.

The OAuth code stays. Broker Truth stays. What changes is **when** things run, **where** secrets appear, and **how** Home and Portfolio **trust** the broker without asking you to be a developer every morning.

---

*Documentation only. No application or backend code modified.*
