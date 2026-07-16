"""One-time Zerodha API setup — shown only when credentials are missing."""

from __future__ import annotations

import streamlit as st

from analyzer.zerodha import kite_app_base_url, save_zerodha_api_credentials_to_env
from ui.broker.bootstrap import is_broker_configured
from ui.components.kite_connect import clear_kite_status_caches


def render_broker_setup_wizard() -> None:
    st.markdown("## Welcome to your Investment OS")
    st.markdown(
        "Connect Zerodha once. After setup, the app loads your portfolio automatically every time you open it."
    )
    redirect_url = kite_app_base_url()
    st.info(
        f"**Redirect URL** (set once at [developers.kite.trade](https://developers.kite.trade/) "
        f"→ your app → **Redirect URL**):\n\n`{redirect_url}`"
    )
    st.caption(
        "Create a Kite Connect app and copy your API Key and API Secret. "
        "You will not be asked for these again."
    )

    with st.form("broker_setup_wizard_form"):
        api_key = st.text_input("API Key", type="password", placeholder="From Kite Connect app")
        api_secret = st.text_input("API Secret", type="password", placeholder="From Kite Connect app")
        submitted = st.form_submit_button("Save and continue", type="primary", use_container_width=True)
        if submitted:
            if not api_key.strip() or not api_secret.strip():
                st.error("Enter both API Key and API Secret.")
            else:
                save_zerodha_api_credentials_to_env(
                    api_key=api_key.strip(),
                    api_secret=api_secret.strip(),
                )
                clear_kite_status_caches()
                st.session_state.pop("_broker_startup_done", None)
                st.session_state.pop("_broker_bootstrap_done", None)
                st.success("Broker configuration saved. Starting your session…")
                st.rerun()


def ensure_broker_configured() -> bool:
    """Return True when API credentials exist; otherwise render the one-time wizard."""
    if is_broker_configured():
        return True
    render_broker_setup_wizard()
    return False
