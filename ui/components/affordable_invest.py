"""Market Pulse — top invest picks under budget."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.affordable_invest import (
    DEFAULT_MAX_INVEST_PRICE_INR,
    DEFAULT_MAX_OPTION_LOT_COST_INR,
    OPTION_LOT_BUDGET_OPTIONS,
    affordable_from_pulse_report,
    affordable_invest_summary,
    build_affordable_index_options,
)
from analyzer.markets import format_price
from analyzer.nse_options import get_fno_lot_size
from ui.navigation import request_nav_tab
from ui.theme import INTRADAY_SETUP_COLORS, OPTIONS_COLORS, REC_COLORS


def _render_index_affordable(
    report,
    max_lot_cost: float,
    period: str,
    load_options: bool,
) -> None:
    st.markdown(f"#### 📈 Nifty & Bank Nifty — 1-lot under ₹{max_lot_cost:,.0f}")
    nifty_lot = get_fno_lot_size("NIFTY")
    bank_lot = get_fno_lot_size("BANKNIFTY")
    st.caption(
        f"Picks **CE/PE** where **premium × lot size ≤ ₹{max_lot_cost:,.0f}**. "
        f"Rough max per unit: Nifty **₹{max_lot_cost / nifty_lot:,.0f}** ({nifty_lot} lot), "
        f"Bank Nifty **₹{max_lot_cost / bank_lot:,.0f}** ({bank_lot} lot). "
        "Margin on Kite may differ — verify before trading."
    )
    if not load_options:
        st.info("Check **Load NSE CE/PE strikes** above to fetch Nifty & Bank Nifty contracts.")
        return

    with st.spinner("Fetching Nifty & Bank Nifty option chains…"):
        index_picks = build_affordable_index_options(
            report, max_lot_cost=max_lot_cost, period=period,
        )

    cols = st.columns(2)
    for col, idx in zip(cols, index_picks):
        with col:
            opt_color = OPTIONS_COLORS.get(idx.options_action, "#ffd600")
            bias_color = REC_COLORS.get(idx.index_bias, "#ffd600")
            st.markdown(f"**{idx.name}** (`{idx.fno_symbol}`)")
            if idx.error and not idx.ce_pick.strip("—"):
                st.warning(idx.error[:100])
            st.metric("Index spot", f"₹{idx.spot:,.2f}" if idx.spot else "—")
            st.metric("Min lot size", f"{idx.lot_size} units" if idx.lot_size else "—")
            if idx.ce_total_cost is not None or idx.pe_total_cost is not None:
                cost_parts = []
                if idx.ce_total_cost is not None:
                    cost_parts.append(f"CE 1 lot ₹{idx.ce_total_cost:,.0f}")
                if idx.pe_total_cost is not None:
                    cost_parts.append(f"PE 1 lot ₹{idx.pe_total_cost:,.0f}")
                st.caption("**Total to buy 1 lot:** " + " · ".join(cost_parts))
            st.caption(f"Expiry **{idx.expiry}** · Bias **{idx.index_bias}**")
            st.markdown(
                f"Signal: <span style='color:{opt_color};font-weight:700'>{idx.options_action}</span> · "
                f"Index TA: <span style='color:{bias_color};font-weight:600'>{idx.index_bias}</span>",
                unsafe_allow_html=True,
            )
            if idx.intraday_note:
                st.caption(idx.intraday_note[:140])
            st.markdown(idx.recommended)
            st.markdown(f"**CE (≤₹{max_lot_cost:,.0f} total):** {idx.ce_pick}")
            st.markdown(f"**PE (≤₹{max_lot_cost:,.0f} total):** {idx.pe_pick}")
            if idx.chain_note:
                st.caption(idx.chain_note)
            if st.button(f"Open {idx.fno_symbol} in NSE Options", key=f"aff_idx_{idx.fno_symbol}"):
                request_nav_tab("NSE Options", nse_opt_symbol=idx.fno_symbol)

    st.divider()


def render_affordable_invest_section(report, period: str = "1y") -> None:
    max_share_price = DEFAULT_MAX_INVEST_PRICE_INR
    default_budget_idx = list(OPTION_LOT_BUDGET_OPTIONS).index(DEFAULT_MAX_OPTION_LOT_COST_INR)

    st.subheader(f"💰 Top 5 stocks under ₹{max_share_price:,.0f} — Delivery · Intraday · CE/PE")
    st.caption(
        "Live **Nifty 50** scan: **delivery/SIP** (share price cap), **intraday MIS**, "
        "and **NSE options** filtered by your **1-lot budget** below."
    )

    max_lot_cost = st.select_slider(
        "Options budget — max to buy 1 F&O lot (premium × lot size)",
        options=list(OPTION_LOT_BUDGET_OPTIONS),
        value=OPTION_LOT_BUDGET_OPTIONS[default_budget_idx],
        format_func=lambda x: f"₹{x:,.0f}",
        key="aff_option_lot_budget",
        help="Lower budget → cheaper (farther OTM) strikes. Nifty 75 lot: ₹10k ≈ ₹133/unit max.",
    )

    load_options = st.checkbox(
        "Load NSE CE/PE strikes (slower)",
        value=True,
        key="aff_load_options",
        help="Fetches Nifty, Bank Nifty, and stock option chains (~10–20 sec).",
    )

    _render_index_affordable(report, max_lot_cost, period, load_options)

    with st.spinner("Ranking stock picks + intraday setups…"):
        picks = affordable_from_pulse_report(
            report,
            limit=5,
            enrich_options=load_options,
            max_option_lot_cost=max_lot_cost,
        )

    if not picks:
        st.warning(affordable_invest_summary(picks, max_share_price))
        st.caption(
            "Most Nifty names may be above ₹3,000 or bearish today. "
            "Check **long-term** picks below or **Compare** tab."
        )
        return

    st.success(affordable_invest_summary(picks, max_share_price))

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
            "CE 1-lot": f"₹{p.ce_total_cost:,.0f}" if p.ce_total_cost else "—",
            "PE 1-lot": f"₹{p.pe_total_cost:,.0f}" if p.pe_total_cost else "—",
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
                st.markdown(f"**🎯 Options (≤₹{max_lot_cost:,.0f}/lot)**")
                st.markdown(
                    f"<span style='color:{opt_color};font-weight:700'>{p.options_action}</span>",
                    unsafe_allow_html=True,
                )
                if p.options_error:
                    st.warning(f"Chain: {p.options_error[:80]}")
                else:
                    if p.lot_size and p.lot_size > 1:
                        st.caption(f"F&O lot size: **{p.lot_size}** shares per lot")
                    if p.ce_total_cost is not None:
                        st.caption(f"CE 1-lot buy: **₹{p.ce_total_cost:,.0f}**")
                    if p.pe_total_cost is not None:
                        st.caption(f"PE 1-lot buy: **₹{p.pe_total_cost:,.0f}**")
                    st.markdown(f"**CE:** {p.options_ce_pick}")
                    st.markdown(f"**PE:** {p.options_pe_pick}")
                    if p.options_chain_note:
                        st.caption(p.options_chain_note)

            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button(f"Single Stock", key=f"aff_open_{p.nse_symbol}"):
                    request_nav_tab("Single Stock", single_ticker=p.nse_symbol)
            with c2:
                if st.button(f"Intraday chart", key=f"aff_intra_{p.nse_symbol}"):
                    request_nav_tab("Suggestions", intraday_ticker=p.nse_symbol)
            with c3:
                if st.button(f"NSE Options", key=f"aff_opt_{p.nse_symbol}"):
                    request_nav_tab("NSE Options", nse_opt_symbol=p.nse_symbol)

    st.caption(
        "Not financial advice. Options can expire worthless. "
        f"Stocks: delivery cap **₹{max_share_price:,.0f}/share**. "
        f"Options: **1-lot budget ₹{max_lot_cost:,.0f}** (premium × lot size). "
        "Size positions in **SIP & Goals** / **Risk & Goals**."
    )
