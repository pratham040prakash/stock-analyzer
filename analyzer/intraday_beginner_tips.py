"""
Top 10 intraday trading tips — capital discipline, timing, risk guards.

Beginner-focused rules: research first, allocate only part of capital,
start small, time the session, avoid penny stocks, exit at target, stop-loss,
few instruments, post-trade review.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.penny_stocks import DEFAULT_MAX_PRICE_INR

IST = ZoneInfo("Asia/Kolkata")

DEFAULT_INTRADAY_ALLOCATION_PCT = 50.0
DEFAULT_MAX_CONCURRENT_TRADES = 2
MIS_SQUARE_OFF_MINUTE = 15 * 60 + 20  # 3:20 PM
OPENING_OBSERVE_UNTIL = (9, 45)  # observe high volatility first ~30 min
WIND_DOWN_FROM = (14, 30)


@dataclass
class IntradayCapitalBudget:
    total_capital_inr: float
    allocation_pct: float
    max_risk_pct: float
    max_concurrent_trades: int
    allocated_inr: float
    per_trade_budget_inr: float
    max_risk_per_trade_inr: float
    notes: list[str] = field(default_factory=list)


@dataclass
class SessionTimingAdvice:
    phase: str
    headline: str
    detail: str
    allow_new_entries: bool
    prefer_exit: bool


@dataclass
class IntradayTip:
    number: int
    title: str
    summary: str
    app_help: str


def allocated_capital(total_inr: float, allocation_pct: float = DEFAULT_INTRADAY_ALLOCATION_PCT) -> float:
    """Only part of total capital for MIS (tip #2)."""
    return round(total_inr * max(0.0, min(100.0, allocation_pct)) / 100, 0)


def build_capital_budget(
    total_capital_inr: float,
    *,
    allocation_pct: float = DEFAULT_INTRADAY_ALLOCATION_PCT,
    max_risk_pct: float = 1.0,
    max_concurrent_trades: int = DEFAULT_MAX_CONCURRENT_TRADES,
) -> IntradayCapitalBudget:
    """Tips #2–3: set funds aside + start with small amounts per trade."""
    allocated = allocated_capital(total_capital_inr, allocation_pct)
    per_trade = round(allocated / max(1, max_concurrent_trades), 0)
    max_risk_inr = round(allocated * max_risk_pct / 100, 0)
    notes = [
        f"Keep **{100 - allocation_pct:.0f}%** of capital away from MIS (delivery/SIP reserve).",
        f"Today's MIS pool: **₹{allocated:,.0f}** ({allocation_pct:.0f}% of ₹{total_capital_inr:,.0f}).",
        f"Tip #3: budget **~₹{per_trade:,.0f}** per trade (split across {max_concurrent_trades} slots).",
        f"Max loss per trade at {max_risk_pct:.1f}% risk ≈ **₹{max_risk_inr:,.0f}** from MIS pool.",
    ]
    return IntradayCapitalBudget(
        total_capital_inr=total_capital_inr,
        allocation_pct=allocation_pct,
        max_risk_pct=max_risk_pct,
        max_concurrent_trades=max_concurrent_trades,
        allocated_inr=allocated,
        per_trade_budget_inr=per_trade,
        max_risk_per_trade_inr=max_risk_inr,
        notes=notes,
    )


def session_timing_advice(now: datetime | None = None) -> SessionTimingAdvice:
    """Tip #9: time trades — observe open, trade mid-session, exit before close."""
    now = now or datetime.now(IST)
    if now.weekday() >= 5:
        return SessionTimingAdvice(
            phase="weekend",
            headline="Market closed — research & build tomorrow's watchlist",
            detail="Use Market Pulse + pre-market watchlist tonight (tips #1, #10).",
            allow_new_entries=False,
            prefer_exit=False,
        )

    t = now.hour * 60 + now.minute
    open_t = 9 * 60 + 15
    observe_end = OPENING_OBSERVE_UNTIL[0] * 60 + OPENING_OBSERVE_UNTIL[1]
    wind_down = WIND_DOWN_FROM[0] * 60 + WIND_DOWN_FROM[1]
    close_t = 15 * 60 + 30
    square_off = MIS_SQUARE_OFF_MINUTE

    if t < open_t:
        return SessionTimingAdvice(
            phase="pre_open",
            headline="Pre-open — finalise watchlist & levels",
            detail="Write entry, stop, target for each name. No live trades yet.",
            allow_new_entries=False,
            prefer_exit=False,
        )
    if t < observe_end:
        return SessionTimingAdvice(
            phase="opening",
            headline="Opening volatility — observe first 30 minutes",
            detail="Watch opening range on 5m chart. Avoid impulsive entries (tip #9).",
            allow_new_entries=False,
            prefer_exit=False,
        )
    if t < wind_down:
        return SessionTimingAdvice(
            phase="core",
            headline="Core session — execute planned trades only",
            detail="Trade from your shortlist. One or two instruments max (tip #8).",
            allow_new_entries=True,
            prefer_exit=False,
        )
    if t < square_off:
        return SessionTimingAdvice(
            phase="wind_down",
            headline="Afternoon — take profits, avoid new risk",
            detail="Prefer exits. Book target hits; do not chase (tip #6).",
            allow_new_entries=False,
            prefer_exit=True,
        )
    if t < close_t:
        return SessionTimingAdvice(
            phase="square_off",
            headline="Square off MIS before 3:20 PM IST",
            detail="Close all intraday positions now. No new entries.",
            allow_new_entries=False,
            prefer_exit=True,
        )
    return SessionTimingAdvice(
        phase="after_hours",
        headline="Session over — post-trade review",
        detail="Review wins/losses in Track Record. Plan tomorrow (tip #10).",
        allow_new_entries=False,
        prefer_exit=False,
    )


def penny_stock_intraday_warning(price: float, *, threshold: float = DEFAULT_MAX_PRICE_INR) -> str | None:
    """Tip #5: avoid penny stocks for MIS beginners."""
    if price <= 0:
        return None
    if price <= threshold:
        return (
            f"**Penny/low-priced stock (₹{price:,.2f} ≤ ₹{threshold:,.0f})** — high volatility and "
            "wide spreads. Beginners should avoid MIS here; use Nifty 50 names instead."
        )
    return None


def too_many_watchlist_warning(pick_count: int, max_trades: int) -> str | None:
    """Tip #8: don't trade too many instruments at once."""
    if pick_count <= max_trades:
        return None
    return (
        f"You have **{pick_count}** watchlist names but planned **{max_trades}** concurrent trades. "
        "Focus on top priorities only."
    )


def ten_intraday_tips() -> list[IntradayTip]:
    return [
        IntradayTip(1, "Do your research", "Verify signals yourself; avoid tip groups.", "Market Pulse scan, watchlist, Investopedia screen."),
        IntradayTip(2, "Set funds aside", "Never put 100% capital in MIS.", "MIS allocation % slider below."),
        IntradayTip(3, "Start small", "Use part of today's pool per trade.", "Per-trade budget from MIS pool ÷ slots."),
        IntradayTip(4, "Allocate time", "Stay focused 9:15–3:30 IST.", "Session timing banner updates live."),
        IntradayTip(5, "Avoid penny stocks", "Low-price names are volatile and illiquid.", "Warning if price ≤ ₹20."),
        IntradayTip(6, "Exit at target", "Book profit; don't wait for more.", "50% at target, trail rest to breakeven."),
        IntradayTip(7, "Always use stop-loss", "Define stop before entry.", "Entry & exit plan on every chart."),
        IntradayTip(8, "Few instruments", "2–3 trades max per day.", "Max concurrent trades + lean watchlist (8)."),
        IntradayTip(9, "Time your trades", "Observe open; exit before close rush.", "Opening observe / 3:20 square-off phases."),
        IntradayTip(10, "Post-trade analysis", "Review what worked.", "Track Record tab + nightly watchlist refresh."),
    ]


@dataclass
class DailyChecklistItem:
    id: str
    phase: str
    tip_number: int
    label: str
    action: str
    link_tab: str = ""
    link_label: str = ""
    focus_key: str = ""


def daily_mis_checklist_items() -> list[DailyChecklistItem]:
    """Step-by-step MIS routine mapped to the 10 beginner tips."""
    return [
        DailyChecklistItem(
            "night_pulse", "night_before", 1,
            "Run Market Pulse — scan full Nifty 50",
            "Note Nifty bias & sector leader",
            link_tab="Market Pulse",
            link_label="Open Market Pulse",
        ),
        DailyChecklistItem(
            "night_watchlist", "night_before", 1,
            "Build pre-market watchlist (max 2–3 names)",
            "Copy Entry · Stop · Target for each pick — no levels = skip",
            link_tab="Suggestions",
            link_label="Open watchlist",
            focus_key="intraday_focus_watchlist",
        ),
        DailyChecklistItem(
            "morning_capital", "morning_setup", 2,
            "Set total capital & MIS allocation %",
            "Only MIS pool is for today — keep rest for delivery / tomorrow",
            link_tab="Suggestions",
            link_label="Set capital",
            focus_key="intraday_focus_capital",
        ),
        DailyChecklistItem(
            "morning_slots", "morning_setup", 3,
            "Set max trades (1–3) & check per-trade budget",
            "Do not exceed per-trade budget or max risk per trade",
            link_tab="Suggestions",
            link_label="Set slots",
            focus_key="intraday_focus_capital",
        ),
        DailyChecklistItem(
            "morning_focus", "morning_setup", 4,
            "Keep Intraday tab open 9:15–3:30 IST",
            "Enable Auto-refresh; watch session timing banner",
            link_tab="Suggestions",
            link_label="Suggestions tab",
        ),
        DailyChecklistItem(
            "open_observe", "during_session", 9,
            "9:15–9:45 — observe opening range only",
            "Note OR High/Low on 5m chart — no new entries yet",
            link_tab="Suggestions",
            link_label="Open chart",
            focus_key="intraday_focus_chart",
        ),
        DailyChecklistItem(
            "trade_watchlist", "during_session", 8,
            "Trade only from tonight's watchlist",
            "Ignore tips from groups; max trades = your slot count",
            link_tab="Suggestions",
            link_label="Watchlist",
            focus_key="intraday_focus_watchlist",
        ),
        DailyChecklistItem(
            "pre_entry_plan", "during_session", 7,
            "Before entry: read Entry & exit plan",
            "Place stop on Kite first; skip if plan says Do not enter",
            link_tab="Suggestions",
            link_label="Entry plan",
            focus_key="intraday_focus_chart",
        ),
        DailyChecklistItem(
            "penny_check", "during_session", 5,
            "Confirm no penny warning (price > ₹20)",
            "Use Nifty 50 liquid names for MIS",
            link_tab="Suggestions",
            link_label="Check chart",
            focus_key="intraday_focus_chart",
        ),
        DailyChecklistItem(
            "target_exit", "during_session", 6,
            "At target: book 50%, trail stop to breakeven",
            "Do not wait for more — stick to written target",
            link_tab="Suggestions",
            link_label="Log exit",
            focus_key="intraday_focus_journal",
        ),
        DailyChecklistItem(
            "square_off", "during_session", 9,
            "Square off all MIS before 3:20 PM IST",
            "Close every intraday position on Kite",
            link_tab="Suggestions",
            link_label="Today's log",
            focus_key="intraday_focus_journal",
        ),
        DailyChecklistItem(
            "options_sideways", "during_session", 9,
            "Sideways? Use strategy advisor (iron condor / butterfly)",
            "When entry gate is yellow/red — credit spreads beat buying CE/PE in chop",
            link_tab="Suggestions",
            link_label="Sideways advisor",
        ),
        DailyChecklistItem(
            "options_or_gate", "during_session", 9,
            "Options: check 🚦 Entry gate before CE/PE",
            "PE only if spot ≤ OR low · CE only if spot ≥ OR high · after 9:45",
            link_tab="Suggestions",
            link_label="Options CE/PE",
        ),
        DailyChecklistItem(
            "options_journal", "after_close", 10,
            "Log mistake + fix in Track Record journal",
            "One line: what went wrong and rule for tomorrow",
            link_tab="Track Record",
            link_label="Trade journal",
        ),
        DailyChecklistItem(
            "post_review", "after_close", 11,
            "Review Track Record & refresh watchlist tonight",
            "What worked → scan for tomorrow",
            link_tab="Track Record",
            link_label="Open Track Record",
        ),
    ]


def checklist_phase_for_session(advice: SessionTimingAdvice) -> str:
    """Highlight checklist section matching current market phase."""
    mapping = {
        "weekend": "night_before",
        "pre_open": "morning_setup",
        "opening": "during_session",
        "core": "during_session",
        "wind_down": "during_session",
        "square_off": "during_session",
        "after_hours": "after_close",
    }
    return mapping.get(advice.phase, "morning_setup")


PHASE_LABELS = {
    "night_before": "🌙 Night before (tips 1, 10)",
    "morning_setup": "☀️ Morning setup (tips 2–4, 8)",
    "during_session": "⏱️ During session (tips 5–9)",
    "after_close": "📊 After close (tip 10)",
}


def tips_summary_markdown() -> str:
    return (
        "**10 beginner intraday rules** built into this tab: research, capital limits, small size, "
        "session timing, no penny MIS, exit at target, stop-loss, few stocks, timed entries, post-trade review."
    )
