"""Simplified Kite Connect — one-time API setup + one-click daily login."""

from __future__ import annotations

import streamlit as st

from analyzer.kite_status import clear_kite_probe_cache, kite_connection_status
from analyzer.zerodha import (
    get_kite_login_url,
    kite_app_base_url,
    kite_runs_on_cloud,
    load_env_credentials,
    save_zerodha_api_credentials_to_env,
)


_CONNECT_UPGRADE_STEPS = (
    "1. [developers.kite.trade](https://developers.kite.trade/) → **Create app** → type **Connect** (₹500/mo)\n"
    "2. Copy new **API Key** + **Secret** into the form below → Save\n"
    "3. **Login with Zerodha** again\n"
    "4. Redirect URL = your app URL (`http://127.0.0.1:8501` when running locally)"
)


def clear_kite_status_caches() -> None:
    """Clear cached Kite probe results; keep OAuth access token in session."""
    clear_kite_probe_cache()
    for key in list(st.session_state.keys()):
        if "kite_status" in str(key).lower():
            st.session_state.pop(key, None)


def _render_kite_redirect_setup() -> None:
    """Explain the one redirect URL Zerodha allows per Kite Connect app."""
    redirect_url = kite_app_base_url()
    st.info(
        f"**Kite redirect URL** (set once at [developers.kite.trade](https://developers.kite.trade/) "
        f"→ your app → **Redirect URL**):\n\n`{redirect_url}`"
    )
    if kite_runs_on_cloud():
        st.warning(
            "You are on a **hosted** app. If Zerodha sends you to `http://127.0.0.1:8501` after login, "
            "your Kite app still has the local redirect URL. Change it to the URL above, then login again. "
            "Kite allows **one** redirect URL per app (use a second app for local dev if needed)."
        )
    else:
        st.caption(
            "Local dev: Redirect URL should be `http://127.0.0.1:8501` (or your Streamlit port)."
        )


def render_kite_connect(*, compact: bool = False, key_prefix: str = "kite") -> bool:
    """
    Show connect UI. Returns True when Kite live data is available.
    - API key + secret: one-time paste (from developers.kite.trade — not from login)
    - Access token: daily one-click Zerodha login (auto-saved on redirect)
    """
    creds = load_env_credentials()
    status = kite_connection_status(probe=True)
    level = status.get("level", "ok")
    if level == "ok":
        if not compact:
            st.success(f"**Kite connected** — {status.get('detail', 'live data active')}")
        return True
    if level == "limited":
        market = status.get("market_data", "")
        if not compact:
            st.success("**Kite logged in** — holdings, positions & sync OK")
            if market == "personal_app":
                st.warning(
                    "**Personal API app** — Zerodha blocks live quote/LTP/WebSocket APIs on free apps."
                )
                st.caption(
                    "You can still use **My Portfolio** and **Daily Advisor** — prices come from "
                    "**Yahoo Finance** (and position data when available). "
                    "Upgrade to a **Connect** app only if you need tick-by-tick Kite LTP."
                )
                with st.expander("Optional: upgrade to Connect app (₹500/mo)"):
                    st.markdown(_CONNECT_UPGRADE_STEPS)
            else:
                st.info(status.get("detail", ""))
        return market != "personal_app"

    if not creds.get("api_key") or not creds.get("api_secret"):
        if compact:
            st.caption("Kite: set up API key once in sidebar expander below.")
            return False
        st.markdown("#### Connect Zerodha Kite")
        _render_kite_redirect_setup()
        st.caption(
            "**One-time:** Create a **Connect** app (₹500/mo) at "
            "[developers.kite.trade](https://developers.kite.trade/) "
            "→ copy **API Key** & **API Secret**. **Personal** apps cannot fetch live quotes. "
            "Set **Redirect URL** to the value shown above."
        )
        with st.form(f"{key_prefix}_creds_form"):
            api_key = st.text_input("API Key", type="password", placeholder="From Kite Connect app")
            api_secret = st.text_input("API Secret", type="password", placeholder="From Kite Connect app")
            if st.form_submit_button("Save API credentials", type="primary"):
                if not api_key.strip() or not api_secret.strip():
                    st.error("Enter both API Key and API Secret.")
                else:
                    save_zerodha_api_credentials_to_env(
                        api_key=api_key.strip(),
                        api_secret=api_secret.strip(),
                    )
                    clear_kite_status_caches()
                    st.success("Saved to `.env` — now click **Login with Zerodha** below.")
                    st.rerun()
        existing = load_env_credentials()
        if existing.get("api_key"):
            hint = existing["api_key"]
            masked = f"{hint[:4]}…{hint[-4:]}" if len(hint) > 8 else "(saved)"
            st.caption(f"API key on file: **{masked}** — must match the app at developers.kite.trade")
        return False

    login_url = get_kite_login_url(creds["api_key"])
    headline = status.get("headline", "Login required")
    detail = status.get("detail", "Daily Zerodha login for live data.")

    if compact:
        st.warning(f"**{headline}**")
        st.link_button(
            "Login with Zerodha",
            login_url,
            key=f"{key_prefix}_login_compact",
            use_container_width=True,
        )
        st.caption("Returns here automatically · token saved to `.env`")
        return False

    st.markdown("#### Connect Zerodha Kite")
    _render_kite_redirect_setup()
    st.warning(f"**{headline}** — {detail}")
    st.link_button(
        "Login with Zerodha",
        login_url,
        type="primary",
        key=f"{key_prefix}_login_full",
        use_container_width=True,
    )
    st.caption(
        "Click → log in on Zerodha → browser returns to **this app** (localhost or cloud URL) "
        "so the token can be saved. Holdings sync automatically; "
        "**marketwatch must be pasted once** (Kite API limitation). "
        "Token valid until ~6 AM IST."
    )
    with st.expander("Manual fallback (if redirect fails)"):
        rt = st.text_input("Paste request_token", key=f"{key_prefix}_request_token")
        if rt and st.button("Exchange token", key=f"{key_prefix}_exchange"):
            from analyzer.zerodha import exchange_request_token, save_access_token_to_env

            try:
                token = exchange_request_token(creds["api_key"], creds["api_secret"], rt.strip())
                save_access_token_to_env(token)
                st.session_state["kite_access_token"] = token
                from analyzer.zerodha import hydrate_kite_access_token

                hydrate_kite_access_token()
                clear_kite_status_caches()
                st.success("Token saved — reload complete.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    return False


def render_kite_connect_sidebar() -> None:
    """Compact Kite block in the app sidebar."""
    creds = load_env_credentials()
    status = kite_connection_status(probe=False if not creds.get("access_token") else True)
    level = status.get("level", "ok")

    with st.expander("🔗 Zerodha Kite", expanded=level != "ok"):
        if level == "ok":
            st.success("Live data connected")
            if st.button("Re-check Kite", key="sidebar_kite_recheck", use_container_width=True):
                clear_kite_status_caches()
                st.rerun()
            return
        if level == "limited":
            market = status.get("market_data", "")
            if market == "personal_app":
                st.success("Logged in — holdings OK")
                st.caption("Personal app: prices via **Yahoo** · Connect app for live Kite LTP")
                with st.expander("Upgrade to Connect (optional)"):
                    st.markdown(_CONNECT_UPGRADE_STEPS)
            else:
                st.warning("Logged in — no quote API yet")
                st.caption("Prices use Yahoo · re-login after Connect subscription")
            if st.button("Re-check Kite", key="sidebar_kite_recheck_lim", use_container_width=True):
                clear_kite_status_caches()
                st.rerun()
            return
        render_kite_connect(compact=False, key_prefix="sidebar_kite")
