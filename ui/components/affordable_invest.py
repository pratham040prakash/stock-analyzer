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
from ui.theme import REC_COLORS


def render_affordable_invest_section(report) -> None:
    picks = affordable_from_pulse_report(report, limit=5)
    max_price = DEFAULT_MAX_INVEST_PRICE_INR

    st.subheader(f"💰 Top 5 to invest under ₹{max_price:,.0f}")
    st.caption(
        "From **live Nifty 50 scan** — ranked on long-term quality + combined score. "
        "Prices use **Kite LTP** when connected, else NSE/Yahoo."
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
            "Name": p.name[:24],
            "Live price": format_price(p.price, f"{p.nse_symbol}.NS"),
            "Source": p.ltp_source,
            "Day chg": chg,
            "Invest score": f"{p.invest_score:.0f}",
            "Long-term": f"{p.long_action} ({p.long_score:+.0f})",
            "Combined": p.combined_rec,
            "Swing": f"{p.short_action} ({p.short_score:+.0f})",
        })
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    st.markdown("#### Why these names")
    for p in picks:
        color = REC_COLORS.get(p.combined_rec, "#69f0ae")
        with st.expander(
            f"#{p.rank} {p.nse_symbol} — {format_price(p.price, f'{p.nse_symbol}.NS')}",
            expanded=p.rank <= 2,
        ):
            st.markdown(
                f"<span style='color:{color};font-weight:700'>{p.combined_rec}</span> · "
                f"invest score **{p.invest_score:.0f}**",
                unsafe_allow_html=True,
            )
            st.markdown(p.reason)
            st.markdown(
                f"**Plan (delivery):** {p.entry_hint} · **Stop:** {p.stop_hint} · **Target:** {p.target_hint}"
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"Analyze {p.nse_symbol}", key=f"aff_open_{p.nse_symbol}"):
                    st.session_state["single_ticker"] = p.nse_symbol
                    st.session_state["nav_tab"] = "Single Stock"
                    st.rerun()
            with c2:
                if st.button(f"SIP plan for {p.nse_symbol}", key=f"aff_sip_{p.nse_symbol}"):
                    st.session_state["nav_tab"] = "SIP & Goals"
                    st.rerun()

    st.caption(
        "Not financial advice. Under ₹3,000 filter is for **affordability** (1 share) — "
        "verify allocation size vs your goals in **SIP & Goals**."
    )
