"""Trade / No trade advisory strip — predictive risk synthesis."""
# APEX-012-LIFECYCLE: QUARANTINED

from __future__ import annotations

import streamlit as st

from analyzer.mis_trade_advisory import build_mis_trade_advisory


def render_mis_trade_advisory_strip(*, market: str = "india", key_prefix: str = "mis_adv") -> None:
    """Prominent TRADE / CAUTION / NO TRADE banner for options MIS."""
    adv = build_mis_trade_advisory(market=market)

    st.markdown("#### 🚦 Trade / No trade")
    st.markdown(f"### {adv.emoji} {adv.headline}")
    st.caption(
        f"Risk score **{adv.score}/100** · confidence **{getattr(adv, 'confidence_pct', adv.score)}/100**"
        f" · regime **{adv.regime or '—'}**"
        + (f" · {adv.time_note}" if adv.time_note else "")
    )
    if getattr(adv, "mtf_summary", ""):
        st.caption(f"MTF: {adv.mtf_summary}")
    if getattr(adv, "flow_summary", ""):
        st.caption(f"Flow: {adv.flow_summary}")
    if getattr(adv, "synthesis_verdict", ""):
        st.caption(
            f"🧠 Multi-strategy: **{adv.synthesis_verdict}** "
            f"({getattr(adv, 'synthesis_confidence', 0)}/100)"
            + (f" · {adv.synthesis_summary}" if getattr(adv, "synthesis_summary", "") else "")
        )
    st.markdown(adv.summary)

    if adv.best_pick:
        st.caption(f"Focus leg: **{adv.best_pick}**")

    if adv.positives:
        for p in adv.positives:
            st.success(p, icon="✅")

    if adv.flags:
        for f in adv.flags:
            if f.startswith("_"):
                st.caption(f.strip("_"))
            elif adv.verdict == "NO_TRADE":
                st.error(f, icon="⛔")
            else:
                st.warning(f, icon="⚠️")

    if adv.loss_streak_days >= 2:
        st.info(
            "Log each session in **Track Record → Trade journal** (symbol, P&L) "
            "so streak detection stays accurate."
        )

    pillars = getattr(adv, "synthesis_pillars", None) or []
    if pillars:
        with st.expander("🧠 All strategy pillars (options)", expanded=False):
            for line in pillars:
                st.caption(line)

    with st.expander("Log session P&L (enables loss-streak alerts)", expanded=adv.loss_streak_days == 0):
        from analyzer.trade_journal import save_journal_entry
        from analyzer.watchlist_history import session_target_date

        c1, c2, c3 = st.columns(3)
        with c1:
            sym = st.text_input("Symbol", value="NIFTY", key=f"{key_prefix}_log_sym")
        with c2:
            leg = st.text_input("Leg", value="CE 24500", key=f"{key_prefix}_log_leg")
        with c3:
            pnl = st.number_input("P&L (₹)", value=0.0, step=50.0, key=f"{key_prefix}_log_pnl")
        if st.button("Save to journal", key=f"{key_prefix}_log_save"):
            save_journal_entry(
                trade_date=session_target_date(),
                symbol=sym,
                leg=leg,
                pnl_inr=pnl,
                mistake="Logged from Trade / No trade strip",
                fix="Follow advisory flags tomorrow",
            )
            st.success("Saved — reload page to refresh streak.")
            st.rerun()
