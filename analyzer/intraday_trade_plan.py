"""
Intraday entry & exit discipline — exits planned before entry.

Aligns with day-trading practice: define stop and target before the trade,
partial profit at target, trail remainder to breakeven, skip if risk is too wide.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from analyzer.trade_ladder import build_equity_ladder, ladder_exit_rules

MIN_RISK_REWARD = 1.5
DEFAULT_MAX_RISK_PCT = 1.0
PARTIAL_EXIT_FRACTION = 0.5
MAX_STOP_PCT_WITHOUT_ACCOUNT = 2.5  # skip if stop wider than this without capital input

BUY_ACTIONS = frozenset({"STRONG BUY", "BUY"})
SELL_ACTIONS = frozenset({"STRONG SELL", "SELL"})


@dataclass
class IntradayTradePlan:
    side: str  # LONG | SHORT | FLAT
    entry: float | None
    stop_loss: float | None
    target: float | None
    partial_exit_fraction: float
    breakeven_stop: float | None
    risk_per_share: float | None
    reward_per_share: float | None
    risk_reward_ratio: float | None
    risk_pct_of_price: float | None
    suggested_shares: int | None
    max_loss_inr: float | None
    can_enter: bool
    skip_reason: str | None
    entry_rules: list[str] = field(default_factory=list)
    exit_rules: list[str] = field(default_factory=list)
    summary: str = ""


def _side_from_action(action: str) -> str:
    if action in BUY_ACTIONS:
        return "LONG"
    if action in SELL_ACTIONS:
        return "SHORT"
    return "FLAT"


def build_intraday_trade_plan(
    action: str,
    entry: float | None,
    stop_loss: float | None,
    target: float | None,
    *,
    account_inr: float | None = None,
    max_risk_pct: float = DEFAULT_MAX_RISK_PCT,
    entry_reasons: list[str] | None = None,
) -> IntradayTradePlan:
    """Build entry checklist + exit rules; block trade if risk is too large."""
    side = _side_from_action(action)
    empty = IntradayTradePlan(
        side="FLAT",
        entry=None,
        stop_loss=None,
        target=None,
        partial_exit_fraction=PARTIAL_EXIT_FRACTION,
        breakeven_stop=None,
        risk_per_share=None,
        reward_per_share=None,
        risk_reward_ratio=None,
        risk_pct_of_price=None,
        suggested_shares=None,
        max_loss_inr=None,
        can_enter=False,
        skip_reason=None,
        summary="Stay flat — no MIS entry until setup is clear.",
    )

    if side == "FLAT" or entry is None or stop_loss is None or target is None:
        rules = [
            "Wait for a clear signal (VWAP hold, opening-range break, or strong candle).",
            "Do not enter without a written stop loss and profit target.",
        ]
        empty.entry_rules = rules
        empty.exit_rules = [
            "No open position — square off any legacy MIS before **3:20 PM IST**.",
        ]
        if action == "WAIT":
            empty.skip_reason = "No entry signal — mixed candles or inside opening range."
        else:
            empty.skip_reason = "Levels incomplete — wait for OR/VWAP-based stop and target."
        return empty

    risk = abs(entry - stop_loss)
    reward = abs(target - entry)
    if risk <= 0:
        empty.skip_reason = "Invalid stop — risk per share is zero."
        return empty

    rr = round(reward / risk, 2)
    risk_pct = round(risk / entry * 100, 2)

    entry_rules: list[str] = []
    if entry_reasons:
        entry_rules.extend(f"Signal: {r}" for r in entry_reasons[:4])
    entry_rules.append(
        f"Entry only if price is near **₹{entry:,.2f}** with stop **₹{stop_loss:,.2f}** already set."
    )
    if rr >= MIN_RISK_REWARD:
        entry_rules.append(f"Reward/risk **{rr:.1f}×** (≥ {MIN_RISK_REWARD}× minimum).")
    else:
        entry_rules.append(f"Reward/risk **{rr:.1f}×** — below {MIN_RISK_REWARD}×; prefer wider target or tighter stop.")

    exit_rules = ladder_exit_rules(
        build_equity_ladder(side, entry, stop_loss, target),
    )

    can_enter = True
    skip_reason = None
    suggested_shares = None
    max_loss_inr = None

    if rr < MIN_RISK_REWARD:
        can_enter = False
        skip_reason = (
            f"Risk/reward {rr:.1f}× is under {MIN_RISK_REWARD}× — widen target or tighten stop before entering."
        )

    if account_inr is not None and account_inr > 0 and max_risk_pct > 0:
        max_loss_inr = round(account_inr * max_risk_pct / 100, 0)
        suggested_shares = int(max_loss_inr // risk)
        if suggested_shares < 1:
            can_enter = False
            skip_reason = (
                f"Stop distance ₹{risk:,.2f}/share exceeds your **{max_risk_pct:.1f}%** risk budget "
                f"(₹{max_loss_inr:,.0f} on ₹{account_inr:,.0f} capital) — skip or use smaller size on options."
            )
        else:
            entry_rules.append(
                f"Size hint: max **{suggested_shares}** shares to keep loss near **₹{max_loss_inr:,.0f}** "
                f"({max_risk_pct:.1f}% of capital)."
            )
    elif risk_pct > MAX_STOP_PCT_WITHOUT_ACCOUNT:
        can_enter = False
        skip_reason = (
            f"Stop is **{risk_pct:.1f}%** from entry — very wide for MIS. "
            "Add trading capital in sidebar or wait for a tighter setup."
        )

    summary = (
        f"**{'Enter LONG' if side == 'LONG' else 'Enter SHORT'}** only with exits pre-written. "
        f"Risk **₹{risk:,.2f}/share** · Target **₹{reward:,.2f}/share** · R:R **{rr:.1f}×**."
    )
    if not can_enter and skip_reason:
        summary = f"**Do not enter** — {skip_reason}"

    return IntradayTradePlan(
        side=side,
        entry=entry,
        stop_loss=stop_loss,
        target=target,
        partial_exit_fraction=PARTIAL_EXIT_FRACTION,
        breakeven_stop=entry,
        risk_per_share=round(risk, 2),
        reward_per_share=round(reward, 2),
        risk_reward_ratio=rr,
        risk_pct_of_price=risk_pct,
        suggested_shares=suggested_shares,
        max_loss_inr=max_loss_inr,
        can_enter=can_enter,
        skip_reason=skip_reason,
        entry_rules=entry_rules,
        exit_rules=exit_rules,
        summary=summary,
    )


def discipline_intro() -> str:
    return (
        "**Exits before entries:** know your stop and target before you buy or sell. "
        "At T1/T2/T3 book **40% / 30% / 30%** and ratchet stop (breakeven → T1 → T2). "
        "Skip the trade if the stop is too wide for your risk budget."
    )
