"""
Daily-chart horizon analysis — short-term swing (weeks) and long-term (months/years).

Uses daily candles only (no intraday). Aligned with Zerodha Varsity TA.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from analyzer.candlesticks import detect_patterns_at
from analyzer.varsity_knowledge import ADX_TREND_THRESHOLD, RSI_OVERBOUGHT, RSI_OVERSOLD


@dataclass
class HorizonAnalysis:
    horizon: str  # short | long
    action: str
    score: float  # -100 to +100
    timeframe: str
    entry_hint: str
    stop_hint: str
    target_hint: str
    chart_signals: list[str] = field(default_factory=list)
    summary: str = ""


def _safe_float(val) -> float | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _macd_hist_col(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if "MACDh" in col or col.endswith("MACDh_12_26_9"):
            return col
    return None


def _adx_cols(df: pd.DataFrame) -> tuple[str | None, str | None, str | None]:
    adx = dip = dim = None
    for col in df.columns:
        if col.startswith("ADX_"):
            adx = col
        elif col.startswith("DMP_"):
            dip = col
        elif col.startswith("DMN_"):
            dim = col
    return adx, dip, dim


def _support_resistance(df: pd.DataFrame, lookback: int = 20) -> tuple[float | None, float | None]:
    tail = df.tail(lookback)
    if tail.empty:
        return None, None
    return float(tail["Low"].min()), float(tail["High"].max())


def _action_short(score: float) -> str:
    if score >= 40:
        return "STRONG BUY"
    if score >= 22:
        return "BUY"
    if score >= 8:
        return "WATCH"
    if score <= -22:
        return "AVOID"
    if score <= -8:
        return "WEAK"
    return "NEUTRAL"


def _action_long(score: float) -> str:
    if score >= 45:
        return "CORE BUY"
    if score >= 28:
        return "ACCUMULATE"
    if score >= 12:
        return "HOLD"
    if score <= -18:
        return "AVOID"
    return "WATCH"


def analyze_short_term_chart(df: pd.DataFrame) -> HorizonAnalysis:
    """
    Swing setup from **daily** chart (typical hold: 2–8 weeks).
    Momentum, trend stack, patterns, volume — Varsity Ch 12–15, 20.
    """
    if len(df) < 30:
        return HorizonAnalysis(
            horizon="short",
            action="NEUTRAL",
            score=0.0,
            timeframe="2–8 weeks (daily chart)",
            entry_hint="—",
            stop_hint="—",
            target_hint="—",
            summary="Not enough daily history",
        )

    row = df.iloc[-1]
    price = float(row["Close"])
    sma20 = _safe_float(row.get("SMA_20"))
    sma50 = _safe_float(row.get("SMA_50"))
    rsi = _safe_float(row.get("RSI_14"))
    atr = _safe_float(row.get("ATR_14"))
    vol = _safe_float(row.get("Volume"))
    vol_sma = _safe_float(row.get("VOL_SMA_20"))

    score = 0.0
    signals: list[str] = []

    if sma20 and price > sma20:
        score += 15
        signals.append(f"Price above SMA-20 (₹{sma20:,.0f}) — short-term uptrend")
    elif sma20:
        score -= 12
        signals.append(f"Price below SMA-20 — swing weakness")

    if sma50 and price > sma50:
        score += 10
        signals.append("Above SMA-50 — intermediate trend intact")
    elif sma50:
        score -= 10

    if sma20 and sma50 and sma20 > sma50:
        score += 12
        signals.append("SMA-20 > SMA-50 — bullish stack")
    elif sma20 and sma50 and sma20 < sma50:
        score -= 12
        signals.append("SMA-20 < SMA-50 — bearish stack")

    hist_col = _macd_hist_col(df)
    if hist_col:
        hist = _safe_float(row.get(hist_col))
        if hist is not None:
            if hist > 0:
                score += 14
                signals.append("MACD histogram positive — momentum up")
            else:
                score -= 14
                signals.append("MACD histogram negative — momentum down")

    if rsi is not None:
        if 40 <= rsi < RSI_OVERBOUGHT:
            score += 8
            signals.append(f"RSI {rsi:.0f} — room to run (not overbought)")
        elif rsi >= RSI_OVERBOUGHT:
            score -= 18
            signals.append(f"RSI {rsi:.0f} overbought — pullback risk on daily")
        elif rsi <= RSI_OVERSOLD:
            score += 12
            signals.append(f"RSI {rsi:.0f} oversold — bounce setup if trend supports")

    adx_col, dmp_col, dmn_col = _adx_cols(df)
    if adx_col:
        adx = _safe_float(row.get(adx_col))
        if adx and adx >= ADX_TREND_THRESHOLD:
            score += 8
            signals.append(f"ADX {adx:.0f} — trending market (Ch 20)")
            if dmp_col and dmn_col:
                dmp = _safe_float(row.get(dmp_col)) or 0
                dmn = _safe_float(row.get(dmn_col)) or 0
                if dmp > dmn:
                    score += 6
                    signals.append("+DI > -DI — buyers dominant")
                else:
                    score -= 6
                    signals.append("-DI > +DI — sellers dominant")

    patterns = detect_patterns_at(df, -1)
    for p in patterns:
        if p.signal == "bullish":
            score += p.score * 18
            signals.append(p.detail)
        elif p.signal == "bearish":
            score += p.score * 18
            signals.append(p.detail)

    if vol and vol_sma and vol > vol_sma * 1.1:
        score += 6
        signals.append("Volume above 20-day avg — participation (Ch 12)")

    support, resistance = _support_resistance(df, 20)
    if support and price <= support * 1.02:
        score += 8
        signals.append(f"Near 20-day support ₹{support:,.0f}")
    if resistance and price >= resistance * 0.98:
        if price > resistance:
            score += 12
            signals.append(f"Breakout above resistance ₹{resistance:,.0f}")
        else:
            signals.append(f"Approaching resistance ₹{resistance:,.0f}")

    score = round(max(-100, min(100, score)), 1)
    action = _action_short(score)

    stop = support or (price - (atr or price * 0.03))
    target = resistance or (price + (atr or price * 0.03) * 2)
    if action in ("STRONG BUY", "BUY"):
        entry = f"₹{price:,.0f} or dip to SMA-20"
        stop_h = f"₹{stop:,.0f} (below support / 1× ATR)"
        target_h = f"₹{target:,.0f} (swing target)"
    else:
        entry = stop_h = target_h = "Wait for clearer daily setup"

    summary = (
        f"**{action}** swing view (score {score:+.0f}) — daily chart, hold **2–8 weeks**. "
        + (signals[0] if signals else "Mixed daily signals.")
    )

    return HorizonAnalysis(
        horizon="short",
        action=action,
        score=score,
        timeframe="2–8 weeks (daily chart)",
        entry_hint=entry,
        stop_hint=stop_h,
        target_hint=target_h,
        chart_signals=signals[:6],
        summary=summary,
    )


def analyze_long_term_chart(df: pd.DataFrame, yf_info: dict | None = None) -> HorizonAnalysis:
    """
    Position / investment setup from **daily** chart (months to years).
    SMA-50/200 structure, multi-month trend — Varsity Ch 13, 11.
    """
    if len(df) < 120:
        return HorizonAnalysis(
            horizon="long",
            action="WATCH",
            score=0.0,
            timeframe="6 months – 3 years (daily chart)",
            entry_hint="—",
            stop_hint="—",
            target_hint="—",
            summary="Need ~6 months of daily data for long-term chart view",
        )

    row = df.iloc[-1]
    price = float(row["Close"])
    sma50 = _safe_float(row.get("SMA_50"))
    sma200 = _safe_float(row.get("SMA_200"))
    rsi = _safe_float(row.get("RSI_14"))

    score = 0.0
    signals: list[str] = []

    if sma200 and price > sma200:
        score += 22
        signals.append(f"Price above SMA-200 (₹{sma200:,.0f}) — primary uptrend")
    elif sma200:
        score -= 28
        signals.append(f"Price below SMA-200 — long-term downtrend")

    if sma50 and sma200:
        if sma50 > sma200:
            score += 18
            signals.append("SMA-50 > SMA-200 — golden structure")
        else:
            score -= 15
            signals.append("SMA-50 below SMA-200 — death cross zone")

    if sma50 and price > sma50:
        score += 12
        signals.append("Holding above SMA-50 — institutional trend")
    elif sma50:
        score -= 12

    # 6-month trend
    if len(df) >= 126:
        ret_6m = (price / float(df["Close"].iloc[-126]) - 1) * 100
        if ret_6m > 5:
            score += 14
            signals.append(f"6-month return {ret_6m:+.1f}% — sustained uptrend")
        elif ret_6m < -10:
            score -= 14
            signals.append(f"6-month return {ret_6m:+.1f}% — structural weakness")

    # SMA-50 slope (rising over ~1 month)
    if sma50 and len(df) >= 25:
        sma50_prev = _safe_float(df.iloc[-22].get("SMA_50"))
        if sma50_prev and sma50 > sma50_prev * 1.01:
            score += 10
            signals.append("SMA-50 rising — trend strengthening")
        elif sma50_prev and sma50 < sma50_prev * 0.99:
            score -= 8
            signals.append("SMA-50 flattening/falling")

    # Recent golden cross (SMA50 crossed above SMA200 in last 60 bars)
    if sma50 and sma200 and len(df) >= 60:
        recent = df.tail(60)
        crosses = 0
        for i in range(1, len(recent)):
            p50 = _safe_float(recent.iloc[i - 1].get("SMA_50"))
            p200 = _safe_float(recent.iloc[i - 1].get("SMA_200"))
            c50 = _safe_float(recent.iloc[i].get("SMA_50"))
            c200 = _safe_float(recent.iloc[i].get("SMA_200"))
            if p50 and p200 and c50 and c200 and p50 <= p200 and c50 > c200:
                crosses += 1
        if crosses:
            score += 12
            signals.append("Recent golden cross on daily — long-term bullish")

    patterns = detect_patterns_at(df, -1)
    for p in patterns:
        if p.signal == "bullish" and "reversal up" in p.detail.lower():
            score += 10
            signals.append(p.detail)
        elif p.signal == "bearish" and "reversal down" in p.detail.lower():
            score -= 10
            signals.append(p.detail)

    if rsi is not None:
        if 40 <= rsi <= 65:
            score += 6
            signals.append(f"RSI {rsi:.0f} — healthy long-term momentum")
        elif rsi > 75:
            score -= 8
            signals.append(f"RSI {rsi:.0f} — extended; prefer dips to SMA-50")

    # Fundamental quality overlay (Yahoo / NSE enriched info)
    if yf_info:
        roe = yf_info.get("roe")
        if roe is not None and roe >= 0.15:
            score += 14
            signals.append(f"ROE {roe * 100:.0f}% — quality compounder")
        elif roe is not None and roe < 0.08:
            score -= 12
            signals.append(f"ROE {roe * 100:.0f}% — weak return on equity")
        eg = yf_info.get("earnings_growth")
        if eg is not None and eg > 0.08:
            score += 10
            signals.append(f"Earnings growth {eg * 100:+.0f}%")
        de = yf_info.get("debt_to_equity")
        if de is not None and de > 1.5:
            score -= 10
            signals.append(f"D/E {de:.1f} — leverage risk")
        pe = yf_info.get("pe_trailing") or yf_info.get("pe_ratio")
        if pe is not None and 10 < pe < 35:
            score += 5
            signals.append(f"P/E {pe:.0f} — reasonable valuation")

    score = round(max(-100, min(100, score)), 1)
    action = _action_long(score)

    support, _ = _support_resistance(df, 60)
    stop = sma200 or support or price * 0.85
    if action in ("CORE BUY", "ACCUMULATE"):
        entry = f"Accumulate near SMA-50 (₹{sma50:,.0f})" if sma50 else f"₹{price:,.0f}"
        stop_h = f"Monthly close below SMA-200 (₹{stop:,.0f})"
        target_h = "Trail with SMA-50; hold 1–3 years if trend intact"
    else:
        entry = stop_h = target_h = "Wait for trend repair on daily/weekly view"

    summary = (
        f"**{action}** long-term view (score {score:+.0f}) — **daily chart**, horizon **6mo–3yr**. "
        + (signals[0] if signals else "Mixed structure.")
    )

    return HorizonAnalysis(
        horizon="long",
        action=action,
        score=score,
        timeframe="6 months – 3 years (daily chart)",
        entry_hint=entry,
        stop_hint=stop_h,
        target_hint=target_h,
        chart_signals=signals[:6],
        summary=summary,
    )


def analyze_intraday_horizon(verdict) -> HorizonAnalysis:
    """
    Intraday buy/sell from 5m live chart (VWAP, OR, candles).
    Typical hold: same day / MIS — square off before 3:20 PM IST.
    """
    action = verdict.action
    score_map = {
        "STRONG BUY": 58,
        "BUY": 40,
        "WAIT": 0,
        "SELL": -40,
        "STRONG SELL": -58,
    }
    score = score_map.get(action, 0)
    conf_mult = {"high": 1.12, "medium": 1.0, "low": 0.88}
    score = round(max(-100, min(100, score * conf_mult.get(verdict.confidence, 1.0))), 1)

    signals: list[str] = list(verdict.reasons[:5])
    if verdict.current_candle:
        signals.insert(0, f"Current candle: {verdict.current_candle.candle_type} ({verdict.current_candle.bias})")
    if verdict.intraday:
        signals.append(f"Session bias: {verdict.intraday.session_bias}")

    if action in ("STRONG BUY", "BUY") and verdict.entry:
        entry = f"₹{verdict.entry:,.2f}"
        stop_h = f"₹{verdict.stop_loss:,.2f}" if verdict.stop_loss else "Below VWAP / OR low"
        target_h = f"₹{verdict.target:,.2f}" if verdict.target else "OR high / prior day high"
    elif action in ("SELL", "STRONG SELL"):
        entry = "Avoid longs / consider short MIS"
        stop_h = f"₹{verdict.stop_loss:,.2f}" if verdict.stop_loss else "—"
        target_h = f"₹{verdict.target:,.2f}" if verdict.target else "—"
    else:
        entry = stop_h = target_h = "Wait for VWAP / OR breakout candle"

    buy_label = action if action in ("STRONG BUY", "BUY") else (
        "NO BUY" if action in ("SELL", "STRONG SELL", "WAIT") else action
    )
    summary = (
        f"**{buy_label}** intraday (score {score:+.0f}) — **5m chart**, hold **today/MIS**. "
        + (verdict.summary[:120] if verdict.summary else "No clear edge.")
    )

    return HorizonAnalysis(
        horizon="intraday",
        action=buy_label if buy_label in ("STRONG BUY", "BUY") else action,
        score=score,
        timeframe="Today / MIS (5m chart)",
        entry_hint=entry,
        stop_hint=stop_h,
        target_hint=target_h,
        chart_signals=signals[:6],
        summary=summary,
    )
