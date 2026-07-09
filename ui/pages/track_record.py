"""Track Record — suggestion hit rate and learning."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.eod_learning import run_eod_learning_cycle
from analyzer.suggestion_journal import count_pending_validation, fetch_suggestions
from analyzer.suggestion_learning import build_learning_report
from analyzer.suggestions_export import build_suggestions_csv
from analyzer.telegram_notify import (
    send_telegram_broadcast,
    telegram_configured,
)
from analyzer.threshold_tuning import get_pulse_thresholds, recent_tuning_history, reset_thresholds
from analyzer.watchlist_eod import score_pinned_plans
from analyzer.whatsapp_export import mis_prep_whatsapp_url
from ui.components.watchlist_stats import (
    render_confidence_calibration_panel,
    render_hit_rate_dashboard,
    render_watchlist_success_panel,
)
from ui.components.trade_journal import render_trade_journal_panel


def _render_journal_validation_panel() -> None:
    """Pulse/Advisor journal — prominent validation UX."""
    pending = count_pending_validation()
    report = build_learning_report()

    st.markdown("### Pulse & Advisor journal")
    st.caption("Swing/long direction picks — validate against next-day moves.")

    if pending > 0:
        st.warning(f"**{pending}** picks waiting for validation — score after market close.")
    else:
        st.success("Journal up to date — no pending validations.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Logged", report.total_suggestions)
    c2.metric("Validated", report.validated_count)
    c3.metric("Pending", pending)
    c4.metric("Direction win %", f"{report.overall_win_rate_pct:.1f}%")

    if st.button("Validate journal now", type="primary", key="validate_suggestions"):
        with st.spinner("Scoring direction vs market moves…"):
            eod = run_eod_learning_cycle(send_telegram_alert=True)
        msg = f"Validated **{eod.validated}** journal rows."
        if eod.tuning and eod.tuning.changes:
            ch = eod.tuning.changes[0]
            msg += f" Gate: {ch.horizon} {ch.old_value}→{ch.new_value}."
        if getattr(eod, "errors", 0):
            st.warning(f"Validation completed with **{eod.errors}** error(s) — check logs.")
        st.success(msg)
        st.rerun()

    gates = get_pulse_thresholds()
    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Intraday min", gates["intraday"])
    g2.metric("Swing min", gates["short"])
    g3.metric("Long min", gates["long"])
    if g4.button("Reset gates", key="reset_thresholds"):
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

    if report.insights:
        for insight in report.insights:
            st.markdown(f"- {insight}")

    if report.slices:
        slice_rows = []
        for s in report.slices:
            slice_rows.append({
                "Segment": s.label,
                "Logged": s.total,
                "Scored": s.scored,
                "Wins": s.wins,
                "Losses": s.losses,
                "Win %": f"{s.win_rate_pct:.1f}",
            })
        st.dataframe(pd.DataFrame(slice_rows), use_container_width=True, hide_index=True)

    if report.recent_validated:
        rows = []
        for r in report.recent_validated:
            result = "✓" if r.outcome_correct == 1 else ("✗" if r.outcome_correct == 0 else "—")
            rows.append({
                "Date": r.signal_date,
                "Symbol": r.symbol,
                "Source": r.source,
                "Action": r.action,
                "1D %": f"{r.outcome_return_1d:+.2f}" if r.outcome_return_1d is not None else "—",
                "Result": result,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_track_record() -> None:
    st.subheader("Track Record — did suggestions hit target?")
    st.markdown(
        "Every **Quick scan** saves top picks with Entry · Stop · Target. "
        "After market close, the app scores **Hit target?** vs the session high/low."
    )

    render_hit_rate_dashboard(market="india")
    st.divider()

    render_watchlist_success_panel(days=7, market="india")

    st.divider()
    render_confidence_calibration_panel(days=90)

    csv_data = build_suggestions_csv(days=30, market="india")
    if csv_data.strip().count("\n") > 0:
        st.download_button(
            "Export CSV — all suggestions + hit/miss (30 days)",
            data=csv_data,
            file_name="suggestions_30d.csv",
            mime="text/csv",
            key="tr_export_csv",
        )

    st.divider()
    render_trade_journal_panel()

    st.divider()
    _render_journal_validation_panel()

    if st.button("Score watchlist now", key="tr_score_pins"):
        with st.spinner("Scoring session OHLC…"):
            scored = score_pinned_plans(market="india")
        st.success(f"Scored **{len(scored)}** pick(s).")
        st.rerun()

    exp_cols = st.columns(2)
    with exp_cols[0]:
        if telegram_configured():
            if st.button("Send EOD hit summary to Telegram", key="tg_track_record"):
                from analyzer.mis_eod_summary import build_mis_eod_summary, format_mis_eod_telegram
                from analyzer.watchlist_history import session_target_date

                td = session_target_date()
                summary = build_mis_eod_summary(td)
                if summary and summary.equity_picks:
                    msg = format_mis_eod_telegram(summary)
                    ok, err = send_telegram_broadcast(msg, alert_type="eod")
                    if ok:
                        st.success("Hit summary sent.")
                    else:
                        st.error(err)
                else:
                    st.warning("No scored suggestions for today yet.")
    with exp_cols[1]:
        from analyzer.mis_eod_summary import build_mis_eod_summary, format_mis_eod_telegram
        from analyzer.watchlist_history import session_target_date

        td = session_target_date()
        summary = build_mis_eod_summary(td)
        if summary and summary.equity_picks:
            wa_text = format_mis_eod_telegram(summary).replace("*", "")
            from analyzer.whatsapp_export import whatsapp_share_url

            st.link_button("Share EOD summary on WhatsApp", whatsapp_share_url(wa_text))
        else:
            st.caption("EOD WhatsApp share available after scoring.")
