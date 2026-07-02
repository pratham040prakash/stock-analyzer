"""Chart- and trend-based market risk for beginners."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from analyzer.earnings_calendar import CorporateEvent
from analyzer.delivery_quality import DeliverySnapshot
from analyzer.fundamentals import FundamentalResult
from analyzer.market_regime import MarketRegime, detect_nifty_regime


@dataclass
class TrendSnapshot:
    direction: str  # Uptrend | Downtrend | Sideways
    strength: str  # Strong | Moderate | Weak
    return_1m_pct: float | None
    return_3m_pct: float | None
    above_sma20: bool | None
    above_sma50: bool | None
    above_sma200: bool | None
    summary: str


@dataclass
class MarketRiskAssessment:
    ticker: str
    name: str
    risk_level: str  # Low | Moderate | High | Very High
    risk_score: float  # 0 (safe) – 100 (risky)
    trend: TrendSnapshot
    volatility_atr_pct: float | None
    max_drawdown_6m_pct: float | None
    distance_from_52w_high_pct: float | None
    fundamental_grade: str  # Strong | Average | Weak | Unknown
    market_regime: str
    risk_factors: list[str] = field(default_factory=list)
    positive_factors: list[str] = field(default_factory=list)
    beginner_verdict: str = ""
    max_suggested_allocation_pct: float = 5.0
    stop_loss_note: str = ""
    experience_tip: str = ""


def _period_return(df: pd.DataFrame, days: int) -> float | None:
    if len(df) < days + 1:
        return None
    start = float(df["Close"].iloc[-days - 1])
    end = float(df["Close"].iloc[-1])
    if start <= 0:
        return None
    return (end / start - 1) * 100


def _max_drawdown_pct(df: pd.DataFrame) -> float | None:
    if len(df) < 5:
        return None
    prices = df["Close"].astype(float)
    peak = prices.cummax()
    dd = (prices / peak - 1) * 100
    return float(dd.min())


def _trend_from_chart(df: pd.DataFrame) -> TrendSnapshot:
    row = df.iloc[-1]
    price = float(row["Close"])
    sma20 = row.get("SMA_20")
    sma50 = row.get("SMA_50")
    sma200 = row.get("SMA_200")

    above20 = bool(price > sma20) if not pd.isna(sma20) else None
    above50 = bool(price > sma50) if not pd.isna(sma50) else None
    above200 = bool(price > sma200) if not pd.isna(sma200) else None

    r1m = _period_return(df, 21)
    r3m = _period_return(df, 63)

    bullish_stack = sum(x is True for x in (above20, above50, above200))
    bearish_stack = sum(x is False for x in (above20, above50, above200))

    if bullish_stack >= 2 and (r1m is None or r1m > -3):
        direction = "Uptrend"
        strength = "Strong" if bullish_stack == 3 and (r3m or 0) > 5 else "Moderate"
        summary = "Price above key moving averages — buyers have controlled recent trend."
    elif bearish_stack >= 2 and (r1m is None or r1m < 3):
        direction = "Downtrend"
        strength = "Strong" if bearish_stack == 3 and (r3m or 0) < -5 else "Moderate"
        summary = "Price below key moving averages — sellers have controlled recent trend."
    else:
        direction = "Sideways"
        strength = "Weak"
        summary = "No clear trend — price is chopping between support and resistance."

    parts = []
    if r1m is not None:
        parts.append(f"1M {r1m:+.1f}%")
    if r3m is not None:
        parts.append(f"3M {r3m:+.1f}%")
    if parts:
        summary += f" Recent: {', '.join(parts)}."

    return TrendSnapshot(
        direction=direction,
        strength=strength,
        return_1m_pct=round(r1m, 1) if r1m is not None else None,
        return_3m_pct=round(r3m, 1) if r3m is not None else None,
        above_sma20=above20,
        above_sma50=above50,
        above_sma200=above200,
        summary=summary,
    )


def _fundamental_grade(fund: FundamentalResult | None) -> str:
    if fund is None:
        return "Unknown"
    if fund.composite_score >= 15:
        return "Strong"
    if fund.composite_score >= -5:
        return "Average"
    return "Weak"


def _risk_level(score: float) -> str:
    if score < 30:
        return "Low"
    if score < 50:
        return "Moderate"
    if score < 70:
        return "High"
    return "Very High"


def _max_allocation(risk_level: str, goal: str, experience: str) -> float:
    caps = {
        ("Low", "long_term", "new"): 10.0,
        ("Low", "long_term", "some"): 12.0,
        ("Moderate", "long_term", "new"): 6.0,
        ("Moderate", "long_term", "some"): 8.0,
        ("High", "long_term", "new"): 3.0,
        ("High", "long_term", "some"): 5.0,
        ("Very High", "long_term", "new"): 0.0,
        ("Very High", "long_term", "some"): 2.0,
    }
    key = (risk_level, goal, experience)
    if key in caps:
        return caps[key]
    if goal == "trading":
        return 2.0 if experience == "new" else 5.0
    if goal == "learning":
        return 0.0
    return 5.0


def assess_market_risk(
    df: pd.DataFrame,
    ticker: str,
    name: str = "",
    yf_info: dict | None = None,
    fund: FundamentalResult | None = None,
    regime: MarketRegime | None = None,
    goal: str = "long_term",
    experience: str = "new",
    earnings_event: CorporateEvent | None = None,
    delivery_snapshot: DeliverySnapshot | None = None,
) -> MarketRiskAssessment:
    """
    Score risk from recent chart trend, volatility, drawdown, fundamentals, and Nifty regime.
    goal: learning | long_term | trading
    experience: new | some
    """
    trend = _trend_from_chart(df)
    row = df.iloc[-1]
    price = float(row["Close"])

    atr = row.get("ATR_14")
    atr_pct = round(float(atr) / price * 100, 2) if not pd.isna(atr) and price > 0 else None
    dd = _max_drawdown_pct(df)
    if dd is not None:
        dd = round(dd, 1)

    hi_52 = yf_info.get("fifty_two_week_high") if yf_info else None
    dist_hi = None
    if hi_52 and price > 0:
        dist_hi = round((price / float(hi_52) - 1) * 100, 1)

    if regime is None:
        try:
            regime = detect_nifty_regime()
        except Exception:
            regime = None

    fund_grade = _fundamental_grade(fund)
    risk_score = 0.0
    risks: list[str] = []
    positives: list[str] = []

    # Trend risk
    if trend.direction == "Downtrend":
        risk_score += 25 if trend.strength == "Strong" else 18
        risks.append(f"Chart downtrend ({trend.strength}) — buying against the trend is risky for beginners.")
    elif trend.direction == "Sideways":
        risk_score += 12
        risks.append("Sideways market — false breakouts are common; wait for clear direction.")
    else:
        positives.append(f"Uptrend on chart ({trend.strength}) — trend is your friend (Varsity Ch 17).")

    if trend.return_1m_pct is not None and trend.return_1m_pct < -8:
        risk_score += 15
        risks.append(f"Sharp 1-month fall ({trend.return_1m_pct:+.1f}%) — may be falling knife.")
    elif trend.return_3m_pct is not None and trend.return_3m_pct > 15:
        risk_score += 8
        risks.append(f"Extended 3-month rally ({trend.return_3m_pct:+.1f}%) — pullback risk elevated.")

    # Volatility
    if atr_pct is not None:
        if atr_pct > 4:
            risk_score += 18
            risks.append(f"High daily volatility (ATR {atr_pct:.1f}% of price) — wide swings; use smaller size.")
        elif atr_pct > 2.5:
            risk_score += 10
            risks.append(f"Moderate volatility (ATR {atr_pct:.1f}%) — plan wider stops.")
        else:
            positives.append(f"Relatively stable price action (ATR {atr_pct:.1f}%).")

    if dd is not None and dd < -20:
        risk_score += 15
        risks.append(f"Large 6-month drawdown ({dd:.1f}%) — stock has already fallen sharply.")
    elif dd is not None and dd > -10:
        positives.append(f"Controlled drawdown ({dd:.1f}% max in 6M).")

    if dist_hi is not None and dist_hi < -25:
        risk_score += 10
        risks.append(f"Far below 52-week high ({dist_hi:+.1f}%) — investigate why before buying.")
    elif dist_hi is not None and dist_hi > -5:
        risk_score += 6
        risks.append(f"Near 52-week high ({dist_hi:+.1f}%) — limited upside cushion if trend reverses.")

    # Fundamentals
    if fund_grade == "Weak":
        risk_score += 20
        risks.append("Weak fundamentals (P/E, debt, ROE, or growth) — quality filter failed.")
    elif fund_grade == "Average":
        risk_score += 8
        risks.append("Average fundamentals — okay for learning, not a high-conviction compounder.")
    elif fund_grade == "Strong":
        positives.append("Strong fundamentals — business quality supports long-term holding.")

    # Market regime
    regime_name = regime.regime if regime else "Unknown"
    if regime and regime.regime == "Trending Bearish":
        risk_score += 15
        risks.append(f"Nifty in bearish regime (ADX {regime.adx}) — market headwind for new buys.")
    elif regime and regime.regime == "Range-bound":
        risk_score += 10
        risks.append(f"Nifty range-bound (ADX {regime.adx}) — stock picks matter more; avoid chasing breakouts.")
    elif regime and regime.regime == "Trending Bullish":
        positives.append(f"Nifty trending up (ADX {regime.adx}) — supportive backdrop for quality names.")

    # Earnings event risk
    if earnings_event and earnings_event.event_type == "Earnings":
        if earnings_event.days_until is not None:
            if earnings_event.days_until <= 3:
                risk_score += 20
                risks.append(earnings_event.guidance or f"Earnings in {earnings_event.days_until} days.")
            elif earnings_event.days_until <= 7:
                risk_score += 12
                risks.append(earnings_event.guidance or f"Earnings in {earnings_event.days_until} days.")
            elif earnings_event.days_until <= 14:
                risk_score += 5
                risks.append(f"Earnings in {earnings_event.days_until} days — on watchlist.")

    if delivery_snapshot and delivery_snapshot.delivery_pct is not None:
        if delivery_snapshot.quality == "speculative":
            risk_score += 15
            risks.append(delivery_snapshot.guidance or "Low delivery — speculative churn.")
        elif delivery_snapshot.quality == "weak":
            risk_score += 8
            risks.append(f"Delivery {delivery_snapshot.delivery_pct:.0f}% — mixed quality.")
        elif delivery_snapshot.quality == "strong":
            positives.append(
                f"Strong delivery {delivery_snapshot.delivery_pct:.0f}% — accumulation signal."
            )

    risk_score = min(100.0, max(0.0, risk_score))
    level = _risk_level(risk_score)
    max_alloc = _max_allocation(level, goal, experience)

    if goal == "learning":
        verdict = (
            "**Paper-trade only** — use this analysis to learn, not to deploy real money yet. "
            "Track the stock for 4–8 weeks and compare your guess vs the chart."
        )
        experience_tip = "Complete 2–3 Varsity TA chapters per week before risking capital."
    elif level in ("High", "Very High") and experience == "new":
        verdict = (
            f"**High risk for beginners** (score {risk_score:.0f}/100). "
            "Prefer index SIP or large-cap names with Low/Moderate risk first."
        )
        experience_tip = "Start with Nifty 50 large caps; max 1–2% position if you still want exposure."
    elif trend.direction == "Downtrend":
        verdict = "Wait for trend reversal (price back above SMA-50) before buying. Don't average down blindly."
        experience_tip = "Set price alerts at support; enter only if stop-loss plan is clear."
    elif level == "Low" and fund_grade == "Strong":
        verdict = "Relatively favourable for long-term learning positions — still use stop-loss and diversify."
        experience_tip = "Good candidate to study in Single Stock tab; add in 2 tranches, not all at once."
    else:
        verdict = (
            f"Moderate setup — acceptable for small starter positions ({max_alloc:.0f}% max of portfolio) "
            "with strict stop-loss."
        )
        experience_tip = "Risk only 1% of capital per trade; never invest emergency fund money."

    stop_note = "Place stop below recent swing low or 2× ATR — whichever is tighter for your horizon."
    if atr_pct and atr_pct > 3:
        stop_note += f" ATR is {atr_pct:.1f}% — expect ±{atr_pct:.0f}% daily moves."

    return MarketRiskAssessment(
        ticker=ticker,
        name=name or ticker,
        risk_level=level,
        risk_score=round(risk_score, 1),
        trend=trend,
        volatility_atr_pct=atr_pct,
        max_drawdown_6m_pct=dd,
        distance_from_52w_high_pct=dist_hi,
        fundamental_grade=fund_grade,
        market_regime=regime_name,
        risk_factors=risks,
        positive_factors=positives,
        beginner_verdict=verdict,
        max_suggested_allocation_pct=max_alloc,
        stop_loss_note=stop_note,
        experience_tip=experience_tip,
    )


def assess_nifty_market_risk(period: str = "6mo") -> MarketRiskAssessment:
    """Market-wide risk from Nifty index chart."""
    from analyzer.data import _fetch_single
    from analyzer.indicators import add_indicators

    df, _ = _fetch_single("^NSEI", period)
    df = add_indicators(df)
    regime = detect_nifty_regime(period=period)
    return assess_market_risk(
        df,
        ticker="^NSEI",
        name="Nifty 50",
        goal="long_term",
        experience="new",
        regime=regime,
    )
