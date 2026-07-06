"""Concise Telegram: morning pick list + EOD hit summary (no MIS ladder noise)."""

from __future__ import annotations

from analyzer.watchlist_eod import outcome_label
from analyzer.watchlist_pins import PinnedPlan
from analyzer.watchlist_history import (
    build_session_watchlist_rows,
    build_watchlist_success_report,
    maybe_score_session_watchlist,
    session_target_date,
)
from analyzer.trade_selection import load_selected_symbols


def _outcome_icon(outcome: str) -> str:
    if outcome == "target_hit":
        return "✅"
    if outcome in ("stop_hit", "mixed"):
        return "❌"
    if outcome in ("flat", "flat_positive"):
        return "➖"
    return "⏳"


def format_equity_pick_line_compact(plan: PinnedPlan, rank: int) -> str:
    return (
        f"#{rank} *{plan.symbol}* · Entry ₹{plan.entry:,.0f} · "
        f"Stop ₹{plan.stop_loss:,.0f} · Target ₹{plan.target:,.0f}"
    )


def format_nightly_suggestions_telegram(
    equity_plans: list[PinnedPlan],
    *,
    market_bias: str = "",
    prep_date: str = "",
) -> str:
    """After Quick scan — tomorrow's top 5 (entry/stop/target only)."""
    trade_date = session_target_date()
    lines = [f"*🌙 Suggestions for {trade_date}*"]
    if market_bias:
        lines.append(f"Bias: *{market_bias}*")
    lines.append("_Star your top 2 in the app before market open._")
    lines.append("")
    if equity_plans:
        for i, p in enumerate(equity_plans, start=1):
            lines.append(format_equity_pick_line_compact(p, i))
    else:
        lines.append("_No picks — run Quick scan in the app._")
    if prep_date:
        lines.append("")
        lines.append(f"_Saved {prep_date} · Not financial advice._")
    return "\n".join(lines)


def format_morning_suggestions_telegram(
    equity_plans: list[PinnedPlan] | None = None,
    *,
    trade_date: str | None = None,
) -> str:
    """Pre-open list from last night's snapshot."""
    trade_date = trade_date or session_target_date()
    if equity_plans is None:
        maybe_score_session_watchlist(trade_date=trade_date, market="india")
        _, rows = build_session_watchlist_rows(trade_date)
        equity_plans = [
            PinnedPlan(
                symbol=r.symbol,
                entry=r.entry,
                stop_loss=r.stop_loss,
                target=r.target,
                prep_date=trade_date,
            )
            for r in rows
        ]

    selected = load_selected_symbols(trade_date)
    lines = [f"*☀️ Today's picks — {trade_date}*"]
    if selected:
        lines.append(f"_Your 2:_ **{', '.join(selected)}**")
    else:
        lines.append("_Star 2 names in the app (or trade top 2 by rank)._")
    lines.append("")
    if equity_plans:
        for i, p in enumerate(equity_plans, start=1):
            star = "⭐ " if selected and p.symbol.upper() in {s.upper() for s in selected} else ""
            lines.append(
                f"{star}#{i} *{p.symbol}* · "
                f"₹{p.entry:,.0f} → target ₹{p.target:,.0f} · stop ₹{p.stop_loss:,.0f}"
            )
    else:
        lines.append("_No list yet — run Quick scan tonight on Suggestions._")
    lines.append("")
    lines.append("_Not financial advice._")
    return "\n".join(lines)


def format_eod_hit_summary_telegram(
    trade_date: str,
    *,
    equity_rows: list | None = None,
    include_weekly: bool = True,
    days: int = 7,
) -> str:
    """After close — did targets hit? Compare your 2 vs full top 5."""
    if equity_rows is None:
        maybe_score_session_watchlist(trade_date=trade_date, market="india")
        _, equity_rows = build_session_watchlist_rows(trade_date)

    selected = {s.upper() for s in load_selected_symbols(trade_date)}
    scored = [r for r in equity_rows if r.scored]
    targets = sum(1 for r in scored if r.outcome == "target_hit")
    decided = sum(1 for r in scored if r.outcome in ("target_hit", "stop_hit", "mixed"))
    wr = f"{100.0 * targets / decided:.0f}%" if decided else "—"

    lines = [f"*📊 Did targets hit? — {trade_date}*"]
    lines.append(f"*Top {len(equity_rows)}:* {targets}/{decided or len(scored)} hit · win **{wr}**")
    for r in equity_rows:
        if not r.scored:
            lines.append(f"⏳ {r.symbol} — pending")
            continue
        icon = _outcome_icon(r.outcome)
        lines.append(f"{icon} {r.symbol} — {outcome_label(r.outcome)}")

    if selected:
        sel_rows = [r for r in equity_rows if r.symbol.upper() in selected]
        sel_scored = [r for r in sel_rows if r.scored]
        sel_t = sum(1 for r in sel_scored if r.outcome == "target_hit")
        sel_d = sum(
            1 for r in sel_scored if r.outcome in ("target_hit", "stop_hit", "mixed")
        )
        sel_wr = f"{100.0 * sel_t / sel_d:.0f}%" if sel_d else "—"
        lines.append("")
        lines.append(f"*Your 2:* {sel_t}/{sel_d or len(sel_scored)} hit · win **{sel_wr}**")
        for r in sel_rows:
            if not r.scored:
                continue
            lines.append(f"{_outcome_icon(r.outcome)} {r.symbol}")

    if include_weekly:
        week = build_watchlist_success_report(days)
        if week.scored_picks:
            wwr = (
                f"{week.win_rate_pct:.0f}%"
                if week.win_rate_pct is not None
                else "—"
            )
            lines.append("")
            lines.append(
                f"_This week ({days}d): {week.scored_picks} suggestions, "
                f"{week.target_hits} hit target ({wwr})_"
            )

    lines.append("")
    lines.append("_Not financial advice._")
    return "\n".join(lines)
