"""Phase 4 — Ask overlay · Answer Canvas (one question, one answer)."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Any

import streamlit as st

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact, DecisionVerdict
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.investment_os import InvestmentOS
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.unified_search import extract_symbol_from_command, unified_search
from analyzer.watchlist_pins import PinnedPlan
from analyzer.zerodha import ZerodhaImportResult
from ui.broker.state import BrokerSnapshot
from ui.components.home_dashboard import (
    _evidence_summary,
    _pick_decision,
    _snapshot_from_cache,
    _strip_md,
    _trim_words,
    _why_bullets,
)
from ui.components.partner_shell import set_partner_dock
from ui.components.proof_runtime import proof_canvas_active

ASK_OVERLAY_OPEN = "ask_overlay_open"
ASK_SUBMITTED_QUERY = "ask_submitted_query"
ASK_DRAFT_KEY = "ask_draft_query"

_SUGGESTION_CHIPS: tuple[str, str] = (
    "Can I afford this trade?",
    "What if Nifty falls 2%?",
)

_BUY_RE = re.compile(r"\b(buy|add|enter|accumulate|pick\s*up)\b", re.I)
_SELL_RE = re.compile(r"\b(sell|exit|dump|book\s*profit|cut\s*loss)\b", re.I)
_AFFORD_RE = re.compile(r"\b(afford|size|capital|risk\s*budget|how\s*much)\b", re.I)
_MACRO_RE = re.compile(r"\b(nifty|sensex|market\s*fall|falls?\s*\d|drop\s*\d|down\s*\d|%\s*fall)\b", re.I)
_AVG_RE = re.compile(r"\b(average\s*down|averaging|double\s*down|add\s*more\s*to)\b", re.I)
_NIFTY_DROP_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%?", re.I)

_ANSWER_CSS_KEYS: dict[str, str] = {
    "wait": "wait",
    "buy": "trade",
    "sell": "pause",
    "reduce": "wait",
    "pass": "rest",
    "risk": "pause",
    "yes": "trade",
    "tight": "wait",
    "no": "pause",
}


@dataclass(frozen=True)
class AskAnswerView:
    query_echo: str
    context_line: str
    answer_key: str
    answer_word: str
    mentor_line: str
    recommendation: str
    why_bullets: tuple[str, ...]
    uncertainty: str
    primary_label: str
    primary_action: str  # back_today | connect


def _esc(text: str) -> str:
    return html.escape(str(text or ""))


def _display_symbol(symbol: str) -> str:
    return str(symbol or "").upper().replace(".NS", "").replace(".BO", "")


def _personalized_opener(broker: BrokerSnapshot) -> str:
    if broker.connected():
        return "If I were managing your portfolio today,"
    return "If I were trading with your settings today,"


def _context_line(broker: BrokerSnapshot) -> str:
    if broker.connected():
        return "Based on today's market and your portfolio."
    return "Based on today's market and your saved plan."


def _resolve_symbol(query: str) -> str | None:
    direct = extract_symbol_from_command(query)
    if direct:
        return _display_symbol(direct)

    hits = unified_search(query, max_results=5)
    for hit in hits:
        if hit.match_type == "tab":
            continue
        sym = _display_symbol(hit.symbol)
        if sym:
            return sym

    tokens = re.findall(r"\b[A-Za-z][A-Za-z0-9&]{1,11}\b", query)
    for token in reversed(tokens):
        upper = token.upper()
        if upper in {
            "I",
            "A",
            "AN",
            "THE",
            "MY",
            "IF",
            "OR",
            "AND",
            "NOT",
            "CAN",
            "SHOULD",
            "WHAT",
            "WHY",
            "HOW",
            "BUY",
            "SELL",
        }:
            continue
        probe = unified_search(upper, max_results=1)
        if probe and probe[0].match_type != "tab":
            return _display_symbol(probe[0].symbol)
    return None


def _holds_symbol(portfolio: ZerodhaImportResult | None, symbol: str) -> bool:
    if not portfolio or not symbol:
        return False
    target = symbol.upper()
    for row in portfolio.holdings:
        sym = _display_symbol(getattr(row, "symbol", "") or getattr(row, "kite_symbol", ""))
        if sym == target:
            return True
    return False


def _classify_intent(query: str) -> str:
    q = query.strip().lower()
    if _AVG_RE.search(q):
        return "average_down"
    if _AFFORD_RE.search(q):
        return "afford"
    if _MACRO_RE.search(q):
        return "macro"
    if _SELL_RE.search(q):
        return "sell"
    if _BUY_RE.search(q):
        return "buy"
    if _resolve_symbol(query):
        return "buy"
    return "generic"


def _verdict_to_answer(decision: DecisionArtifact | None) -> tuple[str, str]:
    if not decision:
        return "wait", "Wait"
    if decision.verdict == DecisionVerdict.ACT:
        return "buy", "Buy"
    if decision.verdict == DecisionVerdict.REDUCE:
        return "reduce", "Reduce"
    if decision.verdict in (DecisionVerdict.PASS, DecisionVerdict.DEFENSIVE):
        return "pass", "Pass"
    return "wait", "Wait"


def _risk_budget_inr(prefs: IntradayPrefs) -> float:
    return float(prefs.capital) * (float(prefs.max_risk_pct) / 100.0)


def _build_afford_answer(
    *,
    broker: BrokerSnapshot,
    prefs: IntradayPrefs,
    mis: MisTradeAdvisory,
    snapshot: ContextSnapshot,
) -> tuple[str, str, str, str]:
    if not broker.connected():
        opener = _personalized_opener(broker)
        mentor = (
            f"{opener} I'd connect Zerodha first so I can size against your real cash and book."
        )
        rec = "Link once — then I can answer afford questions against live positions."
        return "pass", mentor, rec, "connect"

    budget = _risk_budget_inr(prefs)
    budget_txt = f"₹{budget:,.0f}"
    tight = mis.loss_streak_days >= 1 or snapshot.risk_mode in ("RISK-OFF", "CLOSED")
    if tight:
        key = "tight"
        body = f"you can risk about {budget_txt}, but today is not the day to stretch it."
        rec = "Size down if you already traded once today — protect the streak."
    elif budget >= 1500:
        key = "yes"
        body = f"you can afford roughly {budget_txt} risk — that's inside your daily rule."
        rec = "Keep one trade, one plan — don't stack bets on the same session."
    else:
        key = "no"
        body = f"your risk budget is only {budget_txt} — that's too thin for a new idea."
        rec = "Raise capital or wait for a cleaner setup before committing."

    opener = _personalized_opener(broker)
    mentor = f"{opener} {body[0].upper()}{body[1:]}"
    return key, mentor, rec, "back_today"


def _build_macro_answer(
    *,
    broker: BrokerSnapshot,
    snapshot: ContextSnapshot,
    portfolio: ZerodhaImportResult | None,
    drop_pct: float = 2.0,
) -> tuple[str, str, str]:
    sectors = dict(snapshot.sector_strength or {})
    weak = sorted(sectors.items(), key=lambda kv: kv[1])[:2]
    weak_names = ", ".join(name for name, _ in weak) if weak else "cyclicals"
    holding_note = ""
    if portfolio and portfolio.holdings:
        holding_note = f" Your {len(portfolio.holdings)} holdings would feel the drag."
    opener = _personalized_opener(broker)
    mentor = (
        f"{opener} a {drop_pct:g}% Nifty drop would hit {weak_names} hardest — "
        f"expect a quick mark-to-market pinch.{holding_note}"
    ).strip()
    rec = "No action required today — watch support before adding risk."
    return mentor, rec


def _build_average_down_answer(*, broker: BrokerSnapshot, mis: MisTradeAdvisory) -> tuple[str, str, str]:
    opener = _personalized_opener(broker)
    if mis.loss_streak_days >= 1:
        body = "averaging down after a red stretch turns one mistake into two."
    else:
        body = "averaging down isn't in your plan — it hides a bad entry instead of fixing it."
    mentor = f"{opener} {body[0].upper()}{body[1:]}"
    rec = "Wait for a fresh setup with a defined stop instead."
    return mentor, rec


def _build_symbol_answer(
    *,
    symbol: str,
    intent: str,
    broker: BrokerSnapshot,
    snapshot: ContextSnapshot,
    mis: MisTradeAdvisory,
    os_report: InvestmentOS,
    decision: DecisionArtifact | None,
    portfolio: ZerodhaImportResult | None,
) -> tuple[str, str, str, str]:
    starred = _display_symbol(os_report.starred_symbol or "")
    holding = _holds_symbol(portfolio, symbol)
    opener = _personalized_opener(broker)

    if intent == "sell":
        if holding:
            key, word = "wait", "Wait"
            body = f"{symbol} is in your book — I'd hold unless price breaks your stop."
            rec = f"Trim {symbol} only if you need cash; don't panic-sell a recoverable dip."
        else:
            key, word = "pass", "Pass"
            body = f"you don't hold {symbol} — nothing to sell here."
            rec = "Focus on names already in your plan."
    elif snapshot.risk_mode in ("RISK-OFF", "CLOSED") or mis.loss_streak_days >= 2:
        key, word = "wait", "Wait"
        body = f"{symbol} may work later, but today's risk mode says stand down."
        rec = f"Don't add {symbol} today — protect capital first."
    elif decision and starred == symbol:
        key, word = _verdict_to_answer(decision)
        if key == "buy":
            body = f"{symbol} lines up with today's plan — I'd enter only with a hard stop."
            rec = f"Add {symbol} only if size fits your daily risk — one trade, one plan."
        elif key == "reduce":
            body = f"{symbol} is extended in your book — I'd trim, not add."
            rec = f"Reduce {symbol} exposure before chasing more upside."
        else:
            body = f"{symbol} doesn't clear the bar right now — patience beats forcing it."
            rec = f"Pass on {symbol} today and wait for a cleaner trigger."
    elif holding and intent == "buy":
        key, word = "wait", "Wait"
        body = f"you already own {symbol} — I'd wait for a pullback before adding."
        rec = f"Don't stack {symbol}; let the current position prove itself."
    elif snapshot.risk_mode == "RISK-ON":
        key, word = "buy", "Buy"
        body = f"{symbol} can work in this tape — but only with a defined stop and modest size."
        rec = f"Size {symbol} small and respect your max loss for the session."
    else:
        key, word = "wait", "Wait"
        body = f"{symbol} is mixed — I'd wait for price to confirm before risking capital."
        rec = f"Don't add {symbol} until the setup matches your plan."

    mentor = f"{opener} {body[0].upper()}{body[1:]}"
    return key, word, mentor, rec


def build_ask_answer(
    query: str,
    *,
    broker: BrokerSnapshot,
    cached: dict[str, Any],
) -> AskAnswerView:
    """Map one natural-language question to a single Answer Canvas view."""
    raw = (query or "").strip()
    echo = raw if len(raw) <= 72 else f"{raw[:69]}…"
    context = _context_line(broker)

    snapshot = _snapshot_from_cache(cached["snapshot"])
    mis: MisTradeAdvisory = cached["mis"]
    os_report: InvestmentOS = cached["os_report"]
    pins: list[PinnedPlan] = cached["pins"]
    prefs: IntradayPrefs = cached["prefs"]
    portfolio: ZerodhaImportResult | None = cached.get("portfolio")
    decision, _source = _pick_decision(mis, os_report)

    intent = _classify_intent(raw)
    opener = _personalized_opener(broker)

    if intent == "afford":
        key, mentor, rec, action = _build_afford_answer(
            broker=broker,
            prefs=prefs,
            mis=mis,
            snapshot=snapshot,
        )
        word = {"yes": "Yes", "tight": "Tight", "no": "No", "pass": "Pass"}.get(key, "Pass")
        primary = "Connect Zerodha" if action == "connect" else "Back to Today"
        why = tuple(_why_bullets(decision, mis, snapshot, pins=pins))
        unc = "Mixed signals — I'd stay cautious." if key in ("tight", "no") else "I'm fairly sure about this."
        return AskAnswerView(echo, context, key, word, mentor, rec, why, unc, primary, action)

    if intent == "macro":
        drop = 2.0
        match = _NIFTY_DROP_RE.search(raw)
        if match:
            try:
                drop = float(match.group(1))
            except ValueError:
                drop = 2.0
        mentor, rec = _build_macro_answer(
            broker=broker,
            snapshot=snapshot,
            portfolio=portfolio,
            drop_pct=drop,
        )
        why = tuple(_why_bullets(decision, mis, snapshot, pins=pins))
        if snapshot.sector_strength:
            top = max(snapshot.sector_strength.items(), key=lambda kv: kv[1])
            why = (*why, f"Strongest sector today: {top[0]}.")[:6]
        unc = "Scenario estimates — actual moves can differ."
        return AskAnswerView(
            echo, context, "risk", "Risk", mentor, rec, why, unc, "Back to Today", "back_today"
        )

    if intent == "average_down":
        mentor, rec = _build_average_down_answer(broker=broker, mis=mis)
        why = tuple(_why_bullets(decision, mis, snapshot, pins=pins))
        if mis.flags:
            why = (*why, _strip_md(mis.flags[0]))[:6]
        unc = "I'm fairly sure — averaging down rarely fixes a bad entry."
        return AskAnswerView(
            echo, context, "pass", "Pass", mentor, rec, why, unc, "Back to Today", "back_today"
        )

    symbol = _resolve_symbol(raw)
    if symbol and intent in ("buy", "sell", "generic"):
        key, word, mentor, rec = _build_symbol_answer(
            symbol=symbol,
            intent=intent if intent != "generic" else "buy",
            broker=broker,
            snapshot=snapshot,
            mis=mis,
            os_report=os_report,
            decision=decision,
            portfolio=portfolio,
        )
        why = tuple(_why_bullets(decision, mis, snapshot, pins=pins))
        for line in _evidence_summary(decision, limit=2):
            text = _strip_md(line)
            if text not in why:
                why = (*why, text)[:6]
        unc = "I'm fairly sure about this." if key in ("buy", "wait") else "Mixed signals — I'd stay cautious."
        return AskAnswerView(
            echo, context, key, word, _trim_words(mentor, max_words=28), rec, why, unc, "Back to Today", "back_today"
        )

    if not symbol and intent in ("buy", "sell"):
        mentor = (
            f"{opener} I couldn't map that to an NSE symbol — try tickers like HAL or INFY."
        )
        rec = "Rephrase with a clear symbol so I can give a one-word answer."
        return AskAnswerView(
            echo,
            context,
            "pass",
            "Pass",
            mentor,
            rec,
            ("Use NSE tickers or company names from your watchlist.",),
            "I need a symbol to answer precisely.",
            "Back to Today",
            "back_today",
        )

    mentor = f"{opener} I answer trading decisions — try a what-if about a stock or your risk."
    rec = "Ask about a symbol, sizing, or a Nifty scenario."
    return AskAnswerView(
        echo,
        context,
        "pass",
        "Pass",
        mentor,
        rec,
        tuple(_why_bullets(decision, mis, snapshot, pins=pins)),
        "Off-topic questions don't get a trade call.",
        "Back to Today",
        "back_today",
    )


def suggestion_chips() -> tuple[str, str]:
    return _SUGGESTION_CHIPS


def open_ask_overlay() -> None:
    st.session_state[ASK_OVERLAY_OPEN] = True
    st.session_state.pop(ASK_SUBMITTED_QUERY, None)
    st.session_state.pop(ASK_DRAFT_KEY, None)
    st.session_state.pop("partner_ask_stage", None)
    st.rerun()


def close_ask_overlay_silent() -> None:
    st.session_state[ASK_OVERLAY_OPEN] = False
    st.session_state.pop(ASK_SUBMITTED_QUERY, None)
    st.session_state.pop(ASK_DRAFT_KEY, None)
    st.session_state.pop("partner_ask_stage", None)


def close_ask_overlay(*, go_today: bool = False) -> None:
    close_ask_overlay_silent()
    if go_today:
        set_partner_dock("today")
    else:
        st.rerun()


def _handle_primary(action: str) -> None:
    if action == "connect":
        st.session_state[ASK_OVERLAY_OPEN] = False
        st.session_state.pop(ASK_SUBMITTED_QUERY, None)
        st.session_state.pop(ASK_DRAFT_KEY, None)
        from ui.navigation import request_nav_tab

        request_nav_tab("My Portfolio")
        return
    close_ask_overlay(go_today=True)


def is_ask_overlay_open() -> bool:
    return bool(st.session_state.get(ASK_OVERLAY_OPEN))


def render_answer_overlay(*, market: str, cached: dict[str, Any]) -> None:
    del market
    from ui.components.home_dashboard import _broker_snapshot

    broker = _broker_snapshot()

    st.markdown('<div class="answer-canvas-overlay" data-answer-open="1">', unsafe_allow_html=True)

    close_col, _sp = st.columns([1, 5])
    with close_col:
        st.markdown('<div class="ac-close-wrap">', unsafe_allow_html=True)
        if st.button("✕", key="ac_close"):
            close_ask_overlay(go_today=False)
        st.markdown("</div>", unsafe_allow_html=True)

    submitted = str(st.session_state.get(ASK_SUBMITTED_QUERY, "") or "").strip()

    if not submitted:
        st.markdown(
            '<div class="answer-canvas-root ac-idle">'
            '<p class="ac-idle-hero">What if…</p></div>',
            unsafe_allow_html=True,
        )

        draft = str(st.session_state.get(ASK_DRAFT_KEY, "") or "")
        chip_a, chip_b = st.columns(2)
        chips = suggestion_chips()
        with chip_a:
            if st.button(chips[0], key="ac_chip_0"):
                st.session_state[ASK_DRAFT_KEY] = chips[0]
                st.rerun()
        with chip_b:
            if st.button(chips[1], key="ac_chip_1"):
                st.session_state[ASK_DRAFT_KEY] = chips[1]
                st.rerun()

        with st.form("ac_ask_form", clear_on_submit=False):
            query = st.text_input(
                "What if question",
                value=draft,
                placeholder="Ask anything about your trades…",
                label_visibility="collapsed",
            )
            if st.form_submit_button("Submit", use_container_width=True):
                text = (query or "").strip()
                if text:
                    st.session_state[ASK_SUBMITTED_QUERY] = text
                    st.session_state.pop(ASK_DRAFT_KEY, None)
                    st.rerun()
    else:
        answer = build_ask_answer(submitted, broker=broker, cached=cached)
        glow = _ANSWER_CSS_KEYS.get(answer.answer_key, "rest")

        st.markdown(
            f'<div class="answer-canvas-root ac-answer" data-answer="{_esc(answer.answer_key)}">'
            f'<p class="ac-query-echo">You asked: {_esc(answer.query_echo)}</p>'
            f'<p class="ac-context-line">{_esc(answer.context_line)}</p>'
            f'<div class="ac-hero-zone ac-hero-{glow}">'
            f'<p class="ac-answer-word">{_esc(answer.answer_word)}</p></div>'
            f'<p class="ac-mentor">{_esc(answer.mentor_line)}</p>'
            f'<p class="ac-recommendation">{_esc(answer.recommendation)}</p></div>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="vc-primary ac-primary">', unsafe_allow_html=True)
        if st.button(answer.primary_label, key="ac_primary", type="primary", use_container_width=True):
            _handle_primary(answer.primary_action)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="vc-ghost-hint ac-ghost">', unsafe_allow_html=True)
        with st.popover("Why?"):
            for line in answer.why_bullets:
                st.markdown(f"- {line}")
            st.caption(answer.uncertainty)
            if proof_canvas_active() and st.button("See the proof", key="ac_proof"):
                from ui.components.proof_state import open_proof_overlay

                sym = None
                from analyzer.unified_search import unified_search

                hits = unified_search(submitted, max_results=1)
                if hits and hits[0].match_type != "tab":
                    sym = hits[0].symbol
                open_proof_overlay(
                    origin="ask",
                    proof_mode="ask",
                    symbol=sym,
                    ask_query=submitted,
                    ask_answer_word=answer.answer_word,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
