"""Simplified Kite Connect — one-time API setup + one-click daily login."""

from __future__ import annotations

import streamlit as st

from analyzer.kite_status import kite_connection_status
from analyzer.zerodha import (
    get_kite_login_url,
    load_env_credentials,
    save_zerodha_api_credentials_to_env,
)


def clear_kite_status_caches() -> None:
    for key in list(st.session_state.keys()):
        if "kite_status" in str(key).lower() or key == "kite_access_token":
            st.session_state.pop(key, None)


def render_kite_connect(*, compact: bool = False, key_prefix: str = "kite") -> bool:
    """
    Show connect UI. Returns True when Kite live data is available.
    - API key + secret: one-time paste (from developers.kite.trade — not from login)
    - Access token: daily one-click Zerodha login (auto-saved on redirect)
    """
    creds = load_env_credentials()
    status = kite_connection_status(probe=True)
    if status.get("level") == "ok":
        if not compact:
            st.success(f"**Kite connected** — {status.get('detail', 'live data active')}")
        return True

    if not creds.get("api_key") or not creds.get("api_secret"):
        if compact:
            st.caption("Kite: set up API key once in sidebar expander below.")
            return False
        st.markdown("#### Connect Zerodha Kite")
        st.caption(
            "**One-time:** Create a free app at [developers.kite.trade](https://developers.kite.trade/) "
            "→ copy **API Key** & **API Secret** (Zerodha login cannot provide these automatically). "
            "Set redirect URL to `http://127.0.0.1:8501`."
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
        return False

    login_url = get_kite_login_url(creds["api_key"])
    headline = status.get("headline", "Login required")
    detail = status.get("detail", "Daily Zerodha login for live data.")

    if compact:
        st.warning(f"**{headline}**")
        st.link_button("Login with Zerodha", login_url, use_container_width=True)
        st.caption("Returns here automatically · token saved to `.env`")
        return False

    st.markdown("#### Connect Zerodha Kite")
    st.warning(f"**{headline}** — {detail}")
    st.link_button(
        "Login with Zerodha",
        login_url,
        type="primary",
        use_container_width=True,
    )
    st.caption(
        "Click → log in on Zerodha → you return here with token saved automatically "
        "(valid until ~6 AM IST). No copy-paste needed."
    )
    with st.expander("Manual fallback (if redirect fails)"):
        rt = st.text_input("Paste request_token", key=f"{key_prefix}_request_token")
        if rt and st.button("Exchange token", key=f"{key_prefix}_exchange"):
            from analyzer.zerodha import exchange_request_token, save_access_token_to_env

            try:
                token = exchange_request_token(creds["api_key"], creds["api_secret"], rt.strip())
                save_access_token_to_env(token)
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
        render_kite_connect(compact=False, key_prefix="sidebar_kite")
