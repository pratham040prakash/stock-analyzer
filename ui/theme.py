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
.assist-wrap { max-width: 680px; margin: 0 auto; padding: 0 4px; }
.assist-q {
    font-size: 1.05rem;
    font-weight: 600;
    margin: 0 0 12px 0;
    line-height: 1.35;
    opacity: 0.95;
}
.assist-card {
    border-radius: 16px;
    padding: 18px 20px;
    margin-bottom: 14px;
    border: 1px solid rgba(128,128,128,0.28);
    background: rgba(18,18,22,0.5);
}
.assist-hero { padding: 22px 22px 20px 22px; margin-bottom: 16px; }
.assist-verdict-xl {
    font-size: 2.75rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    line-height: 1.1;
    margin: 0 0 14px 0;
}
.assist-reason {
    font-size: 1.12rem;
    line-height: 1.55;
    margin: 0 0 12px 0;
    opacity: 0.94;
}
.assist-conf {
    font-size: 0.88rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    opacity: 0.75;
    margin: 0 0 8px 0;
}
.assist-conf-high { color: #00c853; }
.assist-conf-medium { color: #ffb300; }
.assist-conf-low { color: #ff6e40; }
.assist-conclusion {
    font-size: 0.95rem;
    margin: 14px 0 0 0;
    padding-top: 12px;
    border-top: 1px solid rgba(128,128,128,0.22);
    opacity: 0.88;
}
.assist-levels {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 8px;
    margin: 12px 0 4px 0;
}
.assist-level-box {
    border-radius: 10px;
    padding: 10px 8px;
    background: rgba(128,128,128,0.1);
    text-align: center;
}
.assist-level-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    opacity: 0.55;
    margin: 0 0 4px 0;
}
.assist-level-value {
    font-size: 0.95rem;
    font-weight: 700;
    margin: 0;
}
.assist-broker-ok { border-left: 4px solid #00c853; }
.assist-broker-warn { border-left: 4px solid #ffb300; }
.assist-broker-off { border-left: 4px solid #9e9e9e; opacity: 0.9; }
.assist-search-wrap {
    margin-top: 20px;
    padding-top: 16px;
    border-top: 1px solid rgba(128,128,128,0.2);
}
@media (max-width: 768px) {
    .assist-verdict-xl { font-size: 2.1rem; }
    .assist-levels { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
[data-theme="light"] .assist-card,
.light-theme .assist-card {
    background: rgba(255,255,255,0.96);
    border-color: rgba(0,0,0,0.08);
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

VERDICT_CANVAS_CSS = """
<style>
/* Phase 1 — Verdict Canvas (Today) */
.verdict-canvas-page [data-testid="stAppViewContainer"] > section.main > div {
    max-width: 430px;
    margin: 0 auto;
    padding: 0 0 120px 0;
}
.verdict-canvas-page [data-testid="stAppViewContainer"] {
    background: #0A0A0B;
}
.verdict-canvas-page [data-testid="stHeader"] {
    background: transparent;
}
.verdict-canvas-page .verdict-canvas-root {
    color: #F5F5F7;
    font-family: Inter, "SF Pro Display", system-ui, -apple-system, sans-serif;
    min-height: calc(100vh - 2rem);
    padding: 0 16px;
    box-sizing: border-box;
}
.verdict-canvas-root .vc-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 44px;
    padding-top: env(safe-area-inset-top, 0px);
    margin-bottom: 8px;
}
.verdict-canvas-root .vc-time {
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: rgba(245,245,247,0.45);
    margin: 0;
}
.verdict-canvas-root .vc-sync {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 500;
    color: rgba(245,245,247,0.55);
    margin: 0;
}
.verdict-canvas-root .vc-sync-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.verdict-canvas-root .vc-sync-ok { background: #00E676; }
.verdict-canvas-root .vc-sync-warn { background: #FFC107; }
.verdict-canvas-root .vc-sync-off { background: #FF6B6B; }
.verdict-canvas-root .vc-verdict-zone {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 280px;
    padding: 48px 0;
    border-radius: 0;
}
.verdict-canvas-root[data-verdict="wait"] .vc-verdict-zone {
    background: radial-gradient(ellipse 280px 200px at 50% 45%, rgba(255,193,7,0.06) 0%, transparent 70%);
}
.verdict-canvas-root[data-verdict="trade"] .vc-verdict-zone {
    background: radial-gradient(ellipse 280px 200px at 50% 45%, rgba(0,230,118,0.06) 0%, transparent 70%);
}
.verdict-canvas-root[data-verdict="pause"] .vc-verdict-zone {
    background: radial-gradient(ellipse 280px 200px at 50% 45%, rgba(255,107,107,0.05) 0%, transparent 70%);
}
.verdict-canvas-root .vc-verdict-word {
    font-size: 56px;
    font-weight: 600;
    letter-spacing: -0.02em;
    line-height: 1;
    text-align: center;
    margin: 0;
    width: 100%;
}
.verdict-canvas-root[data-verdict="wait"] .vc-verdict-word { color: #FFC107; }
.verdict-canvas-root[data-verdict="trade"] .vc-verdict-word { color: #00E676; }
.verdict-canvas-root[data-verdict="pause"] .vc-verdict-word { color: #FF6B6B; }
.verdict-canvas-root[data-verdict="rest"] .vc-verdict-word { color: #A1A1A6; }
.verdict-canvas-root[data-verdict="connect"] .vc-verdict-word { color: #64B5F6; }
.verdict-canvas-root .vc-mentor {
    font-size: 20px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.88);
    text-align: left;
    margin: 40px 0 32px 0;
    max-width: 358px;
}
/* AI thinking — partner reviewing, not software loading */
.verdict-canvas-root[data-verdict="thinking"] .vc-verdict-zone {
    background: radial-gradient(ellipse 280px 200px at 50% 45%, rgba(100,181,246,0.08) 0%, transparent 70%);
}
.verdict-canvas-root .vc-verdict-word.vc-thinking-word {
    font-size: 28px;
    font-weight: 500;
    letter-spacing: 0.02em;
    color: rgba(245,245,247,0.72);
    animation: vc-think-pulse 2.4s ease-in-out infinite;
}
.verdict-canvas-root .vc-thinking-dots span {
    display: inline-block;
    width: 6px;
    height: 6px;
    margin: 0 3px;
    border-radius: 50%;
    background: rgba(100,181,246,0.85);
    animation: vc-think-dot 1.2s ease-in-out infinite;
}
.verdict-canvas-root .vc-thinking-dots span:nth-child(2) { animation-delay: 0.15s; }
.verdict-canvas-root .vc-thinking-dots span:nth-child(3) { animation-delay: 0.3s; }
.verdict-canvas-root .vc-mentor.vc-mentor-thinking {
    color: rgba(245,245,247,0.42);
    font-style: normal;
}
.verdict-canvas-root .vc-sync-thinking .vc-sync-dot {
    background: rgba(100,181,246,0.9);
    animation: vc-sync-pulse 1.6s ease-in-out infinite;
}
@keyframes vc-think-pulse {
    0%, 100% { opacity: 0.55; }
    50% { opacity: 1; }
}
@keyframes vc-think-dot {
    0%, 80%, 100% { transform: translateY(0); opacity: 0.35; }
    40% { transform: translateY(-4px); opacity: 1; }
}
@keyframes vc-sync-pulse {
    0%, 100% { opacity: 0.45; transform: scale(0.92); }
    50% { opacity: 1; transform: scale(1); }
}
.verdict-canvas-root .vc-ghost-hint {
    text-align: center;
    margin: 16px 0 0 0;
}
.verdict-canvas-root .vc-ghost-hint [data-testid="stPopover"] button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: rgba(245,245,247,0.4) !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    min-height: 44px !important;
    padding: 10px 16px !important;
}
.verdict-canvas-root .vc-ghost-hint [data-testid="stPopover"] button:hover {
    color: rgba(245,245,247,0.65) !important;
    background: transparent !important;
}
.verdict-canvas-page [data-testid="stButton"] button[kind="primary"],
.verdict-canvas-page .vc-primary [data-testid="stLinkButton"] a {
    width: 100%;
    min-height: 52px !important;
    border-radius: 14px !important;
    font-size: 17px !important;
    font-weight: 600 !important;
    background: #F5F5F7 !important;
    color: #0A0A0B !important;
    border: none !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.24) !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-decoration: none !important;
}
.verdict-canvas-page [data-testid="stButton"] button[kind="primary"]:active,
.verdict-canvas-page .vc-primary [data-testid="stLinkButton"] a:active {
    background: #E8E8ED !important;
    transform: scale(0.98);
}
.verdict-canvas-page [data-testid="stPopover"] button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: rgba(245,245,247,0.4) !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    min-height: 44px !important;
    padding: 10px 16px !important;
}
.verdict-canvas-page [data-testid="stPopover"] button:hover {
    color: rgba(245,245,247,0.65) !important;
    background: transparent !important;
}
.verdict-canvas-page .vc-nav-row {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 999;
    background: #0A0A0B;
    border-top: 1px solid #1C1C1E;
    padding: 0 16px env(safe-area-inset-bottom, 8px) 16px;
    max-width: 430px;
    margin: 0 auto;
}
.verdict-canvas-page .vc-nav-row [data-testid="column"] {
    padding: 0 !important;
}
.verdict-canvas-page .vc-nav-row [data-testid="stButton"] button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: rgba(245,245,247,0.4) !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    min-height: 49px !important;
    padding: 6px 0 4px 0 !important;
    letter-spacing: 0.02em;
}
.verdict-canvas-page .vc-nav-today [data-testid="stButton"] button {
    color: #F5F5F7 !important;
    border-top: 2px solid #F5F5F7 !important;
    border-radius: 0 !important;
}
.verdict-canvas-page .vc-nav-trades [data-testid="stButton"] button {
    color: #F5F5F7 !important;
    border-top: 2px solid #F5F5F7 !important;
    border-radius: 0 !important;
}
.verdict-canvas-page .vc-nav-you [data-testid="stButton"] button {
    color: #F5F5F7 !important;
    border-top: 2px solid #F5F5F7 !important;
    border-radius: 0 !important;
}
.reflection-canvas-root .rc-hero-zone {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 180px;
    padding: 32px 0 20px 0;
    text-align: center;
}
.reflection-canvas-root .rc-hero-growing {
    background: radial-gradient(ellipse 280px 200px at 50% 40%, rgba(0,230,118,0.06) 0%, transparent 70%);
}
.reflection-canvas-root .rc-hero-steady {
    background: radial-gradient(ellipse 280px 200px at 50% 40%, rgba(161,161,166,0.05) 0%, transparent 70%);
}
.reflection-canvas-root .rc-hero-rebuilding {
    background: radial-gradient(ellipse 280px 200px at 50% 40%, rgba(255,193,7,0.06) 0%, transparent 70%);
}
.reflection-canvas-root .rc-hero-focused {
    background: radial-gradient(ellipse 280px 200px at 50% 40%, rgba(100,181,246,0.06) 0%, transparent 70%);
}
.reflection-canvas-root .rc-narrative {
    margin: 20px 0 12px 0;
}
.reflection-canvas-root .rc-narrative:first-of-type {
    margin-top: 24px;
}
.reflection-canvas-root .rc-coaching {
    font-size: 20px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.78);
    margin: 20px 0 12px 0;
    max-width: 358px;
}
.reflection-canvas-root .rc-forward {
    font-size: 17px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.5);
    font-style: italic;
    margin: 0 0 24px 0;
    max-width: 358px;
}
.verdict-canvas-page .vc-ghost-row {
    margin-top: 16px;
}
.verdict-canvas-page .vc-ghost-row [data-testid="stPopover"] button,
.verdict-canvas-page .vc-ghost-row [data-testid="stButton"] button {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: rgba(245,245,247,0.4) !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    min-height: 44px !important;
}
.verdict-canvas-page .vc-ghost-row [data-testid="stPopover"] button:hover,
.verdict-canvas-page .vc-ghost-row [data-testid="stButton"] button:hover {
    color: rgba(245,245,247,0.65) !important;
}
.verdict-canvas-page .vc-secondary [data-testid="stButton"] button {
    width: 100%;
    min-height: 44px !important;
    border-radius: 14px !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    background: transparent !important;
    color: rgba(245,245,247,0.4) !important;
    border: none !important;
    box-shadow: none !important;
    margin-top: 12px;
}
.verdict-canvas-page .vc-secondary [data-testid="stButton"] button:hover {
    color: rgba(245,245,247,0.65) !important;
}
.plan-canvas-root .pc-hero-zone {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 200px;
    padding: 32px 0 24px 0;
    text-align: center;
}
.plan-canvas-root .pc-hero-trade {
    background: radial-gradient(ellipse 280px 200px at 50% 40%, rgba(0,230,118,0.06) 0%, transparent 70%);
}
.plan-canvas-root .pc-context {
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #00E676;
    margin: 0 0 8px 0;
}
.plan-canvas-root .pc-symbol {
    font-size: 48px;
    font-weight: 600;
    letter-spacing: -0.02em;
    line-height: 1;
    color: #F5F5F7;
    margin: 0;
}
.plan-canvas-root .pc-symbol-muted {
    color: #A1A1A6;
}
.plan-canvas-root .pc-side {
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin: 10px 0 0 0;
    opacity: 0.7;
}
.plan-canvas-root .pc-side-long { color: #00E676; }
.plan-canvas-root .pc-side-short { color: #FF6B6B; }
.plan-canvas-root .pc-mentor-open {
    margin: 24px 0 20px 0;
}
.plan-canvas-root .pc-reason {
    font-size: 17px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.55);
    margin: 0 0 28px 0;
    max-width: 358px;
}
.plan-canvas-root .pc-line {
    font-variant-numeric: tabular-nums;
    margin: 0 0 12px 0;
    max-width: 358px;
}
.plan-canvas-root .pc-line-protect {
    font-size: 20px;
    font-weight: 500;
    line-height: 1.45;
    color: rgba(245,245,247,0.92);
}
.plan-canvas-root .pc-line-loss {
    font-size: 20px;
    font-weight: 600;
    line-height: 1.45;
    color: #FF8A80;
    margin-bottom: 20px;
}
.plan-canvas-root .pc-line-target {
    font-size: 17px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.4);
}
.plan-canvas-root .pc-lifecycle {
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 0.04em;
    color: rgba(245,245,247,0.45);
    margin: 24px 0 32px 0;
    max-width: 358px;
}
.verdict-canvas-page .vc-ask-wrap {
    position: fixed;
    right: max(16px, calc(50% - 215px + 16px));
    bottom: calc(49px + env(safe-area-inset-bottom, 8px) + 16px);
    z-index: 1000;
}
.verdict-canvas-page .vc-ask-wrap [data-testid="stButton"] button,
.verdict-canvas-page .vc-ask-wrap [data-testid="stLinkButton"] a {
    width: auto !important;
    min-width: 56px !important;
    height: 56px !important;
    min-height: 56px !important;
    border-radius: 28px !important;
    background: #1C1C1E !important;
    border: 1px solid #2C2C2E !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4) !important;
    color: #F5F5F7 !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    padding: 0 16px !important;
}
.verdict-canvas-root .vc-foot {
    font-size: 11px;
    color: rgba(245,245,247,0.25);
    text-align: center;
    margin: 24px 0 16px 0;
}
.vc-intel-stack {
    max-width: 398px;
    margin: 0 auto 24px;
    padding: 0 4px;
}
.vc-intel-block {
    border-top: 1px solid #2C2C2E;
    padding: 18px 0 4px 0;
}
.vc-intel-block:first-child {
    border-top: none;
    padding-top: 8px;
}
.vc-intel-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: rgba(245,245,247,0.38);
    margin: 0 0 10px 0;
}
.vc-intel-line {
    font-size: 15px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.82);
    margin: 0 0 8px 0;
}
.vc-intel-line.vc-intel-high { color: #00E676; }
.vc-intel-line.vc-intel-medium { color: #FFC107; }
.vc-intel-line.vc-intel-low { color: rgba(245,245,247,0.55); }
.vc-intel-line.vc-intel-warn { color: #FF9E80; }
.vc-intel-actions {
    max-width: 398px;
    margin: 8px auto 16px;
}
.vc-intel-actions [data-testid="stButton"] button {
    background: transparent !important;
    border: 1px solid #2C2C2E !important;
    color: rgba(245,245,247,0.72) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    min-height: 40px !important;
}
.vc-intel-foot {
    text-align: center;
    font-size: 11px;
    color: rgba(245,245,247,0.22);
    margin: 0 0 96px 0;
}
@media (max-width: 360px) {
    .verdict-canvas-root .vc-verdict-word { font-size: 44px; }
}
.verdict-canvas-page .vc-main-dimmed {
    filter: blur(12px);
    pointer-events: none;
    user-select: none;
}
.answer-canvas-overlay {
    position: fixed;
    inset: 0;
    z-index: 1001;
    background: rgba(10,10,11,0.96);
    max-width: 430px;
    margin: 0 auto;
    padding: 16px 16px calc(120px + env(safe-area-inset-bottom, 8px)) 16px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}
.answer-canvas-root {
    flex: 1;
    display: flex;
    flex-direction: column;
    max-width: 398px;
    margin: 0 auto;
    width: 100%;
}
.answer-canvas-overlay .ac-close-wrap {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 8px;
}
.answer-canvas-overlay .ac-close-wrap [data-testid="stButton"] button {
    width: 44px !important;
    min-width: 44px !important;
    height: 44px !important;
    min-height: 44px !important;
    border-radius: 22px !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: rgba(245,245,247,0.55) !important;
    font-size: 20px !important;
    padding: 0 !important;
}
.answer-canvas-root .ac-idle-hero {
    font-size: 32px;
    font-weight: 500;
    text-align: center;
    color: rgba(245,245,247,0.85);
    margin: 48px 0 32px 0;
}
.answer-canvas-overlay [data-testid="stForm"] {
    margin-top: 8px;
}
.answer-canvas-overlay [data-testid="stTextInput"] input {
    min-height: 52px !important;
    border-radius: 14px !important;
    background: #1C1C1E !important;
    border: 1px solid #2C2C2E !important;
    color: #F5F5F7 !important;
    font-size: 17px !important;
}
.answer-canvas-overlay [data-testid="stFormSubmitButton"] {
    display: none !important;
}
.answer-canvas-overlay [data-testid="column"] [data-testid="stButton"] button {
    background: transparent !important;
    border: 1px solid rgba(245,245,247,0.12) !important;
    box-shadow: none !important;
    color: rgba(245,245,247,0.4) !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    min-height: 40px !important;
    border-radius: 20px !important;
}
.answer-canvas-root .ac-query-echo {
    font-size: 13px;
    font-weight: 500;
    color: rgba(245,245,247,0.45);
    margin: 8px 0 6px 0;
    max-width: 358px;
}
.answer-canvas-root .ac-context-line {
    font-size: 13px;
    font-weight: 400;
    color: rgba(245,245,247,0.35);
    margin: 0 0 20px 0;
    max-width: 358px;
}
.answer-canvas-root .ac-hero-zone {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 140px;
    padding: 16px 0 20px 0;
    text-align: center;
}
.answer-canvas-root .ac-hero-trade {
    background: radial-gradient(ellipse 280px 200px at 50% 40%, rgba(0,230,118,0.06) 0%, transparent 70%);
}
.answer-canvas-root .ac-hero-wait {
    background: radial-gradient(ellipse 280px 200px at 50% 40%, rgba(255,193,7,0.06) 0%, transparent 70%);
}
.answer-canvas-root .ac-hero-pause {
    background: radial-gradient(ellipse 280px 200px at 50% 40%, rgba(255,107,107,0.06) 0%, transparent 70%);
}
.answer-canvas-root .ac-hero-rest {
    background: radial-gradient(ellipse 280px 200px at 50% 40%, rgba(161,161,166,0.05) 0%, transparent 70%);
}
.answer-canvas-root .ac-hero-connect {
    background: radial-gradient(ellipse 280px 200px at 50% 40%, rgba(100,181,246,0.06) 0%, transparent 70%);
}
.answer-canvas-root .ac-answer-word {
    font-size: 48px;
    font-weight: 600;
    letter-spacing: -0.02em;
    line-height: 1;
    color: #F5F5F7;
    margin: 0;
}
.answer-canvas-root[data-answer="wait"] .ac-answer-word,
.answer-canvas-root[data-answer="tight"] .ac-answer-word { color: #FFC107; }
.answer-canvas-root[data-answer="trade"] .ac-answer-word,
.answer-canvas-root[data-answer="buy"] .ac-answer-word,
.answer-canvas-root[data-answer="yes"] .ac-answer-word { color: #00E676; }
.answer-canvas-root[data-answer="pause"] .ac-answer-word,
.answer-canvas-root[data-answer="sell"] .ac-answer-word,
.answer-canvas-root[data-answer="no"] .ac-answer-word,
.answer-canvas-root[data-answer="risk"] .ac-answer-word { color: #FF6B6B; }
.answer-canvas-root[data-answer="rest"] .ac-answer-word,
.answer-canvas-root[data-answer="pass"] .ac-answer-word { color: #A1A1A6; }
.answer-canvas-root .ac-mentor {
    font-size: 20px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.92);
    margin: 20px 0 16px 0;
    max-width: 358px;
}
.answer-canvas-root .ac-recommendation {
    font-size: 17px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.55);
    margin: 0 0 28px 0;
    max-width: 358px;
}
.answer-canvas-overlay .ac-primary {
    max-width: 398px;
    margin: 0 auto;
    width: 100%;
}
.answer-canvas-overlay .ac-ghost {
    max-width: 398px;
    margin: 0 auto;
    text-align: center;
}
.trust-canvas-root .tc-hero-zone {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 160px;
    padding: 28px 0 20px 0;
    text-align: center;
}
.trust-canvas-root .tc-hero-honest {
    background: radial-gradient(ellipse 280px 200px at 50% 40%, rgba(161,161,166,0.05) 0%, transparent 70%);
}
.trust-canvas-root .tc-hero-learning {
    background: radial-gradient(ellipse 280px 200px at 50% 40%, rgba(100,181,246,0.06) 0%, transparent 70%);
}
.trust-canvas-root .tc-hero-earned {
    background: radial-gradient(ellipse 280px 200px at 50% 40%, rgba(0,230,118,0.06) 0%, transparent 70%);
}
.trust-canvas-root[data-trust="honest"] .pc-symbol { color: #A1A1A6; }
.trust-canvas-root[data-trust="learning"] .pc-symbol { color: #64B5F6; }
.trust-canvas-root[data-trust="earned"] .pc-symbol { color: #00E676; }
.trust-canvas-root .tc-mentor {
    font-size: 20px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.92);
    margin: 20px 0 14px 0;
    max-width: 358px;
}
.trust-canvas-root .tc-detail {
    font-size: 17px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.55);
    margin: 0 0 14px 0;
    max-width: 358px;
}
.trust-canvas-root .tc-miss {
    font-size: 17px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(255,193,7,0.85);
    margin: 0 0 16px 0;
    max-width: 358px;
}
.trust-canvas-root .tc-forward {
    font-size: 17px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.55);
    font-style: italic;
    margin: 0 0 28px 0;
    max-width: 358px;
}
.proof-canvas-root {
    color: #F5F5F7;
}
.proof-canvas-root .proof-echo {
    font-size: 13px;
    font-weight: 500;
    color: rgba(245,245,247,0.45);
    margin: 4px 0 10px 0;
}
.proof-canvas-root .proof-mentor {
    font-size: 20px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.92);
    margin: 0 0 14px 0;
    max-width: 358px;
}
.proof-canvas-root .proof-frame {
    width: 100%;
    max-width: 358px;
    height: 280px;
    border-radius: 16px;
    border: 1px solid #2C2C2E;
    overflow: hidden;
    margin-bottom: 4px;
}
.proof-canvas-root .proof-action {
    font-size: 17px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.55);
    margin: 12px 0 0 0;
    max-width: 358px;
}
.proof-canvas-root .proof-fossil-badge {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: rgba(255,193,7,0.75);
    margin: 0 0 6px 0;
}
.proof-canvas-root .proof-primary,
.proof-canvas-root .proof-ghost {
    max-width: 398px;
    margin: 0 auto;
    width: 100%;
}
.proof-canvas-root .proof-lwc-wrap {
    max-width: 358px;
    margin: 8px auto 0;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #2C2C2E;
}
.proof-canvas-root .proof-foot {
    text-align: center;
}
.proof-canvas-overlay {
    position: fixed;
    inset: 0;
    z-index: 1002;
    background: rgba(10,10,11,0.96);
    max-width: 430px;
    margin: 0 auto;
    padding: 16px 16px calc(120px + env(safe-area-inset-bottom, 8px)) 16px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}
.proof-canvas-root {
    flex: 1;
    max-width: 398px;
    margin: 0 auto;
    width: 100%;
}
.proof-canvas-overlay .pc-close-wrap {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 4px;
}
.proof-canvas-overlay .pc-close-wrap [data-testid="stButton"] button {
    width: 44px !important;
    min-width: 44px !important;
    height: 44px !important;
    background: transparent !important;
    border: none !important;
    color: rgba(245,245,247,0.55) !important;
    font-size: 20px !important;
}
.proof-canvas-root .proof-echo {
    font-size: 13px;
    font-weight: 500;
    color: rgba(245,245,247,0.45);
    margin: 4px 0 10px 0;
}
.proof-canvas-root .proof-mentor {
    font-size: 20px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.92);
    margin: 0 0 14px 0;
    max-width: 358px;
}
.proof-canvas-root .proof-frame {
    width: 100%;
    max-width: 358px;
    height: 280px;
    border-radius: 16px;
    border: 1px solid #2C2C2E;
    overflow: hidden;
    margin-bottom: 4px;
}
.proof-canvas-root .proof-action {
    font-size: 17px;
    font-weight: 400;
    line-height: 1.45;
    color: rgba(245,245,247,0.55);
    margin: 12px 0 0 0;
    max-width: 358px;
}
.proof-canvas-root .proof-fossil-badge {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: rgba(255,193,7,0.75);
    margin: 0 0 6px 0;
}
.proof-canvas-overlay .proof-primary {
    max-width: 398px;
    margin: 0 auto;
    width: 100%;
}
.proof-canvas-overlay .proof-ghost {
    max-width: 398px;
    margin: 0 auto;
}
.proof-canvas-overlay .proof-lwc-wrap {
    max-width: 358px;
    margin: 8px auto 0;
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #2C2C2E;
}
.proof-canvas-overlay .proof-foot {
    text-align: center;
}
</style>
<script>
(function() {
    var root = document.querySelector('.verdict-canvas-root, .plan-canvas-root, .reflection-canvas-root, .answer-canvas-overlay, .trust-canvas-root, .proof-canvas-root, .proof-canvas-overlay');
    if (root) {
        var app = document.querySelector('[data-testid="stAppViewContainer"]');
        if (app) app.classList.add('verdict-canvas-page');
    }
    if (document.querySelector('.answer-canvas-overlay')) {
        document.body.classList.add('ask-overlay-open');
    }
    if (document.querySelector('.proof-canvas-overlay')) {
        document.body.classList.add('proof-overlay-open');
    }
})();
</script>
"""

PARTNER_PAGE_ACTIVATE_JS = """
<script>
(function() {
    function applyPartnerPage() {
        var root = document.querySelector(
            '.verdict-canvas-root, .plan-canvas-root, .reflection-canvas-root, '
            + '.answer-canvas-overlay, .trust-canvas-root, .proof-canvas-root'
        );
        var app = document.querySelector('[data-testid="stAppViewContainer"]');
        if (root && app) {
            app.classList.add('verdict-canvas-page');
        }
        document.body.classList.toggle(
            'ask-overlay-open',
            !!document.querySelector('.answer-canvas-overlay')
        );
    }
    applyPartnerPage();
    setTimeout(applyPartnerPage, 0);
    setTimeout(applyPartnerPage, 120);
})();
</script>
"""
