"""Command palette — jump to any tab or symbol."""

from __future__ import annotations

import streamlit as st

from analyzer.markets import is_india_market
from analyzer.unified_search import (
    TAB_ALIASES,
    extract_symbol_from_command,
    match_tab_command,
    unified_search,
)
from ui.navigation import request_nav_tab
from ui.theme import active_nav_groups, nav_group_for_tab


def _go(tab: str, symbol: str | None = None) -> None:
    sym = (symbol or "").replace(".NS", "").replace(".BO", "").strip()
    kwargs: dict = {}
    if sym:
        kwargs = {
            "single_ticker": sym,
            "bt_ticker": sym,
            "intraday_ticker": sym,
            "alpha_ai_ticker": sym,
        }
    request_nav_tab(tab, **kwargs)


def render_command_palette(*, market: str = "india") -> None:
    """Unified search bar + command palette at top of app."""
    with st.expander("⌘ Jump — search symbol, name, ISIN, or tab", expanded=False):
        st.caption(
            "Examples: `TCS`, `Reliance`, `INE467B01029`, `alpha INFY`, `>track record`, `suggestions`"
        )
        query = st.text_input(
            "Search",
            placeholder="Symbol · name · ISIN · or tab (alpha, suggestions, portfolio…)",
            key="command_palette_query",
            label_visibility="collapsed",
        )
        if not query or len(query.strip()) < 2:
            st.caption("**Tabs:** " + ", ".join(sorted(set(TAB_ALIASES.keys()))[:12]) + "…")
            return

        q = query.strip()
        tab = match_tab_command(q)
        sym = extract_symbol_from_command(q)

        if tab and sym:
            if st.button(f"Go → **{tab}** · {sym.upper()}", key="cmd_go_tab_sym", type="primary"):
                _go(tab, sym)
            return

        if tab and not sym:
            if st.button(f"Go → **{tab}**", key="cmd_go_tab", type="primary"):
                _go(tab)
            return

        if is_india_market(market):
            hits = unified_search(q, max_results=8)
            if not hits:
                st.caption("No matches — try company name or NSE symbol.")
                return
            for i, h in enumerate(hits):
                label = f"{h.symbol} — {h.name[:36]} ({h.match_type})"
                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.caption(label + (f" · {h.detail}" if h.detail else ""))
                with c2:
                    if st.button("Single Stock", key=f"cmd_ss_{i}_{h.symbol}"):
                        _go("Single Stock", h.symbol)
                with c3:
                    if st.button("Alpha AI", key=f"cmd_alpha_{i}_{h.symbol}"):
                        _go("Alpha AI", h.symbol)
        else:
            sym = q.upper()
            if st.button(f"Analyze **{sym}**", key="cmd_us_stock", type="primary"):
                _go("Single Stock", sym)


def render_tab_quick_links() -> None:
    """Compact tab chips below command palette."""
    groups = active_nav_groups()
    tabs = [t for ts in groups.values() for t in ts]
    preferred = [t for t in ("Suggestions", "Track Record", "Alpha AI", "My Portfolio") if t in tabs]
    cols = st.columns(len(preferred))
    for col, tab in zip(cols, preferred):
        with col:
            if st.button(tab, key=f"quick_nav_{tab}", use_container_width=True):
                st.session_state["nav_group"] = nav_group_for_tab(tab)
                st.session_state["nav_tab"] = tab
                st.rerun()
