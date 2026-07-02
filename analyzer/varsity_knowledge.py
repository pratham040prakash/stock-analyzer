"""
Zerodha Varsity — Technical Analysis knowledge base (cached in-app).

Source: https://zerodha.com/varsity/module/technical-analysis/
© Zerodha Varsity — summaries for educational use within this tool only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

VARSITY_MODULE_URL = "https://zerodha.com/varsity/module/technical-analysis/"


@dataclass(frozen=True)
class VarsityChapter:
    number: int
    title: str
    slug: str
    summary: str
    key_concepts: tuple[str, ...] = ()
    patterns: tuple[str, ...] = ()
    indicators: tuple[str, ...] = ()
    trading_rules: tuple[str, ...] = ()
    app_signals: tuple[str, ...] = ()  # maps to SignalDetail.name in analyzer

    @property
    def url(self) -> str:
        return f"https://zerodha.com/varsity/chapter/{self.slug}/"


# Full module — 22 chapters from Zerodha Varsity Technical Analysis
CHAPTERS: tuple[VarsityChapter, ...] = (
    VarsityChapter(
        1,
        "Background",
        "technical-analysis-background",
        "Introduces technical analysis (TA): studying price/volume charts to forecast short-term "
        "direction. Contrasts with fundamental analysis (business value). Sets realistic return "
        "expectations — TA is probability-based, not certainty.",
        key_concepts=(
            "TA studies price action and volume, not company financials",
            "Works across asset classes: stocks, indices, commodities, currencies",
            "Time-agnostic: same tools on daily, weekly, or intraday charts",
            "Requires discipline, risk management, and a trading plan",
        ),
        trading_rules=(
            "Define risk per trade before entry",
            "TA gives edge over many trades, not every single trade",
            "Combine multiple confirmations rather than one indicator",
        ),
    ),
    VarsityChapter(
        2,
        "Introducing Technical Analysis",
        "technical-analysis-introduction",
        "Core philosophy: all known information is reflected in price. Focus on OHLC (Open, High, "
        "Low, Close) and volume. Markets trend; history tends to repeat via crowd psychology.",
        key_concepts=(
            "Price discounts everything",
            "Prices move in trends (up, down, sideways)",
            "History repeats — chart patterns reflect human behaviour",
            "OHLC summarises each period's auction",
        ),
        indicators=("OHLC", "Volume"),
    ),
    VarsityChapter(
        3,
        "The Chart Types",
        "the-chart-types",
        "Compares line, bar, and candlestick charts. Candlesticks are preferred because they show "
        "open/close relationship and sentiment within each period visually.",
        key_concepts=(
            "Line chart: closing prices only — smooth but less detail",
            "Bar chart: OHLC per period",
            "Candlestick: body = open-close, wicks = high-low",
            "Green/white candle: close > open (bullish)",
            "Red/black candle: close < open (bearish)",
        ),
        app_signals=("Price Action",),
    ),
    VarsityChapter(
        4,
        "Getting Started with Candlesticks",
        "getting-started-with-candlesticks",
        "Candlestick anatomy and pattern families: single, double, and triple candle formations. "
        "Context matters — same pattern means different things in uptrend vs downtrend.",
        key_concepts=(
            "Range = High − Low; body = |Close − Open|",
            "Long wicks show rejection at that price level",
            "Patterns must be read with trend and volume",
            "Classification: bullish reversal, bearish reversal, continuation",
        ),
        patterns=("Bullish/Bearish classification", "Reversal vs continuation"),
        app_signals=("Candlestick (Varsity)",),
    ),
    VarsityChapter(
        5,
        "Single Candlestick Patterns (Part 1)",
        "single-candlestick-patterns-part-1",
        "Marubozu: candle with little or no wicks — strong conviction. Bullish Marubozu (close near "
        "high) suggests buyers dominated; Bearish Marubozu suggests sellers dominated.",
        key_concepts=(
            "Bullish Marubozu: open ≈ low, close ≈ high — buy on close or next day above high",
            "Bearish Marubozu: open ≈ high, close ≈ low — sell/short bias",
            "Stop-loss: opposite end of the Marubozu range",
            "More reliable with above-average volume",
        ),
        patterns=("Bullish Marubozu", "Bearish Marubozu"),
        trading_rules=(
            "Enter in direction of Marubozu on confirmation",
            "Place stop beyond the candle's extreme",
        ),
    ),
    VarsityChapter(
        6,
        "Single Candlestick Patterns (Part 2)",
        "single-candlestick-patterns-part-2",
        "Doji: open ≈ close — indecision. Spinning top: small body, long wicks — hesitation. "
        "Meaning depends on where they appear in a trend.",
        key_concepts=(
            "Doji at top of rally → potential bearish reversal",
            "Doji at bottom of decline → potential bullish reversal",
            "Spinning top signals uncertainty — wait for confirmation",
            "Never trade Doji alone without trend context",
        ),
        patterns=("Doji", "Spinning Top"),
    ),
    VarsityChapter(
        7,
        "Single Candlestick Patterns (Part 3)",
        "single-candlestick-patterns-part-3",
        "Hammer (bullish reversal at bottom) and Hanging Man (bearish reversal at top). Both have "
        "small body at top of range and long lower wick.",
        key_concepts=(
            "Hammer: appears after downtrend — buyers rejected lower prices",
            "Hanging Man: appears after uptrend — selling pressure emerging",
            "Confirm with next candle closing in expected direction",
            "Volume should increase on confirmation candle",
        ),
        patterns=("Hammer", "Hanging Man"),
    ),
    VarsityChapter(
        8,
        "Multiple Candlestick Patterns (Part 1)",
        "multiple-candlestick-patterns-part-1",
        "Engulfing patterns: second candle's body fully engulfs the first. Bullish engulfing at "
        "support is strong reversal signal; bearish engulfing at resistance is bearish.",
        key_concepts=(
            "Bullish Engulfing: red then larger green — buy signal at support",
            "Bearish Engulfing: green then larger red — sell signal at resistance",
            "Stronger when first candle is small and second is large",
            "Validate with volume expansion on engulfing candle",
        ),
        patterns=("Bullish Engulfing", "Bearish Engulfing"),
    ),
    VarsityChapter(
        9,
        "Multiple Candlestick Patterns (Part 2)",
        "multiple-candlestick-patterns-part-2",
        "Harami: inside bar — second candle contained within first. Bullish harami after decline; "
        "bearish harami after rally. Shows momentum pause before potential reversal.",
        key_concepts=(
            "Bullish Harami: large red then small green inside — reversal hint",
            "Bearish Harami: large green then small red inside",
            "Weaker than engulfing — needs confirmation",
            "Mother candle sets the range for stop placement",
        ),
        patterns=("Bullish Harami", "Bearish Harami"),
    ),
    VarsityChapter(
        10,
        "Multiple Candlestick Patterns (Part 3)",
        "multiple-candlestick-patterns-part-3",
        "Price gaps: area with no trading between sessions. Morning Star (bullish) and Evening "
        "Star (bearish) — three-candle reversal patterns.",
        key_concepts=(
            "Gap up/down shows strong overnight sentiment shift",
            "Morning Star: down → small body → strong up — bullish reversal",
            "Evening Star: up → small body → strong down — bearish reversal",
            "Gaps can act as support/resistance",
        ),
        patterns=("Morning Star", "Evening Star", "Gap Up", "Gap Down"),
    ),
    VarsityChapter(
        11,
        "The Support and Resistance",
        "the-support-and-resistance",
        "Support: price floor where buying emerges. Resistance: price ceiling where selling emerges. "
        "Broken support becomes resistance and vice versa. Used for entries, stops, and targets.",
        key_concepts=(
            "Support = demand zone; Resistance = supply zone",
            "More touches = stronger level (but can weaken over time)",
            "Breakout above resistance → bullish; breakdown below support → bearish",
            "Use prior swing highs/lows and round numbers",
        ),
        trading_rules=(
            "Buy near support with stop below; target next resistance",
            "Sell near resistance with stop above; target next support",
            "Wait for retest after breakout for safer entry",
        ),
        app_signals=("Support/Resistance",),
    ),
    VarsityChapter(
        12,
        "Volumes",
        "volumes",
        "Volume validates price moves. Rising price + rising volume = healthy trend. Rising price + "
        "falling volume = weak rally. Volume spikes at breakouts confirm conviction.",
        key_concepts=(
            "Volume precedes or confirms price",
            "High volume breakout is more trustworthy",
            "Low volume pullback in uptrend is often healthy",
            "Volume climax can mark exhaustion tops/bottoms",
        ),
        indicators=("Volume", "OBV"),
        app_signals=("Volume", "OBV"),
        trading_rules=(
            "Require volume confirmation on breakouts",
            "Be cautious of moves on thin volume",
        ),
    ),
    VarsityChapter(
        13,
        "Moving Averages",
        "moving-averages",
        "SMA and EMA smooth price to reveal trend. Common: 20, 50, 200-day. Crossovers (golden "
        "cross / death cross) and price vs MA for trend direction.",
        key_concepts=(
            "SMA: equal weight; EMA: more weight on recent prices",
            "Price above MA → bullish bias; below → bearish",
            "Golden cross: 50 crosses above 200 — long-term bullish",
            "Death cross: 50 crosses below 200 — long-term bearish",
            "MA acts as dynamic support/resistance",
        ),
        indicators=("SMA", "EMA"),
        app_signals=("Moving Averages", "SMA-20", "SMA-50", "SMA-200", "EMA 9/21"),
        trading_rules=(
            "Trade in direction of major MA slope",
            "Use shorter MA for entries, longer MA for trend filter",
        ),
    ),
    VarsityChapter(
        14,
        "Indicators (Part 1) — RSI",
        "indicators-part-1",
        "Relative Strength Index (RSI) measures momentum 0–100. Above 70 overbought; below 30 "
        "oversold. Divergence between price and RSI warns of weakening trend.",
        key_concepts=(
            "RSI 14 is default on daily charts",
            "RSI > 70: overbought — caution on fresh longs",
            "RSI < 30: oversold — potential bounce zone",
            "Bullish divergence: price lower low, RSI higher low",
            "Bearish divergence: price higher high, RSI lower high",
        ),
        indicators=("RSI"),
        app_signals=("RSI (14)", "RSI (7)"),
        trading_rules=(
            "In strong trends RSI can stay overbought/oversold — don't fade blindly",
            "Use RSI with trend filter (e.g. only buy oversold in uptrend)",
        ),
    ),
    VarsityChapter(
        15,
        "Indicators (Part 2) — MACD & Bollinger Bands",
        "indicators-part-2",
        "MACD: trend-following momentum (12/26/9 EMA crossover and histogram). Bollinger Bands: "
        "20-period SMA ± 2 std dev — volatility envelope. Squeeze precedes expansion.",
        key_concepts=(
            "MACD line crossing signal line → momentum shift",
            "MACD histogram expanding → strengthening move",
            "Bollinger squeeze: bands narrow → breakout likely",
            "Price at upper band: strong but possibly extended",
            "Price at lower band: weak but possibly oversold",
        ),
        indicators=("MACD", "Bollinger Bands"),
        app_signals=("MACD", "Bollinger Bands"),
        trading_rules=(
            "MACD works best in trending markets",
            "BB breakouts need volume confirmation",
        ),
    ),
    VarsityChapter(
        16,
        "The Fibonacci Retracements",
        "the-fibonacci-retracements",
        "Fibonacci ratios (23.6%, 38.2%, 50%, 61.8%, 78.6%) mark likely pullback levels in a "
        "trend. Golden ratio 1.618 underpins the sequence.",
        key_concepts=(
            "Draw from swing low to swing high (uptrend pullback)",
            "61.8% retracement is key support in strong trends",
            "38.2% shallow pullback in very strong trends",
            "Confluence with support/MA increases reliability",
        ),
        trading_rules=(
            "Enter long near Fib support in uptrend with stop below next level",
            "Target prior swing high or extension levels",
        ),
    ),
    VarsityChapter(
        17,
        "The Dow Theory (Part 1)",
        "the-dow-theory-part-1",
        "Dow Theory foundations: market has three trends — primary (months-years), secondary "
        "(weeks-months corrections), minor (days-weeks noise). Indices must confirm each other.",
        key_concepts=(
            "Primary trend is the main direction — trade with it",
            "Secondary trend is counter-trend correction",
            "Minor trend is short-term noise for swing traders",
            "Averages must confirm (e.g. Nifty + Bank Nifty alignment)",
            "Volume confirms trend validity",
        ),
        app_signals=("Trend", "Market Pulse"),
    ),
    VarsityChapter(
        18,
        "The Dow Theory (Part 2)",
        "the-dow-theory-part-2",
        "Trading ranges vs trending markets. Flag formations as continuation patterns. Risk-reward "
        "ratio guides position sizing and whether a trade is worth taking.",
        key_concepts=(
            "Identify range-bound vs trending before choosing strategy",
            "Flag: brief consolidation against trend, then continuation",
            "Minimum 1:2 risk-reward for swing trades",
            "Exit when thesis invalidates, not only at target",
        ),
        trading_rules=(
            "Don't use trend strategies in sideways ranges",
            "Size position inversely to stop distance",
            "1:2 R:R means risk ₹1 to make ₹2",
        ),
        app_signals=("Risk/Reward",),
    ),
    VarsityChapter(
        19,
        "The Finale — Daily TA Routine",
        "the-finale-helping-you-get-started",
        "Daily workflow: identify market trend → sector strength → stock setup → entry/stop/target "
        "→ risk check → journal the trade.",
        key_concepts=(
            "Start with index (Nifty) direction",
            "Scan for stocks in strong sectors",
            "Wait for setup at support/resistance with volume",
            "Pre-define entry, stop, and target before order",
            "Maintain a trading journal",
        ),
        trading_rules=(
            "No trade without a written plan",
            "Review losers and winners weekly",
            "Cap daily loss limit — stop trading when hit",
        ),
    ),
    VarsityChapter(
        20,
        "Other Indicators — ADX",
        "other-indicators",
        "Average Directional Index (ADX) measures trend strength (not direction). +DI and -DI "
        "show bullish vs bearish pressure. ADX > 25 suggests trending market.",
        key_concepts=(
            "ADX rising: trend strengthening",
            "ADX > 25: trending; ADX < 20: choppy/ranging",
            "+DI above -DI: bullish pressure",
            "-DI above +DI: bearish pressure",
            "Use ADX to filter — avoid MA crossovers when ADX is low",
        ),
        app_signals=("ADX",),
    ),
    VarsityChapter(
        21,
        "TradingView on Kite",
        "interesting-features-on-tradingview",
        "TradingView integrated in Zerodha Kite for advanced charting, drawing tools, and custom "
        "indicators. Same TA concepts apply — use for visual confirmation.",
        key_concepts=(
            "TradingView available inside Kite terminal",
            "Use for multi-timeframe analysis",
            "Draw S/R, trendlines, and Fibonacci manually",
            "Alerts for price/indicator conditions",
        ),
    ),
    VarsityChapter(
        22,
        "The Central Pivot Range (CPR)",
        "the-central-pivot-range",
        "CPR uses prior session High/Low/Close to compute pivot, BC, TC levels. Narrow CPR → "
        "potential trending day; wide CPR → sideways. Key intraday reference for Indian traders.",
        key_concepts=(
            "Pivot = (H + L + C) / 3",
            "CPR width indicates expected volatility",
            "Price above CPR → bullish bias for the day",
            "Price below CPR → bearish bias for the day",
            "Virgin CPR (untested) acts as magnet",
        ),
        indicators=("Pivot", "CPR", "VWAP"),
        app_signals=("VWAP", "Opening Range"),
        trading_rules=(
            "Use CPR with opening range breakout for intraday",
            "Narrow CPR + gap → strong directional day possible",
        ),
    ),
)

# Quick lookup: app signal name → chapter numbers
_SIGNAL_INDEX: dict[str, list[int]] = {}
for ch in CHAPTERS:
    for sig in ch.app_signals:
        _SIGNAL_INDEX.setdefault(sig, []).append(ch.number)
    for ind in ch.indicators:
        key = ind.upper()
        _SIGNAL_INDEX.setdefault(key, []).append(ch.number)

# Aliases for fuzzy matching
_SIGNAL_ALIASES: dict[str, str] = {
    "RSI": "RSI (14)",
    "SMA": "Moving Averages",
    "EMA": "EMA 9/21",
    "BB": "Bollinger Bands",
    "VOL": "Volume",
    "SUPPORT": "Support/Resistance",
    "RESISTANCE": "Support/Resistance",
    "VWAP": "VWAP",
    "OR": "Opening Range",
    "CANDLESTICK": "Candlestick (Varsity)",
}

# Core engine rules distilled from Varsity Ch 1, 2, 12, 18, 19, 20
ANALYSIS_PRINCIPLES: tuple[str, ...] = (
    "Price and volume together — never read price without volume (Ch 12)",
    "Trade with the primary trend; use ADX to avoid ranging markets (Ch 17, 20)",
    "Require multiple confirmations — no single indicator is enough (Ch 1, 19)",
    "Define entry, stop, and target before the trade; minimum 1:2 risk-reward (Ch 18)",
    "Support/resistance zones guide entries and stops (Ch 11)",
    "Candlestick patterns need trend context and volume confirmation (Ch 4–10)",
)

MIN_RISK_REWARD = 2.0  # Varsity Ch 18
ADX_TREND_THRESHOLD = 20  # Varsity Ch 20
RSI_OVERSOLD = 30  # Varsity Ch 14
RSI_OVERBOUGHT = 70  # Varsity Ch 14


def all_chapters() -> list[VarsityChapter]:
    return list(CHAPTERS)


def get_chapter(number: int) -> VarsityChapter | None:
    for ch in CHAPTERS:
        if ch.number == number:
            return ch
    return None


def search_chapters(query: str) -> list[VarsityChapter]:
    q = query.strip().lower()
    if not q:
        return list(CHAPTERS)
    out = []
    for ch in CHAPTERS:
        blob = " ".join(
            [ch.title, ch.summary, *ch.key_concepts, *ch.patterns, *ch.indicators]
        ).lower()
        if q in blob or q in ch.title.lower():
            out.append(ch)
    return out


def lookup_for_signal(signal_name: str) -> list[VarsityChapter]:
    """Return Varsity chapters relevant to an app signal (e.g. 'RSI (14)')."""
    name = signal_name.strip()
    if name in _SIGNAL_INDEX:
        return [get_chapter(n) for n in _SIGNAL_INDEX[name] if get_chapter(n)]
    for alias, canonical in _SIGNAL_ALIASES.items():
        if alias in name.upper():
            return lookup_for_signal(canonical)
    # partial match
    for key in _SIGNAL_INDEX:
        if key.lower() in name.lower() or name.lower() in key.lower():
            return lookup_for_signal(key)
    return []


def format_chapter_markdown(ch: VarsityChapter) -> str:
    lines = [
        f"### Ch {ch.number}: {ch.title}",
        f"*{ch.summary}*",
        f"[Read on Varsity]({ch.url})",
    ]
    if ch.key_concepts:
        lines.append("**Key concepts:**")
        lines.extend(f"- {c}" for c in ch.key_concepts)
    if ch.patterns:
        lines.append("**Patterns:** " + ", ".join(ch.patterns))
    if ch.indicators:
        lines.append("**Indicators:** " + ", ".join(ch.indicators))
    if ch.trading_rules:
        lines.append("**Rules:**")
        lines.extend(f"- {r}" for r in ch.trading_rules)
    return "\n".join(lines)


def format_signal_context(signal_name: str) -> str:
    """One-liner Varsity reference for a signal shown in analysis UI."""
    chapters = lookup_for_signal(signal_name)
    if not chapters:
        return f"📚 [Varsity TA]({VARSITY_MODULE_URL})"
    ch = chapters[0]
    return f"📚 Varsity Ch {ch.number} — [{ch.title}]({ch.url})"


def varsity_confidence_adjustment(signals: list) -> str:
    """Varsity Ch 1 & 19 — multiple agreeing signals raise confidence."""
    if not signals:
        return "low"
    bullish = sum(1 for s in signals if getattr(s, "signal", None) == "bullish")
    bearish = sum(1 for s in signals if getattr(s, "signal", None) == "bearish")
    magnitude = abs(sum(getattr(s, "score", 0) for s in signals) / max(len(signals), 1))
    if abs(bullish - bearish) >= 4 and magnitude > 0.35:
        return "high"
    if abs(bullish - bearish) >= 2 and magnitude > 0.2:
        return "medium"
    return "low"


def varsity_rr_acceptable(rr_ratio: float) -> bool:
    """Varsity Ch 18 — minimum 1:2 risk-reward."""
    return rr_ratio >= MIN_RISK_REWARD


def varsity_adx_is_trending(adx: float | None) -> bool:
    """Varsity Ch 20 — ADX below threshold = ranging/choppy."""
    if adx is None:
        return True
    return adx >= ADX_TREND_THRESHOLD


def module_overview_markdown() -> str:
    lines = [
        f"## Zerodha Varsity — Technical Analysis",
        f"Full module: [{VARSITY_MODULE_URL}]({VARSITY_MODULE_URL})",
        "",
        "All 22 chapters cached in this app for offline reference:",
        "",
    ]
    for ch in CHAPTERS:
        lines.append(f"**{ch.number}. {ch.title}** — {ch.summary[:120]}… [→]({ch.url})")
    return "\n".join(lines)
