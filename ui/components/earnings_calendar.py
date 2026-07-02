"""Earnings calendar UI — banners and week-ahead strip."""

from __future__ import annotations

import streamlit as st

from analyzer.earnings_calendar import CorporateEvent, trading_guidance, upcoming_within_days

_BAND_COLORS = {
    "critical": "#d50000",
    "elevated": "#ff6e40",
    "watch": "#ffd600",
    "clear": "#69f0ae",
    "past": "#888888",
    "unknown": "#aaaaaa",
}

_BAND_ICONS = {
    "critical": "🔴",
    "elevated": "🟠",
    "watch": "🟡",
    "clear": "🟢",
    "past": "⚪",
    "unknown": "⚪",
}


def render_earnings_banner(event: CorporateEvent | None, *, horizon: str = "all") -> None:
    """Prominent banner on Single Stock / risk pages."""
    if not event:
        st.caption("No upcoming earnings date found (verify on NSE/BSE).")
        return

    icon = _BAND_ICONS.get(event.risk_band, "⚪")
    color = _BAND_COLORS.get(event.risk_band, "#ffd600")

    if event.event_type == "Earnings":
        label = f"{icon} **Earnings**"
        if event.days_until is not None:
            if event.days_until == 0:
                when = "today"
            elif event.days_until == 1:
                when = "tomorrow"
            elif event.days_until > 0:
                when = f"in **{event.days_until} days** ({event.date})"
            else:
                when = f"was **{abs(event.days_until)} days ago** ({event.date})"
            label += f" {when}"
        else:
            label += f" — date **{event.date}**"
    else:
        label = f"{icon} **{event.event_type}** on **{event.date}**"

    st.markdown(
        f"<div style='padding:12px 14px;border-radius:8px;background:#1e1e1e;"
        f"border-left:4px solid {color}'>"
        f"<p style='margin:0;color:#eee'>{label}</p>"
        f"<p style='margin:6px 0 0;color:#aaa;font-size:0.9rem'>"
        f"{trading_guidance(event.days_until, horizon)}</p></div>",
        unsafe_allow_html=True,
    )


def render_earnings_week_strip(events: list[CorporateEvent], *, max_rows: int = 12) -> None:
    """Market Pulse — earnings in the next 14 days."""
    soon = upcoming_within_days(events, days=14)
    if not soon:
        st.success("No Nifty 50 earnings in the next 14 days (per Yahoo calendar).")
        return

    st.markdown("#### 📅 Earnings calendar (next 14 days)")
    rows = []
    for e in soon[:max_rows]:
        icon = _BAND_ICONS.get(e.risk_band, "⚪")
        when = (
            "Today" if e.days_until == 0
            else "Tomorrow" if e.days_until == 1
            else f"{e.days_until}d"
        )
        rows.append({
            "": icon,
            "Stock": e.nse_symbol,
            "Name": e.name[:24],
            "Date": e.date,
            "In": when,
            "Risk": e.risk_band.title(),
            "Guidance": e.guidance[:72] + ("…" if len(e.guidance) > 72 else ""),
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_earnings_compact_table(events: list[CorporateEvent], limit: int = 10) -> None:
    soon = upcoming_within_days(events, days=30)
    if not soon:
        return
    st.markdown("**Upcoming results**")
    for e in soon[:limit]:
        icon = _BAND_ICONS.get(e.risk_band, "⚪")
        st.caption(f"{icon} **{e.nse_symbol}** — {e.date} ({e.days_until}d) · {e.guidance}")
