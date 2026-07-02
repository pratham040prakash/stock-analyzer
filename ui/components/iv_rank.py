"""IV rank / percentile UI for options timing."""

from __future__ import annotations

import streamlit as st

from analyzer.india_macro import IndiaMacroSnapshot
from analyzer.options_analytics import OptionsAnalytics, guidance_for_horizon

_BAND_COLORS = {
    "cheap": "#00c853",
    "mid": "#ffd600",
    "expensive": "#d50000",
    "building": "#64b5f6",
    "unknown": "#888888",
}

_BAND_ICONS = {
    "cheap": "🟢",
    "mid": "🟡",
    "expensive": "🔴",
    "building": "🔵",
    "unknown": "⚪",
}


def render_iv_banner(
    analytics: OptionsAnalytics | None,
    *,
    horizon: str = "options",
    symbol: str = "",
) -> None:
    if not analytics or analytics.atm_iv is None:
        st.caption("IV rank unavailable — symbol may not have F&O or NSE blocked.")
        return

    icon = _BAND_ICONS.get(analytics.iv_band, "⚪")
    color = _BAND_COLORS.get(analytics.iv_band, "#ffd600")
    rank = f"{analytics.iv_rank:.0f}" if analytics.iv_rank is not None else "—"
    pct = f"{analytics.iv_percentile:.0f}" if analytics.iv_percentile is not None else "—"
    label = symbol or analytics.symbol or "Options"
    expiry = f" · exp {analytics.expiry}" if analytics.expiry else ""
    guide = guidance_for_horizon(analytics, horizon)

    st.markdown(
        f"<div style='padding:12px 14px;border-radius:8px;background:#1e1e1e;"
        f"border-left:4px solid {color}'>"
        f"<p style='margin:0;color:#eee'>{icon} <b>{label}</b>{expiry} · "
        f"ATM IV <b>{analytics.atm_iv:.1f}%</b> · IV rank <b>{rank}</b> · "
        f"percentile <b>{pct}</b> · <b>{analytics.iv_band.title()}</b></p>"
        f"<p style='margin:6px 0 0;color:#aaa;font-size:0.9rem'>{guide}</p></div>",
        unsafe_allow_html=True,
    )
    if analytics.flags or analytics.sample_count < 3:
        with st.expander("IV context", expanded=analytics.iv_band == "expensive"):
            if analytics.sample_count:
                st.caption(f"History samples: **{analytics.sample_count}** / 60")
            for f in analytics.flags:
                st.markdown(f"- {f}")
            if analytics.pcr_oi is not None:
                st.caption(f"PCR (OI): **{analytics.pcr_oi:.2f}**")


def render_iv_market_strip(
    macro: IndiaMacroSnapshot | None,
    index_analytics: list[OptionsAnalytics] | None = None,
) -> None:
    """India VIX + index IV rank summary for Market Pulse."""
    parts: list[str] = []
    if macro and macro.india_vix:
        parts.append(f"India VIX **{macro.india_vix.price:.1f}** — {macro.vix_regime}")
    for a in index_analytics or []:
        if a.iv_rank is not None:
            icon = _BAND_ICONS.get(a.iv_band, "⚪")
            parts.append(
                f"{icon} **{a.symbol}** IV rank **{a.iv_rank:.0f}** ({a.iv_band})"
            )
    if not parts:
        return
    st.markdown("#### 📊 IV environment")
    st.info(" · ".join(parts))


def render_iv_table(analytics_list: list[OptionsAnalytics]) -> None:
    ranked = [a for a in analytics_list if a.atm_iv is not None]
    if not ranked:
        return
    st.markdown("#### 📊 IV rank (index options)")
    rows = []
    for a in ranked:
        icon = _BAND_ICONS.get(a.iv_band, "⚪")
        rows.append({
            "": icon,
            "Symbol": a.symbol,
            "ATM IV": f"{a.atm_iv:.1f}",
            "IV Rank": f"{a.iv_rank:.0f}" if a.iv_rank is not None else "—",
            "Percentile": f"{a.iv_percentile:.0f}" if a.iv_percentile is not None else "—",
            "Band": a.iv_band.title(),
            "PCR": f"{a.pcr_oi:.2f}" if a.pcr_oi is not None else "—",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
