"""UI — sideways market options strategy advisor (live CE/PE input)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.options_trade_selection import load_selected_option
from analyzer.sideways_options_advisor import (
    advise_sideways_strategy,
    format_legs_table,
    strategy_comparison_rows,
)
from analyzer.nse_options import fetch_option_chain, INDEX_SYMBOL_MAP


def _prefill_from_starred() -> dict:
    pick = load_selected_option()
    if not pick:
        return {}
    return {
        "index": pick.get("fno_symbol", "NIFTY"),
        "option_type": pick.get("option_type", "CE"),
        "strike": float(pick.get("strike", 0)),
    }


def _render_advice_card(advice) -> None:
    if advice.strategy_id == "no_data":
        st.warning(f"{advice.emoji} **{advice.strategy_name}**")
        for line in advice.rationale:
            st.caption(line)
        return

    risk_label = "Defined risk" if advice.risk_profile == "defined" else "⚠️ Undefined risk"
    st.markdown(
        f"### {advice.emoji} {advice.strategy_name} "
        f"· {advice.market_view} · IV **{advice.iv_tier}** · {risk_label}"
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Spot", f"₹{advice.spot:,.0f}" if advice.spot else "—")
    m2.metric("Range low", f"₹{advice.range_low:,.0f}" if advice.range_low else "—")
    m3.metric("Range high", f"₹{advice.range_high:,.0f}" if advice.range_high else "—")
    m4.metric("OR width", f"{advice.range_pct:.2f}%" if advice.range_pct is not None else "—")

    if advice.blocks_directional:
        st.warning(
            "**Sideways market** — directional CE/PE buy fights theta. "
            "Credit spread below is the income-style alternative."
        )

    for line in advice.rationale:
        st.markdown(f"- {line}")

    if advice.legs:
        st.markdown("**Suggested legs (same expiry)**")
        st.dataframe(
            pd.DataFrame(format_legs_table(advice.legs)),
            use_container_width=True,
            hide_index=True,
        )

    if advice.risk_notes:
        st.markdown("**Risk & exit**")
        for note in advice.risk_notes:
            st.caption(f"· {note}")

    if advice.safer_alternative:
        st.info(f"**Safer / alternative:** {advice.safer_alternative}")

    st.caption(f"**Action:** {advice.action}")
    st.caption(advice.references)


def render_sideways_strategy_advisor_panel(*, market: str = "india", key_prefix: str = "soa") -> None:
    """Interactive advisor — enter CE/PE details for sideways credit strategy."""
    st.markdown("#### 📐 Sideways strategy advisor")
    st.caption(
        "Enter your CE/PE idea — get **iron condor / iron butterfly / credit spread** "
        "when the market is range-bound. "
        "Refs: GTF · [Strike.money](https://www.strike.money/options/best-options-income-strategies) · "
        "[Investopedia](https://www.investopedia.com/trading/options-strategies/)"
    )

    pre = _prefill_from_starred()
    mode = st.radio(
        "Input mode",
        options=["Single leg (CE or PE)", "CE + PE range (strangle anchors)", "OR range only"],
        horizontal=True,
        key=f"{key_prefix}_mode",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        index = st.selectbox(
            "Index",
            options=["NIFTY", "BANKNIFTY"],
            index=0 if pre.get("index", "NIFTY") == "NIFTY" else 1,
            key=f"{key_prefix}_index",
        )
    ce_strike = pe_strike = None
    option_type = strike = None

    if mode == "Single leg (CE or PE)":
        with c2:
            option_type = st.selectbox(
                "Leg",
                options=["CE", "PE"],
                index=0 if pre.get("option_type") == "CE" else 1,
                key=f"{key_prefix}_otype",
            )
        with c3:
            strike = st.number_input(
                "Strike",
                min_value=0.0,
                step=50.0,
                value=float(pre.get("strike") or 0.0),
                key=f"{key_prefix}_strike",
            )
    elif mode == "CE + PE range (strangle anchors)":
        with c2:
            ce_strike = st.number_input(
                "CE strike (upper)",
                min_value=0.0,
                step=50.0,
                value=0.0,
                key=f"{key_prefix}_ce",
            )
        with c3:
            pe_strike = st.number_input(
                "PE strike (lower)",
                min_value=0.0,
                step=50.0,
                value=0.0,
                key=f"{key_prefix}_pe",
            )
    else:
        st.caption("Uses live opening range high/low + IV for strategy pick.")

    if st.button("Get strategy advice", type="primary", key=f"{key_prefix}_go"):
        nse_sym = INDEX_SYMBOL_MAP.get(index, index)
        chain = None
        try:
            chain = fetch_option_chain(nse_sym)
        except Exception:
            chain = None

        iv_rank = None
        iv_band = "unknown"
        spot = getattr(chain, "spot", None) if chain else None
        if chain:
            try:
                from analyzer.options_analytics import analyze_and_record_chain

                analytics = analyze_and_record_chain(chain)
                iv_rank = analytics.iv_rank
                iv_band = analytics.iv_band
            except Exception:
                pass

        advice = advise_sideways_strategy(
            fno_symbol=index,
            ce_strike=ce_strike if ce_strike else None,
            pe_strike=pe_strike if pe_strike else None,
            option_type=option_type,
            strike=strike if strike else None,
            spot=spot,
            iv_rank=iv_rank,
            iv_band=iv_band,
            market=market,
        )
        st.session_state[f"{key_prefix}_last_advice"] = advice

    advice = st.session_state.get(f"{key_prefix}_last_advice")
    if advice:
        st.divider()
        _render_advice_card(advice)

    with st.expander("Sideways credit strategies — quick compare"):
        st.dataframe(
            pd.DataFrame(strategy_comparison_rows()),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "**IV rule of thumb (GTF):** very high IV → strangle/straddle credit (hedge with iron condor); "
            "high IV → iron condor; mid IV → iron butterfly. "
            "**Safest for MIS:** iron condor & iron butterfly (defined risk)."
        )


def render_auto_sideways_hint(
    pick,
    *,
    market: str = "india",
    gate_phase: str | None = None,
) -> None:
    """Compact hint when entry gate blocks directional CE/PE."""
    if gate_phase not in ("wait", "do_not_enter", "observe"):
        return
    advice = advise_sideways_strategy(
        fno_symbol=getattr(pick, "fno_symbol", "NIFTY"),
        option_type=getattr(pick, "option_type", None),
        strike=float(getattr(pick, "strike", 0) or 0),
        market=market,
    )
    if advice.strategy_id in ("no_data", "wait_breakout"):
        return
    st.info(
        f"**Sideways tip:** {advice.emoji} {advice.strategy_name} may fit better than "
        f"buying {getattr(pick, 'option_type', '')} — open **Sideways strategy advisor** below."
    )
