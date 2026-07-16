"""Phase 5 — Trust Canvas (accountability story, presentation only)."""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st

from analyzer.broker_truth.learning import LearningOutcomeRow
from analyzer.context_engine.models import ContextSnapshot
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.suggestion_journal import SuggestionRecord, fetch_suggestions, init_journal
from analyzer.trade_journal import TradeJournalEntry
from analyzer.watchlist_pins import PinnedPlan
from analyzer.zerodha import ZerodhaImportResult
from ui.broker.state import BrokerSnapshot
from ui.components.home_dashboard import _strip_md, _trim_words
from ui.components.partner_shell import clear_partner_depth, set_partner_dock

IST = ZoneInfo("Asia/Kolkata")

_MICRO_LABEL = "I've been reviewing every decision."
_FORWARD_LINE = (
    "I'll continue checking every recommendation against reality. That's how I improve."
)
_THIN_HISTORY_BODY = (
    "I'm still learning your portfolio. Trust will come from consistency, not promises."
)

_TRUST_TOKENS: dict[str, tuple[str, str]] = {
    "honest": ("honest", "Honest"),
    "learning": ("learning", "Learning"),
    "earned": ("earned", "Earned"),
}

_WAIT_ACTIONS = frozenset({"WAIT", "HOLD", "AVOID", "PASS", "PAUSE", "DEFENSIVE"})
_TRADE_ACTIONS = frozenset({"BUY", "LONG", "TRADE", "ACT", "ENTRY"})


@dataclass(frozen=True)
class TrustView:
    micro_label: str
    trust_key: str
    trust_word: str
    last_week: str
    this_week: str
    miss_line: str
    forward_line: str
    wrong_bullets: tuple[str, ...]
    learn_bullets: tuple[str, ...]
    primary_label: str
    primary_action: str  # back_you | connect
    thin_history: bool


def _esc(text: str) -> str:
    return html.escape(str(text or ""))


def _weekday_label(iso_date: str) -> str:
    try:
        dt = datetime.strptime(iso_date[:10], "%Y-%m-%d")
        return dt.strftime("%A")
    except ValueError:
        return "that session"


def _recent_suggestions(*, days: int = 14) -> list[SuggestionRecord]:
    init_journal()
    cutoff = (datetime.now(IST).date() - timedelta(days=days)).isoformat()
    rows = fetch_suggestions(limit=300)
    return [r for r in rows if r.validated and r.signal_date >= cutoff]


def _split_windows(
    suggestions: list[SuggestionRecord],
    learning: list[LearningOutcomeRow],
) -> tuple[list[SuggestionRecord], list[SuggestionRecord], list[LearningOutcomeRow], list[LearningOutcomeRow]]:
    today = datetime.now(IST).date()
    week_cut = (today - timedelta(days=4)).isoformat()
    last_cut = (today - timedelta(days=14)).isoformat()

    last_s = [r for r in suggestions if last_cut <= r.signal_date < week_cut]
    this_s = [r for r in suggestions if r.signal_date >= week_cut]
    last_l = [r for r in learning if last_cut <= r.trade_date < week_cut]
    this_l = [r for r in learning if r.trade_date >= week_cut]
    return last_s, this_s, last_l, this_l


def _is_wait_call(record: SuggestionRecord) -> bool:
    action = str(record.action or "").upper()
    if action in _WAIT_ACTIONS:
        return True
    reason = str(record.reason or "").lower()
    return any(word in reason for word in ("wait", "pause", "avoid", "patience", "sit out"))


def _is_trade_call(record: SuggestionRecord) -> bool:
    action = str(record.action or "").upper()
    return action in _TRADE_ACTIONS or "buy" in action.lower()


def _wait_story(last_suggestions: list[SuggestionRecord], last_learning: list[LearningOutcomeRow]) -> str:
    wait_rows = [r for r in last_suggestions if _is_wait_call(r)]
    wait_count = len(wait_rows) if wait_rows else max(len(last_learning), 0)

    saved = 0
    for row in wait_rows:
        if row.outcome_correct == 1 and row.outcome_return_1d is not None and row.outcome_return_1d < 0:
            saved += 1
        elif row.outcome_correct == 1:
            saved += 1

    if wait_count >= 2 and saved >= 1:
        return (
            f"Last week I told you to wait on {wait_count} sessions. "
            f"{saved} of those days closed against chasing — waiting protected your capital."
        )
    if wait_count >= 1:
        return (
            f"Last week I leaned toward waiting on {wait_count} session"
            f"{'s' if wait_count != 1 else ''}. "
            "Patience kept you out of unnecessary risk."
        )
    flat_days = sum(1 for row in last_learning if row.outcome == "flat")
    if flat_days >= 2:
        return (
            f"Last week I kept {flat_days} sessions light. "
            "Staying flat avoided forcing trades in mixed tape."
        )
    return (
        "Last week I favored patience over action. "
        "That restraint is how capital survives choppy markets."
    )


def _trade_story(
    this_suggestions: list[SuggestionRecord],
    this_learning: list[LearningOutcomeRow],
    pins: list[PinnedPlan],
) -> str:
    trade_rows = [r for r in this_suggestions if _is_trade_call(r)]
    trade_count = len(trade_rows) if trade_rows else len(this_learning)
    recent_pins = [p for p in pins[:3]]

    if trade_count >= 2:
        return (
            f"This week I suggested {trade_count} trades. "
            "Both stayed inside your risk limits — stops defined before entry."
        )
    if trade_count == 1:
        sym = trade_rows[0].symbol if trade_rows else (recent_pins[0].symbol if recent_pins else "the setup")
        sym = sym.upper().replace(".NS", "")
        return (
            f"This week I suggested one trade on {sym}. "
            "It was sized with a defined stop before entry."
        )
    if recent_pins:
        sym = recent_pins[0].symbol.upper().replace(".NS", "")
        return (
            f"This week I'm tracking {sym} with a clear plan. "
            "Risk is capped before any entry."
        )
    return (
        "This week I've kept suggestions narrow. "
        "Every idea comes with a stop and a max loss first."
    )


def _pick_miss(
    suggestions: list[SuggestionRecord],
    journal: list[TradeJournalEntry],
) -> tuple[str, list[str]]:
    misses: list[str] = []
    for row in suggestions:
        if row.outcome_correct != 0:
            continue
        sym = row.symbol.upper().replace(".NS", "")
        day = _weekday_label(row.signal_date)
        note = _strip_md(row.outcome_note or "")
        lesson = note if note else "tightened my confirmation rule"
        line = f"I missed {day}'s {sym} move. I've {lesson.rstrip('.')}."
        misses.append(line)

    for entry in journal:
        if not entry.mistake:
            continue
        sym = entry.symbol.upper().replace(".NS", "") or "that trade"
        day = _weekday_label(entry.trade_date)
        fix = _strip_md(entry.fix or "updated how I read that setup")
        line = f"I missed {day} on {sym}. I've {fix.rstrip('.')}."
        if line not in misses:
            misses.append(line)

    if not misses:
        return "", []
    return misses[0], misses[:4]


def _resolve_trust_word(
    *,
    scored_count: int,
    has_miss: bool,
    wait_saved: int,
    trade_count: int,
) -> tuple[str, str]:
    if scored_count < 3:
        return _TRUST_TOKENS["honest"]
    if has_miss:
        return _TRUST_TOKENS["learning"]
    if wait_saved >= 2 and trade_count >= 1:
        return _TRUST_TOKENS["earned"]
    return _TRUST_TOKENS["honest"]


def _learn_bullets(mis: MisTradeAdvisory, *, has_miss: bool) -> tuple[str, ...]:
    bullets = [
        "Every Wait, Trade, or Pause is checked against what the market actually did.",
        "Your journal and broker fills are the scorecard — I don't grade myself in a vacuum.",
    ]
    if has_miss:
        bullets.append("A miss updates what I watch tomorrow — rules tighten, not excuses.")
    elif mis.flags:
        bullets.append(_strip_md(mis.flags[0]))
    else:
        bullets.append("Consistency over weeks is what earns trust — not one lucky call.")
    return tuple(bullets[:4])


def build_trust_view(
    *,
    broker: BrokerSnapshot,
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
    os_report: InvestmentOS,
    portfolio: ZerodhaImportResult | None,
    journal: list[TradeJournalEntry],
    learning: list[LearningOutcomeRow],
    pins: list[PinnedPlan],
    prefs: IntradayPrefs,
) -> TrustView:
    del snapshot, os_report, portfolio, prefs

    suggestions = _recent_suggestions(days=14)
    last_s, this_s, last_l, this_l = _split_windows(suggestions, learning)
    scored_count = len(suggestions) + len(learning)
    miss_line, wrong_bullets = _pick_miss(suggestions, journal)
    has_miss = bool(miss_line)

    wait_saved = sum(
        1
        for row in last_s
        if _is_wait_call(row) and row.outcome_correct == 1
    )
    trade_count = len([r for r in this_s if _is_trade_call(r)]) + len(this_l)
    trust_key, trust_word = _resolve_trust_word(
        scored_count=scored_count,
        has_miss=has_miss,
        wait_saved=wait_saved,
        trade_count=trade_count,
    )

    if not broker.connected() and scored_count < 2:
        return TrustView(
            micro_label=_MICRO_LABEL,
            trust_key="honest",
            trust_word="Honest",
            last_week="",
            this_week=(
                "Connect Zerodha so I can check every recommendation against your real book — "
                "not estimates."
            ),
            miss_line="",
            forward_line=_FORWARD_LINE,
            wrong_bullets=(),
            learn_bullets=_learn_bullets(mis, has_miss=False),
            primary_label="Connect Zerodha",
            primary_action="connect",
            thin_history=True,
        )

    if scored_count < 3:
        return TrustView(
            micro_label=_MICRO_LABEL,
            trust_key="honest",
            trust_word="Honest",
            last_week="",
            this_week=_THIN_HISTORY_BODY,
            miss_line=miss_line,
            forward_line=_FORWARD_LINE,
            wrong_bullets=tuple(wrong_bullets),
            learn_bullets=_learn_bullets(mis, has_miss=has_miss),
            primary_label="Back to You",
            primary_action="back_you",
            thin_history=True,
        )

    return TrustView(
        micro_label=_MICRO_LABEL,
        trust_key=trust_key,
        trust_word=trust_word,
        last_week=_trim_words(_wait_story(last_s, last_l), max_words=32),
        this_week=_trim_words(_trade_story(this_s, this_l, pins), max_words=28),
        miss_line=_trim_words(miss_line, max_words=24) if miss_line else "",
        forward_line=_FORWARD_LINE,
        wrong_bullets=tuple(wrong_bullets) if wrong_bullets else ("No major misses logged this window.",),
        learn_bullets=_learn_bullets(mis, has_miss=has_miss),
        primary_label="Back to You",
        primary_action="back_you",
        thin_history=False,
    )


def open_trust_canvas() -> None:
    from ui.components.partner_shell import PARTNER_DEPTH_KEY, TRUST_DEPTH

    st.session_state[PARTNER_DEPTH_KEY] = TRUST_DEPTH
    set_partner_dock("you")


def close_trust_canvas() -> None:
    clear_partner_depth()
    st.rerun()


def _handle_primary(action: str) -> None:
    if action == "connect":
        clear_partner_depth()
        from ui.navigation import request_nav_tab

        request_nav_tab("My Portfolio")
        return
    close_trust_canvas()


def render_trust_canvas(*, market: str, cached: dict[str, Any]) -> None:
    del market
    from analyzer.trade_journal import load_journal_entries
    from ui.components.home_dashboard import _broker_snapshot, _snapshot_from_cache

    snapshot = _snapshot_from_cache(cached["snapshot"])
    mis: MisTradeAdvisory = cached["mis"]
    os_report: InvestmentOS = cached["os_report"]
    portfolio: ZerodhaImportResult | None = cached.get("portfolio")
    learning: list[LearningOutcomeRow] = cached.get("learning") or []
    pins: list[PinnedPlan] = cached["pins"]
    prefs: IntradayPrefs = cached["prefs"]
    journal = load_journal_entries(limit=14)
    broker = _broker_snapshot()
    built_at = str(cached["built_at"])

    view = build_trust_view(
        broker=broker,
        mis=mis,
        snapshot=snapshot,
        os_report=os_report,
        portfolio=portfolio,
        journal=journal,
        learning=learning,
        pins=pins,
        prefs=prefs,
    )

    from ui.components.home_dashboard import _sync_status

    sync_cls, dot_cls, sync_label = _sync_status(broker)

    body_parts = []
    if view.thin_history and view.this_week:
        body_parts.append(f'<p class="tc-detail">{_esc(view.this_week)}</p>')
    else:
        if view.last_week:
            body_parts.append(f'<p class="tc-mentor">{_esc(view.last_week)}</p>')
        if view.this_week:
            body_parts.append(f'<p class="tc-detail">{_esc(view.this_week)}</p>')
    if view.miss_line:
        body_parts.append(f'<p class="tc-miss">{_esc(view.miss_line)}</p>')
    body_parts.append(f'<p class="tc-forward">{_esc(view.forward_line)}</p>')
    body_html = "".join(body_parts)

    st.markdown(
        f'<div class="verdict-canvas-root trust-canvas-root" data-trust="{_esc(view.trust_key)}">'
        f'<div class="vc-header">'
        f'<p class="vc-time">{_esc(built_at)}</p>'
        f'<p class="vc-sync {sync_cls}">'
        f'<span class="vc-sync-dot {dot_cls}"></span>{_esc(sync_label)}</p>'
        f"</div>"
        f'<div class="tc-hero-zone tc-hero-{_esc(view.trust_key)}">'
        f'<p class="pc-context">{_esc(view.micro_label)}</p>'
        f'<p class="pc-symbol">{_esc(view.trust_word)}</p>'
        f"</div>"
        f"{body_html}",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="vc-primary">', unsafe_allow_html=True)
    if st.button(view.primary_label, key="tc_primary", type="primary", use_container_width=True):
        _handle_primary(view.primary_action)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="vc-ghost-row">', unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        with st.popover("What we got wrong"):
            for line in view.wrong_bullets:
                st.markdown(f"- {line}")
    with g2:
        with st.popover("How I learn"):
            for line in view.learn_bullets:
                st.markdown(f"- {line}")
    if view.miss_line:
        if st.button("What I saw that day", key="tc_fossil", use_container_width=True):
            from ui.components.proof_canvas import open_proof_overlay

            open_proof_overlay(
                origin="trust",
                proof_mode="fossil",
                miss_note=view.miss_line,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<p class="vc-foot">Zerodha Console is source of truth for P&amp;L.</p></div>',
        unsafe_allow_html=True,
    )
