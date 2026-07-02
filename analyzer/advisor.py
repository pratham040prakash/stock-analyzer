"""Comprehensive investment advisor — synthesizes all analysis into actionable suggestions."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from analyzer.combined import CombinedResult
from analyzer.market_pulse import IndexPulse
from analyzer.relative_strength import RelativeStrengthResult
from analyzer.varsity_knowledge import (
    ANALYSIS_PRINCIPLES,
    MIN_RISK_REWARD,
    VARSITY_MODULE_URL,
)


@dataclass
class InvestmentAdvice:
    ticker: str
    name: str
    final_action: str  # STRONG BUY | BUY | ACCUMULATE | HOLD | REDUCE | SELL | AVOID
    conviction: str  # high | medium | low
    time_horizon: str  # Short (weeks) | Medium (months) | Long (1yr+)
    position_hint: str
    entry_zone: str
    stop_loss: str
    target: str
    risk_reward: str
    score_summary: str
    bullish_factors: list[str] = field(default_factory=list)
    bearish_factors: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    standards_checklist: list[tuple[str, bool, str]] = field(default_factory=list)
    summary: str = ""
    portfolio_tips: list[str] = field(default_factory=list)


def _price_fmt(val: float | None, currency: str = "₹") -> str:
    if val is None:
        return "N/A"
    return f"{currency}{val:,.2f}"


def _resolve_action(combined: CombinedResult, conviction: str, market_bullish: bool | None) -> str:
    s = combined.combined_score
    tech = combined.technical.composite_score
    fund = combined.fundamental.composite_score

    # Strong agreement + strong scores
    if s >= 35 and conviction == "high":
        return "STRONG BUY"
    if s >= 18:
        if fund > 10 and tech > 10:
            return "BUY"
        if fund > 15 and tech < 5:
            return "ACCUMULATE"  # value play, weak timing
        if tech > 15 and fund < 5:
            return "BUY" if market_bullish else "ACCUMULATE"
        return "BUY"
    if s >= 5:
        return "ACCUMULATE"
    if s <= -35 and conviction == "high":
        return "SELL"
    if s <= -18:
        return "REDUCE"
    if s <= -5:
        return "HOLD"  # weak but not sell
    return "HOLD"


def _conviction(combined: CombinedResult, rs: RelativeStrengthResult | None) -> str:
    tech_conf = combined.technical.confidence
    agree = (
        (combined.technical.composite_score > 0 and combined.fundamental.composite_score > 0)
        or (combined.technical.composite_score < 0 and combined.fundamental.composite_score < 0)
    )
    if tech_conf == "high" and agree:
        return "high"
    if tech_conf == "medium" or agree:
        return "medium"
    return "low"


def _time_horizon(combined: CombinedResult, fund_score: float) -> str:
    if abs(combined.technical.composite_score) > 25:
        return "Short (2–8 weeks) — momentum/timing signal"
    if fund_score > 15:
        return "Long (1–3 years) — quality compounder, ignore short-term noise"
    return "Medium (3–12 months)"


def _position_hint(action: str, conviction: str) -> str:
    hints = {
        "STRONG BUY": "Up to 8–10% of portfolio (max single-stock exposure for India)",
        "BUY": "5–8% allocation; enter in 2 tranches (50% now, 50% on dip)",
        "ACCUMULATE": "2–4% starter position; add on dips toward support",
        "HOLD": "Keep existing; no new adds until signals improve",
        "REDUCE": "Trim 25–50% of position; tighten stop-loss",
        "SELL": "Exit or reduce to tracking position (<2%)",
        "AVOID": "Do not initiate; watch from sidelines",
    }
    base = hints.get(action, "Keep position size below 5–8% of portfolio")
    if conviction == "low":
        return base + " — **reduce size by half** due to low conviction"
    return base


def _build_checklist(
    combined: CombinedResult,
    info: dict,
    rs: RelativeStrengthResult | None,
    rr_ratio: float,
) -> list[tuple[str, bool, str]]:
    tech = combined.technical
    fund = combined.fundamental
    raw = fund.raw

    checks: list[tuple[str, bool, str]] = []

    # Graham / value standards
    pe = raw.get("pe_trailing")
    checks.append((
        "P/E in reasonable range (<35)",
        pe is not None and 0 < pe < 35,
        f"P/E = {pe:.1f}" if pe else "No P/E data",
    ))
    checks.append((
        "ROE ≥ 12% (quality business)",
        raw.get("roe") is not None and raw.get("roe", 0) >= 0.12,
        f"ROE = {raw['roe']*100:.1f}%" if raw.get("roe") else "No ROE data",
    ))
    checks.append((
        "Positive earnings growth",
        raw.get("earnings_growth") is not None and raw.get("earnings_growth", 0) > 0,
        f"Growth = {raw['earnings_growth']*100:+.1f}%" if raw.get("earnings_growth") is not None else "N/A",
    ))
    de = raw.get("debt_to_equity")
    checks.append((
        "Debt/Equity < 1.5 (balance sheet safety)",
        de is None or de < 1.5,
        f"D/E = {de:.2f}" if de is not None else "Low/no debt (OK)",
    ))

    # Technical standards
    checks.append((
        "Price above SMA-50 (intermediate trend)",
        any("above SMA-50" in s.detail for s in tech.signals if s.name == "Moving Averages"),
        "Trend filter",
    ))
    checks.append((
        "RSI not overbought (<70)",
        all("overbought" not in s.detail.lower() for s in tech.signals if s.name == "RSI (14)"),
        "Momentum filter",
    ))
    checks.append((
        f"Risk/Reward ≥ {MIN_RISK_REWARD:.0f}:1 (Varsity Ch 18)",
        rr_ratio >= MIN_RISK_REWARD,
        f"R:R = {rr_ratio:.1f}:1",
    ))

    # Varsity Ch 20 — trending market filter
    adx_sig = next((s for s in tech.signals if s.name == "ADX"), None)
    if adx_sig:
        checks.append((
            "ADX confirms trend (Ch 20)",
            "range-bound" not in adx_sig.detail.lower(),
            adx_sig.detail[:60],
        ))

    # Varsity Ch 12 — volume confirmation
    vol_sig = next((s for s in tech.signals if s.name == "Volume"), None)
    if vol_sig:
        checks.append((
            "Volume supports move (Ch 12)",
            vol_sig.signal != "bearish" or "distribution" not in vol_sig.detail.lower(),
            vol_sig.detail[:60],
        ))
    if rs and rs.periods:
        alpha_3m = next((p.alpha_pct for p in rs.periods if "3" in p.label), rs.periods[-1].alpha_pct)
        checks.append((
            "Outperforming benchmark (3–6M)",
            alpha_3m > 0,
            f"Alpha = {alpha_3m:+.1f}%",
        ))

    # Market cap / liquidity (India)
    mcap = info.get("market_cap")
    checks.append((
        "Adequate liquidity (large/mid cap)",
        mcap is None or mcap > 5_000_000_000,
        "Large cap" if mcap and mcap > 200_000_000_000 else "Mid/small — higher risk",
    ))

    return checks


def generate_advice(
    combined: CombinedResult,
    info: dict,
    rs: RelativeStrengthResult | None = None,
    market_pulse: list[IndexPulse] | None = None,
    df: pd.DataFrame | None = None,
) -> InvestmentAdvice:
    """Produce full investment suggestion using all available analysis."""
    tech = combined.technical
    fund = combined.fundamental
    currency = "₹" if info.get("symbol", "").endswith((".NS", ".BO")) else "$"

    # Market regime
    market_bullish: bool | None = None
    sector_note = ""
    if market_pulse:
        nifty = next((p for p in market_pulse if "Nifty 50" in p.name), None)
        if nifty:
            market_bullish = nifty.score > 10
        bank = next((p for p in market_pulse if "Bank" in p.name), None)
        sector = info.get("sector", "")
        if "Financial" in sector and bank:
            sector_note = f"Bank Nifty: {bank.recommendation} ({bank.score:+.0f})"

    conviction = _conviction(combined, rs)
    action = _resolve_action(combined, conviction, market_bullish)

    # Risk/reward
    rr_ratio = 0.0
    if tech.stop_loss and tech.take_profit and tech.current_price:
        risk = tech.current_price - tech.stop_loss
        reward = tech.take_profit - tech.current_price
        rr_ratio = reward / risk if risk > 0 else 0

    # Override action for severe conflicts or bad R:R
    if conviction == "low" and action in ("STRONG BUY", "BUY"):
        action = "ACCUMULATE"
    if rr_ratio < MIN_RISK_REWARD and action in ("STRONG BUY", "BUY"):
        action = "ACCUMULATE"
    if market_bullish is False and action == "STRONG BUY":
        action = "BUY"

    bullish: list[str] = []
    bearish: list[str] = []

    for s in tech.signals:
        if s.signal == "bullish":
            bullish.append(f"Technical: {s.detail}")
        elif s.signal == "bearish":
            bearish.append(f"Technical: {s.detail}")

    for m in fund.metrics:
        if m.signal == "bullish":
            bullish.append(f"Fundamental: {m.name} — {m.detail}")
        elif m.signal == "bearish":
            bearish.append(f"Fundamental: {m.name} — {m.detail}")

    if rs:
        if rs.verdict == "Outperforming":
            bullish.append(f"Outperforming {rs.benchmark_name} across multiple periods")
        elif rs.verdict == "Underperforming":
            bearish.append(f"Underperforming {rs.benchmark_name} — weak relative strength")

    if market_bullish:
        bullish.append("Broader market (Nifty) is in bullish regime — tailwind for longs")
    elif market_bullish is False:
        bearish.append("Broader market is weak — headwind for new long positions")

    if sector_note:
        bullish.append(sector_note) if "BUY" in sector_note else bearish.append(sector_note)

    risks = [
        "Single-stock risk: never exceed 8–10% of portfolio in one name (Indian retail best practice)",
        "Gap risk: overnight news can breach stop-loss (results, RBI, global events)",
        f"Analysis framework: [Zerodha Varsity Technical Analysis]({VARSITY_MODULE_URL})",
    ]
    if info.get("symbol", "").endswith(".NS"):
        risks.append("STCG 20% / LTCG 12.5% (above ₹1.25L) — factor tax into return expectations")
    if conviction == "low":
        risks.append("Low conviction: indicators conflict — size down or wait")
    if raw_pe := fund.raw.get("pe_trailing"):
        if raw_pe > 40:
            risks.append(f"High valuation (P/E {raw_pe:.0f}) — vulnerable to earnings miss")

    checklist = _build_checklist(combined, info, rs, rr_ratio)
    passed = sum(1 for _, ok, _ in checklist if ok)
    total = len(checklist)

    entry_lo = tech.support or tech.current_price * 0.97
    entry_hi = tech.current_price
    entry_zone = f"{_price_fmt(entry_lo, currency)} – {_price_fmt(entry_hi, currency)} (near support to current)"

    portfolio_tips = list(ANALYSIS_PRINCIPLES) + [
        "Diversify across 8–15 stocks; avoid >25% in one sector",
        "Review quarterly results — fundamentals override technical signals",
        "Keep 10–20% cash for opportunities during market corrections",
    ]

    summary_parts = [
        f"**{info.get('name', combined.ticker)}** — Final suggestion: **{action}** "
        f"({conviction} conviction, {combined.combined_score:+.0f} combined score).",
        f"Technical {tech.composite_score:+.0f} + Fundamental {fund.composite_score:+.0f}. "
        f"Standards checklist: **{passed}/{total}** passed. "
        f"Methodology: [Zerodha Varsity TA]({VARSITY_MODULE_URL}).",
    ]

    if action in ("STRONG BUY", "BUY", "ACCUMULATE"):
        summary_parts.append(
            f"Entry zone: {entry_zone}. Stop: {_price_fmt(tech.stop_loss, currency)}. "
            f"Target: {_price_fmt(tech.take_profit, currency)} (R:R {rr_ratio:.1f}:1)."
        )
    elif action in ("SELL", "REDUCE"):
        summary_parts.append(
            "Consider exiting on rallies toward resistance or using a trailing stop below SMA-20."
        )
    else:
        summary_parts.append(
            "No clear edge now. Monitor for breakout above resistance or breakdown below support."
        )

    return InvestmentAdvice(
        ticker=combined.ticker,
        name=info.get("name", combined.ticker),
        final_action=action,
        conviction=conviction,
        time_horizon=_time_horizon(combined, fund.composite_score),
        position_hint=_position_hint(action, conviction),
        entry_zone=entry_zone,
        stop_loss=_price_fmt(tech.stop_loss, currency),
        target=_price_fmt(tech.take_profit, currency),
        risk_reward=f"{rr_ratio:.1f}:1",
        score_summary=f"Combined {combined.combined_score:+.1f} | Tech {tech.composite_score:+.1f} | Fund {fund.composite_score:+.1f}",
        bullish_factors=bullish[:8],
        bearish_factors=bearish[:8],
        risks=risks,
        standards_checklist=checklist,
        summary="\n\n".join(summary_parts),
        portfolio_tips=portfolio_tips,
    )


def generate_portfolio_advice(rows: list) -> str:
    """Top-level portfolio suggestions from analyzed holdings."""
    if not rows:
        return "No holdings to analyze."

    valid = [r for r in rows if not getattr(r, "error", None)]
    if not valid:
        return "No valid holdings analyzed."

    buys = [r for r in valid if r.recommendation in ("STRONG BUY", "BUY")]
    sells = [r for r in valid if r.recommendation in ("STRONG SELL", "SELL", "REDUCE")]
    holds = [r for r in valid if r.recommendation in ("HOLD", "ACCUMULATE")]

    lines = [
        f"**Portfolio overview:** {len(valid)} stocks analyzed.",
        f"**Strongest:** {', '.join(f'{r.kite_symbol} ({r.score:+.0f})' for r in sorted(valid, key=lambda x: -x.score)[:3])}",
    ]
    if sells:
        lines.append(f"**Review/reduce:** {', '.join(r.kite_symbol for r in sells)}")
    if len(valid) < 5:
        lines.append("**Diversification:** Portfolio is concentrated — consider adding 3–5 more uncorrelated names.")
    if len(valid) > 15:
        lines.append("**Diversification:** Many holdings — consider consolidating into highest-conviction 10–12 names.")
    lines.append("**Rebalance rule:** Trim winners above 10% weight; add to high-score laggards in small tranches.")
    return "\n\n".join(lines)
