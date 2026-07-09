"""UI — MIS trade journal on Track Record."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.trade_journal import load_journal_entries, save_journal_entry
from analyzer.watchlist_history import session_target_date


def render_trade_journal_panel() -> None:
    st.markdown("### MIS trade journal — learn from mistakes")
    st.caption(
        "Log what went wrong and your fix **after each session**. "
        "Review weekly — patterns beat memory."
    )

    with st.expander("Add today's lesson", expanded=False):
        td = session_target_date()
        c1, c2 = st.columns(2)
        with c1:
            symbol = st.text_input(
                "Symbol / leg",
                value="BANKNIFTY PE 55000",
                key="tj_symbol",
            )
            entry = st.number_input("Entry (₹)", min_value=0.0, step=1.0, value=0.0, key="tj_entry")
            exit_p = st.number_input("Exit (₹)", min_value=0.0, step=1.0, value=0.0, key="tj_exit")
        with c2:
            leg = st.text_input("Type", value="options", key="tj_leg", help="options | equity")
            pnl = st.number_input("P&L (₹)", step=100.0, value=0.0, key="tj_pnl")
            mistake = st.text_area(
                "What went wrong?",
                placeholder="Entered before 9:45 OR confirm; OTM PE in chop",
                key="tj_mistake",
                height=68,
            )
            fix = st.text_area(
                "Fix for next time",
                placeholder="Wait OR low for PE; exit at stop; one loss = done",
                key="tj_fix",
                height=68,
            )
        if st.button("Save journal entry", type="primary", key="tj_save"):
            if not symbol.strip():
                st.error("Enter a symbol or leg name.")
            else:
                save_journal_entry(
                    trade_date=td,
                    symbol=symbol.strip(),
                    leg=leg.strip(),
                    entry=entry or None,
                    exit=exit_p or None,
                    pnl_inr=pnl if pnl != 0 else None,
                    mistake=mistake,
                    fix=fix,
                )
                st.success("Saved — review before tomorrow's prep.")
                st.rerun()

    entries = load_journal_entries(limit=15)
    if not entries:
        st.info("No journal entries yet — log today's BANKNIFTY PE lesson above.")
        return

    rows = []
    for e in entries:
        rows.append({
            "Date": e.trade_date,
            "Leg": e.symbol,
            "Entry": f"₹{e.entry:g}" if e.entry else "—",
            "Exit": f"₹{e.exit:g}" if e.exit else "—",
            "P&L": f"₹{e.pnl_inr:,.0f}" if e.pnl_inr is not None else "—",
            "Mistake": (e.mistake[:60] + "…") if len(e.mistake) > 60 else e.mistake,
            "Fix": (e.fix[:60] + "…") if len(e.fix) > 60 else e.fix,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("Full text — recent entries"):
        for e in entries[:5]:
            st.markdown(f"**{e.trade_date} · {e.symbol}**")
            if e.mistake:
                st.caption(f"Mistake: {e.mistake}")
            if e.fix:
                st.caption(f"Fix: {e.fix}")
            st.divider()
