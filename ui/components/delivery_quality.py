"""Delivery % and volume-quality UI."""

from __future__ import annotations

import streamlit as st

from analyzer.delivery_quality import DeliverySnapshot

_QUALITY_COLORS = {
    "strong": "#00c853",
    "moderate": "#69f0ae",
    "weak": "#ffd600",
    "speculative": "#d50000",
    "unknown": "#888888",
}

_QUALITY_ICONS = {
    "strong": "🟢",
    "moderate": "🟢",
    "weak": "🟡",
    "speculative": "🔴",
    "unknown": "⚪",
}


def render_delivery_banner(snap: DeliverySnapshot | None) -> None:
    if not snap:
        st.caption("Delivery % unavailable (NSE blocked or non-EQ symbol). Chart volume still shown.")
        return

    icon = _QUALITY_ICONS.get(snap.quality, "⚪")
    color = _QUALITY_COLORS.get(snap.quality, "#ffd600")
    pct = f"{snap.delivery_pct:.1f}%" if snap.delivery_pct is not None else "N/A"
    vol = f"{snap.volume_ratio:.1f}× avg" if snap.volume_ratio is not None else "—"

    st.markdown(
        f"<div style='padding:12px 14px;border-radius:8px;background:#1e1e1e;"
        f"border-left:4px solid {color}'>"
        f"<p style='margin:0;color:#eee'>{icon} <b>Delivery {pct}</b> · "
        f"Volume {vol} · Quality: <b>{snap.quality.title()}</b>"
        f"{f' (as of {snap.as_of_date})' if snap.as_of_date else ''}</p>"
        f"<p style='margin:6px 0 0;color:#aaa;font-size:0.9rem'>{snap.guidance}</p></div>",
        unsafe_allow_html=True,
    )
    if snap.flags:
        with st.expander("Volume & delivery details", expanded=snap.quality == "speculative"):
            for f in snap.flags:
                st.markdown(f"- {f}")
            if snap.avg_delivery_5d is not None:
                st.caption(f"5-day avg delivery: **{snap.avg_delivery_5d:.1f}%**")


def render_delivery_table(snapshots: list[DeliverySnapshot], *, max_rows: int = 15) -> None:
    ranked = [s for s in snapshots if s.delivery_pct is not None]
    if not ranked:
        st.caption("No delivery data loaded.")
        return

    st.markdown("#### 📦 Delivery & volume quality (Nifty 50)")
    rows = []
    for s in ranked[:max_rows]:
        icon = _QUALITY_ICONS.get(s.quality, "⚪")
        rows.append({
            "": icon,
            "Stock": s.nse_symbol,
            "Delivery %": f"{s.delivery_pct:.1f}",
            "Vol vs avg": f"{s.volume_ratio:.1f}×" if s.volume_ratio else "—",
            "Quality": s.quality.title(),
            "Signal": s.signal.title(),
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    weak = [s.nse_symbol for s in ranked if s.quality == "speculative"][:8]
    if weak:
        st.warning(f"Low delivery (speculative churn): **{', '.join(weak)}** — cautious for swing/MIS.")
