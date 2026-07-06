"""End-of-day MIS watchlist Telegram summary (equity + options outcomes)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.market_session import market_session_status
from analyzer.nse_holidays import is_nse_trading_day, skip_scheduled_job_reason
from analyzer.watchlist_eod import outcome_label

IST = ZoneInfo("Asia/Kolkata")
STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "mis_eod_summary.json"

EOD_WINDOW = (15, 35, 20, 0)  # after score window, before late night


@dataclass
class MisEodSummary:
    trade_date: str
    equity_picks: int = 0
    equity_targets: int = 0
    equity_stops: int = 0
    equity_pending: int = 0
    equity_win_rate_pct: float | None = None
    options_picks: int = 0
    options_targets: int = 0
    options_stops: int = 0
    options_pending: int = 0
    options_win_rate_pct: float | None = None
    equity_rows: list = field(default_factory=list)
    options_rows: list = field(default_factory=list)
    gate_changes: list[str] = field(default_factory=list)


def _ensure_dir() -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_state() -> dict:
    _ensure_dir()
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(data: dict) -> None:
    _ensure_dir()
    STATE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def mis_eod_trade_date(now: datetime | None = None) -> str | None:
    """Calendar session date for EOD summary (NSE trading days only)."""
    now = now or datetime.now(IST)
    if not is_nse_trading_day(now.date()):
        return None
    return now.strftime("%Y-%m-%d")


def was_eod_summary_sent(trade_date: str) -> bool:
    return bool(_load_state().get(trade_date, {}).get("sent"))


def mark_eod_summary_sent(trade_date: str) -> None:
    data = _load_state()
    data[trade_date] = {
        "sent": True,
        "at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
    }
    _save_state(data)


def _in_window(now: datetime, start_h: int, start_m: int, end_h: int, end_m: int) -> bool:
    start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = now.replace(hour=end_h, minute=end_m, second=59, microsecond=0)
    return start <= now <= end


def build_mis_eod_summary(
    trade_date: str | None = None,
    *,
    gate_changes: list[str] | None = None,
) -> MisEodSummary | None:
    trade_date = trade_date or mis_eod_trade_date()
    if not trade_date:
        return None

    from analyzer.options_watchlist_history import (
        build_options_session_rows,
        maybe_score_options_watchlist,
    )
    from analyzer.watchlist_history import (
        build_session_watchlist_rows,
        maybe_score_session_watchlist,
    )

    maybe_score_session_watchlist(trade_date=trade_date, market="india")
    maybe_score_options_watchlist(trade_date=trade_date)

    _, eq_rows = build_session_watchlist_rows(trade_date)
    _, opt_rows = build_options_session_rows(trade_date)

    from analyzer.trade_selection import load_selected_symbols

    selected = load_selected_symbols(trade_date)
    if selected:
        sel = {s.upper() for s in selected}
        eq_rows = [r for r in eq_rows if r.symbol.upper() in sel]

    from analyzer.options_trade_selection import load_selected_option, snap_matches_pick
    from analyzer.options_watchlist_history import fetch_options_snapshots_for_date

    selected_opt = load_selected_option(trade_date)
    if selected_opt:
        opt_star = [
            r for r in opt_rows
            if snap_matches_pick(r, selected_opt)
        ]
    else:
        rec_keys = {
            (s.fno_symbol, s.option_type, s.strike)
            for s in fetch_options_snapshots_for_date(trade_date)
            if s.recommended
        }
        opt_star = [r for r in opt_rows if (r.fno_symbol, r.option_type, r.strike) in rec_keys]
    if not opt_star and not selected_opt:
        opt_star = opt_rows

    eq_scored = [r for r in eq_rows if r.scored]
    eq_targets = sum(1 for r in eq_scored if r.outcome == "target_hit")
    eq_stops = sum(1 for r in eq_scored if r.outcome in ("stop_hit", "mixed"))
    eq_pending = sum(1 for r in eq_rows if not r.scored)
    eq_decided = eq_targets + eq_stops

    opt_scored = [r for r in opt_star if r.scored]
    opt_targets = sum(1 for r in opt_scored if r.outcome == "target_hit")
    opt_stops = sum(1 for r in opt_scored if r.outcome in ("stop_hit", "mixed"))
    opt_pending = sum(1 for r in opt_star if not r.scored)
    opt_decided = opt_targets + opt_stops

    return MisEodSummary(
        trade_date=trade_date,
        equity_picks=len(eq_rows),
        equity_targets=eq_targets,
        equity_stops=eq_stops,
        equity_pending=eq_pending,
        equity_win_rate_pct=(100.0 * eq_targets / eq_decided) if eq_decided else None,
        options_picks=len(opt_star),
        options_targets=opt_targets,
        options_stops=opt_stops,
        options_pending=opt_pending,
        options_win_rate_pct=(100.0 * opt_targets / opt_decided) if opt_decided else None,
        equity_rows=eq_rows,
        options_rows=opt_star,
        gate_changes=gate_changes or [],
    )


def format_mis_eod_telegram(summary: MisEodSummary) -> str:
    lines = [f"*📊 MIS EOD — {summary.trade_date}*"]

    if summary.equity_picks:
        wr = (
            f"{summary.equity_win_rate_pct:.0f}%"
            if summary.equity_win_rate_pct is not None
            else "—"
        )
        lines.append(
            f"*Equity:* {summary.equity_targets}/{summary.equity_picks} hit target · "
            f"{summary.equity_stops} stops · win **{wr}**"
        )
        for r in summary.equity_rows[:5]:
            if not r.scored:
                continue
            icon = "✅" if r.outcome == "target_hit" else "❌" if r.outcome in ("stop_hit", "mixed") else "➖"
            lines.append(f"{icon} {r.symbol}")
    else:
        lines.append("_No equity watchlist for this session._")

    lines.append("")
    if summary.options_picks:
        wr = (
            f"{summary.options_win_rate_pct:.0f}%"
            if summary.options_win_rate_pct is not None
            else "—"
        )
        lines.append(
            f"*Options ★:* {summary.options_targets}/{summary.options_picks} premium targets · "
            f"{summary.options_stops} stops · win **{wr}**"
        )
        for r in summary.options_rows:
            if not r.scored:
                continue
            icon = "✅" if r.outcome == "target_hit" else "❌" if r.outcome in ("stop_hit", "mixed") else "➖"
            lines.append(f"{icon} {r.fno_symbol} {r.option_type} {r.strike:g}")
    else:
        lines.append("_No options picks scored._")

    if summary.gate_changes:
        lines.append("")
        lines.append(f"_Gates tuned:_ {', '.join(summary.gate_changes[:3])}")

    lines.append("")
    lines.append("_Log trades in app · Not financial advice._")
    return "\n".join(lines)


def run_mis_eod_summary(
    *,
    trade_date: str | None = None,
    send_telegram: bool = True,
    force: bool = False,
) -> tuple[MisEodSummary | None, bool, str]:
    """
    Build summary, optionally send Telegram once per trade_date.
    Returns (summary, sent_ok, status).
    """
    from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured

    trade_date = trade_date or mis_eod_trade_date()
    if not trade_date:
        return None, False, "Weekend — no EOD summary"

    if not force and was_eod_summary_sent(trade_date):
        return None, False, f"EOD summary already sent for {trade_date}"

    from analyzer.watchlist_learning import run_watchlist_learning_cycle

    learn = run_watchlist_learning_cycle(market="india")
    gate_changes = [f"{c.field} {c.old_value}→{c.new_value}" for c in learn.changes]

    summary = build_mis_eod_summary(trade_date, gate_changes=gate_changes)
    if not summary:
        return None, False, "Could not build summary"

    if not summary.equity_picks and not summary.options_picks:
        return summary, False, "No watchlist data to summarize"

    if not send_telegram:
        return summary, False, "Telegram skipped"

    if not telegram_configured():
        return summary, False, "Telegram not configured"

    ok, err = send_telegram_broadcast(
        format_mis_eod_telegram(summary),
        alert_type="eod",
    )
    if ok:
        mark_eod_summary_sent(trade_date)
        return summary, True, f"EOD summary sent for {trade_date}"
    return summary, False, err


def maybe_send_mis_eod_summary() -> None:
    """Called from app after learning — send once per session in EOD window."""
    from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured

    now = datetime.now(IST)
    if skip_scheduled_job_reason(now):
        return
    if market_session_status().get("is_open"):
        return
    if not _in_window(now, *EOD_WINDOW):
        return

    trade_date = mis_eod_trade_date()
    if not trade_date or was_eod_summary_sent(trade_date):
        return

    summary = build_mis_eod_summary(trade_date)
    if not summary or (not summary.equity_picks and not summary.options_picks):
        return
    if not telegram_configured():
        return

    ok, _ = send_telegram_broadcast(
        format_mis_eod_telegram(summary),
        alert_type="eod",
    )
    if ok:
        mark_eod_summary_sent(trade_date)
