"""Telegram formatting for pinned / watchlist picks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from analyzer.trade_ladder import build_equity_ladder, build_options_ladder, format_equity_ladder_telegram, format_options_ladder_telegram
from analyzer.watchlist_pins import PinnedPlan, infer_trade_side

if TYPE_CHECKING:
    from analyzer.options_expiry_watchlist import OptionsExpiryPick
    from analyzer.options_watchlist_history import OptionsWatchlistSnapshot


def _equity_sizing_context() -> tuple[float, float, float, int]:
    from analyzer.intraday_beginner_tips import build_capital_budget
    from analyzer.intraday_prefs import load_intraday_prefs

    prefs = load_intraday_prefs()
    budget = build_capital_budget(
        prefs.capital,
        allocation_pct=prefs.allocation_pct,
        max_risk_pct=prefs.max_risk_pct,
        max_concurrent_trades=prefs.max_trades,
    )
    return (
        budget.allocated_inr,
        budget.per_trade_budget_inr,
        prefs.max_risk_pct,
        prefs.max_trades,
    )


def _format_equity_pick_line(
    p: PinnedPlan,
    index: int,
    *,
    selected: bool = False,
    with_shares: bool = True,
) -> str:
    from analyzer.trade_selection import is_selected
    from analyzer.watchlist_position_size import equity_position_hint

    mark = "⭐ " if (selected or is_selected(p.symbol)) else ""
    trade_side = infer_trade_side(p.entry, p.stop_loss, explicit=p.side)
    size_bit = ""
    if with_shares:
        allocated, per_trade, max_risk, max_trades = _equity_sizing_context()
        hint = equity_position_hint(
            p.symbol,
            p.entry,
            p.stop_loss,
            p.target,
            allocated_inr=allocated,
            max_risk_pct=max_risk,
            max_concurrent_trades=max_trades,
            per_trade_budget_inr=per_trade,
            side=trade_side,
        )
        if hint.suggested_shares:
            size_bit = f" · **{hint.suggested_shares} sh**"
        elif hint.skip_reason:
            size_bit = " · _skip size_"
    ladder = build_equity_ladder(trade_side, p.entry, p.stop_loss, p.target)
    side_tag = "SHORT" if trade_side == "SHORT" else "LONG"
    return (
        f"*{index}. {mark}{p.symbol}* ({side_tag}){size_bit}\n"
        f"Entry ₹{p.entry:,.0f} · Stop ₹{p.stop_loss:,.0f}\n"
        f"{format_equity_ladder_telegram(ladder)}"
    )


def format_pinned_watchlist_telegram(
    picks: list[PinnedPlan],
    *,
    market_bias: str = "",
    prep_date: str = "",
    with_shares: bool = True,
) -> str:
    if not picks:
        return "*Watchlist* — no top picks yet."

    lines = ["*🌙 Top MIS picks — tomorrow*"]
    if prep_date:
        lines.append(f"Prep date: {prep_date}")
    if market_bias:
        lines.append(f"Bias: *{market_bias}*")
    lines.append("")

    for i, p in enumerate(picks, start=1):
        lines.append(_format_equity_pick_line(p, i, with_shares=with_shares))

    lines.append("")
    lines.append("_Trade only these. Stop on Kite first. Not financial advice._")
    return "\n".join(lines)


def format_options_watchlist_telegram(
    picks: list["OptionsExpiryPick"] | list["OptionsWatchlistSnapshot"],
    *,
    prep_date: str = "",
    stars_only: bool = False,
) -> str:
    """Format Nifty / Bank Nifty CE/PE rows for Telegram."""
    if stars_only:
        picks = [p for p in picks if getattr(p, "recommended", False)]
    if not picks:
        return "*Options expiry* — no CE/PE picks yet."

    lines = ["*📅 Options expiry — CE/PE*"]
    if prep_date:
        lines.append(f"Prep date: {prep_date}")
    lines.append("")

    for p in picks:
        star = "★ " if getattr(p, "recommended", False) else ""
        fno = getattr(p, "fno_symbol", "")
        opt = getattr(p, "option_type", "")
        strike = getattr(p, "strike", 0)
        entry = getattr(p, "premium", None) or getattr(p, "entry", 0)
        stop = getattr(p, "stop_premium", None) or getattr(p, "stop_loss", 0)
        target = getattr(p, "target_premium", None) or getattr(p, "target", 0)
        t2 = getattr(p, "target2_premium", None)
        t3 = getattr(p, "target3_premium", None)
        if entry and t2 and t3:
            ol = build_options_ladder(
                float(entry),
                stop_mult=(stop / entry) if stop and entry else 0.65,
                target_mults=(target / entry, t2 / entry, t3 / entry),
            )
            ladder_line = (
                f"T1 ₹{target:,.2f} → T2 ₹{t2:,.2f} → T3 ₹{t3:,.2f} (40/30/30%)\n"
                f"{format_options_ladder_telegram(ol).split(chr(10), 1)[-1]}"
            )
        elif entry:
            ol = build_options_ladder(float(entry))
            ladder_line = format_options_ladder_telegram(ol)
        else:
            ladder_line = f"Stop ₹{stop:,.2f} · T1 ₹{target:,.2f}"
        lines.append(
            f"*{fno} {star}{opt} {strike:g}*\n"
            f"Prem ₹{entry:,.2f} · {ladder_line}"
        )

    lines.append("")
    lines.append("_★ = signal side · Square off by 3:20 PM. Not financial advice._")
    return "\n".join(lines)


def format_combined_prep_telegram(
    equity_plans: list[PinnedPlan],
    options_picks: list["OptionsExpiryPick"] | list["OptionsWatchlistSnapshot"],
    *,
    market_bias: str = "",
    prep_date: str = "",
    with_gift_nifty: bool = True,
) -> str:
    """Single Telegram message: equity top 5 + options CE/PE."""
    from analyzer.gift_nifty import format_gift_nifty_telegram_line

    lines = ["*🌙 MIS prep — tomorrow*"]
    if prep_date:
        lines.append(f"Prep date: {prep_date}")
    if market_bias:
        lines.append(f"Bias: *{market_bias}*")
    if with_gift_nifty:
        lines.append(format_gift_nifty_telegram_line())
    lines.append("")

    if equity_plans:
        lines.append("*Equity (top 5)*")
        for i, p in enumerate(equity_plans, start=1):
            lines.append(_format_equity_pick_line(p, i, with_shares=True))
    else:
        lines.append("_No equity picks — run Quick scan._")

    lines.append("")
    if options_picks:
        lines.append("*Options expiry (CE/PE)*")
        try:
            from analyzer.options_trade_selection import load_selected_option, snap_matches_pick

            selected_opt = load_selected_option(prep_date or None)
        except Exception:
            selected_opt = None
        shown = options_picks
        if selected_opt:
            shown = [p for p in options_picks if snap_matches_pick(p, selected_opt)]
        if not shown:
            shown = [p for p in options_picks if getattr(p, "recommended", False)] or options_picks[:1]
        for p in shown:
            star = "★ " if getattr(p, "recommended", False) else ""
            fno = getattr(p, "fno_symbol", "")
            opt = getattr(p, "option_type", "")
            strike = getattr(p, "strike", 0)
            entry = getattr(p, "premium", None) or getattr(p, "entry", 0)
            stop = getattr(p, "stop_premium", None) or getattr(p, "stop_loss", 0)
            target = getattr(p, "target_premium", None) or getattr(p, "target", 0)
            t2 = getattr(p, "target2_premium", None)
            t3 = getattr(p, "target3_premium", None)
            if entry and t2 and t3:
                ol = build_options_ladder(
                    float(entry),
                    stop_mult=(stop / entry) if stop and entry else 0.65,
                    target_mults=(target / entry, t2 / entry, t3 / entry),
                )
                lines.append(
                    f"*{fno} {star}{opt} {strike:g}*\n"
                    f"Prem ₹{entry:,.2f}\n{format_options_ladder_telegram(ol)}"
                )
            else:
                lines.append(
                    f"*{fno} {star}{opt} {strike:g}*\n"
                    f"Prem ₹{entry:,.2f} · Stop ₹{stop:,.2f} · Target ₹{target:,.2f}"
                )
    else:
        lines.append("_No options CE/PE loaded._")

    selected = []
    try:
        from analyzer.trade_selection import load_selected_symbols

        selected = load_selected_symbols()
    except Exception:
        pass
    if selected:
        lines.append("")
        lines.append(f"_Your 2 trades: **{', '.join(selected)}**_")
    try:
        from analyzer.options_trade_selection import load_selected_option

        opt = load_selected_option(prep_date or None)
        if opt:
            lines.append(
                f"_Your option: **{opt['fno_symbol']} {opt['option_type']} {opt['strike']:g}**_"
            )
    except Exception:
        pass

    lines.append("")
    lines.append(
        "_Trade only these · Stop on Kite first · Square off 3:20 PM. Not financial advice._"
    )
    return "\n".join(lines)
