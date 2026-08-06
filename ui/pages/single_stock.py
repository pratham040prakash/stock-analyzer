"""Single stock tab — V3-201 Research Workbench."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import streamlit as st

from analyzer.intraday_prefs import load_intraday_prefs
from analyzer.india import indian_ticker_help
from analyzer.markets import is_india_market
from analyzer.portfolio_store import load_saved_portfolio, portfolio_profile_key
from ui.components.partner_data import PARTNER_TODAY_LAST_BUNDLE, load_today_core, read_broker_snapshot
from ui.components.research_workspace_experience import render_research_workbench_surface
from ui.theme import APEX_PARTNER_EXPERIENCE_CSS


def render_research_subnav() -> None:
    st.markdown(
        '<nav class="apex-research-subnav" aria-label="Research sections">',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("Workbench", key="research_sub_workbench", type="primary", disabled=True, use_container_width=True)
    with c2:
        st.button("Explore", key="research_sub_explore", disabled=True, use_container_width=True)
    with c3:
        if st.button("Reports", key="research_sub_reports", use_container_width=True):
            from ui.navigation import request_nav_tab

            request_nav_tab("Alpha AI")
    st.markdown("</nav>", unsafe_allow_html=True)


def render_single_stock(market: str, period: str) -> None:
    default = "RELIANCE" if is_india_market(market) else "AAPL"
    if "single_ticker" not in st.session_state:
        st.session_state["single_ticker"] = default

    st.markdown(APEX_PARTNER_EXPERIENCE_CSS, unsafe_allow_html=True)
    render_research_subnav()

    ticker = st.text_input("Symbol", key="single_ticker").strip()
    if not ticker:
        st.info("Enter a symbol to open the Research Workbench.")
        if is_india_market(market):
            with st.expander("Indian ticker formats & tips"):
                st.markdown(indian_ticker_help())
        return

    cached = st.session_state.get(PARTNER_TODAY_LAST_BUNDLE)
    if not cached:
        try:
            cached = load_today_core(market, period)
        except Exception:
            cached = None

    broker = read_broker_snapshot()
    portfolio = load_saved_portfolio(profile=portfolio_profile_key())
    prefs = load_intraday_prefs()

    render_research_workbench_surface(
        symbol=ticker,
        cached=cached,
        broker=broker,
        portfolio=portfolio,
        prefs=prefs,
    )
