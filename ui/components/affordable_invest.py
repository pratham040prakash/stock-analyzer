"""Market Pulse — top invest picks under ₹3,000."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.affordable_invest import (
    DEFAULT_MAX_INVEST_PRICE_INR,
    affordable_from_pulse_report,
    affordable_invest_summary,
)
from analyzer.markets import format_price
from ui.theme import INTRADAY_SETUP_COLORS, OPTIONS_COLORS, REC_COLORS


def render_affordable_invest_section(report) -> None:
    max_price = DEFAULT_MAX_INVEST_PRICE_INR

    st.subheader(f"💰 Top 5 under ₹{max_price:,.0f} — Delivery · Intraday · CE/PE")
    st.caption(
        "Live **Nifty 50** scan: **delivery/SIP**, **intraday MIS**, and **NSE option strikes** "
        "(Kite LTP + NSE chain when available)."
    )

    load_options = st.checkbox(
        "Load NSE CE/PE strikes (slower)",
        value=True,
        key="aff_load_options",
        help="Fetches live option chain per pick (~5–15 sec). Uncheck for delivery + intraday only.",
    )

    with st.spinner("Ranking picks + intraday setups…"):
        picks = affordable_from_pulse_report(
            report, limit=5, enrich_options=load_options,
        )

    if not picks:
        st.warning(affordable_invest_summary(picks, max_price))
        st.caption(
            "Most Nifty names may be above ₹3,000 or bearish today. "
            "Check **long-term** picks below or **Compare** tab."
        )
        return

    st.success(affordable_invest_summary(picks, max_price))

    table = []
    for p in picks:
        chg = f"{p.price_change_pct:+.1f}%" if p.price_change_pct is not None else "—"
        table.append({
            "Rank": p.rank,
            "Stock": p.nse_symbol,
            "Live price": format_price(p.price, f"{p.nse_symbol}.NS"),
            "Delivery": f"{p.long_action} ({p.long_score:+.0f})",
            "Intraday": f"{p.intraday_action} ({p.intraday_score:+.0f})",
            "Options": p.options_action,
            "CE idea": p.options_ce_pick.replace("**", "")[:36] if p.options_ce_pick != "—" else "—",
            "PE idea": p.options_pe_pick.replace("**", "")[:36] if p.options_pe_pick != "—" else "—",
            "Score": f"{p.invest_score:.0f}",
        })
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    st.markdown("#### Per-stock plans")
    for p in picks:
        color = REC_COLORS.get(p.combined_rec, "#69f0ae")
        intra_color = INTRADAY_SETUP_COLORS.get(p.intraday_action, "#ffd600")
        opt_color = OPTIONS_COLORS.get(p.options_action, "#ffd600")
        with st.expander(
            f"#{p.rank} {p.nse_symbol} — {format_price(p.price, f'{p.nse_symbol}.NS')}",
            expanded=p.rank <= 2,
        ):
            st.markdown(p.reason)

            d1, d2, d3 = st.columns(3)
            with d1:
                st.markdown("**📦 Delivery / SIP**")
                st.markdown(
                    f"<span style='color:{color};font-weight:700'>{p.combined_rec}</span> · "
                    f"{p.long_action} ({p.long_score:+.0f})",
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"Entry: {p.entry_hint} · Stop: {p.stop_hint} · Target: {p.target_hint}"
                )
            with d2:
                st.markdown("**⏱️ Intraday (MIS)**")
                st.markdown(
                    f"<span style='color:{intra_color};font-weight:700'>{p.intraday_action}</span> "
                    f"({p.intraday_score:+.0f})",
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"Entry: {p.intraday_entry} · Stop: {p.intraday_stop} · Target: {p.intraday_target}"
                )
                if p.intraday_summary:
                    st.caption(p.intraday_summary[:120])
                st.caption("Square off MIS before **3:20 PM IST**.")
            with d3:
                st.markdown("**🎯 Options (NSE)**")
                st.markdown(
                    f"<span style='color:{opt_color};font-weight:700'>{p.options_action}</span>",
                    unsafe_allow_html=True,
                )
                if p.options_error:
                    st.warning(f"Chain: {p.options_error[:80]}")
                else:
                    st.markdown(f"**CE:** {p.options_ce_pick}")
                    st.markdown(f"**PE:** {p.options_pe_pick}")
                    if p.options_chain_note:
                        st.caption(p.options_chain_note)

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button(f"Single Stock", key=f"aff_open_{p.nse_symbol}"):
                    st.session_state["single_ticker"] = p.nse_symbol
                    st.session_state["nav_tab"] = "Single Stock"
                    st.rerun()
            with c2:
                if st.button(f"Intraday chart", key=f"aff_intra_{p.nse_symbol}"):
                    st.session_state["intraday_ticker"] = p.nse_symbol
                    st.session_state["nav_tab"] = "Intraday"
                    st.rerun()
            with c3:
                if st.button(f"NSE Options", key=f"aff_opt_{p.nse_symbol}"):
                    st.session_state["nse_opt_symbol"] = p.nse_symbol
                    st.session_state["nav_tab"] = "NSE Options"
                    st.rerun()

    st.caption(
        "Not financial advice. Options can expire worthless. Under ₹3,000 = **1-share affordability** — "
        "size positions in **SIP & Goals** / **Risk & Goals**."
    )
