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

APEX_V2_VISUAL_POLISH_CSS = """
<style>
/* V2-003 — shared design tokens and visual polish */
.verdict-canvas-page {
    --apex-font: Inter, "SF Pro Display", system-ui, -apple-system, sans-serif;
    --apex-text: #F5F5F7;
    --apex-text-secondary: rgba(245,245,247,0.82);
    --apex-text-muted: rgba(245,245,247,0.52);
    --apex-text-subtle: rgba(245,245,247,0.38);
    --apex-surface: rgba(255,255,255,0.04);
    --apex-surface-elevated: rgba(255,255,255,0.06);
    --apex-border: rgba(255,255,255,0.08);
    --apex-radius-sm: 10px;
    --apex-radius-md: 14px;
    --apex-radius-lg: 18px;
    --apex-space-xs: 8px;
    --apex-space-sm: 12px;
    --apex-space-md: 16px;
    --apex-space-lg: 24px;
    --apex-title-size: 38px;
    --apex-section-size: 11px;
    --apex-body-size: 16px;
    --apex-body-lg-size: 18px;
    --apex-badge-buy: #30D158;
    --apex-badge-wait: #0A84FF;
    --apex-badge-pass: #A1A1A6;
    --apex-badge-reduce: #FF9F0A;
    --apex-badge-sell: #FF453A;
}
.verdict-canvas-page .apex-command-badge,
.verdict-canvas-page .apex-inv-badge,
.verdict-canvas-page .apex-rex-badge,
.verdict-canvas-page .apex-thesis-badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-radius: 999px;
    padding: 6px 12px;
    line-height: 1.2;
    margin: 0 0 var(--apex-space-md) 0;
    background: var(--apex-surface-elevated);
    color: var(--apex-text-secondary);
}
.verdict-canvas-page .apex-command-badge[data-badge="buy"],
.verdict-canvas-page .apex-inv-badge[data-badge="buy"],
.verdict-canvas-page .apex-rex-badge.apex-rex-buy {
    color: var(--apex-badge-buy);
    background: rgba(48,209,88,0.16);
}
.verdict-canvas-page .apex-command-badge[data-badge="wait"],
.verdict-canvas-page .apex-inv-badge[data-badge="wait"],
.verdict-canvas-page .apex-rex-badge.apex-rex-wait {
    color: var(--apex-badge-wait);
    background: rgba(10,132,255,0.16);
}
.verdict-canvas-page .apex-command-badge[data-badge="pass"],
.verdict-canvas-page .apex-inv-badge[data-badge="pass"],
.verdict-canvas-page .apex-rex-badge.apex-rex-hold {
    color: var(--apex-badge-pass);
    background: var(--apex-surface-elevated);
}
.verdict-canvas-page .apex-command-badge[data-badge="reduce"],
.verdict-canvas-page .apex-rex-badge.apex-rex-reduce {
    color: var(--apex-badge-reduce);
    background: rgba(255,159,10,0.16);
}
.verdict-canvas-page .apex-command-badge[data-badge="sell"],
.verdict-canvas-page .apex-rex-badge.apex-rex-sell {
    color: var(--apex-badge-sell);
    background: rgba(255,69,58,0.16);
}
.verdict-canvas-page .apex-health-chip,
.verdict-canvas-page .apex-risk-badge,
.verdict-canvas-page .vc-ribbon-chip {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 6px 10px;
    border-radius: 999px;
    line-height: 1.2;
    background: var(--apex-surface-elevated);
    color: var(--apex-text-secondary);
    border: 1px solid var(--apex-border);
}
.verdict-canvas-page .apex-command-hero,
.verdict-canvas-page .apex-inv-hero {
    background: linear-gradient(180deg, rgba(255,255,255,0.035) 0%, transparent 100%);
    border: 1px solid var(--apex-border);
    border-radius: var(--apex-radius-lg);
    padding: var(--apex-space-md) var(--apex-space-sm) var(--apex-space-lg);
    margin-bottom: var(--apex-space-sm);
}
.verdict-canvas-page .apex-command-name,
.verdict-canvas-page .apex-inv-name {
    font-size: var(--apex-title-size);
    font-weight: 600;
    letter-spacing: -0.03em;
    line-height: 1.08;
    color: var(--apex-text);
}
.verdict-canvas-page .apex-section-label {
    font-size: var(--apex-section-size);
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: rgba(245,245,247,0.42);
    margin: 0 0 14px 0;
}
.verdict-canvas-page .apex-command-name {
    margin: 0 0 14px 0;
}
.verdict-canvas-page .apex-status-strip {
    background: var(--apex-surface);
    border: 1px solid var(--apex-border);
    border-radius: var(--apex-radius-md);
    padding: var(--apex-space-md) var(--apex-space-sm);
    margin: var(--apex-space-sm) 0 var(--apex-space-lg);
}
.verdict-canvas-page .apex-review-depth {
    background: var(--apex-surface);
    border: 1px solid var(--apex-border);
    border-radius: var(--apex-radius-md);
    padding: var(--apex-space-md) var(--apex-space-sm) var(--apex-space-xs);
    margin-top: var(--apex-space-md);
}
.verdict-canvas-page .plan-canvas-root .pc-details {
    background: var(--apex-surface);
    border: 1px solid var(--apex-border);
    border-radius: var(--apex-radius-md);
    padding: var(--apex-space-md) var(--apex-space-sm);
    margin-bottom: var(--apex-space-md);
}
.verdict-canvas-page .apex-action-row {
    padding: 0 0 var(--apex-space-md);
    gap: var(--apex-space-xs);
}
.verdict-canvas-page .apex-action-row [data-testid="stPopover"] button {
    width: 100%;
    min-height: 52px !important;
    border-radius: var(--apex-radius-md) !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    background: transparent !important;
    color: var(--apex-text) !important;
    border: 1px solid var(--apex-border) !important;
    box-shadow: none !important;
}
.verdict-canvas-page .apex-action-row [data-testid="stPopover"] button:hover {
    background: var(--apex-surface-elevated) !important;
    border-color: rgba(255,255,255,0.14) !important;
}
.verdict-canvas-page .apex-command-context {
    padding-top: var(--apex-space-lg);
    border-top: 1px solid rgba(255,255,255,0.04);
    margin-top: var(--apex-space-xs);
}
.verdict-canvas-page .apex-loading .apex-greeting-title {
    animation: apex-loading-pulse 1.8s ease-in-out infinite;
}
.verdict-canvas-page .apex-loading .apex-greeting-sub,
.verdict-canvas-page .apex-loading .apex-greeting-meta {
    color: var(--apex-text-subtle);
}
@keyframes apex-loading-pulse {
    0%, 100% { opacity: 0.55; }
    50% { opacity: 1; }
}
.verdict-canvas-page [data-testid="stExpander"] details {
    border: 1px solid var(--apex-border);
    border-radius: var(--apex-radius-sm);
    background: rgba(255,255,255,0.02);
    margin-bottom: var(--apex-space-xs);
}
.verdict-canvas-page [data-testid="stExpander"] summary {
    font-size: 15px !important;
    font-weight: 600 !important;
    color: var(--apex-text-secondary) !important;
    padding: var(--apex-space-sm) var(--apex-space-sm) !important;
}
.verdict-canvas-page [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    padding: 0 var(--apex-space-sm) var(--apex-space-sm) !important;
}
.verdict-canvas-page .plan-canvas-root .vc-mentor {
    font-size: var(--apex-body-lg-size);
    line-height: 1.5;
    color: var(--apex-text-secondary);
    padding: var(--apex-space-md);
    border: 1px solid var(--apex-border);
    border-radius: var(--apex-radius-md);
    background: var(--apex-surface);
}
</style>
"""

APEX_V2_PERFORMANCE_ACCESSIBILITY_CSS = """
<style>
/* V2-004 — performance hints, focus, contrast, responsive, reduced motion */
.verdict-canvas-page {
    --apex-text-subtle: rgba(245,245,247,0.48);
    --apex-focus-ring: #0A84FF;
    --apex-focus-glow: rgba(10,132,255,0.28);
}
.verdict-canvas-page .apex-section-label,
.verdict-canvas-page .apex-command-greeting,
.verdict-canvas-page .apex-greeting-meta,
.verdict-canvas-page .apex-command-freshness,
.verdict-canvas-page .apex-status-k,
.verdict-canvas-page .apex-learning-meta,
.verdict-canvas-page .apex-foot {
    color: var(--apex-text-subtle);
}
.verdict-canvas-page .apex-section-label {
    color: rgba(245,245,247,0.52);
}
.verdict-canvas-page .apex-command-context,
.verdict-canvas-page .apex-review-depth,
.verdict-canvas-page .plan-canvas-root .pc-details {
    content-visibility: auto;
    contain-intrinsic-size: auto 220px;
}
.verdict-canvas-page .apex-status-strip-row {
    row-gap: 12px;
}
@media (max-width: 380px) {
    .verdict-canvas-page .apex-command-name,
    .verdict-canvas-page .apex-inv-name {
        font-size: clamp(28px, 8vw, var(--apex-title-size, 38px));
    }
    .verdict-canvas-page .apex-status-item {
        min-width: calc(50% - 8px);
        flex: 1 1 calc(50% - 8px);
    }
    .verdict-canvas-page .verdict-canvas-root,
    .verdict-canvas-page .plan-canvas-root {
        padding-left: max(12px, env(safe-area-inset-left, 0px));
        padding-right: max(12px, env(safe-area-inset-right, 0px));
    }
}
.verdict-canvas-page :where(
    [data-testid="stButton"] button,
    [data-testid="stPopover"] button,
    [data-testid="stExpander"] summary,
    [data-testid="stLinkButton"] a
):focus-visible {
    outline: 2px solid var(--apex-focus-ring) !important;
    outline-offset: 2px !important;
    box-shadow: 0 0 0 4px var(--apex-focus-glow) !important;
}
.verdict-canvas-page .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}
.verdict-canvas-page :not(.apex-action-row) [data-testid="stPopover"] button {
    color: rgba(245,245,247,0.72) !important;
}
@media (prefers-reduced-motion: reduce) {
    .verdict-canvas-page *,
    .verdict-canvas-page *::before,
    .verdict-canvas-page *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
    .verdict-canvas-page [data-testid="stButton"] button[kind="primary"]:active,
    .verdict-canvas-page .vc-primary [data-testid="stLinkButton"] a:active {
        transform: none !important;
    }
}
</style>
"""

APEX_BRIEF_EXPERIENCE_CSS = """
<style>
.verdict-canvas-page .apex-brief-page,
.verdict-canvas-page .apex-section {
    color: var(--apex-text, #F5F5F7);
    font-family: var(--apex-font, Inter, "SF Pro Display", system-ui, -apple-system, sans-serif);
}
.verdict-canvas-page .apex-section {
    padding: 28px 4px 8px 4px;
    margin: 0;
}
.verdict-canvas-page .apex-greeting-title {
    font-size: 34px;
    font-weight: 600;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin: 0 0 10px 0;
    color: #F5F5F7;
}
.verdict-canvas-page .apex-greeting-sub {
    font-size: 17px;
    line-height: 1.5;
    color: rgba(245,245,247,0.72);
    margin: 0 0 8px 0;
}
.verdict-canvas-page .apex-greeting-meta {
    font-size: 13px;
    color: rgba(245,245,247,0.38);
    margin: 0;
}
.verdict-canvas-page .apex-command-center {
    padding-top: 8px;
}
.verdict-canvas-page .apex-command-greeting {
    font-size: 13px;
    color: rgba(245,245,247,0.42);
    margin: 0 0 12px 0;
}
.verdict-canvas-page .apex-command-why {
    font-size: 18px;
    line-height: 1.5;
    color: rgba(245,245,247,0.86);
    margin: 0 0 10px 0;
}
.verdict-canvas-page .apex-command-confidence {
    font-size: 14px;
    font-weight: 500;
    color: rgba(245,245,247,0.52);
    margin: 0 0 8px 0;
}
.verdict-canvas-page .apex-command-freshness {
    font-size: 13px;
    color: rgba(245,245,247,0.38);
    margin: 0;
}
.verdict-canvas-page .apex-status-strip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 10px 14px;
}
.verdict-canvas-page .apex-status-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 72px;
    flex: 1 1 auto;
}
.verdict-canvas-page .apex-status-k {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(245,245,247,0.38);
}
.verdict-canvas-page .apex-status-v {
    font-size: 13px;
    font-weight: 500;
    line-height: 1.3;
    color: rgba(245,245,247,0.82);
}
.verdict-canvas-page .apex-priority-lead {
    font-size: 20px;
    font-weight: 500;
    margin: 0 0 8px 0;
}
.verdict-canvas-page .apex-priority-detail {
    font-size: 15px;
    line-height: 1.5;
    color: rgba(245,245,247,0.62);
    margin: 0;
}
.verdict-canvas-page .apex-market-head {
    font-size: 20px;
    font-weight: 500;
    margin: 0 0 10px 0;
}
.verdict-canvas-page .apex-market-body {
    font-size: 16px;
    line-height: 1.6;
    color: rgba(245,245,247,0.72);
    margin: 0;
}
.verdict-canvas-page .apex-connect-title {
    font-size: 20px;
    font-weight: 500;
    margin: 0 0 8px 0;
}
.verdict-canvas-page .apex-connect-body {
    font-size: 15px;
    line-height: 1.55;
    color: rgba(245,245,247,0.62);
    margin: 0 0 4px 0;
}
.verdict-canvas-page .apex-learning-title {
    font-size: 18px;
    font-weight: 500;
    margin: 0 0 8px 0;
}
.verdict-canvas-page .apex-learning-body {
    font-size: 15px;
    line-height: 1.6;
    color: rgba(245,245,247,0.72);
    margin: 0 0 8px 0;
}
.verdict-canvas-page .apex-learning-meta {
    font-size: 13px;
    color: rgba(245,245,247,0.38);
    margin: 0;
}
.verdict-canvas-page .apex-stale,
.verdict-canvas-page .apex-failure {
    font-size: 13px;
    padding: 10px 12px;
    border-radius: 10px;
    margin: 8px 0 0 0;
}
.verdict-canvas-page .apex-stale {
    color: #FFC107;
    background: rgba(255,193,7,0.08);
}
.verdict-canvas-page .apex-failure {
    color: #FF8A80;
    background: rgba(255,107,107,0.08);
}
.verdict-canvas-page .apex-foot {
    font-size: 12px;
    color: rgba(245,245,247,0.32);
    text-align: center;
    padding: 24px 8px 8px 8px;
    margin: 0;
}
.verdict-canvas-page .apex-portfolio-command-center {
    padding-top: 8px;
}
.verdict-canvas-page .apex-portfolio-hero {
    padding-top: 4px;
}
.verdict-canvas-page .apex-portfolio-badge {
    display: inline-block;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    padding: 6px 10px;
    border-radius: 999px;
    margin: 0 0 14px 0;
}
.verdict-canvas-page .apex-portfolio-badge[data-badge="healthy"] {
    color: #34C759;
    background: rgba(52,199,89,0.12);
}
.verdict-canvas-page .apex-portfolio-badge[data-badge="attention"] {
    color: #FFC107;
    background: rgba(255,193,7,0.12);
}
.verdict-canvas-page .apex-portfolio-badge[data-badge="connect"] {
    color: rgba(245,245,247,0.72);
    background: rgba(245,245,247,0.08);
}
.verdict-canvas-page .apex-portfolio-headline {
    font-size: 28px;
    font-weight: 600;
    letter-spacing: -0.02em;
    line-height: 1.25;
    margin: 0 0 10px 0;
    color: #F5F5F7;
}
.verdict-canvas-page .apex-portfolio-support,
.verdict-canvas-page .apex-portfolio-stale {
    font-size: 16px;
    line-height: 1.5;
    color: rgba(245,245,247,0.72);
    margin: 0 0 8px 0;
}
.verdict-canvas-page .apex-portfolio-stale {
    color: #FFC107;
}
.verdict-canvas-page .apex-portfolio-below-fold {
    content-visibility: auto;
    contain-intrinsic-size: auto 720px;
}
.verdict-canvas-page .apex-portfolio-card {
    border: 1px solid rgba(245,245,247,0.08);
    border-radius: 14px;
    padding: 16px 14px;
    margin-bottom: 12px;
    background: rgba(245,245,247,0.03);
}
.verdict-canvas-page .apex-portfolio-empty {
    font-size: 15px;
    color: rgba(245,245,247,0.62);
    margin: 0;
}
.verdict-canvas-page .apex-portfolio-alloc-bar {
    display: flex;
    width: 100%;
    height: 10px;
    border-radius: 999px;
    overflow: hidden;
    background: rgba(245,245,247,0.08);
    margin: 10px 0 8px 0;
}
.verdict-canvas-page .apex-portfolio-alloc-core {
    display: block;
    height: 100%;
    background: rgba(52,199,89,0.75);
}
.verdict-canvas-page .apex-portfolio-alloc-tactical {
    display: block;
    height: 100%;
    background: rgba(10,132,255,0.75);
}
.verdict-canvas-page .apex-portfolio-alloc-cash {
    display: block;
    height: 100%;
    background: rgba(245,245,247,0.28);
}
.verdict-canvas-page .apex-portfolio-alloc-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 14px;
    font-size: 13px;
    color: rgba(245,245,247,0.72);
}
.verdict-canvas-page .apex-portfolio-policy {
    font-size: 13px;
    color: rgba(245,245,247,0.52);
    margin: 10px 0 0 0;
}
.verdict-canvas-page .apex-portfolio-standout-line {
    font-size: 15px;
    line-height: 1.55;
    color: rgba(245,245,247,0.78);
    margin: 0;
}
.verdict-canvas-page .apex-portfolio-attention-row {
    display: grid;
    grid-template-columns: 24px 72px 96px 1fr;
    gap: 8px;
    align-items: start;
    font-size: 14px;
    margin-bottom: 10px;
    color: rgba(245,245,247,0.78);
}
.verdict-canvas-page .apex-portfolio-preview-row {
    display: flex;
    gap: 12px;
    align-items: center;
    font-size: 14px;
    margin-bottom: 8px;
    color: rgba(245,245,247,0.78);
}
.verdict-canvas-page .apex-portfolio-preview-symbol {
    min-width: 88px;
    font-weight: 600;
}
.verdict-canvas-page .apex-portfolio-preview-weight {
    min-width: 44px;
}
.verdict-canvas-page .apex-portfolio-preview-health[data-health="healthy"] {
    color: #34C759;
}
.verdict-canvas-page .apex-portfolio-preview-health[data-health="review"] {
    color: #FFC107;
}
.verdict-canvas-page .apex-status-muted {
    color: rgba(245,245,247,0.52);
}
.verdict-canvas-page .apex-portfolio-subnav {
    margin-bottom: 8px;
}
.verdict-canvas-page .apex-portfolio-focus {
    outline: 2px solid rgba(10,132,255,0.45);
    outline-offset: 4px;
}
.verdict-canvas-page .apex-holdings-experience {
    padding-top: 8px;
}
.verdict-canvas-page .apex-holdings-context {
    padding: 12px 16px;
    border-radius: 12px;
    background: rgba(245,245,247,0.04);
    margin-bottom: 12px;
}
.verdict-canvas-page .apex-holdings-summary {
    font-size: 16px;
    line-height: 1.5;
    color: rgba(245,245,247,0.88);
    margin: 0;
}
.verdict-canvas-page .apex-holdings-connect-msg {
    font-size: 14px;
    color: rgba(245,245,247,0.56);
    margin: 8px 0 0 0;
}
.verdict-canvas-page .apex-holdings-toolbar {
    margin-bottom: 12px;
}
.verdict-canvas-page .apex-holdings-table-wrap {
    overflow-x: auto;
}
.verdict-canvas-page .apex-holdings-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}
.verdict-canvas-page .apex-holdings-table th,
.verdict-canvas-page .apex-holdings-table td {
    padding: 10px 8px;
    border-bottom: 1px solid rgba(245,245,247,0.08);
    text-align: left;
}
.verdict-canvas-page .apex-holdings-num {
    text-align: right;
    font-variant-numeric: tabular-nums;
}
.verdict-canvas-page .apex-holdings-symbol {
    font-weight: 600;
}
.verdict-canvas-page .apex-holdings-name {
    color: rgba(245,245,247,0.62);
    max-width: 160px;
}
.verdict-canvas-page .apex-holdings-health[data-health="ok"] {
    color: #34C759;
}
.verdict-canvas-page .apex-holdings-health[data-health="attention"] {
    color: #FFC107;
}
.verdict-canvas-page .apex-holdings-health[data-health="unknown"] {
    color: rgba(245,245,247,0.52);
}
.verdict-canvas-page .apex-holdings-row-stale td,
.verdict-canvas-page .apex-holdings-row-stale th {
    color: rgba(245,245,247,0.48);
}
.verdict-canvas-page .apex-holdings-empty,
.verdict-canvas-page .apex-holdings-empty-state p {
    color: rgba(245,245,247,0.52);
    font-size: 14px;
}
.verdict-canvas-page .apex-holdings-card-list {
    display: none;
}
.verdict-canvas-page .apex-holdings-card {
    border: 1px solid rgba(245,245,247,0.08);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.verdict-canvas-page .apex-holdings-card-title {
    display: flex;
    justify-content: space-between;
    font-weight: 600;
    margin: 0 0 8px 0;
}
.verdict-canvas-page .apex-holdings-card-line {
    margin: 0 0 6px 0;
    color: rgba(245,245,247,0.82);
}
.verdict-canvas-page .apex-holdings-card-muted {
    color: rgba(245,245,247,0.52);
    font-size: 13px;
}
.verdict-canvas-page .apex-holdings-card-health[data-health="ok"] {
    color: #34C759;
}
.verdict-canvas-page .apex-holdings-card-health[data-health="attention"] {
    color: #FFC107;
}
.verdict-canvas-page .apex-holdings-watchlist-row {
    display: grid;
    grid-template-columns: 1fr 1fr auto;
    gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid rgba(245,245,247,0.06);
}
@media (max-width: 768px) {
    .verdict-canvas-page .apex-holdings-table-region {
        display: none;
    }
    .verdict-canvas-page .apex-holdings-row-actions {
        display: none;
    }
    .verdict-canvas-page .apex-holdings-card-list {
        display: block;
    }
}
@media (min-width: 769px) {
    .verdict-canvas-page .apex-holdings-card-list {
        display: none;
    }
}
</style>
"""

APEX_INVESTMENT_HERO_CSS = """
<style>
.verdict-canvas-page .apex-inv-hero {
    padding-top: 0;
    padding-bottom: 0;
}
.verdict-canvas-page .apex-inv-name {
    margin: 0 0 12px 0;
}
.verdict-canvas-page .apex-inv-row {
    font-size: 16px;
    line-height: 1.5;
    color: rgba(245,245,247,0.88);
    margin: 0 0 10px 0;
}
.verdict-canvas-page .apex-inv-k {
    display: block;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: rgba(245,245,247,0.42);
    margin-bottom: 4px;
}
.verdict-canvas-page .apex-inv-fresh {
    font-size: 13px;
    color: rgba(245,245,247,0.38);
    margin: 4px 0 16px 0;
}
</style>
"""

APEX_INVESTMENT_THESIS_CSS = """
<style>
.verdict-canvas-page .apex-thesis {
    padding-top: 12px;
}
.verdict-canvas-page .apex-thesis-badge {
    margin: 0 0 14px 0;
}
.verdict-canvas-page .apex-thesis-strengthening { background: rgba(48,209,88,0.16); color: #30D158; }
.verdict-canvas-page .apex-thesis-stable { background: rgba(10,132,255,0.16); color: #0A84FF; }
.verdict-canvas-page .apex-thesis-weakening { background: rgba(255,159,10,0.16); color: #FF9F0A; }
.verdict-canvas-page .apex-thesis-l1 {
    font-size: 17px;
    line-height: 1.55;
    color: rgba(245,245,247,0.86);
    margin: 0;
}
.verdict-canvas-page .plan-canvas-root .apex-thesis-l1 {
    font-size: 15px;
}
</style>
"""

APEX_BUSINESS_HEALTH_CSS = """
<style>
.verdict-canvas-page .apex-health {
    padding-top: 12px;
}
.verdict-canvas-page .apex-health-l1 {
    font-size: 17px;
    line-height: 1.55;
    color: rgba(245,245,247,0.86);
    margin: 0 0 12px 0;
}
.verdict-canvas-page .plan-canvas-root .apex-health-l1 {
    font-size: 15px;
}
.verdict-canvas-page .apex-health-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 0 0 4px 0;
}
</style>
"""

APEX_RISK_MONITOR_CSS = """
<style>
.verdict-canvas-page .apex-risk {
    padding-top: 12px;
}
.verdict-canvas-page .apex-risk-l1 {
    font-size: 17px;
    line-height: 1.55;
    color: rgba(245,245,247,0.86);
    margin: 0 0 12px 0;
}
.verdict-canvas-page .plan-canvas-root .apex-risk-l1 {
    font-size: 15px;
}
.verdict-canvas-page .apex-risk-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 0 0 4px 0;
}
.verdict-canvas-page .apex-risk-badge {
    background: rgba(255,69,58,0.12);
    color: rgba(255,159,10,0.92);
    border-color: rgba(255,69,58,0.18);
}
</style>
"""

APEX_RECOMMENDATION_EXPLANATION_CSS = """
<style>
.verdict-canvas-page .apex-rex {
    padding-top: 12px;
}
.verdict-canvas-page .apex-rex-badge {
    margin: 0 0 14px 0;
}
.verdict-canvas-page .apex-rex-hold { background: rgba(255,214,10,0.14); color: #FFD60A; }
.verdict-canvas-page .apex-rex-l1 {
    font-size: 17px;
    line-height: 1.55;
    color: rgba(245,245,247,0.86);
    margin: 0;
}
.verdict-canvas-page .plan-canvas-root .apex-rex-l1 {
    font-size: 15px;
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
    min-height: auto;
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
    min-height: 72px;
    padding: 12px 0 4px 0;
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
    margin: 8px 0 4px 0;
    max-width: 358px;
}
.verdict-canvas-root .vc-stale {
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #FFC107;
    background: rgba(255,193,7,0.1);
    border: 1px solid rgba(255,193,7,0.25);
    border-radius: 6px;
    padding: 6px 10px;
    margin: 0 0 8px 0;
    max-width: 358px;
}
.verdict-canvas-root .vc-session-ribbon {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin: 0 0 10px 0;
    max-width: 358px;
}
.verdict-canvas-root .vc-ribbon-chip {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.03em;
    color: rgba(255,255,255,0.72);
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 999px;
    padding: 4px 10px;
}
.verdict-canvas-root .vc-refreshing {
    font-size: 12px;
    font-weight: 500;
    color: rgba(255,255,255,0.55);
    margin: 0 0 8px 0;
}
.verdict-canvas-root .vc-prepare-note {
    font-size: 13px;
    color: rgba(255,255,255,0.5);
    margin-top: 8px;
}
.verdict-canvas-root .vc-failure {
    font-size: 13px;
    font-weight: 500;
    line-height: 1.45;
    color: #FF8A80;
    background: rgba(255,82,82,0.1);
    border: 1px solid rgba(255,82,82,0.28);
    border-radius: 6px;
    padding: 8px 10px;
    margin: 0 0 8px 0;
    max-width: 358px;
}
.verdict-canvas-root .vc-l0-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(245,245,247,0.45);
    margin-right: 6px;
}
.verdict-canvas-root .vc-evidence-teaser {
    font-size: 15px;
    line-height: 1.45;
    color: rgba(245,245,247,0.72);
    margin: 0 0 6px 0;
    max-width: 358px;
}
.verdict-canvas-root .vc-trust-line {
    font-size: 14px;
    line-height: 1.45;
    color: rgba(245,245,247,0.62);
    margin: 0 0 8px 0;
    max-width: 358px;
}
.verdict-canvas-root .vc-confidence-band {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: rgba(245,245,247,0.5);
    border: 1px solid rgba(245,245,247,0.12);
    border-radius: 999px;
    padding: 3px 10px;
    margin: 0 0 8px 0;
}
.verdict-canvas-root .vc-confidence-band[data-band="high"] { color: #00E676; border-color: rgba(0,230,118,0.25); }
.verdict-canvas-root .vc-confidence-band[data-band="medium"] { color: #FFC107; border-color: rgba(255,193,7,0.25); }
.verdict-canvas-root .vc-confidence-band[data-band="low"] { color: rgba(245,245,247,0.45); }
.verdict-canvas-root .vc-portfolio-line {
    font-size: 13px;
    line-height: 1.4;
    color: rgba(245,245,247,0.5);
    margin: 0 0 8px 0;
    max-width: 358px;
}
.verdict-canvas-page [data-testid="stVerticalBlock"] {
    gap: 0.35rem !important;
}
.verdict-canvas-page [data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}
.verdict-canvas-page [data-testid="stMainBlockContainer"] {
    padding-top: 0.35rem !important;
}
.verdict-canvas-root .vc-intel-stack-hero {
    margin: 0 auto 4px;
    padding-top: 0;
}
.verdict-canvas-root .vc-intel-stack-hero .vc-intel-block:first-child {
    padding-top: 0;
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
    margin-top: 8px;
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
    margin: 0 auto 12px;
    padding: 0 4px;
}
.vc-intel-block {
    border-top: 1px solid #2C2C2E;
    padding: 14px 0 2px 0;
}
.vc-intel-block:first-child {
    border-top: none;
    padding-top: 4px;
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

APEX_PARTNER_EXPERIENCE_CSS = (
    APEX_V2_VISUAL_POLISH_CSS
    + APEX_V2_PERFORMANCE_ACCESSIBILITY_CSS
    + APEX_BRIEF_EXPERIENCE_CSS
    + APEX_RECOMMENDATION_EXPLANATION_CSS
    + APEX_INVESTMENT_THESIS_CSS
    + APEX_BUSINESS_HEALTH_CSS
    + APEX_RISK_MONITOR_CSS
    + APEX_INVESTMENT_HERO_CSS
    + VERDICT_CANVAS_CSS
)
