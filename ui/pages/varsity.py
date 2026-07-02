"""Varsity TA reference tab."""

from __future__ import annotations

import streamlit as st

from analyzer.varsity_knowledge import (
    VARSITY_MODULE_URL,
    ANALYSIS_PRINCIPLES,
    format_chapter_markdown,
    get_chapter,
    module_overview_markdown,
    search_chapters,
)


def render_varsity_guide() -> None:
    st.subheader("Zerodha Varsity — Technical Analysis")
    st.markdown(
        f"This app uses **[Zerodha Varsity TA]({VARSITY_MODULE_URL})** as its **primary knowledge base** "
        "for all signals, candlestick patterns, and trade rules."
    )

    st.markdown("**Engine principles (from Varsity):**")
    for principle in ANALYSIS_PRINCIPLES:
        st.markdown(f"- {principle}")

    search = st.text_input("Search chapters", placeholder="e.g. RSI, candlestick, support, CPR")
    if search:
        hits = search_chapters(search)
        st.caption(f"{len(hits)} chapter(s) found")
    else:
        hits = search_chapters("")

    ch_num = st.selectbox(
        "Jump to chapter",
        options=[ch.number for ch in hits],
        format_func=lambda n: f"Ch {n}: {get_chapter(n).title}" if get_chapter(n) else str(n),
    )
    ch = get_chapter(ch_num)
    if ch:
        st.markdown(format_chapter_markdown(ch))

    with st.expander("Full module overview (all 22 chapters)", expanded=not search):
        st.markdown(module_overview_markdown())

    st.divider()
    st.markdown("**How this connects to your analysis**")
    st.markdown(
        "| App signal | Varsity chapter |\n"
        "|------------|----------------|\n"
        "| RSI (14) | Ch 14 — Indicators (RSI) |\n"
        "| MACD | Ch 15 — MACD & Bollinger |\n"
        "| Moving Averages | Ch 13 — Moving Averages |\n"
        "| Volume / OBV | Ch 12 — Volumes |\n"
        "| Support/Resistance | Ch 11 — S&R |\n"
        "| ADX | Ch 20 — ADX |\n"
        "| VWAP / Opening Range | Ch 22 — Central Pivot Range |\n"
    )
    st.caption("© Zerodha Varsity — educational summaries only. Read full chapters on zerodha.com.")
