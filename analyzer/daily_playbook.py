"""Personalized step-by-step daily MIS guide — beginner-safe, equity-first."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.context_engine import build_context_snapshot
from analyzer.context_engine.migration import regime_from_snapshot
from analyzer.intraday_beginner_tips import build_capital_budget
from analyzer.intraday_prefs import IntradayPrefs, load_intraday_prefs
from analyzer.intraday_trade_plan import build_intraday_trade_plan
from analyzer.mis_trade_advisory import build_mis_trade_advisory, recent_loss_streak_days
from analyzer.trade_selection import load_selected_symbols
from analyzer.watchlist_history import session_target_date
from analyzer.watchlist_pins import load_pinned_plans

IST = ZoneInfo("Asia/Kolkata")

WEALTH_GOAL_DEFAULT_INR = 10_00_00_000.0


@dataclass
class PlaybookStep:
    id: str
    window: str
    title: str
    action: str
    skip_if: str = ""
    is_current: bool = False
    status: str = "pending"  # pending | current | done | blocked
    emoji: str = "⬜"


@dataclass
class DailyPlaybook:
    trade_date: str
    phase: str
    headline: str
    next_step: str
    daily_profit_target_inr: float
    max_loss_inr: float
    equity_only: bool
    beginner_mode: bool
    wealth_goal_inr: float
    focus_symbol: str
    can_trade_today: bool
    verdict: str
    steps: list[PlaybookStep] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _focus_equity_pick() -> tuple[str, float, float, float, bool, str]:
    """Best equity name to focus today with plan gate."""
    selected = load_selected_symbols()
    pinned = load_pinned_plans()
    sym = ""
    entry = stop = target = 0.0
    if selected:
        sym = selected[0]
        for p in pinned:
            if p.symbol.upper() == sym.upper():
                entry, stop, target = p.entry, p.stop_loss, p.target
                break
    elif pinned:
        p = pinned[0]
        sym, entry, stop, target = p.symbol, p.entry, p.stop_loss, p.target
    if not sym:
        return "", 0.0, 0.0, 0.0, False, "No starred stock — auto-pick from watchlist tonight."

    prefs = load_intraday_prefs()
    plan = build_intraday_trade_plan(
        "BUY", entry, stop, target,
        account_inr=prefs.capital,
        max_risk_pct=prefs.max_risk_pct,
    )
    skip = plan.skip_reason or ""
    return sym, entry, stop, target, plan.can_enter, skip


def _step_status(
    step_id: str,
    *,
    phase: str,
    timing_phase: str,
    can_enter: bool,
    equity_only: bool,
) -> tuple[bool, str]:
    """Return (is_current, status) for a step."""
    current_map = {
        "night_capital": ("weekend", "after_hours", "pre_open"),
        "morning_verdict": ("pre_open",),
        "observe_or": ("opening",),
        "equity_enter": ("core",),
        "manage_trade": ("core",),
        "book_profit": ("core", "wind_down"),
        "no_new_risk": ("wind_down",),
        "square_off": ("square_off",),
        "journal": ("after_hours",),
        "options_gate": (),
    }
    is_current = timing_phase in current_map.get(step_id, ())
    status = "current" if is_current else "pending"
    if step_id == "options_gate" and equity_only:
        return False, "blocked"
    if step_id == "equity_enter" and not can_enter and timing_phase == "core":
        status = "blocked"
    return is_current, status


def build_daily_playbook(
    *,
    market: str = "india",
    now: datetime | None = None,
    prefs: IntradayPrefs | None = None,
) -> DailyPlaybook:
    """One guided routine: realistic daily profit target + ordered steps."""
    now = now or datetime.now(IST)
    prefs = prefs or load_intraday_prefs()
    ctx = build_context_snapshot(market=market, now=now)
    session = dict(ctx.market_session)
    timing_phase = str(ctx.metadata.get("timing_phase", ctx.market_phase))
    allow_entries = bool(ctx.metadata.get("allow_new_entries", False))
    timing_headline = ctx.trading_restrictions[0] if ctx.trading_restrictions else ctx.market_phase
    regime = regime_from_snapshot(ctx)
    regime_name = regime.regime if regime else ctx.market_regime
    adv = build_mis_trade_advisory(market=market, now=now)
    budget = build_capital_budget(
        prefs.capital,
        allocation_pct=prefs.allocation_pct,
        max_risk_pct=prefs.max_risk_pct,
        max_concurrent_trades=1 if prefs.beginner_mode else prefs.max_trades,
    )

    equity_only = prefs.equity_only
    daily_target = round(prefs.capital * prefs.min_daily_profit_pct / 100, 0)
    max_loss = budget.max_risk_per_trade_inr
    sym, entry, stop, target, can_enter, plan_note = _focus_equity_pick()
    loss_streak = recent_loss_streak_days()

    can_trade = (
        allow_entries
        and loss_streak < 2
        and adv.verdict != "NO_TRADE"
        and session.get("is_open", False)
    )
    if equity_only and regime_name == "Range-bound":
        can_trade = can_trade and can_enter

    warnings: list[str] = []
    if loss_streak >= 1:
        warnings.append(f"{loss_streak} loss day(s) logged — max 1 trade, ₹{max_loss:.0f} risk cap.")
    if not equity_only and regime_name == "Range-bound":
        warnings.append("Range-bound chop — equity only recommended until ADX ≥ 15.")
    if equity_only:
        warnings.append("Equity-only mode ON — skip all index CE/PE today.")

    focus_line = (
        f"**{sym}** E ₹{entry:,.2f} · S ₹{stop:,.2f} · T ₹{target:,.2f}"
        if sym else "Star 1 stock in watchlist tonight."
    )
    enter_line = (
        "Coach says **ENTER** — stop on Kite first, then buy."
        if can_enter
        else f"Coach says **WAIT** — {plan_note or 'plan not ready'}"
    )

    raw_steps: list[tuple[str, str, str, str, str]] = [
        (
            "night_capital",
            "Night / weekend",
            "Confirm capital & mode",
            f"Capital **₹{prefs.capital:,.0f}** · mode **{prefs.profit_mode}** · "
            f"today's realistic goal **+₹{daily_target:,.0f}** (+{prefs.min_daily_profit_pct:.0f}%), "
            f"not +5% revenge.",
            "",
        ),
        (
            "morning_verdict",
            "8:30–9:14 AM",
            "Read today's verdict",
            f"Open Suggestions → **Trade / No trade**: {adv.emoji} **{adv.headline}**. "
            f"If NO_TRADE or equity WAIT → sit out.",
            "",
        ),
        (
            "observe_or",
            "9:15–9:45 AM",
            "Observe opening range only",
            f"Watch **{sym or 'starred stock'}** — note OR high/low. **No buy yet.**",
            "",
        ),
        (
            "equity_enter",
            "9:46–11:30 AM",
            "One equity trade only (if green)",
            f"{focus_line}. {enter_line}. Risk cap **₹{max_loss:.0f}**.",
            "Skip if WAIT or NO_TRADE",
        ),
        (
            "manage_trade",
            "While in trade",
            "Manage with written plan",
            "If stop hit → exit. If target hit → book **50%**, trail rest to breakeven. "
            "Never move stop away from you.",
            "",
        ),
        (
            "book_profit",
            "Any time in profit",
            "Book when target hits",
            f"Goal **+₹{daily_target:,.0f}** for the day — take it when plan target hits; "
            "don't wait for home runs.",
            "",
        ),
        (
            "no_new_risk",
            "After 2:00 PM",
            "No new trades",
            "Manage open position only. Theta and chop kill late entries.",
            "",
        ),
        (
            "square_off",
            "3:15–3:20 PM",
            "Square off everything",
            "Close **all** MIS on Kite — stocks and any legacy options.",
            "",
        ),
        (
            "journal",
            "After 3:30 PM",
            "Log result + one lesson",
            "Track Record → journal: symbol, P&L, mistake, fix. Builds loss-streak alerts.",
            "",
        ),
        (
            "options_gate",
            "Options (advanced only)",
            "Options only if equity-only OFF + gate green",
            "CE if spot ≥ OR high · PE if spot ≤ OR low · lot ≤ 40% capital · SL before entry.",
            "Skip in equity-only / beginner mode",
        ),
    ]

    steps: list[PlaybookStep] = []
    next_step = ""
    for sid, window, title, action, skip_if in raw_steps:
        is_current, status = _step_status(
            sid,
            phase=session.get("phase", ""),
            timing_phase=timing_phase,
            can_enter=can_enter,
            equity_only=equity_only,
        )
        emoji = "⬜"
        if status == "current":
            emoji = "👉"
            if not next_step:
                next_step = f"{title} — {action}"
        elif status == "blocked":
            emoji = "🚫"
        steps.append(
            PlaybookStep(
                id=sid,
                window=window,
                title=title,
                action=action,
                skip_if=skip_if,
                is_current=is_current,
                status=status,
                emoji=emoji,
            )
        )

    if not next_step:
        if timing_phase == "after_hours":
            next_step = "Session over — log journal and review Track Record."
        elif timing_phase == "weekend":
            next_step = "Market closed — run Quick scan tonight for Monday picks."
        else:
            next_step = timing_headline

    rules = [
        f"Daily profit **goal** ₹{daily_target:,.0f} · max loss **₹{max_loss:.0f}** (not guaranteed — process first).",
        "1 trade max until 2 green journal days.",
        "Only ENTER when coach says ENTER — WAIT means skip.",
        f"₹10 Cr path: SIP + compounding; MIS pool stays small (₹{prefs.capital:,.0f}).",
    ]

    return DailyPlaybook(
        trade_date=session_target_date(now),
        phase=timing_phase,
        headline=timing_headline,
        next_step=next_step,
        daily_profit_target_inr=daily_target,
        max_loss_inr=max_loss,
        equity_only=equity_only,
        beginner_mode=prefs.beginner_mode,
        wealth_goal_inr=prefs.wealth_goal_inr,
        focus_symbol=sym,
        can_trade_today=can_trade,
        verdict=adv.verdict,
        steps=steps,
        rules=rules,
        warnings=warnings,
    )


def format_playbook_text(playbook: DailyPlaybook) -> str:
    """Plain-text guide for terminal / Telegram."""
    lines = [
        f"📋 Daily playbook — {playbook.trade_date}",
        f"Phase: {playbook.phase} · {playbook.headline}",
        "",
        f"👉 NEXT: {playbook.next_step}",
        "",
        f"Goal today: +₹{playbook.daily_profit_target_inr:,.0f} · Max loss: ₹{playbook.max_loss_inr:,.0f}",
        f"Focus: {playbook.focus_symbol or '—'} · Trade today? {'YES' if playbook.can_trade_today else 'NO'}",
        "",
        "Steps:",
    ]
    for s in playbook.steps:
        if s.status == "blocked":
            lines.append(f"  🚫 [{s.window}] {s.title} — SKIP ({s.skip_if})")
        else:
            mark = "👉" if s.is_current else s.emoji
            lines.append(f"  {mark} [{s.window}] {s.title}")
            lines.append(f"      {s.action}")
    if playbook.warnings:
        lines.append("")
        lines.append("Warnings:")
        for w in playbook.warnings:
            lines.append(f"  ⚠ {w}")
    lines.append("")
    lines.append("Rules:")
    for r in playbook.rules:
        lines.append(f"  • {r}")
    return "\n".join(lines)
