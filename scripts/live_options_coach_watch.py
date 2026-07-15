#!/usr/bin/env python3
"""Print NIFTY + BANKNIFTY options board every N seconds (terminal)."""

from __future__ import annotations

import argparse
import sys
import warnings
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

IST = ZoneInfo("Asia/Kolkata")

INDICES = ("NIFTY", "BANKNIFTY")
LOT_SIZES = {"NIFTY": 75, "BANKNIFTY": 30, "FINNIFTY": 40, "MIDCPNIFTY": 50}
PEAK_DIR = ROOT / "data" / "intraday"


def _peak_store_path(fno: str, option_type: str, strike: float, entry: float) -> Path:
    key = f"{fno.upper()}_{option_type.upper()}_{strike:g}_{entry:g}"
    return PEAK_DIR / f"coach_peak_{key}.json"


def _load_peak_premium(path: Path) -> float | None:
    if not path.exists():
        return None
    try:
        import json

        data = json.loads(path.read_text(encoding="utf-8"))
        peak = float(data.get("peak_premium", 0))
        return peak if peak > 0 else None
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def _save_peak_premium(path: Path, peak: float) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"peak_premium": round(peak, 2)}, indent=2),
        encoding="utf-8",
    )


def _spot_vs_or(spot: float | None, or_low: float | None, or_high: float | None) -> str:
    if spot is None or or_low is None or or_high is None:
        return "OR —"
    if spot > or_high:
        return "above OR high"
    if spot < or_low:
        return "below OR low"
    return "inside OR"


def _resolve_focus_leg(
    *,
    fno: str | None,
    option_type: str | None,
    strike: float | None,
    budget: float,
    auto: bool,
) -> tuple[str, str, float, float | None, int]:
    from analyzer.affordable_invest import DEFAULT_MAX_OPTION_LOT_COST_INR
    from analyzer.options_expiry_watchlist import build_options_expiry_watchlist
    from analyzer.options_trade_selection import load_selected_option

    if fno and option_type and strike:
        f = fno.upper()
        return f, option_type.upper(), float(strike), None, LOT_SIZES.get(f, 75)

    if not auto:
        return "NIFTY", "CE", 24000.0, None, 75

    starred = load_selected_option()
    if starred:
        f = starred["fno_symbol"].upper()
        return (
            f,
            starred["option_type"].upper(),
            float(starred["strike"]),
            None,
            LOT_SIZES.get(f, 75),
        )

    max_lot = budget if budget > 0 else DEFAULT_MAX_OPTION_LOT_COST_INR
    wl = build_options_expiry_watchlist(max_lot_cost=max_lot)
    pick = next((p for p in wl.picks if p.recommended), None) or (wl.picks[0] if wl.picks else None)
    if not pick:
        raise RuntimeError("No options pick — run Prep all or pass --fno --type --strike")

    return (
        pick.fno_symbol.upper(),
        pick.option_type.upper(),
        float(pick.strike),
        float(pick.premium) if pick.premium else None,
        pick.lot_size or LOT_SIZES.get(pick.fno_symbol.upper(), 75),
    )


def _advice_in_trade(
    *,
    entry: float,
    premium: float | None,
    spot: float | None,
    or_high: float | None,
    gate_phase: str,
    reversal_phase: str,
    option_type: str,
    peak_premium: float | None = None,
    targets: "ProfitTargets | None" = None,
) -> tuple[str, str]:
    """1-lot MIS: sell full lot at configured targets; exit on trail / giveback / spot stop."""
    from analyzer.profit_targets import ProfitTargets, build_profit_targets

    if premium is None:
        return "WAIT", "Premium loading — keep last verdict."

    if targets is None:
        targets = build_profit_targets(entry, mode="aggressive")

    pnl_pct = (premium - entry) / entry * 100.0
    opt = option_type.upper()
    t1, t2, stretch = targets.t1, targets.t2, targets.stretch
    trail = targets.trail
    peak = peak_premium if peak_premium is not None else premium
    chase_stretch = targets.chase_stretch

    # Never give back below minimum floor after touching it
    if peak >= t1 and premium < t1:
        return (
            "EXIT ALL",
            f"Below min +{targets.t1_pct:.0f}% ₹{t1:.2f} (peak ₹{peak:.2f}) — sell now",
        )

    if premium <= targets.hard_stop:
        return "EXIT ALL", f"Hard stop — premium ₹{premium:.2f}"

    if reversal_phase == "invalidated":
        return "EXIT ALL", f"{opt} thesis invalidated"

    if opt == "CE" and spot is not None and or_high is not None and spot < or_high:
        return "EXIT ALL", f"Spot ₹{spot:,.0f} < OR high ₹{or_high:,.0f}"

    if opt == "PE" and spot is not None and or_high is not None and spot > or_high:
        return "EXIT ALL", f"Spot ₹{spot:,.0f} > OR high ₹{or_high:,.0f}"

    if premium <= trail:
        return "EXIT ALL", f"Trail ₹{trail:.2f} hit (premium ₹{premium:.2f})"

    if chase_stretch:
        if premium >= stretch:
            return (
                "SELL ALL",
                f"Stretch +{targets.stretch_pct:.0f}% ₹{stretch:.2f} — sell full lot (+{pnl_pct:.1f}%)",
            )
        if peak >= stretch * 0.98 and premium < stretch * 0.98:
            return "EXIT ALL", f"Fading from ₹{peak:.2f} peak — protect before ₹{stretch:.0f}"
        if peak >= t2 and premium < t2:
            return "EXIT ALL", f"Gave back below +{targets.t2_pct:.0f}% ₹{t2:.2f} — lock profit"
        if premium >= t2:
            return "HOLD", f"+{pnl_pct:.1f}% — ride to stretch ₹{stretch:.2f} (+{targets.stretch_pct:.0f}%)"
        if premium >= t1:
            return "TIGHTEN", f"+{pnl_pct:.1f}% — min hit; hold toward ₹{stretch:.2f} (+{targets.stretch_pct:.0f}%)"
    else:
        if premium >= t2:
            return (
                "SELL ALL",
                f"Target +{targets.t2_pct:.0f}% ₹{t2:.2f} hit — minimum goal (+{pnl_pct:.1f}%)",
            )
        if premium >= t1:
            return "TIGHTEN", f"+{pnl_pct:.1f}% — min +{targets.t1_pct:.0f}% hit; aim ₹{t2:.2f} (+{targets.t2_pct:.0f}%)"
        if peak >= t2 * 0.98 and premium < t2 * 0.98:
            return "EXIT ALL", f"Fading from ₹{peak:.2f} peak — protect +{targets.t2_pct:.0f}%"

    if premium < entry:
        return "EXIT ALL", f"In loss ₹{premium:.2f} vs entry ₹{entry:.2f} — cut now"

    if premium <= entry * 1.02 and peak >= t1:
        return "EXIT ALL", f"Profit almost gone — sell before red"

    if gate_phase == "enter_ok" and reversal_phase == "ok":
        if premium < entry:
            return "EXIT ALL", f"In loss — cut now (+{pnl_pct:.1f}%)"
        if premium >= entry * 1.05:
            if chase_stretch:
                return "TIGHTEN", f"+{pnl_pct:.1f}% — min ₹{t1:.0f} · lock ₹{t2:.0f} · stretch ₹{stretch:.0f}"
            return "TIGHTEN", f"+{pnl_pct:.1f}% — min ₹{t1:.0f} · sell at ₹{t2:.0f} (+{targets.t2_pct:.0f}%)"
        if chase_stretch:
            return "HOLD", f"+{pnl_pct:.1f}% · stretch mode · min +{targets.t1_pct:.0f}% → +{targets.stretch_pct:.0f}%"
        return "HOLD", f"+{pnl_pct:.1f}% · thesis OK · min +{targets.t1_pct:.0f}% → +{targets.t2_pct:.0f}%"

    if gate_phase == "wait":
        return "TIGHTEN", "Inside OR — watch premium"

    return "TIGHTEN", "Monitor — prefer exit on weakness"


def _trade_detail_lines(
    *,
    entry: float,
    premium: float | None,
    spot: float | None,
    or_high: float | None,
    or_low: float | None,
    lot: int,
    lots: int,
    verdict: str,
    targets: "ProfitTargets | None" = None,
) -> list[str]:
    """Sell/hold levels printed every tick in trade mode."""
    from analyzer.profit_targets import build_profit_targets

    if targets is None:
        targets = build_profit_targets(entry, mode="aggressive")
    t1, t2, stretch = targets.t1, targets.t2, targets.stretch
    trail, hard = targets.trail, targets.hard_stop

    lines = [
        f"  📋 TRADE PLAN @ entry ₹{entry:.2f} × {lots} lot(s)",
        f"     {targets.headline}",
    ]
    if premium is not None:
        pnl = (premium - entry) * lot * lots
        pct = (premium / entry - 1) * 100
        lines.append(f"     Live ₹{premium:.2f} │ P&L ₹{pnl:+,.0f} ({pct:+.1f}%)")
        if targets.chase_stretch:
            lines.append(
                f"     MIN ₹{t1:.2f} (+{targets.t1_pct:.0f}%) │ LOCK ₹{t2:.2f} (+{targets.t2_pct:.0f}%) │ "
                f"STRETCH ₹{stretch:.2f} (+{targets.stretch_pct:.0f}%)"
            )
        else:
            lines.append(
                f"     MIN ₹{t1:.2f} (+{targets.t1_pct:.0f}%) │ SELL ALL @ ₹{t2:.2f} (+{targets.t2_pct:.0f}%)"
            )
        lines.append(f"     EXIT ALL @ prem ≤ ₹{trail:.2f} (trail) or ≤ ₹{hard:.2f} (hard)")
        sell_at = stretch if targets.chase_stretch else t2
        if premium >= sell_at:
            lines.append(f"     ⚡ TARGET HIT — sell full lot (prem ≥ ₹{sell_at:.2f})")
        elif premium >= t1:
            lines.append(f"     👀 Min hit — protect ₹{t1:.2f}, aim ₹{sell_at:.2f}")
    if spot is not None and or_high is not None:
        buf = spot - or_high
        lines.append(
            f"     Spot ₹{spot:,.0f} │ OR high ₹{or_high:,.0f} │ buffer {buf:+.0f} pts"
        )
        if spot < or_high:
            lines.append("     🚨 SPOT BELOW OR HIGH — EXIT ALL")
        elif buf < 15:
            lines.append("     ⚠️ Thin buffer — tighten stop")
    if or_low is not None and spot is not None:
        lines.append(f"     Hard spot stop: NIFTY < ₹{or_high:,.0f}")
    action = {
        "HOLD": "✅ HOLD — sell full lot at T1/T2 (no half-lot on NSE)",
        "TIGHTEN": "⚠️ TIGHTEN — ready to sell on next slip",
        "SELL ALL": "💰 SELL FULL LOT NOW — target hit",
        "BOOK 1": "💰 SELL FULL LOT — book profits",
        "EXIT ALL": "🛑 SELL EVERYTHING NOW",
        "WAIT": "⏳ WAIT — data loading",
    }.get(verdict, verdict)
    lines.append(f"     ▶ ACTION: {action}")
    return lines


def _user_action(verdict: str) -> str:
    """Map internal verdict → PURCHASE | HOLD | SELL | WAIT."""
    v = verdict.upper().strip()
    if v in ("ENTER OK", "PURCHASE", "BUY"):
        return "PURCHASE"
    if v in ("EXIT ALL", "SELL ALL", "BOOK 1", "SELL"):
        return "SELL"
    if v in ("HOLD", "TIGHTEN"):
        return "HOLD"
    if v in ("NO TRADE", "SKIP", "OBSERVE"):
        return "WAIT"
    return "WAIT"


def _advice_flat(
    *,
    premium: float | None,
    gate_phase: str,
    gate_headline: str,
    reversal_phase: str,
    lot_cost: float | None,
    budget: float,
    synthesis_verdict: str = "",
    synthesis_ok: bool = False,
    synthesis_conf: int = 0,
) -> tuple[str, str]:
    if lot_cost is not None and budget > 0 and lot_cost > budget:
        return "NO TRADE", f"1-lot ₹{lot_cost:,.0f} > budget ₹{budget:,.0f}"

    if gate_phase in ("observe", "wait") and "9:45" in (gate_headline or ""):
        return "OBSERVE", gate_headline or "Before 9:45 — wait for OR"

    if premium is None:
        return "WAIT", "Premium loading"

    if gate_phase == "do_not_enter":
        return "NO TRADE", gate_headline or "Gate blocked"

    if reversal_phase == "invalidated":
        return "NO TRADE", "Thesis invalidated"

    if gate_phase == "enter_ok" and reversal_phase in ("ok", "confirmed", ""):
        if synthesis_ok and synthesis_verdict in ("STRONG_BUY", "BUY"):
            return "ENTER OK", f"{gate_headline} · synthesis {synthesis_verdict} {synthesis_conf}%"
        if synthesis_verdict in ("NO_TRADE", "WAIT") and synthesis_conf < 50:
            return "NO TRADE", f"Synthesis {synthesis_verdict} {synthesis_conf}% — wait"
        return "ENTER OK", gate_headline or "OR gate open"

    return "WAIT", gate_headline or "Wait for OR breakout"


def _leg_tick(
    *,
    fno: str,
    option_type: str,
    strike: float,
    market: str,
    force_chain: bool,
) -> dict:
    from analyzer.live_options_coach import build_live_options_coach

    snap = build_live_options_coach(
        fno_symbol=fno,
        option_type=option_type,
        strike=strike,
        market=market,
        force_chain=force_chain,
    )
    gate = snap.gate
    return {
        "spot": snap.spot,
        "or_low": snap.or_low,
        "or_high": snap.or_high,
        "premium": snap.premium,
        "gate_phase": gate.phase if gate else "",
        "gate_headline": gate.headline if gate else "",
        "gate_emoji": gate.emoji if gate else "⚪",
        "reversal_phase": snap.reversal.phase if snap.reversal else "",
        "updated_at": snap.updated_at,
    }


def _build_market_board(
    *,
    market: str,
    budget: float,
    force_chain: bool,
) -> tuple[list[str], str]:
    """NIFTY + BANKNIFTY spot/OR and top CE/PE legs under budget."""
    from analyzer.affordable_invest import DEFAULT_MAX_OPTION_LOT_COST_INR
    from analyzer.mis_trade_advisory import build_mis_trade_advisory
    from analyzer.nse_options import fetch_option_leg_ltp
    from analyzer.opening_range_confirm import fetch_symbol_opening_range
    from analyzer.options_entry_gate import assess_option_entry_gate
    from analyzer.options_expiry_watchlist import build_options_expiry_watchlist
    from analyzer.options_reversal_alerts import INDEX_YAHOO
    from analyzer.providers import get_live_ltp

    max_lot = budget if budget > 0 else DEFAULT_MAX_OPTION_LOT_COST_INR
    wl = build_options_expiry_watchlist(max_lot_cost=max_lot)
    picks_by: dict[str, dict[str, object]] = {idx: {} for idx in INDICES}
    for p in wl.picks:
        sym = p.fno_symbol.upper()
        if sym not in picks_by:
            continue
        side = p.option_type.upper()
        if side not in picks_by[sym]:
            picks_by[sym][side] = p

    lines: list[str] = []
    at = datetime.now(IST).strftime("%H:%M:%S IST")

    for idx in INDICES:
        yahoo = INDEX_YAHOO.get(idx)
        if not yahoo:
            continue
        spot, _ = get_live_ltp(yahoo, market=market)
        or_rng = fetch_symbol_opening_range(yahoo, market=market)
        or_low = or_high = None
        if or_rng:
            or_high, or_low = or_rng
        spot_s = f"₹{spot:,.0f}" if spot else "—"
        if or_low is not None and or_high is not None:
            or_s = f"OR ₹{or_low:,.0f}–₹{or_high:,.0f}"
        else:
            or_s = "OR —"
        pos = _spot_vs_or(spot, or_low, or_high)
        star = "★ " if any(
            getattr(picks_by[idx].get(s), "recommended", False)
            for s in ("CE", "PE")
            if picks_by[idx].get(s)
        ) else ""
        lines.append(f"  {star}{idx} │ spot {spot_s} │ {or_s} │ {pos}")

        try:
            from analyzer.multi_timeframe import index_mtf
            from analyzer.options_flow_snapshot import fetch_index_flow

            mtf = index_mtf(idx, market=market)
            mtf_short = " · ".join(
                f"{f.interval}:{f.action.replace('STRONG ', '')}" for f in mtf.frames if not f.error
            ) or "MTF loading"
            lines.append(
                f"    📊 MTF {mtf.alignment_pct}% │ {mtf_short} → {mtf.consensus_action}"
            )
            if force_chain:
                flow = fetch_index_flow(idx)
                if flow.lines:
                    lines.append(f"    📈 {flow.lines[0]}")
                elif flow.error:
                    lines.append(f"    📈 Flow — {flow.error[:50]}")
        except Exception:
            lines.append("    📊 MTF — loading…")

        for side in ("CE", "PE"):
            pick = picks_by[idx].get(side)
            if not pick:
                lines.append(f"    {side} — (no pick under ₹{budget:,.0f}/lot)")
                continue
            strike = float(pick.strike)
            lot = pick.lot_size or LOT_SIZES.get(idx, 75)
            prem = pick.premium
            if force_chain:
                live = fetch_option_leg_ltp(idx, side, strike)
                if live is not None:
                    prem = live
            prem_s = f"₹{prem:.2f}" if prem else "—"
            lot_cost = prem * lot if prem else None
            cost_s = f"₹{lot_cost:,.0f}" if lot_cost else "—"
            gate = assess_option_entry_gate(
                side,
                fno_symbol=idx,
                strike=strike,
                spot=spot,
                or_high=or_high,
                or_low=or_low,
            )
            rec = "★" if pick.recommended else " "
            over = " OVER BUDGET" if lot_cost and budget > 0 and lot_cost > budget else ""
            lines.append(
                f"    {rec}{side} {strike:g} │ prem {prem_s} │ 1-lot {cost_s}{over} │ "
                f"{gate.emoji} {gate.headline}"
            )

    adv = build_mis_trade_advisory()
    conf = getattr(adv, "confidence_pct", adv.score)
    mtf_s = getattr(adv, "mtf_summary", "") or ""
    flow_s = getattr(adv, "flow_summary", "") or ""
    summary = f"🚦 {adv.emoji} {adv.headline} (confidence {conf}/100)"
    lines.append(f"  {summary}")
    if mtf_s:
        lines.append(f"  📊 {mtf_s.replace('**', '')}")
    if flow_s:
        lines.append(f"  📈 {flow_s}")
    return lines, at


def main() -> int:
    from analyzer.env_loader import load_app_env

    load_app_env()
    warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")
    p = argparse.ArgumentParser(description="Live NIFTY + BANKNIFTY options board (terminal)")
    p.add_argument("--fno", default="", help="Focus leg index (optional)")
    p.add_argument("--type", default="", choices=("", "CE", "PE"))
    p.add_argument("--strike", type=float, default=0.0)
    p.add_argument("--entry", type=float, default=0.0, help="Your fill; 0 = flat / watch mode")
    p.add_argument("--lots", type=int, default=1, help="Lots on focus leg")
    p.add_argument("--budget", type=float, default=5000.0, help="Max 1-lot cost filter")
    p.add_argument("--auto", action="store_true", help="Auto-pick focus leg from ★ / watchlist")
    p.add_argument("--interval", type=float, default=5.0, help="Seconds between ticks (default 5)")
    p.add_argument("--chain-every", type=int, default=2, help="Refresh premiums every N ticks")
    p.add_argument("--peak-premium", type=float, default=0.0, help="Session high (e.g. 92.75) if coach restarted")
    p.add_argument(
        "--profit-mode",
        default="",
        choices=("", "conservative", "standard", "aggressive"),
        help="Exit ladder (default: prefs.json profit_mode)",
    )
    p.add_argument(
        "--min-daily-pct",
        type=float,
        default=0.0,
        help="Daily capital goal %% (default: prefs min_daily_profit_pct)",
    )
    p.add_argument("--focus-only", action="store_true", help="Only your trade + sell levels (less noise)")
    p.add_argument("--market", default="india")
    p.add_argument("--log", default="", help="Optional log file path")
    args = p.parse_args()

    interval = max(args.interval, 1.0)
    use_auto = args.auto or not (args.fno and args.type and args.strike)
    fno, opt_type, strike, ref_prem, lot = _resolve_focus_leg(
        fno=args.fno or None,
        option_type=args.type or None,
        strike=args.strike or None,
        budget=args.budget,
        auto=use_auto,
    )
    in_trade = args.entry > 0
    log_path = Path(args.log).expanduser() if args.log else None
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)

    from analyzer.intraday_prefs import load_intraday_prefs
    from analyzer.market_regime import detect_nifty_regime
    from analyzer.profit_targets import build_profit_targets, capital_profit_inr

    prefs = load_intraday_prefs()
    profit_mode = args.profit_mode or prefs.profit_mode
    min_daily_pct = args.min_daily_pct if args.min_daily_pct > 0 else prefs.min_daily_profit_pct
    regime = None
    try:
        regime = detect_nifty_regime()
    except Exception:
        pass
    profit_targets = (
        build_profit_targets(
            args.entry,
            mode=profit_mode,
            min_trade_pct=prefs.min_daily_profit_pct,
            target_trade_pct=prefs.target_daily_profit_pct,
            stretch_trade_pct=prefs.stretch_daily_profit_pct,
            min_daily_capital_pct=prefs.min_daily_profit_pct,
            regime=regime,
        )
        if in_trade
        else None
    )

    mode = f"IN TRADE {fno} {opt_type} {strike:g} @ ₹{args.entry:.2f} × {args.lots}" if in_trade else "FLAT"
    goal_line = ""
    if in_trade and profit_targets:
        min_inr = capital_profit_inr(prefs.capital, prefs.min_daily_profit_pct)
        tgt_inr = capital_profit_inr(prefs.capital, prefs.target_daily_profit_pct)
        goal_line = (
            f"Goals: min ₹{min_inr:,.0f} (+{prefs.min_daily_profit_pct:.0f}%) · "
            f"target ₹{tgt_inr:,.0f} (+{prefs.target_daily_profit_pct:.0f}%) · "
            f"stretch up to +{prefs.stretch_daily_profit_pct:.0f}%\n"
        )
    print(
        f"⚡ Options board · NIFTY + BANKNIFTY · {mode}\n"
        f"{goal_line}"
        f"Focus: {fno} {opt_type} {strike:g} │ budget ≤ ₹{args.budget:,.0f}/lot │ "
        f"every {interval:g}s (Ctrl+C stop)\n",
        flush=True,
    )

    tick_n = 0
    last_focus_prem: float | None = ref_prem
    peak_path = _peak_store_path(fno, opt_type, strike, args.entry) if in_trade else None
    stored_peak = _load_peak_premium(peak_path) if peak_path else None
    peak_premium: float | None = ref_prem
    seeds = [p for p in (stored_peak, args.peak_premium or None, ref_prem, args.entry) if p]
    if seeds:
        peak_premium = max(seeds)
    if peak_path and peak_premium:
        _save_peak_premium(peak_path, peak_premium)
    if in_trade and peak_premium and profit_targets:
        lock = profit_targets.t1 if not profit_targets.regime_ok_for_stretch else profit_targets.t2
        if peak_premium >= lock:
            print(f"  📈 Session peak ₹{peak_premium:.2f} (protect below ₹{lock:.0f})\n", flush=True)

    while True:
        tick_n += 1
        force = tick_n == 1 or tick_n % max(args.chain_every, 1) == 0
        try:
            if args.focus_only and in_trade:
                board_lines, at = [], datetime.now(IST).strftime("%H:%M:%S IST")
            else:
                board_lines, at = _build_market_board(
                    market=args.market,
                    budget=args.budget,
                    force_chain=force,
                )
            focus = _leg_tick(
                fno=fno,
                option_type=opt_type,
                strike=strike,
                market=args.market,
                force_chain=force,
            )
        except Exception as exc:
            msg = str(exc).lower()
            if "too many requests" in msg:
                board_lines = ["  (rate limited — retrying…)"]
                at = datetime.now(IST).strftime("%H:%M:%S IST")
                focus = {
                    "premium": last_focus_prem,
                    "spot": None,
                    "or_high": None,
                    "or_low": None,
                    "gate_phase": "",
                    "gate_headline": "",
                    "reversal_phase": "",
                }
            else:
                raise

        prem = focus["premium"] if focus["premium"] is not None else last_focus_prem
        if focus["premium"] is not None:
            last_focus_prem = prem
            if prem is not None and (peak_premium is None or prem > peak_premium):
                peak_premium = prem
                if peak_path:
                    _save_peak_premium(peak_path, peak_premium)

        lot_cost = prem * lot if prem else None

        syn_lines: list[str] = []
        syn_verdict = ""
        syn_ok = False
        syn_conf = 0
        try:
            from analyzer.strategy_synthesis import format_synthesis_terminal, synthesize_options

            syn = synthesize_options(
                fno, opt_type, strike, market=args.market, budget=args.budget,
            )
            syn_verdict = syn.verdict
            syn_ok = syn.trade_allowed
            syn_conf = syn.confidence_pct
            syn_lines = format_synthesis_terminal(syn, max_pillars=6)
        except Exception:
            pass

        if in_trade:
            verdict, reason = _advice_in_trade(
                entry=args.entry,
                premium=prem,
                spot=focus["spot"],
                or_high=focus["or_high"],
                gate_phase=focus["gate_phase"],
                reversal_phase=focus["reversal_phase"],
                option_type=opt_type,
                peak_premium=peak_premium,
                targets=profit_targets,
            )
            pnl_inr = (prem - args.entry) * lot * args.lots if prem else 0.0
            focus_line = (
                f"  ▶ FOCUS **{verdict}** │ {fno} {opt_type} {strike:g} prem "
                f"{'₹' + f'{prem:.2f}' if prem else '—'} │ P&L ₹{pnl_inr:+,.0f} │ {reason}"
            )
        else:
            verdict, reason = _advice_flat(
                premium=prem,
                gate_phase=focus["gate_phase"],
                gate_headline=focus["gate_headline"],
                reversal_phase=focus["reversal_phase"],
                lot_cost=lot_cost,
                budget=args.budget,
                synthesis_verdict=syn_verdict,
                synthesis_ok=syn_ok,
                synthesis_conf=syn_conf,
            )
            focus_line = (
                f"  ▶ FOCUS **{verdict}** │ {fno} {opt_type} {strike:g} prem "
                f"{'₹' + f'{prem:.2f}' if prem else '—'} │ {reason}"
            )

        action = _user_action(verdict)
        action_line = f"  🎯 ACTION: **{action}** │ {reason}"

        print(f"─── [{at}] ───", flush=True)
        print(action_line, flush=True)
        for line in board_lines:
            print(line, flush=True)
        if in_trade:
            for line in _trade_detail_lines(
                entry=args.entry,
                premium=prem,
                spot=focus["spot"],
                or_high=focus["or_high"],
                or_low=focus["or_low"],
                lot=lot,
                lots=args.lots,
                verdict=verdict,
                targets=profit_targets,
            ):
                print(line, flush=True)
        if not args.focus_only:
            for line in syn_lines:
                print(line, flush=True)
        if action == "SELL":
            print(f"🚨{focus_line}🚨", flush=True)
        elif action == "PURCHASE":
            print(f"🟢{focus_line}", flush=True)
        else:
            print(focus_line, flush=True)
        print(flush=True)

        if log_path:
            log_path.write_text(
                f"─── [{at}] ───\n" + "\n".join(board_lines) + "\n" + focus_line + "\n",
                encoding="utf-8",
            )

        time.sleep(interval)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
