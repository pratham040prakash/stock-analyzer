"""Watchlist success stats UI (last 7+ days)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from analyzer.watchlist_eod import outcome_label
from analyzer.watchlist_profit import (
    equity_target_profit_one_share,
    format_expected_profit,
    options_target_profit_one_lot,
)
from analyzer.watchlist_history import (
    MIN_RETENTION_DAYS,
    build_recent_suggested_picks,
    build_selected_trades_success_report,
    build_session_watchlist_rows,
    build_watchlist_success_report,
    can_score_trade_date,
    maybe_score_session_watchlist,
    session_target_date,
    success_summary_line,
    todays_track_record_date,
)
from analyzer.watchlist_learning import (
    build_watchlist_learning_report,
    get_watchlist_strategy,
    recent_strategy_history,
    reset_watchlist_strategy,
    run_watchlist_learning_cycle,
)
from analyzer.options_watchlist_history import (
    build_options_success_report,
    build_recent_options_picks,
    build_options_session_rows,
    maybe_score_options_watchlist,
    score_options_daily_watchlist,
    todays_options_track_date,
)
from analyzer.options_watchlist_learning import (
    build_options_learning_report,
    get_options_premium_strategy,
    reset_options_strategy,
    run_options_learning_cycle,
)
from ui.components.intraday_journal import render_todays_trade_journal


def _target_hit_label(outcome: str, *, scored: bool) -> str:
    if not scored or outcome == "pending":
        return "⏳ Pending"
    if outcome == "target_hit":
        return "✅ Yes"
    if outcome in ("stop_hit", "mixed"):
        return "❌ No"
    if outcome in ("flat", "flat_positive"):
        return "➖ No"
    return "—"


def _suggested_pick_row_dict(trade_date: str, r) -> dict:
    return {
        "Date": trade_date,
        "Rank": r.rank,
        "Stock": r.symbol,
        "Entry": f"₹{r.entry:,.2f}",
        "Stop": f"₹{r.stop_loss:,.2f}",
        "Target": f"₹{r.target:,.2f}",
        "Exp. profit (1 sh)": format_expected_profit(
            equity_target_profit_one_share(r.entry, r.target)
        ),
        "Day high": f"₹{r.session_high:,.2f}" if r.session_high else "—",
        "Day low": f"₹{r.session_low:,.2f}" if r.session_low else "—",
        "Hit target?": _target_hit_label(r.outcome, scored=r.scored),
        "Result": outcome_label(r.outcome) if r.scored else "⏳ Pending",
    }


def render_all_suggested_picks_table(
    *,
    days: int = 7,
    market: str = "india",
    title: str | None = None,
) -> int:
    """Table of every suggested stock and whether it hit target."""
    days = max(days, MIN_RETENTION_DAYS)
    picks = build_recent_suggested_picks(days, market=market)
    heading = title or f"All suggested picks (last {days} days)"
    st.markdown(f"##### {heading}")

    if not picks:
        st.info(
            "No watchlist snapshots yet. Run **Quick scan** on Intraday tonight — "
            "top **5** picks are saved automatically."
        )
        return 0

    targets = sum(1 for _, r in picks if r.outcome == "target_hit")
    stops = sum(1 for _, r in picks if r.outcome in ("stop_hit", "mixed"))
    pending = sum(1 for _, r in picks if not r.scored)
    st.caption(
        f"**{len(picks)}** suggestions · **{targets}** hit target · "
        f"**{stops}** hit stop · **{pending}** pending"
    )

    table = [_suggested_pick_row_dict(d, r) for d, r in picks]
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
    return len(picks)


def _options_pick_row_dict(trade_date: str, r) -> dict:
    contract = f"{r.fno_symbol} {r.option_type} {r.strike:g}"
    return {
        "Date": trade_date,
        "Rank": r.rank,
        "Contract": contract,
        "Expiry": r.expiry,
        "Entry (prem)": f"₹{r.entry:,.2f}",
        "Stop (prem)": f"₹{r.stop_loss:,.2f}",
        "Target (prem)": f"₹{r.target:,.2f}",
        "Exp. profit (1 lot)": format_expected_profit(
            options_target_profit_one_lot(r.entry, r.target, r.lot_size)
        ),
        "Prem high": f"₹{r.session_high:,.2f}" if r.session_high else "—",
        "Prem low": f"₹{r.session_low:,.2f}" if r.session_low else "—",
        "Hit target?": _target_hit_label(r.outcome, scored=r.scored),
        "Result": outcome_label(r.outcome) if r.scored else "⏳ Pending",
    }


def render_all_options_picks_table(*, days: int = 7) -> int:
    """All saved CE/PE picks and premium target outcomes."""
    days = max(days, MIN_RETENTION_DAYS)
    picks = build_recent_options_picks(days)
    st.markdown(f"##### Options CE/PE track record (last {days} days)")
    st.caption(
        "Scores **premium** high/low vs stop/target. **Kite** first, then **NSE** historical."
    )

    if not picks:
        st.info(
            "No options snapshots yet. Open **Options expiry watchlist** above — "
            "picks save automatically when CE/PE loads."
        )
        return 0

    targets = sum(1 for _, r in picks if r.outcome == "target_hit")
    stops = sum(1 for _, r in picks if r.outcome in ("stop_hit", "mixed"))
    pending = sum(1 for _, r in picks if not r.scored)
    st.caption(
        f"**{len(picks)}** contracts · **{targets}** hit target · "
        f"**{stops}** hit stop · **{pending}** pending"
    )

    table = [_options_pick_row_dict(d, r) for d, r in picks]
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
    return len(picks)


def render_todays_options_track_record() -> str | None:
    trade_date = todays_options_track_date()
    if not trade_date:
        st.markdown("##### 📅 Today's options track record")
        st.caption("No scored options session yet.")
        return None

    maybe_score_options_watchlist(trade_date=trade_date)
    _, rows = build_options_session_rows(trade_date)

    st.markdown(f"##### 📅 Today's options track record ({trade_date})")
    if not rows:
        st.caption("Fetch **CE/PE** in options watchlist to save tonight's contracts.")
        return trade_date

    scored = [r for r in rows if r.scored]
    targets = sum(1 for r in scored if r.outcome == "target_hit")
    stops = sum(1 for r in scored if r.outcome in ("stop_hit", "mixed"))
    wr = (100.0 * targets / (targets + stops)) if (targets + stops) else None
    c1, c2, c3 = st.columns(3)
    c1.metric("Premium targets hit", targets)
    c2.metric("Premium stops hit", stops)
    c3.metric("Win rate", f"{wr:.0f}%" if wr is not None else "—")

    table = []
    for r in rows:
        row = _options_pick_row_dict(trade_date, r)
        row.pop("Date", None)
        table.append(row)
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
    return trade_date


def render_todays_track_record(*, market: str = "india") -> str | None:
    """Today's (or latest scored) watchlist results — targets vs stops."""
    trade_date = todays_track_record_date()
    if not trade_date:
        st.markdown("##### 📊 Today's track record")
        st.info("No scored session yet. After market close, tap **Score watchlist** below.")
        return None

    maybe_score_session_watchlist(trade_date=trade_date, market=market)
    _, rows = build_session_watchlist_rows(trade_date)

    st.markdown(f"##### 📊 Today's track record ({trade_date})")
    if not rows:
        st.caption("No picks saved for this session yet — run **Quick scan**.")
        return trade_date

    scored = [r for r in rows if r.scored]
    if not scored and not can_score_trade_date(trade_date):
        st.caption("Session not scored yet — available after **3:30 PM IST**.")

    targets = sum(1 for r in scored if r.outcome == "target_hit")
    stops = sum(1 for r in scored if r.outcome in ("stop_hit", "mixed"))
    wr = (100.0 * targets / (targets + stops)) if (targets + stops) else None
    wr_s = f"{wr:.0f}%" if wr is not None else "—"
    c1, c2, c3 = st.columns(3)
    c1.metric("Targets hit", targets)
    c2.metric("Stops hit", stops)
    c3.metric("Win rate", wr_s)

    table = [_suggested_pick_row_dict(trade_date, r) for r in rows]
    # Drop Date column — same session
    for row in table:
        row.pop("Date", None)
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
    return trade_date


def render_selected_vs_all_banner(*, days: int = 7) -> None:
    """Compare win rate for your 2 starred picks vs full top-5."""
    days = max(days, MIN_RETENTION_DAYS)
    all_report = build_watchlist_success_report(days)
    sel_report = build_selected_trades_success_report(days)
    if all_report.total_picks == 0:
        return
    all_wr = (
        f"{all_report.win_rate_pct:.0f}%"
        if all_report.win_rate_pct is not None
        else "—"
    )
    if sel_report.scored_picks == 0:
        st.caption(
            f"**Your 2 vs top 5 ({days}d):** all **{all_wr}** "
            f"({all_report.scored_picks} picks) · _star 2 each night for split stats_"
        )
        return
    sel_wr = (
        f"{sel_report.win_rate_pct:.0f}%"
        if sel_report.win_rate_pct is not None
        else "—"
    )
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Your 2 — win % ({days}d)", sel_wr)
    c2.metric(f"Top 5 — win % ({days}d)", all_wr)
    c3.metric("Your 2 scored", sel_report.scored_picks)
    st.caption(
        f"Learning uses all top 5; **your 2** is what you actually traded "
        f"({sel_report.target_hits} targets · {sel_report.stop_hits} stops)."
    )


def render_hit_rate_dashboard(*, market: str = "india") -> int | None:
    """30 / 90 / 180-day win-rate summary for Suggestions home."""
    st.markdown("#### Hit rate dashboard")
    cols = st.columns(3)
    best_days = None
    best_wr = -1.0
    for col, days in zip(cols, (30, 90, 180)):
        days = max(days, MIN_RETENTION_DAYS)
        report = build_watchlist_success_report(days)
        with col:
            if report.scored_picks == 0:
                col.metric(f"{days}d win rate", "—")
                col.caption("No scored picks yet")
                continue
            wr = report.win_rate_pct
            wr_s = f"{wr:.0f}%" if wr is not None else "—"
            col.metric(f"{days}d win rate", wr_s)
            col.caption(
                f"{report.target_hits}T · {report.stop_hits}S · {report.scored_picks} scored"
            )
            if wr is not None and wr > best_wr:
                best_wr = wr
                best_days = days
    if best_days:
        st.caption(f"Best window in retention: **{best_days}d** at **{best_wr:.0f}%**")
    return best_days


def render_confidence_calibration_panel(*, days: int = 90) -> None:
    """Confidence % buckets vs actual target-hit rate."""
    from analyzer.confidence_calibration import build_confidence_calibration

    st.markdown("##### Confidence vs actual hit rate")
    st.caption(
        "Backtests the **Conf.** column on watchlist picks against EOD target/stop outcomes."
    )
    buckets = build_confidence_calibration(days=days)
    if not any(b.picks for b in buckets):
        st.info("Need more scored picks with saved confidence — run Quick scan after update.")
        return
    rows = []
    for b in buckets:
        if b.picks == 0:
            continue
        rows.append({
            "Confidence bucket": b.label,
            "Picks": b.picks,
            "Targets": b.targets,
            "Stops": b.stops,
            "Actual hit %": f"{b.actual_hit_pct:.0f}" if b.actual_hit_pct is not None else "—",
            "Avg conf.": f"{b.avg_confidence:.0f}%" if b.avg_confidence is not None else "—",
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_watchlist_success_banner(*, days: int = 7) -> None:
    days = max(days, MIN_RETENTION_DAYS)
    report = build_watchlist_success_report(days)
    if report.total_picks == 0:
        st.caption(
            "📊 **Weekly track record** — builds after **Quick scan** and **Score watchlist**."
        )
        return

    wr = f"{report.win_rate_pct:.0f}%" if report.win_rate_pct is not None else "—"
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Win rate ({days}d)", wr)
    c2.metric("Targets hit", report.target_hits)
    c3.metric("Stops hit", report.stop_hits)
    c4.metric("Picks scored", report.scored_picks)
    st.caption(success_summary_line(days))


def render_session_watchlist_results(
    *,
    trade_date: str | None = None,
    market: str = "india",
    auto_score: bool = True,
    title: str | None = None,
) -> str | None:
    """All snapshot picks for a session with target/stop outcome."""
    trade_date = trade_date or session_target_date()
    if auto_score:
        maybe_score_session_watchlist(trade_date=trade_date, market=market)

    _, rows = build_session_watchlist_rows(trade_date)
    if not rows:
        return trade_date

    pending = sum(1 for r in rows if not r.scored)
    scored = len(rows) - pending
    targets = sum(1 for r in rows if r.outcome == "target_hit")
    stops = sum(1 for r in rows if r.outcome == "stop_hit")

    heading = title or f"Watchlist results — **{len(rows)} picks** ({trade_date})"
    st.markdown(f"##### {heading}")
    if pending == len(rows) and not can_score_trade_date(trade_date):
        st.info(
            f"Session **{trade_date}** has not closed yet — results appear after "
            "**3:30 PM IST** when you tap **Score watchlist**."
        )
    elif scored:
        st.caption(
            f"**{targets}** hit target · **{stops}** hit stop · "
            f"**{scored}/{len(rows)}** scored vs session high/low."
        )

    table = []
    for r in rows:
        row = _suggested_pick_row_dict(trade_date, r)
        row.pop("Date", None)
        if r.scored:
            row["Close"] = f"₹{r.session_close:,.2f}" if r.session_close else "—"
        else:
            row["Close"] = "—"
        table.append(row)
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
    return trade_date


def render_learning_honesty_banner() -> None:
    st.info(
        "**Learning improves your gates over time — it does not guarantee 100% wins.** "
        "Use stops, max 2 trades/day, and square off by 3:20 PM."
    )


def render_options_learning_panel() -> None:
    st.markdown("##### 🧠 Options premium strategy (★ side)")
    st.caption(
        "Stop/target multipliers tune from scored **recommended** CE/PE outcomes."
    )
    strat = get_options_premium_strategy()
    c1, c2, c3 = st.columns(3)
    c1.metric("Stop mult", f"{strat['stop_mult']:.2f}")
    c2.metric("Target mult", f"{strat['target_mult']:.2f}")
    c3.metric("★ only", "Yes" if strat.get("prefer_recommended_only") else "No")

    report = build_options_learning_report()
    for line in report.insights:
        st.markdown(f"- {line}")

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Run options learning", key="opt_learn_now"):
            with st.spinner("Tuning options premium gates…"):
                result = run_options_learning_cycle()
            if result.changes:
                st.success(f"Updated **{len(result.changes)}** option gate(s).")
            else:
                st.info("No option gate changes (need more ★ scored picks).")
            st.rerun()
    with b2:
        if st.button("Reset options defaults", key="opt_reset_strategy"):
            reset_options_strategy()
            st.success("Options strategy reset.")
            st.rerun()


def render_watchlist_learning_panel() -> None:
    """Auto-tuned gates from target-hit history."""
    render_learning_honesty_banner()
    st.markdown("##### 🧠 Learned equity strategy (updates daily after close)")
    st.caption(
        "Screening rules tighten when stops dominate and relax when targets hit."
    )
    gates = get_watchlist_strategy()
    g1, g2, g3, g4, g5 = st.columns(5)
    g1.metric("Min ATR%", f"{gates['min_atr_pct']:.1f}")
    g2.metric("Checklist", f"{gates['min_checklist_passed']}/5")
    g3.metric("Min score", f"{gates['min_prep_score']:.0f}")
    g4.metric("Max picks", gates["max_watchlist"])
    g5.metric("RSI+MACD", "Yes" if gates["require_rsi_macd"] else "No")

    weights = gates.get("feature_weights") or {}
    baseline = gates.get("baseline_hit_rate")
    if weights:
        st.caption(
            f"**Suggestion intelligence** · baseline hit **{float(baseline or 0.52) * 100:.0f}%** "
            f"· research v{gates.get('research_version', 0)} "
            f"({gates.get('research_samples', 0)} setups)"
        )
        wcols = st.columns(min(len(weights), 5))
        for i, (k, v) in enumerate(sorted(weights.items(), key=lambda x: -x[1])[:5]):
            wcols[i % len(wcols)].caption(f"{k}: **{float(v):.0%}**")

    learn = build_watchlist_learning_report()
    for line in learn.insights:
        st.markdown(f"- {line}")

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Run learning now", key="wl_learn_now"):
            with st.spinner("Scoring + tuning from target hits…"):
                result = run_watchlist_learning_cycle(market="india")
            if result.changes:
                st.success(f"Updated **{len(result.changes)}** gate(s).")
            else:
                st.info("No gate changes (need more scored picks or win rate OK).")
            st.rerun()
    with b2:
        if st.button("6mo pattern research", key="wl_strategy_research"):
            with st.spinner("Mining Nifty 50 patterns (6 months)…"):
                from analyzer.strategy_research import run_strategy_research

                report = run_strategy_research(period="6mo", market="india", apply=True)
            if report.applied:
                st.success(
                    f"Updated weights from **{report.samples}** setups "
                    f"({report.win_rate_pct:.0f}% simulated hit rate)."
                )
            else:
                st.info(report.insights[0] if report.insights else "Research complete.")
            for line in report.insights[1:4]:
                st.caption(line)
            st.rerun()
    with b3:
        if st.button("Reset strategy defaults", key="wl_reset_strategy"):
            reset_watchlist_strategy()
            st.success("Watchlist gates reset.")
            st.rerun()


def render_watchlist_success_panel(
    *,
    days: int = 7,
    market: str = "india",
) -> None:
    """Full watchlist track record for the Track Record tab."""
    days = max(days, MIN_RETENTION_DAYS)
    st.subheader("Intraday watchlist track record")
    st.caption(
        f"Top **5** auto-picks per session · scored vs day high/low after close · "
        f"last **{days}** days kept."
    )

    render_todays_track_record(market=market)
    st.divider()

    report = build_watchlist_success_report(days)
    if report.total_picks == 0:
        st.info(
            "No scored watchlist days yet. Run **Quick scan** on **Intraday**, then "
            "**Score watchlist** after market close."
        )
    else:
        render_watchlist_success_banner(days=days)
        render_selected_vs_all_banner(days=days)
        if report.daily:
            st.markdown("##### Daily breakdown")
            daily_rows = []
            for d in report.daily:
                wr = f"{d.success_pct:.0f}%" if d.success_pct is not None else "—"
                daily_rows.append({
                    "Date": d.trade_date,
                    "Picks": d.pick_count,
                    "Scored": d.scored_count,
                    "Targets": d.target_hits,
                    "Stops": d.stop_hits,
                    "Win %": wr,
                })
            st.dataframe(pd.DataFrame(daily_rows), use_container_width=True, hide_index=True)

    st.divider()
    render_all_suggested_picks_table(days=days, market=market)

    st.divider()
    render_todays_options_track_record()
    render_all_options_picks_table(days=days)

    st.divider()
    render_session_watchlist_results(
        market=market,
        auto_score=True,
        title="Latest session detail",
    )

    st.divider()
    render_watchlist_learning_panel()

    st.divider()
    render_options_learning_panel()

    history = recent_strategy_history(5)
    if history:
        st.caption(
            "Recent gate tuning: "
            + " · ".join(
                f"{h.get('field', '?')} {h.get('old', '?')}→{h.get('new', '?')}"
                for h in history
            )
        )


def render_intraday_track_record(
    *,
    days: int = 7,
    market: str = "india",
    max_trades: int = 3,
) -> None:
    """Intraday tab — weekly stats, learning, trade log."""
    st.markdown("#### 📊 Intraday track record")
    st.caption(
        f"Weekly stats · auto-learning · trade journal · "
        f"last **{max(days, MIN_RETENTION_DAYS)}** days kept."
    )

    render_learning_honesty_banner()

    render_selected_vs_all_banner(days=days)

    _, c2 = st.columns([3, 1])
    with c2:
        if st.button("Score watchlist", key="intra_tr_score", use_container_width=True):
            with st.spinner("Scoring equity + options outcomes…"):
                result = run_watchlist_learning_cycle(market=market)
                try:
                    score_options_daily_watchlist(trade_date=session_target_date())
                except Exception:
                    pass
            if result.changes:
                st.success(
                    f"Tuned **{len(result.changes)}** gate(s) · "
                    f"win rate **{result.win_rate_pct:.0f}%**"
                    if result.win_rate_pct is not None
                    else f"Tuned **{len(result.changes)}** gate(s)."
                )
            elif result.samples > 0:
                st.info("Scored — no gate changes needed yet.")
            else:
                td = session_target_date()
                if not can_score_trade_date(td):
                    st.info(f"Session **{td}** not finished yet — score after market close.")
                else:
                    st.info("Already scored or no snapshot data.")
            st.rerun()

    report = build_watchlist_success_report(days)
    if report.total_picks > 0:
        render_watchlist_success_banner(days=days)

    render_todays_track_record(market=market)
    render_todays_options_track_record()

    st.divider()
    render_all_suggested_picks_table(days=days, market=market)

    opt_report = build_options_success_report(days)
    if opt_report.scored_picks > 0:
        wr = (
            f"{opt_report.win_rate_pct:.0f}%"
            if opt_report.win_rate_pct is not None
            else "—"
        )
        st.caption(
            f"Options ({days}d): **{opt_report.target_hits}** premium targets · "
            f"**{opt_report.stop_hits}** stops · win rate **{wr}**"
        )

    st.divider()
    render_all_options_picks_table(days=days)

    st.divider()
    render_watchlist_learning_panel()

    st.divider()
    render_options_learning_panel()

    st.markdown("##### Today's trades")
    render_todays_trade_journal(max_trades=max_trades)