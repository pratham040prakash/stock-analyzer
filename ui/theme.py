"""Shared Streamlit theme constants."""

DISCLAIMER = (
    "**Disclaimer:** Technical analysis follows **[Zerodha Varsity TA](https://zerodha.com/varsity/module/technical-analysis/)**. "
    "Options data from **[NSE India](https://www.nseindia.com/)** (OI, IV, LTP). Combined with fundamentals. "
    "**Not financial advice.** Verify contracts on Kite before trading."
)

NAV_TABS = [
    "Risk & Goals",
    "Market Pulse",
    "Daily Advisor",
    "Global Markets",
    "Single Stock",
    "Intraday",
    "Live Charts",
    "NSE Options",
    "Watchlist",
    "Zerodha Portfolio",
    "Backtest",
    "Track Record",
    "Varsity TA",
]

MOBILE_CSS = """
<style>
@media (max-width: 768px) {
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
}
</style>
"""

REC_COLORS = {
    "STRONG BUY": "#00c853",
    "BUY": "#69f0ae",
    "HOLD": "#ffd600",
    "SELL": "#ff6e40",
    "STRONG SELL": "#d50000",
    "ERROR": "#888888",
}

ACTION_COLORS = {
    "STRONG BUY": "#00c853",
    "BUY": "#69f0ae",
    "ACCUMULATE": "#a5d6a7",
    "HOLD": "#ffd600",
    "REDUCE": "#ff6e40",
    "SELL": "#d50000",
    "AVOID": "#d50000",
    **REC_COLORS,
}

SIGNAL_ICONS = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}

INTRADAY_SETUP_COLORS = {
    "BUY": "#00c853",
    "SELL": "#d50000",
    "WAIT": "#ffd600",
    "STRONG BUY": "#00c853",
    "STRONG SELL": "#d50000",
}

OPTIONS_COLORS = {
    "STRONG CE": "#00e676",
    "BUY CE": "#69f0ae",
    "NO TRADE": "#ffd600",
    "BUY PE": "#ff8a80",
    "STRONG PE": "#ff1744",
}

GLOBAL_BIAS_COLORS = {
    "BULLISH": "#00c853",
    "BEARISH": "#d50000",
    "NEUTRAL": "#ffd600",
}
