"""Live Options Coach — 5s CE/PE advisor with strategies."""
# APEX-012-LIFECYCLE: QUARANTINED

from __future__ import annotations

from datetime import timedelta

import streamlit as st

from analyzer.cache_utils import cached_compute
from analyzer.live_options_coach import build_live_options_coach, suggest_strike
from analyzer.market_session import market_session_status
from analyzer.options_premium_chart import (
    fetch_option_premium_intraday,
    index_context_chart,
    options_premium_chart,
)
from analyzer.options_trade_selection import load_selected_option
from analyzer.providers import get_live_ltp, is_kite_live
from analyzer.sideways_options_advisor import format_legs_table, strike_step
from analyzer.trade_ladder import build_options_ladder
from analyzer.options_reversal_alerts import INDEX_YAHOO
from analyzer.intraday_data import INTERVAL_OPTIONS, fetch_intraday
from ui.components.data_mode_banner import render_data_mode_banner
from ui.components.mis_trade_advisory import render_mis_trade_advisory_strip
from ui.components.sideways_options_advisor import _render_advice_card

_CHART_CACHE_TTL = 30  # seconds — Kite rate-limits historical/instruments API


def _safe_fetch_premium_intraday(**kwargs):
    try:
        return fetch_option_premium_intraday(**kwargs)
    except Exception as exc:
        msg = str(exc).lower()
        if "too many requests" in msg or "network" in msg:
            return None
        raise


def _safe_fetch_intraday(*args, **kwargs):
    try:
        return fetch_intraday(*args, **kwargs)
    except Exception as exc:
        msg = str(exc).lower()
        if "too many requests" in msg or "network" in msg:
            return None, {}
        raise


def _interval_api(interval_key: str) -> str:
    """Map UI label ('5 min') or legacy key ('5m') → fetch_intraday interval."""
    if interval_key in ("1m", "5m", "15m"):
        return interval_key
    return INTERVAL_OPTIONS.get(interval_key, "5m")


def _normalize_interval_session() -> None:
    """Migrate loc_interval if an old API key was stored in session state."""
    raw = st.session_state.get("loc_interval", "5 min")
    if raw in ("1m", "5m", "15m"):
        reverse = {v: k for k, v in INTERVAL_OPTIONS.items()}
        st.session_state["loc_interval"] = reverse.get(raw, "5 min")


def _init_session_defaults() -> None:
    starred = load_selected_option()
    if starred and "loc_index" not in st.session_state:
        st.session_state["loc_index"] = starred.get("fno_symbol", "NIFTY")
        st.session_state["loc_option_type"] = starred.get("option_type", "CE")
        st.session_state["loc_strike"] = float(starred.get("strike", 0))
    st.session_state.setdefault("loc_index", "NIFTY")
    st.session_state.setdefault("loc_option_type", "CE")
    st.session_state.setdefault("loc_strike", 24500.0)
    st.session_state.setdefault("loc_interval", "5 min")
    st.session_state.setdefault("loc_auto_refresh", True)
    _normalize_interval_session()


def _render_coach_signals(
    *,
    market: str,
    fno_symbol: str,
    option_type: str,
    strike: float,
) -> object:
    """Live gate + strategy read (5s) — no heavy Kite chart calls."""
    snap = build_live_options_coach(
        fno_symbol=fno_symbol,
        option_type=option_type,
        strike=strike,
        market=market,
    )

    st.caption(f"Updated **{snap.updated_at}** · {snap.data_source}")

    st.markdown(
        f"## {snap.primary_emoji} **{snap.primary_action}**"
    )
    st.markdown(snap.whats_happening)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Index spot", f"₹{snap.spot:,.0f}" if snap.spot else "—")
    m2.metric("OR", (
        f"₹{snap.or_low:,.0f}–₹{snap.or_high:,.0f}"
        if snap.or_low and snap.or_high else "—"
    ))
    m3.metric(f"{option_type} {strike:g}", (
        f"₹{snap.premium:,.2f}" if snap.premium else "—"
    ))
    m4.metric("Spot vs OR", snap.spot_vs_or[:28] + ("…" if len(snap.spot_vs_or) > 28 else ""))

    if snap.gate:
        with st.expander(f"{snap.gate.emoji} OR entry gate — {snap.gate.headline}", expanded=True):
            st.markdown(snap.gate.detail)
            st.markdown(f"**Do:** {snap.gate.action}")
            for chk in snap.gate.checks:
                st.caption(chk)

    if snap.reversal and snap.reversal.phase == "invalidated":
        st.error(f"{snap.reversal.emoji} **{snap.reversal.label}** — {snap.reversal.detail}")
        st.warning(f"**Action:** {snap.reversal.action}")
    elif snap.reversal:
        st.info(f"{snap.reversal.emoji} **{snap.reversal.label}** — {snap.reversal.detail}")

    st.markdown("#### Strategy signals (every 5 sec)")
    for sig in sorted(snap.signals, key=lambda s: s.priority):
        st.markdown(
            f"**{sig.emoji} {sig.headline}** ({sig.category})  \n"
            f"{sig.detail}  \n"
            f"*→ {sig.action}*"
        )

    if snap.iv_guidance:
        st.caption(f"📊 {snap.iv_guidance}")
    if snap.premium_status:
        st.caption(snap.premium_status)

    if snap.sideways and snap.sideways.strategy_id != "no_data":
        st.divider()
        st.markdown("#### Sideways / credit strategy advisor")
        _render_advice_card(snap.sideways)
        if snap.sideways.legs:
            import pandas as pd

            st.dataframe(
                pd.DataFrame(format_legs_table(snap.sideways.legs)),
                use_container_width=True,
                hide_index=True,
            )

    return snap


def _render_coach_charts(
    snap,
    *,
    market: str,
    fno_symbol: str,
    option_type: str,
    strike: float,
    interval: str,
) -> None:
    """Charts refresh every 30s to avoid Kite rate limits."""
    st.caption(f"Charts refresh every {_CHART_CACHE_TTL}s (Kite API limit)")

    c_chart, c_index = st.columns(2)
    with c_chart:
        st.markdown(f"##### {fno_symbol} {option_type} {strike:g} — live chart")
        if not snap.expiry:
            st.caption("Loading expiry from NSE chain…")
        else:
            cache_key = f"loc_prem_{fno_symbol}_{option_type}_{strike}_{snap.expiry}_{interval}"
            prem = cached_compute(
                cache_key,
                _CHART_CACHE_TTL,
                lambda: _safe_fetch_premium_intraday(
                    fno_symbol=fno_symbol,
                    strike=strike,
                    expiry=snap.expiry,
                    option_type=option_type,
                    interval=interval,
                ),
            )
            if prem:
                df, meta = prem
                entry = float(snap.premium or df["Close"].iloc[-1])
                ladder = build_options_ladder(entry)
                st.plotly_chart(
                    options_premium_chart(df, ladder, title=f"Premium · {meta.source}"),
                    use_container_width=True,
                    key=f"loc_prem_{fno_symbol}_{option_type}_{strike}_{interval}",
                )
                st.caption(meta.lag_note or meta.source)
            else:
                yahoo = INDEX_YAHOO.get(fno_symbol.upper())
                if yahoo and snap.spot:
                    idf, _ = cached_compute(
                        f"loc_idx_fb_{yahoo}_{interval}",
                        _CHART_CACHE_TTL,
                        lambda: _safe_fetch_intraday(yahoo, interval=interval, market=market),
                    )
                    if idf is not None and not idf.empty:
                        st.plotly_chart(
                            index_context_chart(
                                idf,
                                strike=strike,
                                spot=snap.spot,
                                title=f"{fno_symbol} index (premium chart needs Kite NFO)",
                            ),
                            use_container_width=True,
                            key=f"loc_idx_{fno_symbol}_{interval}",
                        )
                        st.caption("Premium candles need Kite NFO — showing index context + strike line.")
                    else:
                        st.caption("Kite rate limit or no data — charts pause briefly, signals still update.")
                else:
                    st.caption("Chart unavailable — check Kite login or wait for NSE.")

    with c_index:
        st.markdown(f"##### {fno_symbol} index ({interval})")
        yahoo = INDEX_YAHOO.get(fno_symbol.upper())
        if yahoo and snap.spot:
            idf, meta = cached_compute(
                f"loc_spot_{yahoo}_{interval}",
                _CHART_CACHE_TTL,
                lambda: _safe_fetch_intraday(yahoo, interval=interval, market=market),
            )
            if idf is not None and not idf.empty:
                st.plotly_chart(
                    index_context_chart(
                        idf,
                        strike=strike,
                        spot=snap.spot,
                        title=f"{fno_symbol} · OR context",
                    ),
                    use_container_width=True,
                    key=f"loc_spot_{fno_symbol}_{interval}",
                )
                lag = meta.get("lag_note", "") if isinstance(meta, dict) else getattr(meta, "lag_note", "")
                st.caption(f"{meta.get('source', '—') if isinstance(meta, dict) else meta.source}{(' · ' + lag) if lag else ''}")
            else:
                st.caption("Index chart paused (Kite rate limit) — retry in ~30s.")
        else:
            st.caption("Index chart loading…")


def _render_coach_body(
    *,
    market: str,
    fno_symbol: str,
    option_type: str,
    strike: float,
    interval: str,
) -> None:
    snap = _render_coach_signals(
        market=market,
        fno_symbol=fno_symbol,
        option_type=option_type,
        strike=strike,
    )
    _render_coach_charts(
        snap,
        market=market,
        fno_symbol=fno_symbol,
        option_type=option_type,
        strike=strike,
        interval=interval,
    )


@st.fragment(run_every=timedelta(seconds=5))
def _live_coach_signals_fragment(
    market: str,
    fno_symbol: str,
    option_type: str,
    strike: float,
) -> None:
    _render_coach_signals(
        market=market,
        fno_symbol=fno_symbol,
        option_type=option_type,
        strike=strike,
    )


@st.fragment(run_every=timedelta(seconds=30))
def _live_coach_charts_fragment(
    market: str,
    fno_symbol: str,
    option_type: str,
    strike: float,
    interval: str,
) -> None:
    snap = build_live_options_coach(
        fno_symbol=fno_symbol,
        option_type=option_type,
        strike=strike,
        market=market,
    )
    _render_coach_charts(
        snap,
        market=market,
        fno_symbol=fno_symbol,
        option_type=option_type,
        strike=strike,
        interval=interval,
    )


def render_live_options_advisor(market: str, *, period: str = "1y") -> None:
    """Dedicated tab: pick CE/PE, auto-refresh coach every 5 seconds."""
    _init_session_defaults()
    session = market_session_status()

    st.subheader("⚡ Live Options Coach")
    st.markdown(
        "Pick **Nifty** or **Bank Nifty**, choose **CE** or **PE**, enter strike. "
        "Every **5 seconds** the tool reads live index + premium, applies **OR gate**, "
        "**reversal**, **IV**, and **sideways** strategies (iron condor, credit spreads), "
        "and tells you **what to do now**."
    )
    st.caption(
        f"Session: **{session.get('status', '—')}** · "
        f"{'🟢 Kite live' if is_kite_live() else '🟡 Yahoo lag — connect Kite for real-time'}"
    )

    render_data_mode_banner(key_prefix="loc_data")
    render_mis_trade_advisory_strip(market=market, key_prefix="loc_mis_adv")

    c1, c2, c3, c4 = st.columns([2, 1, 2, 1])
    with c1:
        index = st.selectbox(
            "Index",
            options=["NIFTY", "BANKNIFTY"],
            key="loc_index",
        )
    with c2:
        option_type = st.radio(
            "Leg",
            options=["CE", "PE"],
            horizontal=True,
            key="loc_option_type",
        )
    with c3:
        step = strike_step(index)
        strike = st.number_input(
            f"Strike (step {step})",
            min_value=float(step),
            max_value=200000.0,
            step=float(step),
            key="loc_strike",
            format="%.0f",
        )
    with c4:
        if st.button("ATM strike", use_container_width=True, key="loc_atm"):
            atm = suggest_strike(index, option_type, market=market)
            if atm:
                st.session_state["loc_strike"] = atm
                st.rerun()
            else:
                st.warning("Need live spot for ATM")

    c5, c6, c7 = st.columns([2, 2, 2])
    with c5:
        st.selectbox(
            "Chart interval",
            options=list(INTERVAL_OPTIONS.keys()),
            index=list(INTERVAL_OPTIONS.keys()).index(
                st.session_state.get("loc_interval", "5 min")
            )
            if st.session_state.get("loc_interval", "5 min") in INTERVAL_OPTIONS
            else 1,
            key="loc_interval",
        )
    interval = _interval_api(st.session_state["loc_interval"])
    with c6:
        auto = st.checkbox(
            "Auto-refresh every 5 sec",
            key="loc_auto_refresh",
            help="Runs OR gate + strategies on a 5-second loop during market hours.",
        )
    with c7:
        if st.button("Refresh chain now", use_container_width=True, key="loc_chain_refresh"):
            build_live_options_coach(
                fno_symbol=index,
                option_type=option_type,
                strike=float(strike),
                market=market,
                force_chain=True,
            )
            st.rerun()

    st.divider()

    if auto:
        _live_coach_signals_fragment(
            market=market,
            fno_symbol=index,
            option_type=option_type,
            strike=float(strike),
        )
        _live_coach_charts_fragment(
            market=market,
            fno_symbol=index,
            option_type=option_type,
            strike=float(strike),
            interval=interval,
        )
    else:
        _render_coach_body(
            market=market,
            fno_symbol=index,
            option_type=option_type,
            strike=float(strike),
            interval=interval,
        )

    with st.expander("How strategies are applied"):
        st.markdown(
            "- **9:15–9:45** — observe OR only; no entries  \n"
            "- **After 9:45** — CE needs spot ≥ OR high; PE needs spot ≤ OR low  \n"
            "- **OTM >3.5%** — blocked (lottery ticket)  \n"
            "- **Inside OR (chop)** — bear call / bull put / iron condor instead of buying CE/PE  \n"
            "- **Reversal** — PE invalidated above OR high; CE below OR low → exit  \n"
            "- **Premium ladder** — T1 book partial, trail stop, square off MIS ~3:20 PM"
        )
