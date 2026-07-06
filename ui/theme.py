"""Shared Streamlit theme constants."""

DISCLAIMER = (
    "**Disclaimer:** Technical analysis follows **[Zerodha Varsity TA](https://zerodha.com/varsity/module/technical-analysis/)**. "
    "Options data from **[NSE India](https://www.nseindia.com/)** (OI, IV, LTP). Combined with fundamentals. "
    "**Not financial advice.** Verify contracts on Kite before trading."
)

NAV_TABS = [
    "Suggestions",
    "Track Record",
    "Risk & Goals",
    "SIP & Goals",
    "Market Pulse",
    "Daily Advisor",
    "Global Markets",
    "Single Stock",
    "Alpha AI",
    "Compare",
    "Live Charts",
    "NSE Options",
    "Batch Scanner",
    "Screener",
    "Penny Picks",
    "My Portfolio",
    "Backtest",
    "Varsity TA",
]

NAV_GROUPS: dict[str, list[str]] = {
    "🎯 Suggestions": [
        "Suggestions",
        "Track Record",
    ],
    "📈 More trading": [
        "Market Pulse",
        "Live Charts",
        "NSE Options",
    ],
    "🔍 Research": [
        "Alpha AI",
        "Single Stock",
        "Compare",
        "Batch Scanner",
        "Screener",
        "Penny Picks",
        "Global Markets",
    ],
    "💼 Portfolio": [
        "My Portfolio",
        "Daily Advisor",
        "SIP & Goals",
        "Risk & Goals",
    ],
    "📚 Learn": [
        "Backtest",
        "Varsity TA",
    ],
}

from analyzer.app_mode import is_simple_cloud_mode

SIMPLE_NAV_GROUPS: dict[str, list[str]] = {
    "🎯 Suggestions": [
        "Suggestions",
        "Track Record",
    ],
    "🔍 Research": [
        "Alpha AI",
    ],
}

DEFAULT_NAV_GROUP = "🎯 Suggestions"
DEFAULT_NAV_TAB = "Suggestions"


def active_nav_groups() -> dict[str, list[str]]:
    """Full nav by default; SIMPLE_CLOUD_MODE=1 trims to suggestions + Alpha AI."""
    if is_simple_cloud_mode():
        return SIMPLE_NAV_GROUPS
    return NAV_GROUPS


def nav_group_for_tab(tab: str) -> str:
    for group, tabs in active_nav_groups().items():
        if tab in tabs:
            return group
    return DEFAULT_NAV_GROUP


def ensure_tab_in_group(tab: str, group: str) -> str:
    tabs = active_nav_groups().get(group, active_nav_groups()[DEFAULT_NAV_GROUP])
    return tab if tab in tabs else tabs[0]

MOBILE_CSS = """
<style>
@media (max-width: 768px) {
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    div[data-testid="stRadio"] > div {
        flex-wrap: wrap !important;
    }
    .compact-nav-hint {
        display: block !important;
    }
}
.watchlist-card {
    border: 1px solid rgba(128,128,128,0.35);
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
    background: rgba(30,30,30,0.25);
}
.watchlist-card h4 {
    margin: 0 0 6px 0;
    font-size: 1.05rem;
}
.watchlist-levels {
    font-size: 0.95rem;
    line-height: 1.5;
    margin: 6px 0;
}
.watchlist-meta {
    font-size: 0.8rem;
    opacity: 0.85;
}
</style>
"""

LIGHT_THEME_CSS = """
<style>
[data-testid="stAppViewContainer"] {
    background-color: #f5f7fa !important;
    color: #1a1a2e !important;
}
[data-testid="stSidebar"] {
    background-color: #ffffff !important;
}
[data-testid="stMetric"] {
    background-color: rgba(0,0,0,0.04);
    border-radius: 8px;
    padding: 8px;
}
.watchlist-card {
    background: rgba(255,255,255,0.9) !important;
    border-color: rgba(0,0,0,0.12) !important;
}
</style>
"""

STICKY_SUMMARY_CSS = """
<style>
.alpha-sticky-summary {
    position: sticky;
    top: 3.5rem;
    z-index: 100;
    background: rgba(14, 17, 23, 0.92);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(128,128,128,0.35);
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 16px;
}
[data-theme="light"] .alpha-sticky-summary,
.light-theme .alpha-sticky-summary {
    background: rgba(245, 247, 250, 0.95);
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
