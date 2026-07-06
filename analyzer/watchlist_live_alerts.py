"""Live Telegram alerts when starred picks hit entry / stop / T1/T2/T3 zones."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.market_session import market_session_status
from analyzer.nse_holidays import skip_scheduled_job_reason
from analyzer.nse_options import fetch_option_leg_ltp
from analyzer.options_watchlist_history import fetch_options_snapshots_for_date
from analyzer.providers import get_live_ltp
from analyzer.options_trade_selection import load_selected_option, snap_matches_pick
from analyzer.trade_selection import effective_trade_plans, load_selected_symbols
from analyzer.watchlist_history import session_target_date
from analyzer.watchlist_pins import infer_trade_side
from analyzer.trade_ladder import format_stop_trail_telegram
from analyzer.watchlist_plan_tracker import assess_live_plan, assess_options_live_plan

IST = ZoneInfo("Asia/Kolkata")
STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "watchlist_live_alerts.json"

ALERT_LABELS = {
    "Near entry": "entry_near",
    "At entry": "entry_at",
    "At/below stop": "stop_hit",
    "At/above stop": "stop_hit",
    "Near stop": "near_stop",
    "At/above target": "t1_hit",
    "Near target": "t1_near",
    "Near T1": "t1_near",
    "T1 hit — book 40%": "t1_hit",
    "Near T2": "t2_near",
    "T2 hit — trail to T3": "t2_hit",
    "Near T3": "t3_near",
    "T3 hit — exit rest": "t3_hit",
    "Below entry": "below_entry",
    "Above entry": "above_entry",
}


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


def _state_key(trade_date: str, symbol: str) -> str:
    return f"{trade_date}:{symbol}"


def _was_alert_sent(trade_date: str, symbol: str, kind: str) -> bool:
    return bool(_load_state().get(_state_key(trade_date, symbol), {}).get(kind))


def _mark_alert_sent(trade_date: str, symbol: str, kind: str) -> None:
    data = _load_state()
    key = _state_key(trade_date, symbol)
    sym = data.setdefault(key, {})
    sym[kind] = datetime.now(IST).strftime("%H:%M IST")
    _save_state(data)


def format_live_alert(status, *, plan, ladder_line: str = "") -> str:
    trade_side = infer_trade_side(plan.entry, plan.stop_loss, explicit=getattr(plan, "side", None))
    extra = ""
    if status.target2 and status.target3:
        extra = (
            f"\nT1 ₹{plan.target:,.0f} · T2 ₹{status.target2:,.0f} · "
            f"T3 ₹{status.target3:,.0f}"
        )
        if status.active_stop:
            extra += f"\nActive stop **₹{status.active_stop:,.0f}**"
    if ladder_line:
        extra += f"\n{ladder_line}"
    return (
        f"*{status.emoji} {plan.symbol} ({trade_side}) — {status.label}*\n"
        f"{status.detail}{extra}\n"
        f"Plan: entry ₹{plan.entry:,.0f} · stop ₹{plan.stop_loss:,.0f}"
    )


def format_options_live_alert(status, *, snap) -> str:
    label = f"{snap.fno_symbol} {snap.option_type} {snap.strike:g}"
    extra = ""
    if status.target2 and status.target3:
        extra = (
            f"\nT1 ₹{snap.target:,.2f} · T2 ₹{status.target2:,.2f} · "
            f"T3 ₹{status.target3:,.2f}"
        )
        if status.active_stop:
            extra += f"\nActive prem stop **₹{status.active_stop:,.2f}**"
    return (
        f"*{status.emoji} {label} — {status.label}*\n"
        f"{status.detail}{extra}\n"
        f"Entry prem ₹{snap.entry:,.2f} · stop ₹{snap.stop_loss:,.2f}"
    )


def check_watchlist_live_alerts(
    *,
    trade_date: str | None = None,
    market: str = "india",
) -> list[str]:
    """Return new alert messages (does not send)."""
    trade_date = trade_date or session_target_date()
    messages: list[str] = []

    if load_selected_symbols(trade_date):
        for plan in effective_trade_plans(trade_date):
            ltp, _src = get_live_ltp(plan.symbol, market=market)
            trade_side = infer_trade_side(plan.entry, plan.stop_loss, explicit=plan.side)
            status = assess_live_plan(
                ltp,
                entry=plan.entry,
                stop_loss=plan.stop_loss,
                target=plan.target,
                symbol=plan.symbol,
                side=trade_side,
            )
            kind = ALERT_LABELS.get(status.label)
            if not kind or kind in ("in_zone", "below_entry", "above_entry") or _was_alert_sent(trade_date, plan.symbol, kind):
                continue
            from analyzer.trade_ladder import build_equity_ladder

            ladder = build_equity_ladder(
                trade_side, plan.entry, plan.stop_loss, plan.target,
            )
            ladder_line = format_stop_trail_telegram(ladder)
            messages.append(format_live_alert(status, plan=plan, ladder_line=ladder_line))
            _mark_alert_sent(trade_date, plan.symbol, kind)

    selected_opt = load_selected_option(trade_date)
    for snap in fetch_options_snapshots_for_date(trade_date):
        if selected_opt:
            if not snap_matches_pick(snap, selected_opt):
                continue
        elif not snap.recommended:
            continue
        sym_key = f"OPT:{snap.fno_symbol}:{snap.option_type}:{snap.strike:g}"
        prem = fetch_option_leg_ltp(
            snap.fno_symbol, snap.option_type, snap.strike, expiry=snap.expiry,
        )
        status = assess_options_live_plan(
            prem,
            entry=snap.entry,
            stop_loss=snap.stop_loss,
            target=snap.target,
            label=sym_key,
        )
        kind = ALERT_LABELS.get(status.label)
        if not kind or kind in ("in_zone", "below_entry") or _was_alert_sent(trade_date, sym_key, kind):
            continue
        messages.append(format_options_live_alert(status, snap=snap))
        _mark_alert_sent(trade_date, sym_key, kind)

    return messages


def run_watchlist_live_alerts(
    *,
    trade_date: str | None = None,
    market: str = "india",
) -> tuple[int, str]:
    """Send Telegram for new entry/stop/T1/T2/T3 zone hits on your picks."""
    from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured

    now = datetime.now(IST)
    skip = skip_scheduled_job_reason(now)
    if skip:
        return 0, skip

    session = market_session_status()
    if not session.get("is_open"):
        return 0, "Market closed"

    if not telegram_configured():
        return 0, "Telegram not configured"

    messages = check_watchlist_live_alerts(trade_date=trade_date, market=market)
    if not messages:
        return 0, "No new live alerts"

    ok, err = send_telegram_broadcast("\n\n".join(messages), alert_type="intraday")
    if ok:
        return len(messages), f"Sent {len(messages)} live alert(s)"
    return 0, err


def maybe_send_watchlist_live_alerts() -> None:
    """Poll during open session when app is running."""
    run_watchlist_live_alerts()
