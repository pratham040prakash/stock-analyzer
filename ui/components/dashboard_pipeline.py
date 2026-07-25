"""Shared loader → DTO helpers for Home dashboard data-flow restoration (P0)."""

from __future__ import annotations

from typing import Any

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.watchlist_pins import PinnedPlan
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult


def decision_reason(decision: DecisionArtifact | None) -> str:
    if not decision:
        return ""
    explain = decision.explainability
    if explain and explain.why:
        return str(explain.why).strip()
    return str(decision.reason or "").strip()


def is_equity_decision(artifact: object | None) -> bool:
    if artifact is None:
        return False
    subject_type = str(getattr(artifact, "subject_type", "equity") or "equity").lower()
    return subject_type == "equity"


def portfolio_metrics(
    portfolio: ZerodhaImportResult | None,
    prefs: IntradayPrefs,
    *,
    journal_today_pnl: float | None,
) -> dict[str, Any]:
    holdings = portfolio.holdings if portfolio and portfolio.holdings else []
    invested = 0.0
    unrealized = 0.0
    allocation: list[tuple[str, float]] = []
    for holding in holdings:
        ltp = holding.last_price or holding.average_price or 0.0
        value = float(holding.quantity or 0) * float(ltp)
        invested += value
        if holding.pnl is not None:
            unrealized += float(holding.pnl)
        if value > 0:
            allocation.append((holding.tradingsymbol or holding.kite_symbol or "", value))
    allocation.sort(key=lambda item: item[1], reverse=True)
    capital = float(prefs.capital or 0)
    exposure_pct = round(100.0 * invested / capital, 1) if capital > 0 else None
    alloc_lines = []
    total = invested or 1.0
    for sym, val in allocation[:4]:
        alloc_lines.append(f"{sym} {100.0 * val / total:.0f}%")
    return {
        "today_pnl": journal_today_pnl if journal_today_pnl is not None else unrealized,
        "today_pnl_source": "journal" if journal_today_pnl is not None else "holdings",
        "exposure_pct": exposure_pct,
        "allocation": alloc_lines,
        "holding_count": len(holdings),
    }


def portfolio_health_label(
    snapshot: ContextSnapshot,
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
) -> tuple[str, str]:
    """Return (label, detail) from engine outputs — no synthetic score."""
    risk_mod = os_report.module("risk")
    flag_count = len(mis.flags or ())
    mode = snapshot.risk_mode or "NEUTRAL"

    if mode == "CLOSED" or (risk_mod and risk_mod.status in ("warn", "off")):
        label = "High Risk"
    elif mode == "RISK-OFF" or flag_count >= 2 or (risk_mod and risk_mod.status == "wait"):
        label = "Needs Review"
    else:
        label = "Healthy"

    detail = risk_mod.headline if risk_mod and risk_mod.headline else os_report.next_step
    if not detail and mis.flags:
        detail = mis.flags[0]
    if not detail:
        detail = f"Market is {mode.lower().replace('_', ' ')} — stay within your plan."
    return label, str(detail)


def holding_extremes(holdings: list[ZerodhaHolding]) -> tuple[str, str]:
    scored: list[tuple[str, float]] = []
    for holding in holdings:
        if holding.pnl is None or not holding.average_price or not holding.quantity:
            continue
        cost = float(holding.average_price) * float(holding.quantity)
        if cost <= 0:
            continue
        pct = 100.0 * float(holding.pnl) / cost
        scored.append((holding.tradingsymbol or holding.kite_symbol or "—", pct))
    if not scored:
        return "—", "—"
    scored.sort(key=lambda item: item[1])
    weakest = f"{scored[0][0]} ({scored[0][1]:+.1f}%)"
    strongest = f"{scored[-1][0]} ({scored[-1][1]:+.1f}%)"
    return weakest, strongest


def fmt_inr(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "—"
    if signed:
        return f"{'+' if value >= 0 else ''}₹{value:,.0f}"
    return f"₹{value:,.0f}"


def watch_bullets(
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
    *,
    opportunity_tickers: list[tuple[str, float]],
    pins: list[PinnedPlan],
) -> list[str]:
    """Pre-0240c3f watch list — flags, restrictions, staged entries."""
    bullets: list[str] = []
    for flag in (mis.flags or ())[:2]:
        bullets.append(str(flag).strip())
    for restriction in snapshot.trading_restrictions[:2]:
        if restriction not in bullets:
            bullets.append(str(restriction).strip())
    for ticker, entry in opportunity_tickers[:2]:
        line = f"{ticker} — watch entry near ₹{entry:,.0f}"
        if line not in bullets:
            bullets.append(line)
    if not bullets and pins:
        pin = pins[0]
        sym = pin.symbol.upper().replace(".NS", "")
        bullets.append(f"{sym} — plan entry ₹{pin.entry:,.0f}, stop ₹{pin.stop_loss:,.0f}")
    if not bullets:
        bullets.append("No urgent items — stick to your trade plan.")
    return bullets[:3]
