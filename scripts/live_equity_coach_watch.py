#!/usr/bin/env python3
"""Print equity MIS coaching for today's ★ picks every N seconds (terminal)."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

IST = ZoneInfo("Asia/Kolkata")


def _verdict_flat(
    *,
    or_ok: bool,
    or_phase: str,
    can_enter: bool,
    affordable: bool,
) -> tuple[str, str]:
    if or_phase == "observe":
        return "OBSERVE", "Before 9:45 — note OR levels only"
    if not affordable:
        return "SKIP", "Over per-trade budget — pick a cheaper name"
    if not can_enter:
        return "WAIT", "Plan blocked (wide stop / R:R) — wait for tighter setup"
    if or_ok:
        return "ENTER", "OR breakout + plan OK"
    if or_phase == "invalid":
        return "SKIP", "Thesis invalid vs opening range"
    if or_phase == "wait":
        return "WAIT", "Below OR high or above entry — wait for breakout"
    return "WAIT", "Monitor"


def _verdict_in_trade(plan_status) -> tuple[str, str]:
    label = (plan_status.label or "").lower()
    if "stop" in label and "near" not in label:
        return "EXIT ALL", plan_status.label
    if "t3 hit" in label or "exit rest" in label:
        return "EXIT ALL", plan_status.label
    if "t1 hit" in label or "t2 hit" in label:
        return "BOOK PARTIAL", plan_status.label
    if "near stop" in label:
        return "TIGHTEN", plan_status.label
    if "near t" in label or "trail" in label:
        return "HOLD", plan_status.label
    return "HOLD", plan_status.label or "Monitor"


def _budget_from_args(args) -> tuple[float, float, float, int]:
    from analyzer.intraday_beginner_tips import build_capital_budget
    from analyzer.intraday_prefs import load_intraday_prefs

    prefs = load_intraday_prefs()
    capital = float(args.capital) if args.capital is not None else prefs.capital
    alloc = float(args.allocation) if args.allocation is not None else prefs.allocation_pct
    risk = float(args.max_risk) if args.max_risk is not None else prefs.max_risk_pct
    trades = int(args.max_trades) if args.max_trades is not None else prefs.max_trades
    b = build_capital_budget(
        capital,
        allocation_pct=alloc,
        max_risk_pct=risk,
        max_concurrent_trades=trades,
    )
    return b.allocated_inr, b.per_trade_budget_inr, b.max_risk_per_trade_inr, trades, risk


def _symbols_to_watch(args) -> list[str]:
    if args.symbol:
        return [args.symbol.upper().replace(".NS", "")]
    if args.symbols:
        return [s.strip().upper().replace(".NS", "") for s in args.symbols.split(",") if s.strip()]

    from analyzer.trade_selection import effective_trade_plans

    plans = effective_trade_plans()
    if plans:
        return [p.symbol.upper() for p in plans]

    from analyzer.watchlist_pins import load_pinned_plans

    pins = load_pinned_plans()
    return [p.symbol.upper() for p in pins[:2]]


def _plan_for_symbol(sym: str):
    from analyzer.watchlist_pins import load_pinned_plans

    for p in load_pinned_plans():
        if p.symbol.upper() == sym.upper():
            return p
    return None


def _tick_symbol(
    sym: str,
    *,
    market: str,
    allocated_inr: float,
    per_trade_inr: float,
    max_risk_pct: float,
    in_position: bool,
    entry_price: float | None,
    shares: int | None,
    affordable_only: bool,
) -> dict:
    from analyzer.opening_range_confirm import confirm_or_entry, fetch_symbol_opening_range
    from analyzer.providers import get_live_ltp
    from analyzer.watchlist_plan_tracker import assess_live_plan
    from analyzer.watchlist_position_size import equity_position_hint

    plan = _plan_for_symbol(sym)
    ltp, _src = get_live_ltp(sym, market=market)
    or_rng = fetch_symbol_opening_range(sym, market=market)
    or_high = or_low = None
    or_ok = False
    or_phase = "wait"
    or_detail = "OR unavailable"

    if plan:
        entry = float(plan.entry)
        stop = float(plan.stop_loss)
        target = float(plan.target)
        side = plan.side or "LONG"
    else:
        entry = float(ltp or 0)
        stop = entry * 0.975 if entry else 0
        target = entry * 1.02 if entry else 0
        side = "LONG"

    if or_rng:
        or_high, or_low = or_rng
        or_res = confirm_or_entry(
            ltp,
            entry=entry,
            or_high=or_high,
            or_low=or_low,
            side=side,
        )
        or_ok = or_res.allow_entry
        or_phase = or_res.phase
        or_detail = or_res.label

    hint = equity_position_hint(
        sym,
        entry,
        stop,
        target,
        allocated_inr=allocated_inr,
        max_risk_pct=max_risk_pct,
        per_trade_budget_inr=per_trade_inr,
        side=side,
    )
    affordable = True
    if affordable_only and ltp and ltp > per_trade_inr:
        affordable = False
    if hint.skip_reason and "cannot buy 1 share" in (hint.skip_reason or "").lower():
        affordable = False

    plan_status = assess_live_plan(
        ltp,
        entry=entry,
        stop_loss=stop,
        target=target,
        symbol=sym,
        side=side,
    )

    if in_position and entry_price and shares:
        pnl = (ltp - entry_price) * shares if ltp else None
        verdict, reason = _verdict_in_trade(plan_status)
    else:
        pnl = None
        verdict, reason = _verdict_flat(
            or_ok=or_ok,
            or_phase=or_phase,
            can_enter=hint.can_enter,
            affordable=affordable,
        )

    return {
        "sym": sym,
        "ltp": ltp,
        "entry": entry,
        "stop": stop,
        "target": target,
        "side": side,
        "or_high": or_high,
        "or_low": or_low,
        "or_detail": or_detail,
        "verdict": verdict,
        "reason": reason,
        "shares": shares if in_position else hint.suggested_shares,
        "pnl": pnl,
        "plan_label": plan_status.label,
        "active_stop": plan_status.active_stop,
        "affordable": affordable,
    }


def _session_line() -> str:
    from analyzer.market_regime import detect_nifty_regime
    from analyzer.market_session import market_session_status

    sess = market_session_status()
    try:
        reg = detect_nifty_regime()
        regime = f"{reg.regime} ADX {reg.adx:.0f}"
    except Exception:
        regime = "regime —"
    return f"{sess.get('status', '—')} · {sess.get('time_ist', '')} · {regime}"


def main() -> int:
    from analyzer.env_loader import load_app_env

    load_app_env()
    p = argparse.ArgumentParser(description="Live equity MIS coach (terminal, 5s default)")
    p.add_argument("--symbol", help="Single symbol in-trade mode (e.g. JIOFIN)")
    p.add_argument("--symbols", help="Comma list override (e.g. JIOFIN,BAJFINANCE)")
    p.add_argument("--entry", type=float, help="Your fill price when in a trade")
    p.add_argument("--shares", type=int, help="Shares held when in a trade")
    p.add_argument("--interval", type=float, default=5.0, help="Seconds between ticks (default 5)")
    p.add_argument("--market", default="india")
    p.add_argument("--capital", type=float, default=None, help="Total capital (default: saved prefs)")
    p.add_argument("--allocation", type=float, default=None, help="MIS %% of capital (default: prefs)")
    p.add_argument("--max-risk", type=float, default=None, help="Max risk %% per trade")
    p.add_argument("--max-trades", type=int, default=None, help="Concurrent trade slots")
    p.add_argument("--affordable-only", action="store_true", help="Flag names above per-trade budget")
    p.add_argument("--log", default="", help="Optional log file (last line only)")
    args = p.parse_args()

    interval = max(args.interval, 1.0)
    syms = _symbols_to_watch(args)
    if not syms:
        print("No symbols — run Prep all or pass --symbol / --symbols", file=sys.stderr)
        return 1

    in_position = bool(args.symbol and args.entry and args.shares)
    allocated, per_trade, max_loss, slots, max_risk_pct = _budget_from_args(args)
    log_path = Path(args.log).expanduser() if args.log else None
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)

    mode = (
        f"IN TRADE {args.symbol} × {args.shares} @ ₹{args.entry:.2f}"
        if in_position
        else f"WATCH {', '.join(syms)}"
    )
    print(
        f"📈 Equity coach · {mode}\n"
        f"Capital MIS ₹{allocated:,.0f} · per trade ₹{per_trade:,.0f} · "
        f"max loss ₹{max_loss:,.0f} · every {interval:g}s (Ctrl+C stop)\n",
        flush=True,
    )

    tick_n = 0
    while True:
        tick_n += 1
        at = datetime.now(IST).strftime("%H:%M:%S IST")
        header = f"─── [{at}] {_session_line()} ───"
        print(header, flush=True)

        lines: list[str] = []
        for sym in syms:
            try:
                row = _tick_symbol(
                    sym,
                    market=args.market,
                    allocated_inr=allocated,
                    per_trade_inr=per_trade,
                    max_risk_pct=max_risk_pct,
                    in_position=in_position and sym == args.symbol.upper(),
                    entry_price=args.entry,
                    shares=args.shares,
                    affordable_only=args.affordable_only,
                )
            except Exception as exc:
                msg = str(exc).lower()
                if "too many requests" in msg:
                    lines.append(f"  {sym}: rate limited — retrying…")
                    continue
                raise

            ltp_s = f"₹{row['ltp']:,.2f}" if row["ltp"] else "—"
            or_s = ""
            if row["or_high"] is not None:
                or_s = f" | OR ₹{row['or_low']:,.0f}–₹{row['or_high']:,.0f}"
            sh = row["shares"]
            sh_s = f"{sh} sh" if sh else "—"
            pnl_s = ""
            if row["pnl"] is not None:
                pnl_s = f" | P&L ₹{row['pnl']:+,.0f}"

            line = (
                f"  **{row['verdict']}** {sym} {row['side']} | LTP {ltp_s}{or_s} | "
                f"plan E ₹{row['entry']:,.0f} S ₹{row['stop']:,.0f} T ₹{row['target']:,.0f} | "
                f"{sh_s}{pnl_s} | {row['or_detail']} · {row['reason']}"
            )
            if row["verdict"] in ("EXIT ALL", "EXIT"):
                line = f"  🚨 {line} 🚨"
            elif row["verdict"] == "ENTER":
                line = f"  🟢 {line}"
            lines.append(line)

        block = "\n".join(lines)
        print(block, flush=True)
        print(flush=True)
        if log_path:
            log_path.write_text(header + "\n" + block + "\n", encoding="utf-8")

        time.sleep(interval)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
