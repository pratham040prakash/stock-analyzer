"""Phase 3 — You tab · Reflection Canvas (trader relationship, presentation only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st

from analyzer.broker_truth.learning import LearningOutcomeRow
from analyzer.context_engine.models import ContextSnapshot
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.trade_journal import TradeJournalEntry
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult
from ui.broker.state import BrokerSnapshot
from ui.components.home_dashboard import (
    _broker_snapshot,
    _esc,
    _strip_md,
    _sync_status,
    _trim_words,
)
from ui.components.partner_shell import set_partner_dock
from ui.navigation import request_nav_tab

_MICRO_LABEL = "I've noticed"
_NARRATIVE_MAX_WORDS = 22
_COACHING_MAX_WORDS = 24
_FORWARD_MAX_WORDS = 18

# Four trader state words — encouraging, not evaluative.
_STATE_TOKENS: dict[str, tuple[str, str]] = {
    "growing": ("Growing", "growing"),
    "steady": ("Steady", "steady"),
    "rebuilding": ("Rebuilding", "rebuilding"),
    "focused": ("Focused", "focused"),
}


@dataclass(frozen=True)
class ReflectionView:
    state_key: str
    state_word: str
    narrative: tuple[str, ...]
    coaching_insight: str
    forward_line: str
    recommendation: str
    change_prose: str
    primary_label: str
    primary_action: str  # good | connect | today


def _journal_recent(entries: list[TradeJournalEntry], *, days: int = 7) -> list[TradeJournalEntry]:
    return entries[:days]


def _count_wait_wins(mis: MisTradeAdvisory, snapshot: ContextSnapshot) -> int:
    """Proxy for disciplined sit-outs — flags and restrictions, not portfolio."""
    n = 0
    if mis.loss_streak_days == 0:
        n += 1
    if snapshot.risk_mode in ("NEUTRAL", "RISK-ON"):
        n += 1
    if not mis.flags:
        n += 1
    return n


def _learning_summary(rows: list[LearningOutcomeRow]) -> tuple[int, int, int]:
    wins = sum(1 for r in rows if r.outcome == "target_hit")
    losses = sum(1 for r in rows if r.outcome == "stop_hit")
    flats = sum(1 for r in rows if r.outcome == "flat")
    return wins, losses, flats


def _resolve_trader_state(
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
    journal: list[TradeJournalEntry],
    learning: list[LearningOutcomeRow],
) -> str:
    if mis.loss_streak_days >= 2:
        return "rebuilding"
    wins, losses, _flats = _learning_summary(learning)
    if mis.loss_streak_days == 0 and wins >= 2 and losses == 0:
        return "growing"
    if mis.loss_streak_days == 0 and losses == 0 and _count_wait_wins(mis, snapshot) >= 2:
        return "focused"
    if wins > losses and mis.loss_streak_days <= 1:
        return "growing"
    return "steady"


def _trader_narrative(
    state_key: str,
    *,
    mis: MisTradeAdvisory,
    journal: list[TradeJournalEntry],
    learning: list[LearningOutcomeRow],
) -> tuple[str, ...]:
    wins, losses, flats = _learning_summary(learning)
    recent = _journal_recent(journal)
    traded_days = len({e.trade_date for e in recent if e.pnl_inr is not None})
    sit_outs = max(0, 7 - traded_days)

    if state_key == "rebuilding":
        return (
            _trim_words(
                "A rough patch doesn't define you — how you respond this week does.",
                max_words=_NARRATIVE_MAX_WORDS,
            ),
            _trim_words(
                "You're pulling back at the right time instead of forcing trades.",
                max_words=_NARRATIVE_MAX_WORDS,
            ),
        )

    if state_key == "growing":
        lines = [
            "You're stacking good decisions, not just good days.",
        ]
        if wins:
            lines.append(f"You followed through on {wins} planned trade(s) recently.")
        lines.append("That consistency is how better traders are built.")
        return tuple(_trim_words(line, max_words=_NARRATIVE_MAX_WORDS) for line in lines[:3])

    if state_key == "focused":
        if sit_outs >= 3:
            first = f"You sat out {sit_outs} sessions when the setup wasn't there."
        else:
            first = "You kept discipline when the market pushed you to chase."
        return (
            _trim_words(first, max_words=_NARRATIVE_MAX_WORDS),
            _trim_words(
                "Patience like that compounds — most traders never learn it.",
                max_words=_NARRATIVE_MAX_WORDS,
            ),
        )

    # steady
    if sit_outs >= 2:
        return (
            _trim_words(
                "You're trading with restraint when others would overtrade.",
                max_words=_NARRATIVE_MAX_WORDS,
            ),
            _trim_words(
                "That steadiness is a skill — keep protecting it.",
                max_words=_NARRATIVE_MAX_WORDS,
            ),
        )
    return (
        _trim_words(
            "You're showing up with a plan and respecting your limits.",
            max_words=_NARRATIVE_MAX_WORDS,
        ),
        _trim_words(
            "You're on a path — small choices are adding up.",
            max_words=_NARRATIVE_MAX_WORDS,
        ),
    )


def _coaching_insight(
    state_key: str,
    *,
    mis: MisTradeAdvisory,
    journal: list[TradeJournalEntry],
) -> str:
    if state_key == "focused" or mis.loss_streak_days == 0:
        return _trim_words(
            "The hardest trade this week was waiting. You made the right decision.",
            max_words=_COACHING_MAX_WORDS,
        )
    if state_key == "rebuilding":
        recent_mistake = next((e for e in journal if e.mistake), None)
        if recent_mistake and recent_mistake.mistake:
            return _trim_words(
                f"The hardest moment was after {_strip_md(recent_mistake.mistake)[:40]}. "
                "You're already correcting course.",
                max_words=_COACHING_MAX_WORDS,
            )
        return _trim_words(
            "The hardest trade was stepping away. That's strength, not failure.",
            max_words=_COACHING_MAX_WORDS,
        )
    if state_key == "growing":
        return _trim_words(
            "The hardest trade was trusting your plan when doubt crept in. You did.",
            max_words=_COACHING_MAX_WORDS,
        )
    return _trim_words(
        "The hardest trade this week was waiting. You made the right decision.",
        max_words=_COACHING_MAX_WORDS,
    )


def _forward_line(
    *,
    snapshot: ContextSnapshot,
    os_report: InvestmentOS,
    mis: MisTradeAdvisory,
) -> str:
    if mis.loss_streak_days >= 1:
        return _trim_words(
            "Tomorrow I'll keep risk tight until your habits feel steady again.",
            max_words=_FORWARD_MAX_WORDS,
        )
    phase = str(dict(snapshot.market_session or {}).get("phase", "") or snapshot.market_phase or "")
    if phase in ("weekend", "holiday", "after_hours", "closed"):
        return _trim_words(
            "Next session I'll watch for clean setups worth your capital.",
            max_words=_FORWARD_MAX_WORDS,
        )
    if os_report.starred_symbol:
        sym = os_report.starred_symbol.upper().replace(".NS", "")
        return _trim_words(
            f"Tomorrow I'll keep watching {sym} and similar high-quality breakouts.",
            max_words=_FORWARD_MAX_WORDS,
        )
    return _trim_words(
        "Tomorrow I'll continue watching for high-quality breakouts.",
        max_words=_FORWARD_MAX_WORDS,
    )


def _recommendation(state_key: str, *, mis: MisTradeAdvisory) -> str:
    if state_key == "rebuilding":
        return "Rest is part of the process — one good day at a time."
    if state_key == "growing":
        return "Keep doing what you're doing — momentum is on your side."
    if state_key == "focused":
        return "Stay patient — the right trade will come."
    return "You're becoming a more deliberate trader."


def _what_id_change(
    portfolio: ZerodhaImportResult | None,
    *,
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
) -> str:
    holdings = portfolio.holdings if portfolio and portfolio.holdings else []
    if not holdings:
        return (
            "If I were beside you today, I'd change nothing about how you're approaching risk — "
            "connect your book when you're ready so I can coach against real positions."
        )
    if mis.flags:
        flag = _strip_md(mis.flags[0])
        return _trim_words(
            f"If I were beside you, I'd change one habit first: {flag}. Your trader instincts matter more than any single stock.",
            max_words=40,
        )
    if snapshot.risk_mode == "RISK-OFF":
        return (
            "If I were beside you, I'd change nothing on your watchlist today — "
            "I'd change your pace: slower entries until the market settles."
        )
    top = _top_holding_name(holdings)
    return _trim_words(
        f"If I were beside you, I'd change nothing urgent — stay the course and don't let {top} become an emotional anchor.",
        max_words=40,
    )


def _top_holding_name(holdings: list[ZerodhaHolding]) -> str:
    best = max(
        holdings,
        key=lambda h: float(h.quantity or 0) * float(h.last_price or h.average_price or 0),
        default=None,
    )
    if not best:
        return "one name"
    return best.tradingsymbol or best.kite_symbol or "one name"


def build_reflection_view(
    *,
    broker: BrokerSnapshot,
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
    os_report: InvestmentOS,
    portfolio: ZerodhaImportResult | None,
    journal: list[TradeJournalEntry],
    learning: list[LearningOutcomeRow],
) -> ReflectionView:
    if not broker.connected():
        return ReflectionView(
            state_key="steady",
            state_word="Steady",
            narrative=(
                "I want to coach the trader you're becoming — not just the stocks you hold.",
                "Link Zerodha once and I'll remember how you actually trade.",
            ),
            coaching_insight="The first step is letting me see your real decisions.",
            forward_line="Once connected, I'll watch your habits as closely as your positions.",
            recommendation="You're worth investing in — connect when you're ready.",
            change_prose="Connect your broker and I'll tell you what I'd change — trader-first.",
            primary_label="Connect Zerodha",
            primary_action="connect",
        )

    state_key = _resolve_trader_state(mis, snapshot, journal, learning)
    state_word, _ = _STATE_TOKENS[state_key]

    return ReflectionView(
        state_key=state_key,
        state_word=state_word,
        narrative=_trader_narrative(state_key, mis=mis, journal=journal, learning=learning),
        coaching_insight=_coaching_insight(state_key, mis=mis, journal=journal),
        forward_line=_forward_line(snapshot=snapshot, os_report=os_report, mis=mis),
        recommendation=_recommendation(state_key, mis=mis),
        change_prose=_what_id_change(portfolio, mis=mis, snapshot=snapshot),
        primary_label="I'm good",
        primary_action="good",
    )


def _render_reflection_body(view: ReflectionView, *, built_at: str, broker: BrokerSnapshot) -> None:
    sync_cls, dot_cls, sync_label = _sync_status(broker)
    narrative_html = "".join(f'<p class="vc-mentor rc-narrative">{_esc(line)}</p>' for line in view.narrative)
    st.markdown(
        f'<div class="verdict-canvas-root reflection-canvas-root" data-reflection="{_esc(view.state_key)}">'
        f'<div class="vc-header">'
        f'<p class="vc-time">{_esc(built_at)}</p>'
        f'<p class="vc-sync {sync_cls}">'
        f'<span class="vc-sync-dot {dot_cls}"></span>{_esc(sync_label)}</p>'
        f"</div>"
        f'<div class="rc-hero-zone rc-hero-{_esc(view.state_key)}">'
        f'<p class="pc-context">{_esc(_MICRO_LABEL)}</p>'
        f'<p class="pc-symbol">{_esc(view.state_word)}</p>'
        f"</div>"
        f"{narrative_html}"
        f'<p class="rc-coaching">{_esc(view.coaching_insight)}</p>'
        f'<p class="rc-forward">{_esc(view.forward_line)}</p>'
        f'<p class="pc-reason">{_esc(view.recommendation)}</p>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="vc-primary">', unsafe_allow_html=True)
    if st.button(view.primary_label, key="rc_primary", type="primary", use_container_width=True):
        if view.primary_action == "good":
            st.toast("Keep going — you're on the right path.")
        elif view.primary_action == "connect":
            request_nav_tab("My Portfolio")
        elif view.primary_action == "today":
            set_partner_dock("today")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="vc-ghost-row">', unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        with st.popover("What I'd change"):
            st.markdown(view.change_prose)
    with g2:
        if st.button("How we're doing", key="rc_history", use_container_width=True):
            from ui.components.trust_canvas import open_trust_canvas

            open_trust_canvas()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<p class="vc-foot">Zerodha Console is source of truth for P&amp;L.</p></div>',
        unsafe_allow_html=True,
    )


def render_reflection_canvas(*, market: str, cached: dict[str, Any]) -> None:
    del market
    from analyzer.trade_journal import load_journal_entries
    from ui.components.home_dashboard import _snapshot_from_cache

    snapshot_obj = _snapshot_from_cache(cached["snapshot"])
    mis: MisTradeAdvisory = cached["mis"]
    os_report: InvestmentOS = cached["os_report"]
    portfolio: ZerodhaImportResult | None = cached.get("portfolio")
    learning: list[LearningOutcomeRow] = cached.get("learning") or []
    journal = load_journal_entries(limit=14)
    broker = _broker_snapshot()
    built_at = str(cached["built_at"])

    view = build_reflection_view(
        broker=broker,
        mis=mis,
        snapshot=snapshot_obj,
        os_report=os_report,
        portfolio=portfolio,
        journal=journal,
        learning=learning,
    )
    _render_reflection_body(view, built_at=built_at, broker=broker)
