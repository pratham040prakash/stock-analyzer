"""Track Record — suggestion journal, validation, and learning."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.eod_learning import run_eod_learning_cycle
from analyzer.suggestion_journal import count_pending_validation, fetch_suggestions
from analyzer.suggestion_learning import build_learning_report
from analyzer.telegram_notify import (
    format_track_record_telegram,
    send_telegram_broadcast,
    telegram_configured,
)
from analyzer.threshold_tuning import TuningResult, get_pulse_thresholds, recent_tuning_history, reset_thresholds
from analyzer.watchlist_eod import score_pinned_plans
from ui.components.watchlist_stats import render_watchlist_success_panel


def render_track_record() -> None:
    st.subheader("Track Record — Suggestion Journal & Learning")
    st.markdown(
        "Every **Market Pulse** and **Daily Advisor** pick is logged. "
        "After market close, outcomes are scored vs actual price moves so the app "
        "**learns what worked** and surfaces calibration hints."
    )

    pending = count_pending_validation()
    c1, c2, c3 = st.columns(3)
    report = build_learning_report()

    c1.metric("Total logged", report.total_suggestions)
    c2.metric("Validated", report.validated_count)
    c3.metric("Win rate", f"{report.overall_win_rate_pct:.1f}%")

    gates = get_pulse_thresholds()
    st.subheader("Auto-tuned score gates (Market Pulse)")
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Intraday min", gates["intraday"])
    g2.metric("Swing min", gates["short"])
    g3.metric("Long min", gates["long"])
    if g4.button("Reset gates to defaults", key="reset_thresholds"):
        reset_thresholds()
        st.success("Score gates reset to defaults.")
        st.rerun()
    history = recent_tuning_history(5)
    if history:
        st.caption(
            "Recent tuning: "
            + " · ".join(
                f"{h['horizon']} {h['old']}→{h['new']} ({h.get('win_rate_pct', '?')}%)"
                for h in history
            )
        )
    else:
        st.caption(
            "Gates adjust automatically after 8+ scored picks per horizon. "
            "Low win rate tightens; high win rate relaxes slightly."
        )

    if pending > 0:
        st.info(f"**{pending}** past suggestions ready to score against market data.")
        if st.button("Validate past suggestions now", type="primary", key="validate_suggestions"):
            with st.spinner("Scoring outcomes, tuning gates, sending Telegram if configured..."):
                eod = run_eod_learning_cycle(send_telegram_alert=True)
            msg = f"Validated **{eod.validated}** suggestions."
            if eod.tuning and eod.tuning.changes:
                ch = eod.tuning.changes[0]
                msg += f" Gate update: {ch.horizon} {ch.old_value}→{ch.new_value}."
            if eod.telegram_sent:
                msg += " Telegram scorecard sent."
            st.success(msg)
            st.rerun()
    else:
        st.caption("All past suggestions scored. New picks log automatically when you run Pulse / Advisor.")

    if telegram_configured():
        if st.button("Send Telegram scorecard now", key="tg_track_record"):
            tuning = TuningResult(thresholds=get_pulse_thresholds())
            msg = format_track_record_telegram(report, tuning, {"validated": 0})
            ok, err = send_telegram_broadcast(msg, alert_type="eod")
            if ok:
                st.success("Scorecard sent to Telegram.")
            else:
                st.error(err)
    else:
        st.caption("Subscribe to Telegram in the sidebar for EOD scorecards.")

    if report.insights:
        st.subheader("Daily learning insights")
        for insight in report.insights:
            st.markdown(f"- {insight}")

    if report.slices:
        st.subheader("Performance by source & horizon")
        slice_rows = []
        for s in report.slices:
            slice_rows.append({
                "Segment": s.label,
                "Logged": s.total,
                "Scored": s.scored,
                "Wins": s.wins,
                "Losses": s.losses,
                "Win %": f"{s.win_rate_pct:.1f}",
                "Avg 1D %": f"{s.avg_return_1d:+.2f}" if s.avg_return_1d is not None else "—",
                "Avg α vs Nifty": f"{s.avg_alpha_1d:+.2f}" if s.avg_alpha_1d is not None else "—",
            })
        st.dataframe(pd.DataFrame(slice_rows), use_container_width=True, hide_index=True)

    render_watchlist_success_panel(days=7, market="india")
    if st.button("Score watchlist now", key="tr_score_pins"):
        with st.spinner("Scoring session OHLC…"):
            scored = score_pinned_plans(market="india")
        st.success(f"Scored **{len(scored)}** pick(s).")
        st.rerun()

    st.subheader("Recent validated suggestions")
    if report.recent_validated:
        rows = []
        for r in report.recent_validated:
            result = "—"
            if r.outcome_correct == 1:
                result = "✓ Hit"
            elif r.outcome_correct == 0:
                result = "✗ Miss"
            rows.append({
                "Date": r.signal_date,
                "Symbol": r.symbol,
                "Source": r.source,
                "Horizon": r.horizon,
                "Action": r.action,
                "Score": f"{r.score:+.0f}" if r.score is not None else "—",
                "1D %": f"{r.outcome_return_1d:+.2f}" if r.outcome_return_1d is not None else "—",
                "Result": result,
                "Note": (r.outcome_note or "")[:80],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.caption(
            "No validated suggestions yet. Run **Market Pulse** (refresh scan) and "
            "**Daily Advisor** (generate briefing) today; validate tomorrow after close."
        )

    with st.expander("All logged suggestions (latest 100)"):
        all_rows = fetch_suggestions(limit=100)
        if all_rows:
            st.dataframe(
                pd.DataFrame([
                    {
                        "Date": r.signal_date,
                        "Symbol": r.symbol,
                        "Source": r.source,
                        "Horizon": r.horizon,
                        "Action": r.action,
                        "Price": f"₹{r.price_at_signal:,.2f}" if r.price_at_signal else "—",
                        "Validated": "Yes" if r.validated else "No",
                    }
                    for r in all_rows
                ]),
                use_container_width=True,
                hide_index=True,
            )

    st.caption(
        "EOD: `python scripts/validate_suggestions.py` (validates + tunes + Telegram scorecard). "
        "Journal: `data/suggestions/journal.db`"
    )
