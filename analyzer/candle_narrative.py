"""
Per-candle narrative and live buy/sell verdict from the current chart.

Uses Zerodha Varsity candlestick framework (Ch 3–10).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from analyzer.candlesticks import detect_patterns_at
from analyzer.intraday_signals import IntradayAnalysis, analyze_intraday, compute_trade_levels


@dataclass
class CandleNarrative:
    time: str
    open: float
    high: float
    low: float
    close: float
    change_pct: float
    candle_type: str
    bias: str  # bullish | bearish | neutral
    story: str
    pattern: str | None = None
    volume_note: str = ""


@dataclass
class LiveChartVerdict:
    ticker: str
    interval: str
    action: str  # STRONG BUY | BUY | WAIT | SELL | STRONG SELL
    confidence: str  # high | medium | low
    summary: str
    reasons: list[str] = field(default_factory=list)
    current_candle: CandleNarrative | None = None
    recent_candles: list[CandleNarrative] = field(default_factory=list)
    session_story: str = ""
    entry: float | None = None
    stop_loss: float | None = None
    target: float | None = None
    intraday: IntradayAnalysis | None = None
    directional_score: float = 0.0
    options: "OptionsVerdict | None" = None


def _body(o: float, c: float) -> float:
    return abs(c - o)


def _range(h: float, l: float) -> float:
    return max(h - l, 1e-9)


def _upper_wick(o: float, c: float, h: float) -> float:
    return h - max(o, c)


def _lower_wick(o: float, c: float, l: float) -> float:
    return min(o, c) - l


def _classify_candle(o: float, h: float, l: float, c: float) -> tuple[str, str]:
    """Return (candle_type, bias)."""
    rng = _range(h, l)
    body = _body(o, c)
    br = body / rng
    lw = _lower_wick(o, c, l)
    uw = _upper_wick(o, c, h)
    bull = c > o

    if br > 0.85:
        return ("Bullish Marubozu" if bull else "Bearish Marubozu", "bullish" if bull else "bearish")
    if br < 0.08:
        return ("Doji", "neutral")
    if br < 0.35 and lw > body and uw > body:
        return ("Spinning Top", "neutral")
    if lw >= 2 * max(body, rng * 0.05) and uw <= body * 0.6:
        return ("Hammer shape", "bullish")
    if uw >= 2 * max(body, rng * 0.05) and lw <= body * 0.6:
        return ("Shooting Star shape", "bearish")
    if br > 0.6:
        return ("Strong Green" if bull else "Strong Red", "bullish" if bull else "bearish")
    if uw > body * 1.5 and bull:
        return ("Green with upper rejection", "neutral")
    if lw > body * 1.5 and not bull:
        return ("Red with lower rejection", "neutral")
    return ("Green candle" if bull else "Red candle", "bullish" if bull else "bearish")


def _volume_note(vol: float, vol_sma: float | None, bull: bool) -> str:
    if vol_sma is None or vol_sma <= 0:
        return ""
    ratio = vol / vol_sma
    if ratio > 1.5:
        side = "buyers" if bull else "sellers"
        return f"Volume {ratio:.1f}x average — strong {side} participation (Varsity Ch 12)."
    if ratio < 0.7:
        return f"Thin volume ({ratio:.1f}x avg) — weak conviction."
    return f"Normal volume ({ratio:.1f}x avg)."


def _compare_prev(
    o: float, h: float, l: float, c: float,
    po: float, ph: float, pl: float, pc: float,
) -> str:
    parts = []
    if h > ph and l >= pl:
        parts.append("made a higher high")
    elif h <= ph and l < pl:
        parts.append("made a lower low")
    if c > pc:
        parts.append("closed above prior close")
    elif c < pc:
        parts.append("closed below prior close")
    if h <= ph and l >= pl:
        parts.append("inside prior candle (consolidation)")
    if o <= pc and c >= po:
        parts.append("engulfed previous candle body")
    elif o >= pc and c <= po:
        parts.append("bearish engulf of prior body")
    return "; ".join(parts) if parts else "similar to prior candle"


def narrate_candle_at(
    df: pd.DataFrame,
    index: int,
    vol_sma_col: str | None = "VOL_SMA",
) -> CandleNarrative:
    """Tell the story of one candle bar."""
    row = df.iloc[index]
    ts = df.index[index]
    time_str = ts.strftime("%H:%M") if hasattr(ts, "strftime") else str(ts)

    o, h, l, c = float(row["Open"]), float(row["High"]), float(row["Low"]), float(row["Close"])
    prev_close = float(df.iloc[index - 1]["Close"]) if index > 0 else o
    change_pct = ((c - prev_close) / prev_close * 100) if prev_close else 0.0

    candle_type, bias = _classify_candle(o, h, l, c)

    # Pattern overlay from Varsity detector
    patterns = detect_patterns_at(df, index)
    pattern_name = None
    if patterns:
        pattern_name = patterns[0].detail.split("—")[0].strip()
        bias = patterns[0].signal
        if "Marubozu" in patterns[0].detail:
            candle_type = "Bullish Marubozu" if patterns[0].signal == "bullish" else "Bearish Marubozu"
        elif "Engulfing" in patterns[0].detail:
            candle_type = "Bullish Engulfing" if patterns[0].signal == "bullish" else "Bearish Engulfing"
        elif "Hammer" in patterns[0].detail:
            candle_type = "Hammer"
        elif "Hanging" in patterns[0].detail:
            candle_type = "Hanging Man"
        elif "Doji" in patterns[0].detail:
            candle_type = "Doji"
        elif "Morning Star" in patterns[0].detail:
            candle_type = "Morning Star"
        elif "Evening Star" in patterns[0].detail:
            candle_type = "Evening Star"

    vol = float(row.get("Volume", 0))
    vol_sma = float(row[vol_sma_col]) if vol_sma_col and vol_sma_col in df.columns and not pd.isna(row.get(vol_sma_col)) else None
    vnote = _volume_note(vol, vol_sma, c > o)

    # Build narrative sentence
    direction = "green (bullish)" if c > o else "red (bearish)" if c < o else "doji (indecision)"
    move = f"{'rose' if change_pct >= 0 else 'fell'} {abs(change_pct):.2f}% from prior close"

    if index > 0:
        prev = df.iloc[index - 1]
        comp = _compare_prev(o, h, l, c, float(prev["Open"]), float(prev["High"]), float(prev["Low"]), float(prev["Close"]))
        rel = f" It {comp}."
    else:
        rel = " Opening candle of the session."

    wick_story = ""
    lw, uw = _lower_wick(o, c, l), _upper_wick(o, c, h)
    rng = _range(h, l)
    if uw > rng * 0.4:
        wick_story = " Long upper wick — sellers rejected higher prices."
    elif lw > rng * 0.4:
        wick_story = " Long lower wick — buyers defended lower prices."

    pattern_bit = f" Pattern: **{pattern_name}**." if pattern_name else ""
    story = (
        f"**{time_str}** — {candle_type} ({direction}). "
        f"O ₹{o:,.2f} → H ₹{h:,.2f} → L ₹{l:,.2f} → C ₹{c:,.2f}; {move}.{rel}"
        f"{wick_story}{pattern_bit} {vnote}"
    ).strip()

    return CandleNarrative(
        time=time_str,
        open=round(o, 2),
        high=round(h, 2),
        low=round(l, 2),
        close=round(c, 2),
        change_pct=round(change_pct, 2),
        candle_type=candle_type,
        bias=bias,
        story=story,
        pattern=pattern_name,
        volume_note=vnote,
    )


def narrate_session(
    df: pd.DataFrame,
    last_n: int = 15,
    vol_sma_col: str | None = "VOL_SMA",
) -> list[CandleNarrative]:
    """Narrate the last N candles of the session."""
    start = max(0, len(df) - last_n)
    return [narrate_candle_at(df, i, vol_sma_col=vol_sma_col) for i in range(start, len(df))]


def _session_story(candles: list[CandleNarrative]) -> str:
    if not candles:
        return "No candles to analyze."
    greens = sum(1 for c in candles if c.bias == "bullish")
    reds = sum(1 for c in candles if c.bias == "bearish")
    net = candles[-1].close - candles[0].open
    trend = "uptrend" if net > 0 else "downtrend" if net < 0 else "flat"

    patterns = [c.candle_type for c in candles if c.pattern or c.candle_type not in ("Green candle", "Red candle")]
    pattern_str = f" Notable patterns: {', '.join(dict.fromkeys(patterns[-3:]))}." if patterns else ""

    return (
        f"Session flow ({len(candles)} candles): **{trend}** with {greens} bullish vs {reds} bearish bars. "
        f"Price moved ₹{candles[0].open:,.2f} → ₹{candles[-1].close:,.2f} "
        f"({(candles[-1].close - candles[0].open) / candles[0].open * 100:+.2f}%)."
        f"{pattern_str}"
    )


def _score_to_equity_action(score: float) -> tuple[str, str, str | None]:
    """Map directional score to equity BUY/SELL/WAIT."""
    extra = None
    if score >= 3:
        return "STRONG BUY", "high", extra
    if score >= 1.2:
        return "BUY", "medium", extra
    if score <= -3:
        return "STRONG SELL", "high", extra
    if score <= -1.2:
        return "SELL", "medium", extra
    return "WAIT", "low", "Mixed signals — wait for next candle to confirm direction (Varsity Ch 6)."


def _verdict_from_candles(
    current: CandleNarrative,
    patterns: list,
    intraday: IntradayAnalysis,
) -> tuple[str, str, list[str], float]:
    """Derive BUY/SELL/WAIT from current candle + intraday context."""
    from analyzer.options_signal import compute_directional_score

    score, reasons = compute_directional_score(current, patterns, intraday)
    action, conf, wait_note = _score_to_equity_action(score)
    if wait_note:
        reasons.append(wait_note)
    return action, conf, reasons[:6], score


def analyze_live_chart(
    df: pd.DataFrame,
    ticker: str,
    interval: str,
) -> LiveChartVerdict:
    """Full live chart read: every recent candle's story + buy/sell verdict."""
    from analyzer.intraday_signals import add_intraday_indicators

    df_ind = add_intraday_indicators(df)
    intraday = analyze_intraday(df, ticker, interval)

    recent = narrate_session(df_ind, last_n=min(20, len(df_ind)), vol_sma_col="VOL_SMA")
    current = recent[-1] if recent else None
    patterns = detect_patterns_at(df_ind, -1)

    if not current:
        raise ValueError("No candles available for narrative.")

    action, confidence, reasons, score = _verdict_from_candles(current, patterns, intraday)
    session_story = _session_story(recent)

    from analyzer.options_signal import suggest_options
    options = suggest_options(current, patterns, intraday, ticker, directional_score=score)

    summary_parts = [
        f"**{action}** ({confidence} confidence) based on the **{current.candle_type}** at {current.time}.",
    ]
    if action in ("STRONG BUY", "BUY"):
        summary_parts.append(
            f"Bulls in control if price holds above ₹{intraday.vwap:,.2f} (VWAP). "
            f"Invalidation below ₹{intraday.opening_range_low:,.2f}."
        )
    elif action in ("STRONG SELL", "SELL"):
        summary_parts.append(
            f"Sellers in control below VWAP ₹{intraday.vwap:,.2f}. "
            f"Cover shorts if price reclaims OR high ₹{intraday.opening_range_high:,.2f}."
        )
    else:
        summary_parts.append("No high-conviction edge on the latest candle — stay flat or reduce size.")

    entry, stop_loss, target = compute_trade_levels(intraday, action)

    return _finalize_live_chart(
        LiveChartVerdict(
            ticker=ticker,
            interval=interval,
            action=action,
            confidence=confidence,
            summary=" ".join(summary_parts),
            reasons=reasons,
            current_candle=current,
            recent_candles=recent,
            session_story=session_story,
            entry=entry,
            stop_loss=stop_loss,
            target=target,
            intraday=intraday,
            directional_score=score,
            options=options,
        )
    )


def _finalize_live_chart(verdict: LiveChartVerdict) -> LiveChartVerdict:
    from analyzer.decision_engine.verdict_bridge import attach_decision_to_live_chart

    attach_decision_to_live_chart(verdict)
    action = verdict.action
    confidence = verdict.confidence
    summary_parts = [
        f"**{action}** ({confidence} confidence) based on the **{verdict.current_candle.candle_type}** at {verdict.current_candle.time}."
        if verdict.current_candle
        else f"**{action}** ({confidence} confidence).",
    ]
    if verdict.intraday:
        if action in ("STRONG BUY", "BUY"):
            summary_parts.append(
                f"Bulls in control if price holds above ₹{verdict.intraday.vwap:,.2f} (VWAP). "
                f"Invalidation below ₹{verdict.intraday.opening_range_low:,.2f}."
            )
        elif action in ("STRONG SELL", "SELL"):
            summary_parts.append(
                f"Sellers in control below VWAP ₹{verdict.intraday.vwap:,.2f}. "
                f"Cover shorts if price reclaims OR high ₹{verdict.intraday.opening_range_high:,.2f}."
            )
        else:
            summary_parts.append("No high-conviction edge on the latest candle — stay flat or reduce size.")
    verdict.summary = " ".join(summary_parts)
    entry, stop_loss, target = compute_trade_levels(verdict.intraday, action)
    verdict.entry = entry
    verdict.stop_loss = stop_loss
    verdict.target = target
    return verdict
