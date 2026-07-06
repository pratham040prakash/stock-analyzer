"""Position size hints for equity watchlist picks (capital + stop distance)."""

from __future__ import annotations

from dataclasses import dataclass

from analyzer.intraday_trade_plan import build_intraday_trade_plan


@dataclass
class EquityPositionHint:
    symbol: str
    suggested_shares: int | None
    max_loss_inr: float | None
    risk_per_share: float | None
    can_enter: bool
    skip_reason: str | None
    label: str
    per_trade_budget_inr: float | None = None


def equity_position_hint(
    symbol: str,
    entry: float,
    stop_loss: float,
    target: float,
    *,
    allocated_inr: float,
    max_risk_pct: float = 1.0,
    max_concurrent_trades: int = 2,
    per_trade_budget_inr: float | None = None,
) -> EquityPositionHint:
    """
    Shares sized by risk budget (% of MIS pool) and capped by per-trade capital slot.
    """
    slots = max(1, max_concurrent_trades)
    per_trade = per_trade_budget_inr
    if per_trade is None:
        per_trade = round(allocated_inr / slots, 0)

    plan = build_intraday_trade_plan(
        "BUY",
        entry,
        stop_loss,
        target,
        account_inr=allocated_inr,
        max_risk_pct=max_risk_pct,
    )

    suggested = plan.suggested_shares
    can_enter = plan.can_enter
    skip_reason = plan.skip_reason

    if suggested and entry > 0 and per_trade > 0:
        cap_shares = int(per_trade // entry)
        if cap_shares < 1:
            can_enter = False
            skip_reason = (
                f"Per-trade budget **₹{per_trade:,.0f}** cannot buy 1 share at **₹{entry:,.0f}**."
            )
            suggested = None
        else:
            suggested = min(suggested, cap_shares)

    max_loss = plan.max_loss_inr
    if suggested and plan.risk_per_share:
        max_loss = round(suggested * plan.risk_per_share, 0)

    if suggested and max_loss:
        label = f"{suggested} sh · risk ₹{max_loss:,.0f}"
    elif skip_reason:
        label = "Skip"
    else:
        label = "—"

    return EquityPositionHint(
        symbol=symbol,
        suggested_shares=suggested,
        max_loss_inr=max_loss,
        risk_per_share=plan.risk_per_share,
        can_enter=can_enter,
        skip_reason=skip_reason,
        label=label,
        per_trade_budget_inr=per_trade,
    )


def equity_hint_from_budget(
    symbol: str,
    entry: float,
    stop_loss: float,
    target: float,
    budget,
) -> EquityPositionHint:
    """Build hint from IntradayCapitalBudget + prefs-like object."""
    return equity_position_hint(
        symbol,
        entry,
        stop_loss,
        target,
        allocated_inr=budget.allocated_inr,
        max_risk_pct=budget.max_risk_pct,
        max_concurrent_trades=budget.max_concurrent_trades,
        per_trade_budget_inr=budget.per_trade_budget_inr,
    )


def format_entry_status(
    pick,
    hint: EquityPositionHint,
) -> str:
    """Human-readable enter/skip status for the watchlist table."""
    if hint.can_enter and getattr(pick, "can_enter", True):
        return "✅ OK"
    reason = hint.skip_reason
    if not reason and not getattr(pick, "can_enter", True):
        summary = getattr(pick, "plan_summary", "") or ""
        reason = summary.replace("**Do not enter** — ", "").replace("**", "")
    if reason:
        clean = reason.replace("**", "").strip()
        if len(clean) > 72:
            clean = clean[:69] + "…"
        return f"Skip: {clean}"
    return "Skip"


def format_shares_cell(hint: EquityPositionHint) -> str:
    if hint.suggested_shares and hint.suggested_shares > 0:
        return str(hint.suggested_shares)
    if hint.skip_reason:
        return "Skip"
    return "—"


def format_risk_cell(hint: EquityPositionHint) -> str:
    if hint.max_loss_inr is not None and hint.suggested_shares:
        return f"₹{hint.max_loss_inr:,.0f}"
    return "—"
