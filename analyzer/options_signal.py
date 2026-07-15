"""
CE / PE (Call / Put) options suggestions from candlestick + intraday analysis.

CE = Call (bullish) · PE = Put (bearish) — Indian F&O convention.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from analyzer.candlesticks import PatternHit
from analyzer.candle_narrative import CandleNarrative
from analyzer.intraday_signals import IntradayAnalysis


@dataclass
class OptionsVerdict:
    action: str  # STRONG CE | BUY CE | NO TRADE | BUY PE | STRONG PE
    confidence: str  # high | medium | low
    summary: str
    strike_hint: str
    invalidation: str
    reasons: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    nse_picks: list = field(default_factory=list)
    nse_chain: object | None = None
    nse_error: str | None = None


# Score thresholds — options need clearer edge (theta decay)
STRONG_CE_SCORE = 2.8
BUY_CE_SCORE = 1.4
BUY_PE_SCORE = -1.4
STRONG_PE_SCORE = -2.8


def _pattern_ce_pe_boost(patterns: list[PatternHit]) -> tuple[float, list[str]]:
    """Extra weight for high-conviction Varsity patterns."""
    boost = 0.0
    notes: list[str] = []
    for p in patterns:
        d = p.detail.lower()
        if "marubozu" in d and p.signal == "bullish":
            boost += 1.2
            notes.append("Bullish Marubozu → momentum favours CE (Ch 5)")
        elif "marubozu" in d and p.signal == "bearish":
            boost -= 1.2
            notes.append("Bearish Marubozu → momentum favours PE (Ch 5)")
        elif "bullish engulfing" in d:
            boost += 1.0
            notes.append("Bullish Engulfing → CE setup (Ch 8)")
        elif "bearish engulfing" in d:
            boost -= 1.0
            notes.append("Bearish Engulfing → PE setup (Ch 8)")
        elif "morning star" in d:
            boost += 1.1
            notes.append("Morning Star → reversal CE (Ch 10)")
        elif "evening star" in d:
            boost -= 1.1
            notes.append("Evening Star → reversal PE (Ch 10)")
        elif "hammer" in d and p.signal == "bullish":
            boost += 0.9
            notes.append("Hammer → bounce CE (Ch 7)")
        elif "hanging" in d and p.signal == "bearish":
            boost -= 0.9
            notes.append("Hanging Man → fade PE (Ch 7)")
    return boost, notes


def compute_directional_score(
    current: CandleNarrative,
    patterns: list[PatternHit],
    intraday: IntradayAnalysis,
) -> tuple[float, list[str]]:
    """Unified bullish (+) / bearish (-) score for equity and options."""
    score = 0.0
    reasons: list[str] = []

    for p in patterns:
        score += p.score * 2.2
        reasons.append(f"Candle: {p.detail}")

    if current.bias == "bullish":
        score += 0.9
        reasons.append(f"{current.candle_type} — bullish")
    elif current.bias == "bearish":
        score -= 0.9
        reasons.append(f"{current.candle_type} — bearish")

    # Indecision candles — bad for directional options
    if current.candle_type in ("Doji", "Spinning Top", "Spinning top"):
        score *= 0.35
        reasons.append("Doji/Spinning top — poor edge for CE/PE; theta decay risk")

    id_map = {"BUY": 1.6, "SELL": -1.6, "WAIT": 0}
    score += id_map.get(intraday.trade_setup, 0)

    for sig in intraday.signals:
        if sig.bias == "bullish":
            score += 0.45
        elif sig.bias == "bearish":
            score -= 0.45
        if sig.name == "VWAP" and sig.bias != "neutral":
            reasons.append(sig.detail)
        if sig.name == "Opening Range" and sig.bias != "neutral":
            reasons.append(sig.detail)

    pat_boost, pat_notes = _pattern_ce_pe_boost(patterns)
    score += pat_boost
    reasons.extend(pat_notes)

    # RSI filter for options (Ch 14)
    if intraday.rsi is not None:
        if intraday.rsi > 72 and score > 0:
            score *= 0.75
            reasons.append(f"RSI {intraday.rsi:.0f} overbought — fade STRONG CE; consider PE on rejection")
        elif intraday.rsi < 28 and score < 0:
            score *= 0.75
            reasons.append(f"RSI {intraday.rsi:.0f} oversold — fade STRONG PE; bounce CE possible")
        elif intraday.rsi < 35 and score > 0:
            score += 0.3
        elif intraday.rsi > 65 and score < 0:
            score -= 0.3

    return score, reasons


def suggest_options(
    current: CandleNarrative,
    patterns: list[PatternHit],
    intraday: IntradayAnalysis,
    ticker: str,
    directional_score: float | None = None,
) -> OptionsVerdict:
    """CE/PE suggestion from current candles and session context."""
    if directional_score is not None:
        score = directional_score
        _, reasons = compute_directional_score(current, patterns, intraday)
    else:
        score, reasons = compute_directional_score(current, patterns, intraday)

    price = intraday.last_price
    vwap = intraday.vwap
    or_h, or_l = intraday.opening_range_high, intraday.opening_range_low

    risk_notes = [
        "Options decay fast intraday — prefer **current / next weekly** expiry for stocks; index weekly for Nifty/Bank Nifty.",
        "Exit CE/PE before **3:20 PM IST** on expiry day or intraday positions.",
        "Use underlying stop (VWAP/OR) — not premium alone.",
        "Not advice — verify liquidity (OI/volume) on Kite before placing orders.",
    ]

    if score >= STRONG_CE_SCORE:
        action, conf = "STRONG CE", "high"
        strike = "Buy **ATM or 1-strike OTM CE** (slightly OTM for better risk/reward)"
        inv = f"Invalid if spot closes below VWAP ₹{vwap:,.2f} or OR low ₹{or_l:,.2f}"
        summary = (
            f"**STRONG CE** — candles + session favour **calls**. "
            f"Bullish {current.candle_type} at {current.time}; hold above VWAP ₹{vwap:,.2f}."
        )
    elif score >= BUY_CE_SCORE:
        action, conf = "BUY CE", "medium"
        strike = "Buy **ATM CE**; add only if next candle confirms green"
        inv = f"Invalid below ₹{or_l:,.2f} (opening range low)"
        summary = (
            f"**BUY CE** — moderate bullish candle bias. "
            f"Target spot move toward OR high ₹{or_h:,.2f}."
        )
    elif score <= STRONG_PE_SCORE:
        action, conf = "STRONG PE", "high"
        strike = "Buy **ATM or 1-strike OTM PE**"
        inv = f"Invalid if spot reclaims VWAP ₹{vwap:,.2f} or OR high ₹{or_h:,.2f}"
        summary = (
            f"**STRONG PE** — candles + session favour **puts**. "
            f"Bearish {current.candle_type} at {current.time}; weakness below VWAP ₹{vwap:,.2f}."
        )
    elif score <= BUY_PE_SCORE:
        action, conf = "BUY PE", "medium"
        strike = "Buy **ATM PE**; confirm with next red candle"
        inv = f"Invalid above ₹{or_h:,.2f} (opening range high)"
        summary = (
            f"**BUY PE** — moderate bearish candle bias. "
            f"Target spot move toward OR low ₹{or_l:,.2f}."
        )
    else:
        action, conf = "NO TRADE", "low"
        strike = "No CE/PE — wait for Marubozu, Engulfing, or OR breakout"
        inv = f"Re-assess on break above ₹{or_h:,.2f} (CE) or below ₹{or_l:,.2f} (PE)"
        summary = (
            "**NO TRADE** — mixed candles; no strong CE or PE edge. "
            "Varsity Ch 6: wait for confirmation before buying options."
        )
        risk_notes.insert(0, "Avoid buying OTM CE/PE in chop — theta will erode premium.")

    # Index-specific hint
    sym = ticker.upper()
    if sym in ("NIFTY50", "NIFTY", "BANKNIFTY", "NIFTY BANK", "^NSEBANK", "^NSEI"):
        risk_notes.append("Index options: check **lot size** and **weekly expiry** on NSE.")

    hint = "bullish" if score > 0 else ("bearish" if score < 0 else "neutral")
    result = OptionsVerdict(
        action=action,
        confidence=conf,
        summary=summary,
        strike_hint=strike,
        invalidation=inv,
        reasons=reasons[:8],
        risk_notes=risk_notes,
    )
    from analyzer.decision_engine.verdict_bridge import attach_decision_to_options_verdict

    attach_decision_to_options_verdict(result, ticker, score=score, directional_hint=hint)
    return result


def suggest_options_daily(
    current: CandleNarrative,
    patterns: list[PatternHit],
    technical_score: float,
    support: float | None,
    resistance: float | None,
    ticker: str,
) -> OptionsVerdict:
    """CE/PE for swing/daily timeframe from latest daily candle."""
    score = technical_score / 35.0  # normalize ~composite -100..100 to roughly -3..3
    if current.bias == "bullish":
        score += 0.6
    elif current.bias == "bearish":
        score -= 0.6
    boost, notes = _pattern_ce_pe_boost(patterns)
    score += boost

    fake_intraday = IntradayAnalysis(
        ticker=ticker,
        interval="1d",
        last_price=current.close,
        vwap=current.close,
        opening_range_high=resistance or current.high,
        opening_range_low=support or current.low,
        rsi=None,
        session_bias="BULLISH" if score > 0 else "BEARISH" if score < 0 else "NEUTRAL",
        trade_setup="BUY" if score > 1 else "SELL" if score < -1 else "WAIT",
        entry=current.close,
        stop_loss=support,
        target=resistance,
    )
    ov = suggest_options(current, patterns, fake_intraday, ticker, directional_score=score)
    ov.risk_notes = [
        "Daily timeframe — use **monthly or next monthly** expiry for stock options.",
        "Hold 2–10 sessions; exit if daily candle invalidates thesis.",
    ] + ov.risk_notes[2:]
    ov.summary = ov.summary.replace("intraday", "daily").replace("session", "trend")
    return ov
