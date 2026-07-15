"""Shared Streamlit theme constants."""

DISCLAIMER = (
    "**Disclaimer:** Technical analysis follows **[Zerodha Varsity TA](https://zerodha.com/varsity/module/technical-analysis/)**. "
    "Options data from **[NSE India](https://www.nseindia.com/)** (OI, IV, LTP). Combined with fundamentals. "
    "**Not financial advice.** Verify contracts on Kite before trading."
)

NAV_TABS = [
    "Home",
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
    "Live Options Coach",
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
        "Home",
        "Suggestions",
        "Track Record",
    ],
    "📈 More trading": [
        "Market Pulse",
        "Live Charts",
        "Live Options Coach",
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
        "Home",
        "Suggestions",
        "Track Record",
    ],
    "🔍 Research": [
        "Alpha AI",
    ],
}

DEFAULT_NAV_GROUP = "🎯 Suggestions"
DEFAULT_NAV_TAB = "Home"


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

HOME_UI_CSS = """
<style>
.home-wrap { max-width: 640px; margin: 0 auto; }
.dash-wrap { max-width: 1120px; margin: 0 auto; padding: 0 4px; }
.dash-brand {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    opacity: 0.55;
    margin: 0 0 2px 0;
}
.dash-tagline {
    font-size: 1.05rem;
    opacity: 0.82;
    margin: 0 0 20px 0;
    font-weight: 500;
}
.dash-section-head {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin: 22px 0 10px 0;
}
.dash-section-title {
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    opacity: 0.7;
    margin: 0;
    font-weight: 700;
}
.dash-section-sub {
    font-size: 0.78rem;
    opacity: 0.5;
}
.dash-card {
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 4px;
    border: 1px solid rgba(128,128,128,0.28);
    background: rgba(18,18,22,0.45);
}
.dash-half-card { min-height: 180px; }
.dash-tile-grid {
    display: grid;
    gap: 10px;
    margin-bottom: 10px;
}
.dash-tile-grid-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.dash-tile-grid-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.dash-tile {
    border-radius: 10px;
    padding: 10px 12px;
    background: rgba(128,128,128,0.1);
    border: 1px solid rgba(128,128,128,0.18);
}
.dash-tile-label {
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    opacity: 0.58;
    margin: 0 0 4px 0;
}
.dash-tile-value {
    font-size: 0.95rem;
    font-weight: 600;
    margin: 0;
    line-height: 1.35;
}
.dash-tile-hint {
    font-size: 0.72rem;
    opacity: 0.55;
    margin: 4px 0 0 0;
}
.dash-decision-card { padding: 18px 20px; }
.dash-verdict {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 12px;
    border: 2px solid transparent;
}
.dash-verdict-label {
    font-size: 1.65rem;
    font-weight: 800;
    letter-spacing: 0.04em;
}
.dash-verdict-conf {
    font-size: 0.95rem;
    opacity: 0.85;
    white-space: nowrap;
}
.dash-verdict-act {
    background: linear-gradient(135deg, rgba(0,200,83,0.2), rgba(0,200,83,0.06));
    border-color: #00c853;
}
.dash-verdict-wait {
    background: linear-gradient(135deg, rgba(255,179,0,0.18), rgba(255,110,64,0.06));
    border-color: #ffb300;
}
.dash-verdict-pass {
    background: linear-gradient(135deg, rgba(213,0,0,0.18), rgba(255,82,82,0.06));
    border-color: #ff5252;
}
.dash-verdict-reduce {
    background: linear-gradient(135deg, rgba(255,214,0,0.16), rgba(255,193,7,0.05));
    border-color: #ffd600;
}
.dash-verdict-defensive {
    background: linear-gradient(135deg, rgba(158,158,158,0.16), rgba(117,117,117,0.06));
    border-color: #9e9e9e;
}
.dash-reason {
    font-size: 1.02rem;
    line-height: 1.5;
    margin: 0 0 10px 0;
    opacity: 0.92;
}
.dash-evidence-title {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    opacity: 0.6;
    margin: 12px 0 6px 0;
}
.dash-evidence-list {
    margin: 0;
    padding-left: 18px;
    font-size: 0.9rem;
    line-height: 1.45;
    opacity: 0.88;
}
.dash-next {
    margin: 12px 0 0 0;
    font-size: 0.95rem;
    padding: 10px 12px;
    border-radius: 10px;
    background: rgba(33,150,243,0.1);
    border-left: 3px solid #2196f3;
}
@media (max-width: 900px) {
    .dash-tile-grid-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .dash-tile-grid-3 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .dash-verdict { flex-direction: column; align-items: flex-start; }
}
@media (max-width: 768px) {
    .dash-wrap { padding: 0 2px; }
    .dash-verdict-label { font-size: 1.4rem; }
}
[data-theme="light"] .dash-card,
.light-theme .dash-card {
    background: rgba(255,255,255,0.94);
    border-color: rgba(0,0,0,0.08);
}
[data-theme="light"] .dash-tile,
.light-theme .dash-tile {
    background: rgba(0,0,0,0.04);
    border-color: rgba(0,0,0,0.06);
}
.home-hero {
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 14px;
    border: 2px solid transparent;
}
.home-hero-ok {
    background: linear-gradient(135deg, rgba(0,200,83,0.18), rgba(0,200,83,0.06));
    border-color: #00c853;
}
.home-hero-wait {
    background: linear-gradient(135deg, rgba(213,0,0,0.16), rgba(255,110,64,0.06));
    border-color: #ff6e40;
}
.home-hero h2 { margin: 0 0 6px 0; font-size: 1.55rem; font-weight: 700; }
.home-hero p { margin: 0; font-size: 1rem; opacity: 0.92; }
.home-now {
    border-radius: 12px;
    padding: 14px 16px;
    margin: 12px 0 18px 0;
    background: rgba(33,150,243,0.12);
    border-left: 4px solid #2196f3;
    font-size: 1.05rem;
    line-height: 1.45;
}
.home-stock {
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 8px;
    border: 1px solid rgba(128,128,128,0.35);
    background: rgba(30,30,30,0.2);
}
.home-stock-selected {
    border: 2px solid #ffd600;
    background: rgba(255,214,0,0.08);
}
.home-stock .sym { font-size: 1.25rem; font-weight: 700; margin: 0 0 6px 0; }
.home-stock .levels { font-size: 0.95rem; margin: 0; opacity: 0.9; }
.home-section { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em;
    opacity: 0.65; margin: 18px 0 8px 0; }
div[data-testid="stHorizontalBlock"] .home-metric [data-testid="stMetric"] {
    background: rgba(128,128,128,0.12);
    border-radius: 10px;
    padding: 10px 8px;
}
.home-wrap [data-testid="stButton"] button {
    min-height: 3rem;
    font-size: 1rem;
    font-weight: 600;
    border-radius: 10px;
}
@media (max-width: 768px) {
    .home-hero h2 { font-size: 1.35rem; }
    .home-wrap { padding: 0 2px; }
    .home-wrap [data-testid="stButton"] button { min-height: 3.25rem; font-size: 1.05rem; }
}
[data-theme="light"] .home-stock,
.light-theme .home-stock {
    background: rgba(255,255,255,0.95);
    border-color: rgba(0,0,0,0.1);
}
[data-theme="light"] .home-stock-selected,
.light-theme .home-stock-selected {
    background: rgba(255,214,0,0.15);
}
/* Investment OS */
.os-brand {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    opacity: 0.55;
    margin: 0 0 4px 0;
}
.os-hero-prep { border-color: #9e9e9e; background: rgba(158,158,158,0.1); }
.os-hero-closed { border-color: #757575; background: rgba(117,117,117,0.12); }
.os-module {
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 8px;
    border: 1px solid rgba(128,128,128,0.3);
    background: rgba(20,20,24,0.35);
}
.os-module-ok { border-left: 4px solid #00c853; }
.os-module-wait { border-left: 4px solid #ff6e40; }
.os-module-warn { border-left: 4px solid #ffd600; }
.os-module-info { border-left: 4px solid #2196f3; }
.os-module-off { border-left: 4px solid #616161; opacity: 0.85; }
.os-module-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 4px;
}
.os-module-label {
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    opacity: 0.75;
}
.os-module-q { font-size: 0.82rem; opacity: 0.6; margin: 0 0 6px 0; }
.os-module-answer { font-size: 1.02rem; font-weight: 600; margin: 0; line-height: 1.35; }
.os-module-detail { font-size: 0.88rem; opacity: 0.78; margin: 6px 0 0 0; line-height: 1.4; }
.os-conf {
    font-size: 0.75rem;
    opacity: 0.65;
    white-space: nowrap;
}
[data-theme="light"] .os-module,
.light-theme .os-module {
    background: rgba(255,255,255,0.92);
    border-color: rgba(0,0,0,0.08);
}
</style>
"""
