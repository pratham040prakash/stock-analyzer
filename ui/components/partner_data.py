"""Progressive data loading for AI Trading Partner canvases (lazy by surface)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st

from analyzer.broker_truth.learning import LearningOutcomeRow, resolve_learning_outcomes
from analyzer.context_engine.models import ContextSnapshot
from analyzer.intraday_prefs import load_intraday_prefs
from analyzer.investment_os import InvestmentOS, build_investment_os
from analyzer.market_pulse_scan import MarketPulseReport
from analyzer.mis_trade_advisory import MisTradeAdvisory, build_mis_trade_advisory
from analyzer.portfolio_store import load_saved_portfolio, portfolio_profile_key
from analyzer.pulse_cache import load_pulse_cache_with_stale
from analyzer.trade_journal import load_journal_entries
from analyzer.watchlist_pins import load_pinned_plans
from ui.broker.state import BrokerSnapshot, load_broker_snapshot

IST = ZoneInfo("Asia/Kolkata")
PULSE_CACHE_TTL = 86_400


def _snapshot_to_cache(snapshot: ContextSnapshot) -> dict[str, Any]:
    return snapshot.as_dict()


def _load_pulse(market: str, period: str) -> MarketPulseReport | None:
    key = f"pulse_{period}_{market}"
    report, _fresh = load_pulse_cache_with_stale(key, PULSE_CACHE_TTL)
    return report


def _journal_pnl_for_date(trade_date: str) -> float | None:
    total = 0.0
    found = False
    for entry in load_journal_entries(limit=60):
        if entry.trade_date == trade_date and entry.pnl_inr is not None:
            total += float(entry.pnl_inr)
            found = True
    return total if found else None

PARTNER_TODAY_KEY = "partner_today_key"
PARTNER_TODAY_STAGE = "partner_today_stage"
PARTNER_TODAY_CORE = "partner_today_core"
PARTNER_TODAY_STATE = "partner_today_state"
PARTNER_TODAY_READY = "partner_today_ready"
PARTNER_BG_DONE = "partner_bg_done"
PARTNER_DOCK_STAGE = "partner_dock_stage"


def _built_at() -> str:
    return datetime.now(IST).strftime("%H:%M IST")


def _merge(*parts: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for part in parts:
        out.update(part)
    return out


def read_broker_snapshot() -> BrokerSnapshot:
    """Disk/session broker only — never triggers a live sync."""
    raw = st.session_state.get("broker_snapshot")
    if raw:
        return BrokerSnapshot.from_dict(raw)
    return load_broker_snapshot()


@st.cache_data(ttl=45, show_spinner=False)
def load_today_core(market: str, period: str) -> dict[str, Any]:
    """Minimal bundle for Today verdict + mentor (Stages 2–3)."""
    from analyzer.context_engine import build_context_snapshot

    prefs = load_intraday_prefs()
    snapshot = build_context_snapshot(market=market, use_cache=True)
    mis = build_mis_trade_advisory(market=market)
    os_report = build_investment_os(market, period=period, prefs=prefs, deep=False)
    pins = load_pinned_plans()
    return {
        "snapshot": _snapshot_to_cache(snapshot),
        "mis": mis,
        "os_report": os_report,
        "pins": pins,
        "prefs": prefs,
        "built_at": _built_at(),
    }


@st.cache_data(ttl=120, show_spinner=False)
def load_portfolio_data() -> dict[str, Any]:
    prof = portfolio_profile_key()
    return {"portfolio": load_saved_portfolio(profile=prof)}


@st.cache_data(ttl=120, show_spinner=False)
def load_background_modules(market: str, period: str) -> dict[str, Any]:
    """Optional modules — pulse, learning, journal P&L (Stage 6)."""
    pulse = _load_pulse(market, period)
    learning: list[LearningOutcomeRow] = resolve_learning_outcomes(days=14)
    journal_today = None
    try:
        from analyzer.context_engine import build_context_snapshot

        snapshot = build_context_snapshot(market=market, use_cache=True)
        session_date = str(dict(snapshot.market_session).get("date", ""))
        if session_date:
            journal_today = _journal_pnl_for_date(session_date)
    except Exception:
        journal_today = None
    return {
        "pulse": pulse,
        "learning": learning,
        "journal_today_pnl": journal_today,
    }


def load_trades_bundle(market: str, period: str) -> dict[str, Any]:
    return load_today_core(market, period)


def load_reflection_bundle(market: str, period: str) -> dict[str, Any]:
    return _merge(
        load_today_core(market, period),
        load_portfolio_data(),
        load_background_modules(market, period),
    )


def load_ask_bundle(market: str, period: str) -> dict[str, Any]:
    return _merge(load_today_core(market, period), load_portfolio_data())


def load_proof_bundle(market: str, period: str) -> dict[str, Any]:
    broker = read_broker_snapshot()
    return _merge(
        load_today_core(market, period),
        {"broker": broker.to_dict(), "built_at": _built_at()},
    )


def load_dashboard_data(market: str, period: str, deep: bool) -> dict[str, Any]:
    """Full bundle — compatibility / tests only; home shell uses lazy loaders."""
    del deep
    return _merge(
        load_today_core(market, period),
        load_portfolio_data(),
        load_background_modules(market, period),
    )


def reset_today_pipeline(*, market: str, period: str) -> None:
    key = f"{market}:{period}"
    if st.session_state.get(PARTNER_TODAY_KEY) == key:
        return
    st.session_state[PARTNER_TODAY_KEY] = key
    st.session_state[PARTNER_TODAY_STAGE] = 1
    st.session_state.pop(PARTNER_TODAY_CORE, None)
    st.session_state.pop(PARTNER_TODAY_STATE, None)
    st.session_state.pop(PARTNER_TODAY_READY, None)
    st.session_state[PARTNER_BG_DONE] = False


def reset_dock_stage(dock: str) -> None:
    st.session_state[f"{PARTNER_DOCK_STAGE}_{dock}"] = 1


def ensure_background_modules(market: str, period: str) -> None:
    if st.session_state.get(PARTNER_BG_DONE):
        return
    load_portfolio_data()
    load_background_modules(market, period)
    st.session_state[PARTNER_BG_DONE] = True


def clear_partner_caches_on_pickle_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    if "pickle" in msg or "serializ" in msg or "mappingproxy" in msg or "cache" in msg:
        load_today_core.clear()
        load_portfolio_data.clear()
        load_background_modules.clear()
        load_dashboard_data.clear()
        return True
    return False
