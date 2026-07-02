"""India macro strip and pulse color helpers."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.theme import REC_COLORS


def pulse_buy_color(action: str) -> str:
    if action in ("STRONG BUY", "BUY", "CORE BUY", "ACCUMULATE"):
        return REC_COLORS.get(action, "#00c853")
    if action in ("SELL", "STRONG SELL", "AVOID", "WEAK"):
        return REC_COLORS.get(action, "#d50000")
    return "#ffd600"


def render_india_macro_strip(macro) -> None:
    if not macro:
        return
    st.subheader("🇮🇳 India macro pulse")
    c1, c2, c3, c4 = st.columns(4)
    if macro.india_vix:
        c1.metric("India VIX", f"{macro.india_vix.price:.2f}", macro.india_vix.change_1d_pct)
        c1.caption(macro.vix_regime)
    if macro.fii_dii:
        c2.markdown("**FII / DII (cash)**")
        c2.caption(macro.fii_dii.summary)
    if macro.sector_leader:
        c3.markdown(f"**Sector leader:** {macro.sector_leader}")
    if macro.sector_laggard:
        c4.markdown(f"**Sector laggard:** {macro.sector_laggard}")
    if macro.premarket_note:
        st.info(macro.premarket_note)
    if getattr(macro, "errors", None):
        for err in macro.errors[:4]:
            st.caption(f"⚠ {err}")
    if macro.sectors:
        with st.expander("Sector indices (1D %)", expanded=False):
            rows = [
                {"Sector": s.name, "Price": f"{s.price:,.0f}", "1D %": s.change_1d_pct}
                for s in macro.sectors
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
