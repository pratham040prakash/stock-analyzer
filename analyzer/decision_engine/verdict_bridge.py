"""Verdict bridge — evidence producers route legacy labels through Decision Engine only."""

from __future__ import annotations

import logging
from typing import Callable

from analyzer.decision_engine.engine import DecisionEngine, default_decision_engine
from analyzer.decision_engine.migration import (
    capital_constraints_from_prefs,
    decide_from_packet,
    legacy_advisor_action,
    legacy_mis_verdict,
    legacy_synthesis_verdict,
    market_context_from_timing,
    user_preferences_from_prefs,
)
from analyzer.decision_engine.models import (
    DecisionArtifact,
    DecisionVerdict,
    MarketContext,
    RiskSettings,
    UncertaintyVector,
)
from analyzer.evidence_engine.builder import EvidenceBuilder
from analyzer.evidence_engine.models import (
    EvidenceCategory,
    EvidenceConfidence,
    EvidenceSource,
    EvidenceType,
)

logger = logging.getLogger(__name__)

LegacyMapper = Callable[[DecisionArtifact], str]


def _clamp_vote(score: float, scale: float = 50.0) -> float:
    return max(-2.0, min(2.0, score / scale))


def _market_session_item() -> list:
    b = EvidenceBuilder()
    try:
        from analyzer.intraday_beginner_tips import session_timing_advice

        timing = session_timing_advice()
        return [
            b.fact(
                category=EvidenceCategory.MARKET,
                label="Session timing",
                value=timing.headline[:80],
                explanation=timing.detail or timing.headline,
                source=EvidenceSource.INTERNAL_MODEL,
                metadata={"signal": "neutral" if timing.allow_new_entries else "bearish"},
            )
        ]
    except Exception:
        return [
            b.fact(
                category=EvidenceCategory.MARKET,
                label="Session",
                value="unknown",
                explanation="Session context unavailable",
                source=EvidenceSource.INTERNAL_MODEL,
            )
        ]


def evidence_items_from_score(
    score: float,
    *,
    label: str = "Composite score",
    category: EvidenceCategory = EvidenceCategory.TECHNICAL,
    explanation: str = "",
    weight: float = 0.8,
    scale: float = 50.0,
    source: EvidenceSource = EvidenceSource.INTERNAL_MODEL,
) -> list:
    """Score signal as evidence — not a verdict."""
    b = EvidenceBuilder()
    return [
        b.estimate(
            category=category,
            label=label,
            value=round(score, 2),
            explanation=explanation or f"Internal score {score:+.1f} — input to Decision Engine",
            source=source,
            confidence=EvidenceConfidence.MEDIUM,
            weight=weight,
            metadata={"vote": _clamp_vote(score, scale), "score": score},
        )
    ]


def evidence_items_from_signal_details(signals, *, category: EvidenceCategory = EvidenceCategory.TECHNICAL) -> list:
    """Convert SignalDetail / similar objects to evidence votes."""
    b = EvidenceBuilder()
    items = []
    for sig in signals[:12]:
        name = getattr(sig, "name", "signal")
        detail = getattr(sig, "detail", "")
        vote = float(getattr(sig, "score", 0) or 0)
        bias = getattr(sig, "signal", getattr(sig, "bias", "neutral"))
        items.append(
            b.estimate(
                category=category,
                label=str(name)[:60],
                value=detail[:120] if detail else str(bias),
                explanation=detail or str(bias),
                source=EvidenceSource.INTERNAL_MODEL,
                confidence=EvidenceConfidence.LOW,
                weight=0.4,
                metadata={"vote": vote, "signal": str(bias).lower()},
            )
        )
    return items


def evidence_items_from_reasons(reasons: list[str], *, category: EvidenceCategory = EvidenceCategory.TECHNICAL) -> list:
    b = EvidenceBuilder()
    items = []
    for idx, reason in enumerate(reasons[:8]):
        sig = "bullish" if any(w in reason.lower() for w in ("bull", "buy", "above", "breakout")) else (
            "bearish" if any(w in reason.lower() for w in ("bear", "sell", "below", "fade", "weak")) else "neutral"
        )
        vote = 0.4 if sig == "bullish" else (-0.4 if sig == "bearish" else 0.0)
        items.append(
            b.opinion(
                category=category,
                label=f"Signal {idx + 1}",
                value=reason[:120],
                explanation=reason,
                metadata={"signal": sig, "vote": vote},
            )
        )
    return items


def evidence_items_from_intraday_signals(signals) -> list:
    b = EvidenceBuilder()
    items = []
    for sig in signals[:10]:
        bias = getattr(sig, "bias", "neutral")
        vote = 0.6 if bias == "bullish" else (-0.6 if bias == "bearish" else 0.0)
        items.append(
            b.estimate(
                category=EvidenceCategory.TECHNICAL,
                label=getattr(sig, "name", "intraday"),
                value=getattr(sig, "detail", "")[:120],
                explanation=getattr(sig, "detail", ""),
                source=EvidenceSource.INTERNAL_MODEL,
                metadata={"vote": vote, "signal": bias},
            )
        )
    return items


def evidence_items_from_daily_context(
    *,
    combined_rec: str,
    tech: float,
    fund: float,
    pnl: float | None = None,
    weight: float | None = None,
    intraday_action: str | None = None,
    session_bias: str | None = None,
    is_watchlist: bool = False,
) -> list:
    """Portfolio / watchlist context as evidence."""
    b = EvidenceBuilder()
    items = [
        b.estimate(
            category=EvidenceCategory.TECHNICAL,
            label="Technical score",
            value=tech,
            explanation=f"Technical composite {tech:+.1f}",
            source=EvidenceSource.INTERNAL_MODEL,
            metadata={"vote": _clamp_vote(tech), "score": tech},
        ),
        b.estimate(
            category=EvidenceCategory.FUNDAMENTAL,
            label="Fundamental score",
            value=fund,
            explanation=f"Fundamental composite {fund:+.1f}",
            source=EvidenceSource.INTERNAL_MODEL,
            metadata={"vote": _clamp_vote(fund), "score": fund},
        ),
        b.opinion(
            category=EvidenceCategory.TECHNICAL,
            label="Combined signal",
            value=combined_rec,
            explanation=f"Combined recommendation input: {combined_rec}",
            metadata={"signal": _rec_to_signal(combined_rec), "vote": _rec_to_vote(combined_rec)},
        ),
    ]
    if pnl is not None:
        items.append(
            b.fact(
                category=EvidenceCategory.RISK,
                label="Position P&L",
                value=f"{pnl:+.1f}%",
                explanation="Unrealized P&L context",
                source=EvidenceSource.INTERNAL_MODEL,
                metadata={"vote": -0.5 if pnl < -10 else (0.3 if pnl > 15 else 0.0)},
            )
        )
    if weight is not None and weight > 12:
        items.append(
            b.opinion(
                category=EvidenceCategory.RISK,
                label="Portfolio weight",
                value=f"{weight:.0f}%",
                explanation="Overweight position",
                metadata={"vote": -0.6, "signal": "bearish"},
            )
        )
    if intraday_action:
        items.append(
            b.estimate(
                category=EvidenceCategory.TECHNICAL,
                label="Intraday action",
                value=intraday_action,
                explanation="Live chart action input",
                metadata={"signal": _rec_to_signal(intraday_action), "vote": _rec_to_vote(intraday_action)},
            )
        )
    if session_bias:
        items.append(
            b.fact(
                category=EvidenceCategory.MARKET,
                label="Session bias",
                value=session_bias,
                explanation=f"Intraday session bias: {session_bias}",
                metadata={"signal": session_bias.lower(), "vote": 0.5 if session_bias == "BULLISH" else (-0.5 if session_bias == "BEARISH" else 0.0)},
            )
        )
    if is_watchlist:
        items.append(
            b.fact(
                category=EvidenceCategory.EXECUTION,
                label="Position",
                value="watchlist",
                explanation="No open position — watchlist candidate",
                metadata={"vote": 0.0},
            )
        )
    return items


def evidence_items_from_investment_os_context(
    *,
    has_star: bool,
    session_open: bool,
    allow_entries: bool,
    can_enter: bool,
    synthesis_verdict: str | None,
    plan_blocked: bool,
    net_score: float = 0.0,
) -> list:
    b = EvidenceBuilder()
    items = [
        b.fact(
            category=EvidenceCategory.EXECUTION,
            label="Starred plan",
            value="yes" if has_star else "no",
            explanation="Pinned trade plan selected",
            source=EvidenceSource.INTERNAL_MODEL,
            metadata={"vote": 0.3 if has_star else -0.5},
        ),
        b.fact(
            category=EvidenceCategory.MARKET,
            label="Session open",
            value="yes" if session_open else "no",
            explanation="Market session status",
            source=EvidenceSource.INTERNAL_MODEL,
            metadata={"vote": 0.0 if session_open else -1.5},
        ),
        b.fact(
            category=EvidenceCategory.EXECUTION,
            label="Entries allowed",
            value="yes" if allow_entries else "no",
            explanation="Timing gate for new entries",
            source=EvidenceSource.INTERNAL_MODEL,
            metadata={"vote": 0.5 if allow_entries else -1.2},
        ),
        b.fact(
            category=EvidenceCategory.RISK,
            label="Risk plan",
            value="ok" if can_enter else "blocked",
            explanation="Position sizing / risk plan",
            source=EvidenceSource.INTERNAL_MODEL,
            metadata={"vote": 0.8 if can_enter else -1.0},
        ),
    ]
    if synthesis_verdict:
        items.append(
            b.estimate(
                category=EvidenceCategory.TECHNICAL,
                label="Synthesis verdict",
                value=synthesis_verdict,
                explanation="Strategy synthesis input",
                metadata={"vote": _synthesis_to_vote(synthesis_verdict)},
            )
        )
    if plan_blocked:
        items.append(
            b.opinion(
                category=EvidenceCategory.RISK,
                label="Plan blocked",
                value="yes",
                explanation="Trade plan cannot enter",
                metadata={"vote": -1.2, "signal": "bearish"},
            )
        )
    if net_score:
        items.extend(evidence_items_from_score(net_score, label="OS net score", scale=1.0))
    return items


def _rec_to_signal(rec: str) -> str:
    r = rec.upper()
    if "BUY" in r or "ACCUMULATE" in r or "CE" in r or "PE" in r:
        if "NO" in r or "AVOID" in r:
            return "bearish"
        return "bullish"
    if "SELL" in r or "AVOID" in r or "REDUCE" in r or "TRIM" in r or "EXIT" in r:
        return "bearish"
    return "neutral"


def _rec_to_vote(rec: str) -> float:
    r = rec.upper()
    if "STRONG" in r and "BUY" in r:
        return 1.5
    if "BUY" in r or "ACCUMULATE" in r:
        return 1.0
    if "STRONG" in r and "SELL" in r:
        return -1.5
    if "SELL" in r or "AVOID" in r or "REDUCE" in r:
        return -1.0
    return 0.0


def _synthesis_to_vote(verdict: str) -> float:
    v = verdict.upper()
    if v in ("STRONG_BUY", "STRONG BUY"):
        return 1.5
    if v == "BUY":
        return 1.0
    if v in ("NO_TRADE", "NO TRADE"):
        return -1.2
    if v == "CAUTION":
        return -0.4
    return 0.0


def _build_packet(subject: str, subject_type: str, items: list, *, engine=None):
    from analyzer.evidence_engine import EvidenceEngine

    eng = engine or EvidenceEngine()
    merged = list(items) + _market_session_item()
    return eng.build_packet(subject=subject, subject_type=subject_type, items=merged)


def resolve_verdict(
    subject: str,
    subject_type: str,
    items: list,
    legacy_mapper: LegacyMapper,
    *,
    market: MarketContext | None = None,
    risk: RiskSettings | None = None,
    prefs=None,
    persist: bool = False,
    engine: DecisionEngine | None = None,
) -> tuple[DecisionArtifact | None, str]:
    """Build evidence packet, decide, return (artifact, legacy string)."""
    try:
        packet = _build_packet(subject, subject_type, items)
        if market is None:
            try:
                from analyzer.context_engine import build_context_snapshot
                from analyzer.context_engine.migration import market_context_from_snapshot

                market = market_context_from_snapshot(build_context_snapshot(use_cache=True))
            except Exception:
                try:
                    market = market_context_from_timing(
                        __import__(
                            "analyzer.intraday_beginner_tips",
                            fromlist=["session_timing_advice"],
                        ).session_timing_advice()
                    )
                except Exception:
                    market = MarketContext()
        decision = decide_from_packet(
            packet,
            market=market,
            capital=capital_constraints_from_prefs(prefs) if prefs else None,
            preferences=user_preferences_from_prefs(prefs) if prefs else None,
            risk=risk,
            subject_type=subject_type,
            engine=engine,
            persist=persist,
        )
        snapshot_id = ""
        try:
            from analyzer.context_engine import get_cached

            hit = get_cached("india", True)
            if hit is not None:
                snapshot_id = hit.snapshot_id
        except Exception:
            pass
        if snapshot_id:
            decision.metadata["context_snapshot_id"] = snapshot_id
        return decision, legacy_mapper(decision)
    except Exception as exc:
        logger.warning("verdict bridge resolve failed for %s: %s", subject, exc)
        return None, legacy_mapper_fallback(legacy_mapper)


def _wait_artifact() -> DecisionArtifact:
    return DecisionArtifact(
        decision_id="dec_fallback",
        timestamp="",
        verdict=DecisionVerdict.WAIT,
        reason="Decision Engine unavailable",
        evidence_packet_id="",
        confidence=0.0,
        uncertainty=UncertaintyVector(),
        capital_recommendation="",
        execution_recommendation="",
        trade_allowed=False,
        net_score=0.0,
    )


def legacy_mapper_fallback(mapper: LegacyMapper) -> str:
    """Safe WAIT/HOLD fallback when Decision Engine unavailable."""
    try:
        return mapper(_wait_artifact())
    except Exception:
        return "HOLD"


# --- Legacy mappers (DecisionArtifact → UI strings) ---


def legacy_equity_recommendation(decision: DecisionArtifact) -> str:
    if decision.verdict == DecisionVerdict.ACT:
        return "STRONG BUY" if decision.confidence >= 70 else "BUY"
    if decision.verdict == DecisionVerdict.REDUCE:
        return "SELL"
    if decision.verdict == DecisionVerdict.PASS:
        return "STRONG SELL" if decision.net_score < -0.5 else "SELL"
    if decision.verdict == DecisionVerdict.DEFENSIVE:
        return "HOLD"
    return "HOLD"  # WAIT


def legacy_chart_action(decision: DecisionArtifact) -> str:
    if decision.verdict == DecisionVerdict.ACT:
        return "STRONG BUY" if decision.confidence >= 70 else "BUY"
    if decision.verdict == DecisionVerdict.REDUCE:
        return "SELL"
    if decision.verdict == DecisionVerdict.PASS:
        return "STRONG SELL" if decision.net_score < -0.5 else "SELL"
    return "WAIT"


def legacy_chart_confidence(decision: DecisionArtifact) -> str:
    if decision.confidence >= 70:
        return "high"
    if decision.confidence >= 45:
        return "medium"
    return "low"


def legacy_short_horizon_action(decision: DecisionArtifact) -> str:
    if decision.verdict == DecisionVerdict.ACT:
        return "STRONG BUY" if decision.confidence >= 70 else "BUY"
    if decision.verdict == DecisionVerdict.WAIT and decision.net_score > 0.1:
        return "WATCH"
    if decision.verdict == DecisionVerdict.REDUCE:
        return "WEAK"
    if decision.verdict == DecisionVerdict.PASS:
        return "AVOID"
    return "NEUTRAL"


def legacy_long_horizon_action(decision: DecisionArtifact) -> str:
    if decision.verdict == DecisionVerdict.ACT:
        return "CORE BUY" if decision.confidence >= 70 else "ACCUMULATE"
    if decision.verdict == DecisionVerdict.WAIT:
        return "HOLD" if decision.net_score > 0 else "WATCH"
    if decision.verdict in (DecisionVerdict.PASS, DecisionVerdict.REDUCE):
        return "AVOID"
    return "WATCH"


def legacy_options_action(decision: DecisionArtifact, *, directional_hint: str = "neutral") -> str:
    hint = directional_hint.lower()
    if decision.verdict == DecisionVerdict.PASS:
        return "NO TRADE"
    if decision.verdict in (DecisionVerdict.WAIT, DecisionVerdict.DEFENSIVE):
        return "NO TRADE"
    if decision.verdict == DecisionVerdict.ACT:
        strong = decision.confidence >= 70
        if hint == "bullish" or decision.net_score > 0.3:
            return "STRONG CE" if strong else "BUY CE"
        if hint == "bearish" or decision.net_score < -0.3:
            return "STRONG PE" if strong else "BUY PE"
        return "NO TRADE"
    if decision.verdict == DecisionVerdict.REDUCE:
        return "NO TRADE"
    return "NO TRADE"


def legacy_intraday_setup(decision: DecisionArtifact) -> str:
    if decision.verdict == DecisionVerdict.ACT:
        return "BUY" if decision.net_score >= 0 else "SELL"
    if decision.verdict == DecisionVerdict.REDUCE:
        return "SELL" if decision.net_score < 0 else "WAIT"
    if decision.verdict == DecisionVerdict.PASS:
        return "SELL" if decision.net_score < -0.2 else "WAIT"
    return "WAIT"


def legacy_mtf_consensus(decision: DecisionArtifact) -> str:
    return legacy_chart_action(decision)


def legacy_daily_holding_action(decision: DecisionArtifact, *, pnl: float | None = None, overweight: bool = False) -> str:
    if decision.verdict == DecisionVerdict.PASS:
        if pnl is not None and pnl < -10:
            return "EXIT — cut loss"
        if pnl is not None and pnl > 15:
            return "TRIM — book profits"
        return "REDUCE position"
    if decision.verdict == DecisionVerdict.REDUCE:
        if overweight:
            return "TRIM — overweight"
        return "REDUCE position"
    if decision.verdict == DecisionVerdict.ACT:
        if pnl is not None and pnl < -8:
            return "ADD in tranches"
        return "HOLD / add small"
    if decision.verdict == DecisionVerdict.DEFENSIVE:
        return "DO NOT add today"
    if pnl is not None and pnl > 25:
        return "PARTIAL book profit"
    return "HOLD — no urgency"


def legacy_watchlist_action(decision: DecisionArtifact) -> str:
    if decision.verdict == DecisionVerdict.PASS:
        return "AVOID"
    if decision.verdict == DecisionVerdict.ACT:
        return "BUY WATCH — setup ready"
    if decision.verdict == DecisionVerdict.WAIT and decision.net_score > 0.2:
        return "INTRADAY WATCH"
    if decision.verdict == DecisionVerdict.WAIT:
        return "ACCUMULATE WATCH" if decision.net_score > 0.1 else "MONITOR — neutral"
    if decision.verdict == DecisionVerdict.DEFENSIVE:
        return "WAIT — weak session"
    return "MONITOR — neutral"


def legacy_investment_os_verdict(
    decision: DecisionArtifact,
    *,
    has_star: bool,
    session_open: bool,
) -> str:
    if not has_star:
        return "PREP"
    if not session_open:
        return "CLOSED"
    if decision.verdict == DecisionVerdict.ACT and decision.trade_allowed:
        return "TRADE OK"
    if decision.verdict == DecisionVerdict.PASS:
        return "NO TRADE"
    return "WAIT"


# --- Attach hooks (mutate result objects in place) ---


def attach_decision_to_analysis(result, *, prefs=None) -> None:
    items = evidence_items_from_score(
        result.composite_score,
        label="Technical composite",
        explanation="Technical signal composite score",
    )
    items.extend(evidence_items_from_signal_details(result.signals))
    decision, rec = resolve_verdict(
        result.ticker,
        "equity",
        items,
        legacy_equity_recommendation,
        prefs=prefs,
    )
    result.decision_artifact = decision
    result.recommendation = rec


def attach_decision_to_fundamental(result, *, prefs=None) -> None:
    items = evidence_items_from_score(
        result.composite_score,
        label="Fundamental composite",
        category=EvidenceCategory.FUNDAMENTAL,
        explanation="Fundamental signal composite score",
    )
    for m in getattr(result, "metrics", [])[:10]:
        items.append(
            EvidenceBuilder().estimate(
                category=EvidenceCategory.FUNDAMENTAL,
                label=getattr(m, "name", "metric"),
                value=getattr(m, "value", ""),
                explanation=getattr(m, "detail", ""),
                source=EvidenceSource.YAHOO_FINANCE,
                metadata={"vote": float(getattr(m, "score", 0) or 0), "signal": getattr(m, "signal", "neutral")},
            )
        )
    decision, rec = resolve_verdict(
        result.ticker,
        "equity",
        items,
        legacy_equity_recommendation,
        prefs=prefs,
    )
    result.decision_artifact = decision
    result.recommendation = rec


def attach_decision_to_combined(result, *, prefs=None) -> None:
    items = evidence_items_from_score(
        result.combined_score,
        label="Combined score",
        explanation="Technical + fundamental combined score",
    )
    items.extend(
        evidence_items_from_score(
            result.technical.composite_score,
            label="Technical score",
            scale=50.0,
        )
    )
    items.extend(
        evidence_items_from_score(
            result.fundamental.composite_score,
            label="Fundamental score",
            category=EvidenceCategory.FUNDAMENTAL,
            scale=50.0,
        )
    )
    decision, rec = resolve_verdict(
        result.ticker,
        "equity",
        items,
        legacy_equity_recommendation,
        prefs=prefs,
    )
    result.decision_artifact = decision
    result.combined_recommendation = rec


def attach_decision_to_live_chart(verdict, *, prefs=None) -> None:
    items = evidence_items_from_score(
        verdict.directional_score,
        label="Directional score",
        scale=1.5,
        explanation="Live chart directional score",
    )
    items.extend(evidence_items_from_reasons(verdict.reasons))
    if verdict.intraday:
        items.extend(evidence_items_from_intraday_signals(verdict.intraday.signals))
    decision, action = resolve_verdict(
        verdict.ticker,
        "intraday",
        items,
        legacy_chart_action,
        prefs=prefs,
    )
    verdict.decision_artifact = decision
    verdict.action = action
    verdict.confidence = legacy_chart_confidence(decision)


def attach_decision_to_horizon(analysis, ticker: str, *, prefs=None, mapper: LegacyMapper | None = None) -> None:
    mapper = mapper or (legacy_short_horizon_action if analysis.horizon == "short" else legacy_long_horizon_action)
    items = evidence_items_from_score(
        analysis.score,
        label=f"{analysis.horizon} horizon score",
        explanation=analysis.summary[:120] if analysis.summary else "",
    )
    items.extend(evidence_items_from_reasons(getattr(analysis, "chart_signals", []) or []))
    decision, action = resolve_verdict(
        ticker,
        "equity",
        items,
        mapper,
        prefs=prefs,
    )
    analysis.decision_artifact = decision
    analysis.action = action
    if analysis.summary and "**" in analysis.summary:
        parts = analysis.summary.split("**", 2)
        if len(parts) >= 3:
            analysis.summary = f"**{action}**{parts[2]}"


def attach_decision_to_options_verdict(options, ticker: str, *, score: float, directional_hint: str = "neutral", prefs=None) -> None:
    items = evidence_items_from_score(score, label="Options directional score", scale=1.5)
    items.extend(evidence_items_from_reasons(getattr(options, "reasons", []) or []))

    def _mapper(d: DecisionArtifact) -> str:
        return legacy_options_action(d, directional_hint=directional_hint)

    decision, action = resolve_verdict(ticker, "options", items, _mapper, prefs=prefs)
    options.decision_artifact = decision
    options.action = action
    conf = legacy_chart_confidence(decision)
    options.confidence = conf


def attach_decision_to_intraday(analysis, *, prefs=None) -> None:
    items = evidence_items_from_intraday_signals(analysis.signals)
    net = sum(
        0.6 if s.bias == "bullish" else (-0.6 if s.bias == "bearish" else 0.0)
        for s in analysis.signals
    )
    items.extend(evidence_items_from_score(net, label="Intraday net", scale=2.0))
    decision, setup = resolve_verdict(
        analysis.ticker,
        "intraday",
        items,
        legacy_intraday_setup,
        prefs=prefs,
    )
    analysis.decision_artifact = decision
    analysis.trade_setup = setup
    if setup == "BUY":
        analysis.session_bias = "BULLISH"
    elif setup == "SELL":
        analysis.session_bias = "BEARISH"
    else:
        analysis.session_bias = "NEUTRAL"


def attach_decision_to_mtf_report(report, *, prefs=None) -> None:
    items = evidence_items_from_score(report.net_score, label="MTF net score", scale=1.5)
    for frame in report.frames:
        if frame.error:
            continue
        items.append(
            EvidenceBuilder().estimate(
                category=EvidenceCategory.TECHNICAL,
                label=f"MTF {frame.interval}",
                value=frame.action,
                explanation=f"{frame.interval} frame action",
                metadata={"vote": _rec_to_vote(frame.action), "signal": _rec_to_signal(frame.action)},
            )
        )
    decision, consensus = resolve_verdict(
        report.symbol,
        "intraday",
        items,
        legacy_mtf_consensus,
        prefs=prefs,
    )
    report.decision_artifact = decision
    report.consensus_action = consensus


def attach_decision_to_holding_advice(
    advice,
    *,
    combined_rec: str,
    tech: float,
    fund: float,
    pnl: float | None = None,
    weight: float | None = None,
    intraday_action: str | None = None,
    session_bias: str | None = None,
    is_watchlist: bool = False,
    prefs=None,
) -> None:
    items = evidence_items_from_daily_context(
        combined_rec=combined_rec,
        tech=tech,
        fund=fund,
        pnl=pnl,
        weight=weight,
        intraday_action=intraday_action,
        session_bias=session_bias,
        is_watchlist=is_watchlist,
    )

    def _mapper(d: DecisionArtifact) -> str:
        if is_watchlist:
            return legacy_watchlist_action(d)
        return legacy_daily_holding_action(d, pnl=pnl, overweight=weight is not None and weight > 12)

    subject = getattr(advice, "yahoo_symbol", None) or getattr(advice, "kite_symbol", "holding")
    decision, action = resolve_verdict(subject, "equity", items, _mapper, prefs=prefs)
    advice.decision_artifact = decision
    advice.today_action = action


def attach_decision_to_investment_os(
    os_result,
    *,
    has_star: bool,
    session_open: bool,
    allow_entries: bool,
    can_enter: bool,
    synthesis_verdict: str | None,
    plan_blocked: bool,
    prefs=None,
) -> None:
    items = evidence_items_from_investment_os_context(
        has_star=has_star,
        session_open=session_open,
        allow_entries=allow_entries,
        can_enter=can_enter,
        synthesis_verdict=synthesis_verdict,
        plan_blocked=plan_blocked,
    )

    def _mapper(d: DecisionArtifact) -> str:
        return legacy_investment_os_verdict(d, has_star=has_star, session_open=session_open)

    subject = getattr(os_result, "starred_symbol", None) or "INVESTMENT_OS"
    market = None
    snapshot_id = getattr(os_result, "context_snapshot_id", "") or ""
    try:
        from analyzer.context_engine import build_context_snapshot
        from analyzer.context_engine.migration import evidence_items_from_snapshot, market_context_from_snapshot

        snap = build_context_snapshot(use_cache=True)
        market = market_context_from_snapshot(snap)
        items = evidence_items_from_snapshot(snap) + items
        snapshot_id = snap.snapshot_id
    except Exception:
        pass

    decision, verdict = resolve_verdict(subject, "equity", items, _mapper, prefs=prefs, market=market)
    os_result.decision_artifact = decision
    os_result.verdict = verdict
    if decision and snapshot_id:
        decision.metadata["context_snapshot_id"] = snapshot_id
    if decision:
        os_result.can_trade = verdict == "TRADE OK"


# Re-export canonical mappers for compatibility
__all__ = [
    "attach_decision_to_analysis",
    "attach_decision_to_combined",
    "attach_decision_to_fundamental",
    "attach_decision_to_holding_advice",
    "attach_decision_to_horizon",
    "attach_decision_to_intraday",
    "attach_decision_to_investment_os",
    "attach_decision_to_live_chart",
    "attach_decision_to_mtf_report",
    "attach_decision_to_options_verdict",
    "evidence_items_from_daily_context",
    "evidence_items_from_intraday_signals",
    "evidence_items_from_reasons",
    "evidence_items_from_score",
    "evidence_items_from_signal_details",
    "legacy_chart_action",
    "legacy_daily_holding_action",
    "legacy_equity_recommendation",
    "legacy_investment_os_verdict",
    "legacy_intraday_setup",
    "legacy_long_horizon_action",
    "legacy_mtf_consensus",
    "legacy_options_action",
    "legacy_short_horizon_action",
    "legacy_watchlist_action",
    "resolve_verdict",
]
