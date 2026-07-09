"""Plain-text MIS checklist for phone notes / Telegram / WhatsApp."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from analyzer.intraday_beginner_tips import build_capital_budget
from analyzer.intraday_prefs import load_intraday_prefs
from analyzer.options_trade_selection import load_selected_option, snap_matches_pick
from analyzer.trade_selection import load_selected_symbols
from analyzer.watchlist_history import fetch_snapshots_for_date, session_target_date
from analyzer.watchlist_pins import PinnedPlan, infer_trade_side, load_pinned_plans
from analyzer.watchlist_position_size import equity_position_hint

IST = ZoneInfo("Asia/Kolkata")


@dataclass
class PrintableChecklistContext:
    trade_date: str
    prep_date: str
    equity_plans: list[PinnedPlan]
    options_picks: list[Any]
    selected_symbols: list[str]
    selected_option: dict[str, Any] | None
    market_bias: str
    gift_nifty_line: str
    allocated_inr: float
    per_trade_inr: float
    max_risk_pct: float
    max_trades: int
    total_capital_inr: float
    allocation_pct: float
    max_loss_day_inr: float


def _iso_to_display(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return iso


def _blank(value: str | float | int | None, *, prefix: str = "") -> str:
    if value is None or value == "":
        return "___________"
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        num = float(value)
        if prefix == "₹":
            return f"{prefix}{num:,.0f}" if num == int(num) else f"{prefix}{num:,.2f}"
        return f"{num:g}"
    return str(value)


def _pick_attr(p: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(p, name):
            val = getattr(p, name)
            if val is not None:
                return val
        if isinstance(p, dict) and name in p:
            return p[name]
    return default


def _resolve_equity_plans(trade_date: str) -> list[PinnedPlan]:
    plans = load_pinned_plans()
    if plans:
        return plans
    snaps = fetch_snapshots_for_date(trade_date)
    return [
        PinnedPlan(
            symbol=s.symbol,
            entry=s.entry,
            stop_loss=s.stop_loss,
            target=s.target,
            prep_date=s.prep_date,
            side=s.side,
        )
        for s in snaps
    ]


def _resolve_options_picks(
    trade_date: str,
    options_picks: list[Any] | None,
) -> list[Any]:
    if options_picks:
        return options_picks
    try:
        from analyzer.options_watchlist_history import fetch_options_snapshots_for_date

        snaps = fetch_options_snapshots_for_date(trade_date)
        if snaps:
            return snaps
    except Exception:
        pass
    return []


def _resolve_market_bias(trade_date: str, market_bias: str) -> str:
    if market_bias:
        return market_bias
    snaps = fetch_snapshots_for_date(trade_date)
    for s in snaps:
        if s.market_bias:
            return s.market_bias
    return ""


def _gift_nifty_plain(*, include_live: bool) -> str:
    if not include_live:
        return "___________"
    try:
        from analyzer.gift_nifty import fetch_gift_nifty_cue

        cue = fetch_gift_nifty_cue()
        if not cue:
            return "___________"
        chg = f"{cue.change_1d_pct:+.2f}%" if cue.change_1d_pct is not None else "—"
        return f"{cue.name} {chg} · ₹{cue.price:,.0f}"
    except Exception:
        return "___________"


def gather_printable_checklist_context(
    *,
    trade_date: str | None = None,
    prep_date: str = "",
    options_picks: list[Any] | None = None,
    market_bias: str = "",
    include_live_cues: bool = True,
) -> PrintableChecklistContext:
    trade_date = trade_date or session_target_date()
    prefs = load_intraday_prefs()
    budget = build_capital_budget(
        prefs.capital,
        allocation_pct=prefs.allocation_pct,
        max_risk_pct=prefs.max_risk_pct,
        max_concurrent_trades=prefs.max_trades,
    )
    equity = _resolve_equity_plans(trade_date)
    options = _resolve_options_picks(trade_date, options_picks)
    selected = load_selected_symbols(trade_date)
    selected_opt = load_selected_option(trade_date)
    bias = _resolve_market_bias(trade_date, market_bias)
    if not prep_date and equity:
        prep_date = equity[0].prep_date
    return PrintableChecklistContext(
        trade_date=trade_date,
        prep_date=prep_date,
        equity_plans=equity,
        options_picks=options,
        selected_symbols=selected,
        selected_option=selected_opt,
        market_bias=bias,
        gift_nifty_line=_gift_nifty_plain(include_live=include_live_cues),
        allocated_inr=budget.allocated_inr,
        per_trade_inr=budget.per_trade_budget_inr,
        max_risk_pct=prefs.max_risk_pct,
        max_trades=prefs.max_trades,
        total_capital_inr=prefs.capital,
        allocation_pct=prefs.allocation_pct,
        max_loss_day_inr=round(budget.max_risk_per_trade_inr * prefs.max_trades, 0),
    )


def _equity_stock_block(ctx: PrintableChecklistContext) -> list[str]:
    lines: list[str] = []
    selected_set = {s.upper() for s in ctx.selected_symbols}
    for i, p in enumerate(ctx.equity_plans[:5], start=1):
        side = infer_trade_side(p.entry, p.stop_loss, explicit=p.side)
        starred = p.symbol.upper() in selected_set
        hint = equity_position_hint(
            p.symbol,
            p.entry,
            p.stop_loss,
            p.target,
            allocated_inr=ctx.allocated_inr,
            max_risk_pct=ctx.max_risk_pct,
            max_concurrent_trades=ctx.max_trades,
            per_trade_budget_inr=ctx.per_trade_inr,
            side=side,
        )
        sh = hint.suggested_shares if hint.suggested_shares else "___"
        lines.append(
            f"#{i} {p.symbol}  {side}"
            f"{'  ⭐' if starred else ''}"
        )
        lines.append(
            f"   Entry {_blank(p.entry, prefix='₹')}  "
            f"Stop {_blank(p.stop_loss, prefix='₹')}  "
            f"Target {_blank(p.target, prefix='₹')}  ({sh} sh)"
        )
        lines.append(f"   □ Starred" if not starred else "   ☑ Starred")
        lines.append("")
    for n in range(len(ctx.equity_plans) + 1, 6):
        lines.append(f"#{n} __________  LONG/SHORT")
        lines.append("   Entry ₹_____  Stop ₹_____  Target ₹_____  (___ sh)")
        lines.append("   □ Starred")
        lines.append("")
    backup = ctx.equity_plans[2:5]
    if backup:
        names = ", ".join(p.symbol for p in backup)
    else:
        names = "#3 __________   #4 __________   #5 __________"
    lines.append(f"Backup (do NOT trade unless star fails): {names}")
    my2 = ", ".join(ctx.selected_symbols) if ctx.selected_symbols else "__________ , __________"
    lines.append(f"MY 2 TRADES: {my2}")
    return lines


def _option_rows_for_symbol(picks: list[Any], fno_symbol: str) -> list[Any]:
    return [p for p in picks if str(_pick_attr(p, "fno_symbol", default="")).upper() == fno_symbol]


def _format_option_leg(p: Any, *, starred: bool) -> list[str]:
    opt = _pick_attr(p, "option_type", default="")
    strike = _pick_attr(p, "strike", default=0)
    entry = _pick_attr(p, "premium", "entry", default=None)
    stop = _pick_attr(p, "stop_premium", "stop_loss", default=None)
    t1 = _pick_attr(p, "target_premium", "target", default=None)
    t2 = _pick_attr(p, "target2_premium", default=None)
    t3 = _pick_attr(p, "target3_premium", default=None)
    rec = bool(_pick_attr(p, "recommended", default=False))
    ce_mark = "☑" if opt == "CE" and (starred or rec) else "□"
    pe_mark = "☑" if opt == "PE" and (starred or rec) else "□"
    return [
        f"   {ce_mark} CE  {pe_mark} PE   Strike {_blank(strike)}  Prem {_blank(entry, prefix='₹')}",
        f"   Stop {_blank(stop, prefix='₹')}  "
        f"T1 {_blank(t1, prefix='₹')}  "
        f"T2 {_blank(t2, prefix='₹')}  "
        f"T3 {_blank(t3, prefix='₹')}",
        "   ☑ Starred" if starred else "   □ Starred",
    ]


def _options_block(ctx: PrintableChecklistContext) -> list[str]:
    lines: list[str] = []
    for label, sym in (("NIFTY", "NIFTY"), ("BANKNIFTY", "BANKNIFTY")):
        rows = _option_rows_for_symbol(ctx.options_picks, sym)
        lines.append(f"{label}")
        if rows:
            pick = rows[0]
            for extra in rows[1:]:
                if _pick_attr(extra, "recommended", default=False):
                    pick = extra
                    break
            starred = False
            if ctx.selected_option and snap_matches_pick(pick, ctx.selected_option):
                starred = True
            elif _pick_attr(pick, "recommended", default=False) and not ctx.selected_option:
                starred = False
            lines.extend(_format_option_leg(pick, starred=starred))
        else:
            lines.append("   □ CE  □ PE   Strike _____  Prem ₹_____")
            lines.append("   Stop ₹_____  T1 ₹_____  T2 ₹_____  T3 ₹_____")
            lines.append("   □ Starred")
        lines.append("")
    if ctx.selected_option:
        so = ctx.selected_option
        lines.append(
            f"MY OPTION LEG: {so['fno_symbol']} {so['option_type']} {so['strike']:g}"
        )
    else:
        lines.append("MY OPTION LEG: __________ __________ _____")
    return lines


def format_printable_mis_checklist(
    *,
    trade_date: str | None = None,
    prep_date: str = "",
    options_picks: list[Any] | None = None,
    market_bias: str = "",
    include_live_cues: bool = True,
) -> str:
    """Full evening → EOD checklist with levels auto-filled from last prep."""
    ctx = gather_printable_checklist_context(
        trade_date=trade_date,
        prep_date=prep_date,
        options_picks=options_picks,
        market_bias=market_bias,
        include_live_cues=include_live_cues,
    )
    today = datetime.now(IST).strftime("%d/%m/%Y")
    trade_disp = _iso_to_display(ctx.trade_date)
    bias = ctx.market_bias or "___________"

    sections: list[str] = []

    sections.append(f"📋 MIS PREP — {today} (trade date: {trade_disp})")
    sections.append("")
    sections.append("□ App: Suggestions → Prep all tonight")
    sections.append("□ Prep checklist 5/5: Equity · Options · Telegram · 2 trades · MIS checklist")
    sections.append("")
    sections.append(f"BIAS: {bias}  (BULLISH / BEARISH / NEUTRAL)")
    sections.append(f"GIFT NIFTY: {ctx.gift_nifty_line}")
    sections.append("")
    sections.append("━━━ STOCKS (star 2 only) ━━━")
    sections.extend(_equity_stock_block(ctx))
    sections.append("")
    sections.append("━━━ OPTIONS (1 lot each max) ━━━")
    sections.extend(_options_block(ctx))
    sections.append("")
    sections.append("CAPITAL TODAY")
    sections.append(
        f"Total ₹{ctx.total_capital_inr:,.0f}  · MIS pool {ctx.allocation_pct:.0f}%  "
        f"= ₹{ctx.allocated_inr:,.0f}"
    )
    sections.append(f"Max trades: {ctx.max_trades} stocks + 1–2 option lot(s)")
    sections.append(f"Per-trade risk: {ctx.max_risk_pct:g}% max")
    sections.append("")
    sections.append("□ Stop orders planned on Kite before sleep")
    sections.append("□ Phone charged · Kite logged in")
    sections.append("")
    sections.append("─" * 40)
    sections.append("")
    sections.append(f"☀️ OPEN DAY — {trade_disp}")
    sections.append("")
    my2 = ", ".join(ctx.selected_symbols) if ctx.selected_symbols else "________ , ________"
    opt_line = "________ ________ ______"
    if ctx.selected_option:
        so = ctx.selected_option
        opt_line = f"{so['fno_symbol']} {so['option_type']} {so['strike']:g}"
    sections.append("□ Read Telegram morning list (or reopen Suggestions)")
    sections.append(f"□ Confirm my 2 stocks: {my2}")
    sections.append(f"□ Confirm my option: {opt_line}")
    sections.append("")
    sections.append("PRE-MARKET")
    sections.append(
        f"□ Capital unchanged? ₹{ctx.total_capital_inr:,.0f}  "
        f"MIS {ctx.allocation_pct:.0f}%  Max risk {ctx.max_risk_pct:g}%"
    )
    sections.append("□ No new names — only last night's list")
    sections.append("□ Kite margin OK for MIS + F&O")
    sections.append("")
    sections.append("9:15–9:45 = OBSERVE ONLY")
    sections.append("□ Note OR high/low on starred stocks")
    sections.append("□ Note index direction (Nifty / Bank Nifty)")
    sections.append("□ NO entries before 9:45")
    sections.append("")
    sections.append(f"□ Max loss today = ₹{ctx.max_loss_day_inr:,.0f} (2 × risk per trade)")
    sections.append("□ If 2 stops hit → done for the day")
    sections.append("")
    sections.append("─" * 40)
    sections.append("")
    sections.append("⏱️ IN TRADE CHECKLIST")
    sections.append("")
    sections.append("BEFORE EVERY ENTRY:")
    sections.append("□ Symbol on tonight's starred list?")
    sections.append("□ Price near Entry (not chasing)?")
    sections.append("□ Stop distance OK for my size?")
    sections.append("□ Place STOP on Kite FIRST, then entry")
    sections.append("")
    sections.append("STOCKS")
    for i, sym in enumerate((ctx.selected_symbols + ["________", "________"])[:2], start=1):
        sections.append(f"□ Trade {i}: {sym}  Entry ₹_____  Stop ₹_____")
    sections.append("□ At T1: book 40–50%, trail stop to breakeven")
    sections.append("")
    sections.append("OPTIONS")
    sections.append("□ Re-scan CE/PE after 9:46 (post-OR)")
    sections.append("□ PE only if index ≤ OR low · CE only if ≥ OR high")
    sections.append("□ Skip strike if >3.5% OTM vs spot")
    sections.append("□ Only starred CE/PE from prep")
    sections.append("□ 1 lot · premium levels (not index spot)")
    sections.append("□ Trail per ladder (T1 → T2 → T3)")
    sections.append("")
    sections.append("HARD RULES")
    sections.append("□ No tips from groups / random scans")
    sections.append("□ No revenge trades")
    sections.append("□ 3:20 PM — SQUARE OFF ALL MIS + OPTIONS")
    sections.append("")
    sections.append("─" * 40)
    sections.append("")
    sections.append(f"📊 EOD — {trade_disp}")
    sections.append("")
    sections.append("□ App → Score today's picks")
    sections.append("□ Stocks: hit target? ___ / 2")
    sections.append("□ Options: hit T1/T2? ___")
    sections.append("")
    sections.append("QUICK JOURNAL (1 line each):")
    sections.append("Stock 1: ________  → W / L / BE  ₹_____")
    sections.append("Stock 2: ________  → W / L / BE  ₹_____")
    sections.append("Option:  ________  → W / L / BE  ₹_____")
    sections.append("")
    sections.append("□ Check hit rate (30d) on Track Record")
    sections.append("□ Tomorrow: Prep all tonight again")
    sections.append("")
    sections.append("─" * 40)
    sections.append(
        "🌙 3:45 PM — Prep all tonight → star 2 stocks + 1 option. "
        "☀️ 9:45+ trade starred only. 🔴 3:20 square off."
    )
    return "\n".join(sections)
