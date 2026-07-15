"""Migration layer — legacy verdict mapping and integration hooks."""

from __future__ import annotations

import logging

from analyzer.decision_engine.engine import DecisionEngine, default_decision_engine
from analyzer.decision_engine.models import (
    CapitalConstraints,
    DecisionArtifact,
    DecisionVerdict,
    MarketContext,
    PortfolioState,
    RiskSettings,
    UserPreferences,
)
from analyzer.evidence_engine.builder import EvidenceBuilder
from analyzer.evidence_engine.models import EvidenceCategory, EvidenceConfidence, EvidenceSource, EvidenceType

logger = logging.getLogger(__name__)


def legacy_synthesis_verdict(decision: DecisionArtifact) -> str:
    """Map canonical verdict → legacy strategy synthesis label for UI."""
    if decision.verdict == DecisionVerdict.ACT:
        return "STRONG_BUY" if decision.confidence >= 70 else "BUY"
    if decision.verdict == DecisionVerdict.WAIT:
        return "WAIT"
    if decision.verdict == DecisionVerdict.PASS:
        return "NO_TRADE"
    if decision.verdict == DecisionVerdict.REDUCE:
        return "CAUTION"
    return "CAUTION"  # DEFENSIVE


def legacy_advisor_action(decision: DecisionArtifact) -> str:
    """Map canonical verdict → legacy InvestmentAdvice.final_action."""
    if decision.verdict == DecisionVerdict.ACT:
        return "STRONG BUY" if decision.confidence >= 70 else "BUY"
    if decision.verdict == DecisionVerdict.WAIT:
        return "ACCUMULATE" if decision.net_score > 0 else "HOLD"
    if decision.verdict == DecisionVerdict.PASS:
        return "AVOID"
    if decision.verdict == DecisionVerdict.REDUCE:
        return "REDUCE"
    return "HOLD"  # DEFENSIVE


def legacy_alpha_recommendation(decision: DecisionArtifact) -> str:
    """Map canonical verdict → legacy Alpha AI recommendation label."""
    action = legacy_advisor_action(decision)
    mapping = {
        "STRONG BUY": "Strong Buy",
        "BUY": "Buy",
        "ACCUMULATE": "Accumulate",
        "HOLD": "Hold",
        "REDUCE": "Reduce",
        "SELL": "Sell",
        "AVOID": "Avoid",
    }
    return mapping.get(action, "Hold")


def legacy_mis_verdict(decision: DecisionArtifact) -> str:
    """Map canonical verdict → legacy MIS advisory label for UI."""
    if decision.verdict == DecisionVerdict.ACT:
        return "TRADE_OK"
    if decision.verdict == DecisionVerdict.WAIT:
        return "CAUTION"
    if decision.verdict == DecisionVerdict.PASS:
        return "NO_TRADE"
    if decision.verdict == DecisionVerdict.REDUCE:
        return "CAUTION"
    return "OBSERVE"  # DEFENSIVE


def legacy_mis_headline(decision: DecisionArtifact) -> tuple[str, str, str]:
    """Emoji, headline, summary from canonical decision."""
    mapping = {
        DecisionVerdict.ACT: ("🟢", "Trade OK — follow gate & stop", decision.reason),
        DecisionVerdict.WAIT: ("🟡", "Caution — 1 lot only if you must", decision.reason),
        DecisionVerdict.PASS: ("🔴", "No trade — sit out", decision.reason),
        DecisionVerdict.REDUCE: ("🟡", "Caution — reduce exposure", decision.reason),
        DecisionVerdict.DEFENSIVE: ("⚪", "Observe — defensive posture", decision.reason),
    }
    return mapping.get(decision.verdict, ("⚪", "Observe", decision.reason))


def legacy_buy_decision(decision: DecisionArtifact) -> tuple[str, str]:
    """Map to Alpha AI buy_decision YES/NO/WAIT."""
    if decision.verdict == DecisionVerdict.ACT and decision.trade_allowed:
        return "YES", f"**ACT** — {decision.reason}"
    if decision.verdict == DecisionVerdict.PASS:
        return "NO", f"**PASS** — {decision.reason}"
    if decision.verdict == DecisionVerdict.REDUCE:
        return "NO", f"**REDUCE** — {decision.reason}"
    if decision.verdict == DecisionVerdict.DEFENSIVE:
        return "WAIT", f"**DEFENSIVE** — {decision.reason}"
    return "WAIT", f"**WAIT** — {decision.reason}"


def capital_constraints_from_prefs(prefs) -> CapitalConstraints:
    daily_cap = None
    if prefs and getattr(prefs, "capital", None):
        daily_cap = round(prefs.capital * getattr(prefs, "max_risk_pct", 2.0) / 100 * 3)
    return CapitalConstraints(
        capital_inr=float(getattr(prefs, "capital", 50_000) or 50_000),
        max_risk_pct=float(getattr(prefs, "max_risk_pct", 2.0) or 2.0),
        max_trades=int(getattr(prefs, "max_trades", 3) or 3),
        allocation_pct=float(getattr(prefs, "allocation_pct", 100) or 100),
        daily_loss_cap_inr=daily_cap,
    )


def user_preferences_from_prefs(prefs) -> UserPreferences:
    return UserPreferences(
        beginner_mode=bool(getattr(prefs, "beginner_mode", False)),
        equity_only=bool(getattr(prefs, "equity_only", False)),
        profit_mode=str(getattr(prefs, "profit_mode", "aggressive") or "aggressive"),
    )


def market_context_from_timing(timing, *, regime=None) -> MarketContext:
    allow_agg = True
    regime_name = None
    if regime is not None:
        regime_name = getattr(regime, "regime", None)
        allow_agg = bool(getattr(regime, "allow_aggressive_intraday", True))
    return MarketContext(
        regime=regime_name,
        allow_new_entries=bool(getattr(timing, "allow_new_entries", True)),
        allow_aggressive=allow_agg,
        timing_headline=str(getattr(timing, "headline", "") or ""),
    )


def evidence_items_from_advisor_signals(
    *,
    heuristic_action: str,
    conviction: str,
    bullish: list[str],
    bearish: list[str],
    risks: list[str],
) -> list:
    """Evidence-only signals from advisor analysis — not verdicts."""
    b = EvidenceBuilder()
    items = [
        b.estimate(
            category=EvidenceCategory.TECHNICAL,
            label="Heuristic action signal",
            value=heuristic_action,
            explanation=f"Internal heuristic ({conviction} conviction) — input to Decision Engine",
            source=EvidenceSource.INTERNAL_MODEL,
            confidence=EvidenceConfidence.LOW,
            weight=0.5,
            metadata={"signal": _action_to_signal(heuristic_action)},
        ),
    ]
    for factor in bullish[:5]:
        items.append(
            b.opinion(
                category=EvidenceCategory.TECHNICAL,
                label="Bullish factor",
                value=factor[:120],
                explanation=factor,
                metadata={"signal": "bullish"},
            )
        )
    for factor in bearish[:5]:
        items.append(
            b.opinion(
                category=EvidenceCategory.RISK,
                label="Bearish factor",
                value=factor[:120],
                explanation=factor,
                metadata={"signal": "bearish"},
            )
        )
    for risk in risks[:5]:
        items.append(
            b.opinion(
                category=EvidenceCategory.RISK,
                label="Risk",
                value=risk[:120],
                explanation=risk,
                metadata={"signal": "bearish"},
            )
        )
    return items


def _action_to_signal(action: str) -> str:
    a = action.upper()
    if "BUY" in a or "ACCUMULATE" in a:
        return "bullish"
    if "SELL" in a or "REDUCE" in a or "AVOID" in a:
        return "bearish"
    return "neutral"


def risk_settings_from_mis(
    *,
    loss_streak_days: int = 0,
    gate_allowed: bool = True,
    prefs=None,
) -> RiskSettings:
    max_risk = float(getattr(prefs, "max_risk_pct", 2.0) or 2.0) if prefs else 2.0
    return RiskSettings(
        max_risk_pct=max_risk,
        loss_streak_days=loss_streak_days,
        gate_allowed=gate_allowed,
        require_gate_green=True,
    )


def evidence_items_from_mis_signals(
    *,
    flags: list[str],
    positives: list[str],
    score: int,
    gate_allowed: bool,
    regime: str,
    loss_streak_days: int,
    synthesis_confidence: int = 0,
    pick_label: str = "",
    mtf_alignment: int = 0,
) -> list:
    """Evidence-only MIS signals — not verdicts."""
    b = EvidenceBuilder()
    items = [
        b.estimate(
            category=EvidenceCategory.EXECUTION,
            label="MIS composite score",
            value=score,
            explanation=f"Internal score {score}/100 — input to Decision Engine",
            source=EvidenceSource.INTERNAL_MODEL,
            confidence=EvidenceConfidence.MEDIUM,
            weight=0.6,
            metadata={"score": score},
        ),
        b.fact(
            category=EvidenceCategory.EXECUTION,
            label="Entry gate",
            value="green" if gate_allowed else "red",
            explanation="Option entry gate status",
            source=EvidenceSource.INTERNAL_MODEL,
            metadata={"vote": 0.8 if gate_allowed else -1.2},
        ),
        b.fact(
            category=EvidenceCategory.MARKET,
            label="Regime",
            value=regime or "unknown",
            explanation=f"Market regime: {regime or 'unknown'}",
            source=EvidenceSource.INTERNAL_MODEL,
            metadata={"signal": "bearish" if regime == "Range-bound" else "neutral"},
        ),
        b.estimate(
            category=EvidenceCategory.OPTIONS,
            label="MIS option pick",
            value=pick_label or "index",
            explanation="Selected MIS option context",
            source=EvidenceSource.INTERNAL_MODEL,
            confidence=EvidenceConfidence.MEDIUM,
            metadata={"vote": 0.6 if gate_allowed and score >= 60 else -0.2},
        ),
    ]
    if mtf_alignment:
        items.append(
            b.estimate(
                category=EvidenceCategory.TECHNICAL,
                label="MTF alignment",
                value=mtf_alignment,
                explanation=f"Multi-timeframe alignment {mtf_alignment}%",
                source=EvidenceSource.INTERNAL_MODEL,
                metadata={"score": mtf_alignment, "vote": 0.5 if mtf_alignment >= 60 else -0.4},
            )
        )
    if loss_streak_days >= 2:
        items.append(
            b.opinion(
                category=EvidenceCategory.RISK,
                label="Loss streak",
                value=f"{loss_streak_days} days",
                explanation="Consecutive loss days — risk pause signal",
                metadata={"vote": -1.5},
            )
        )
    if synthesis_confidence:
        items.append(
            b.estimate(
                category=EvidenceCategory.TECHNICAL,
                label="Synthesis confidence",
                value=synthesis_confidence,
                explanation="Strategy synthesis confidence input",
                metadata={"score": synthesis_confidence},
            )
        )
    for flag in flags[:6]:
        items.append(
            b.opinion(
                category=EvidenceCategory.RISK,
                label="Risk flag",
                value=flag[:120],
                explanation=flag,
                metadata={"signal": "bearish", "vote": -0.6},
            )
        )
    for pos in positives[:4]:
        items.append(
            b.opinion(
                category=EvidenceCategory.TECHNICAL,
                label="Positive signal",
                value=pos[:120],
                explanation=pos,
                metadata={"signal": "bullish", "vote": 0.5},
            )
        )
    return items


def decide_from_packet(
    packet,
    *,
    market: MarketContext | None = None,
    capital: CapitalConstraints | None = None,
    portfolio: PortfolioState | None = None,
    preferences: UserPreferences | None = None,
    risk: RiskSettings | None = None,
    subject_type: str | None = None,
    engine: DecisionEngine | None = None,
    persist: bool = True,
) -> DecisionArtifact:
    eng = engine or default_decision_engine(persist=persist)
    return eng.decide(
        packet,
        market=market,
        capital=capital,
        portfolio=portfolio,
        preferences=preferences,
        risk=risk,
        subject_type=subject_type,
        persist=persist,
    )


def attach_decision_to_synthesis(synthesis, *, prefs=None) -> None:
    """Apply Decision Engine verdict to StrategySynthesis (legacy fields mapped)."""
    packet = getattr(synthesis, "evidence_packet", None)
    if packet is None:
        synthesis.decision_artifact = None
        return
    market = MarketContext()
    snapshot_id = ""
    try:
        from analyzer.context_engine import build_context_snapshot
        from analyzer.context_engine.migration import market_context_from_snapshot

        snap = build_context_snapshot(use_cache=True)
        market = market_context_from_snapshot(snap)
        snapshot_id = snap.snapshot_id
    except Exception:
        try:
            from analyzer.intraday_beginner_tips import session_timing_advice

            market = market_context_from_timing(session_timing_advice())
        except Exception:
            pass
    try:
        capital = capital_constraints_from_prefs(prefs)
        preferences = user_preferences_from_prefs(prefs)
        decision = decide_from_packet(
            packet,
            market=market,
            capital=capital,
            preferences=preferences,
            subject_type=synthesis.asset_class,
        )
        if snapshot_id:
            decision.metadata["context_snapshot_id"] = snapshot_id
        synthesis.decision_artifact = decision
        synthesis.verdict = legacy_synthesis_verdict(decision)
        synthesis.headline = decision.reason
        synthesis.confidence_pct = int(decision.confidence)
        synthesis.net_score = decision.net_score
        synthesis.trade_allowed = decision.trade_allowed
        if decision.alternative_actions:
            synthesis.negatives = (synthesis.negatives or [])[:3] + decision.alternative_actions[:3]
    except Exception as exc:
        logger.warning("decision synthesis attach failed: %s", exc)
        synthesis.decision_artifact = None
        synthesis.verdict = "WAIT"
        synthesis.trade_allowed = False


def attach_decision_to_advice(advice, *, prefs=None, market_pulse=None) -> None:
    """Apply Decision Engine verdict to InvestmentAdvice."""
    packet = getattr(advice, "evidence_packet", None)
    if packet is None:
        advice.decision_artifact = None
        return
    try:
        market = MarketContext()
        if market_pulse:
            nifty = next((p for p in market_pulse if "Nifty" in getattr(p, "name", "")), None)
            if nifty:
                market.market_bias = getattr(nifty, "recommendation", "")
                market.allow_aggressive = getattr(nifty, "score", 0) > -10
        capital = capital_constraints_from_prefs(prefs)
        preferences = user_preferences_from_prefs(prefs)
        decision = decide_from_packet(
            packet,
            market=market,
            capital=capital,
            preferences=preferences,
            subject_type="equity",
        )
        advice.decision_artifact = decision
        advice.final_action = legacy_advisor_action(decision)
    except Exception as exc:
        logger.warning("decision advisor attach failed: %s", exc)
        advice.decision_artifact = None
        advice.final_action = "HOLD"


def attach_decision_to_alpha_report(report, *, prefs=None) -> None:
    """Apply Decision Engine verdict to AlphaAIReport legacy recommendation fields."""
    packet = getattr(report, "evidence_packet", None)
    if packet is None:
        report.decision_artifact = None
        return
    try:
        capital = capital_constraints_from_prefs(prefs)
        preferences = user_preferences_from_prefs(prefs)
        decision = decide_from_packet(
            packet,
            capital=capital,
            preferences=preferences,
            subject_type="research",
        )
        report.decision_artifact = decision
        report.recommendation = legacy_alpha_recommendation(decision)
        report.verdict = report.recommendation
        buy, buy_why = legacy_buy_decision(decision)
        report.buy_decision = buy
        report.buy_decision_why = buy_why
    except Exception as exc:
        logger.warning("decision alpha attach failed: %s", exc)
        report.decision_artifact = None
        report.recommendation = "Hold"
        report.verdict = "Hold"
        report.buy_decision = "WAIT"
        report.buy_decision_why = "**WAIT** — Decision Engine unavailable"


def attach_decision_to_mis_advisory(
    advisory,
    *,
    prefs=None,
    session_open: bool = True,
    pick_label: str = "",
    context_snapshot=None,
) -> None:
    """Build evidence from MIS signals and apply Decision Engine verdict."""
    from analyzer.evidence_engine import EvidenceEngine

    subject = pick_label or "MIS_OPTIONS"
    items = evidence_items_from_mis_signals(
        flags=getattr(advisory, "flags", []) or [],
        positives=getattr(advisory, "positives", []) or [],
        score=int(getattr(advisory, "score", 0) or 0),
        gate_allowed=bool(getattr(advisory, "gate_allowed", False)),
        regime=str(getattr(advisory, "regime", "") or ""),
        loss_streak_days=int(getattr(advisory, "loss_streak_days", 0) or 0),
        synthesis_confidence=int(getattr(advisory, "synthesis_confidence", 0) or 0),
        pick_label=pick_label,
        mtf_alignment=int(getattr(advisory, "mtf_alignment", 0) or 0),
    )
    snapshot_id = ""
    if context_snapshot is not None:
        try:
            from analyzer.context_engine.migration import evidence_items_from_snapshot

            items = evidence_items_from_snapshot(context_snapshot) + items
            snapshot_id = context_snapshot.snapshot_id
        except Exception:
            pass
    packet = EvidenceEngine().build_packet(
        subject=subject,
        subject_type="options",
        items=items,
        metadata={"origin": "mis_trade_advisory", "context_snapshot_id": snapshot_id or None},
    )
    advisory.evidence_packet = packet

    market = MarketContext(
        regime=str(getattr(advisory, "regime", "") or "") or None,
        session_open=session_open,
        allow_new_entries=session_open,
        allow_aggressive=session_open and str(getattr(advisory, "regime", "")) != "Range-bound",
    )
    if context_snapshot is not None:
        try:
            from analyzer.context_engine.migration import market_context_from_snapshot

            market = market_context_from_snapshot(context_snapshot)
        except Exception:
            pass
    elif not session_open:
        market.allow_new_entries = False
        market.timing_headline = "Market closed"

    try:
        decision = decide_from_packet(
            packet,
            market=market,
            capital=capital_constraints_from_prefs(prefs),
            preferences=user_preferences_from_prefs(prefs),
            risk=risk_settings_from_mis(
                loss_streak_days=int(getattr(advisory, "loss_streak_days", 0) or 0),
                gate_allowed=bool(getattr(advisory, "gate_allowed", False)),
                prefs=prefs,
            ),
            subject_type="options",
        )
        if snapshot_id:
            decision.metadata["context_snapshot_id"] = snapshot_id
        advisory.decision_artifact = decision
        advisory.verdict = legacy_mis_verdict(decision)
        emoji, headline, summary = legacy_mis_headline(decision)
        advisory.emoji = emoji
        advisory.headline = headline
        advisory.summary = summary
        advisory.confidence_pct = int(decision.confidence)
    except Exception as exc:
        logger.warning("decision mis attach failed: %s", exc)
        advisory.decision_artifact = None
        advisory.verdict = "OBSERVE"
        advisory.emoji = "⚪"
        advisory.headline = "Observe — decision unavailable"
        advisory.summary = "Decision Engine could not evaluate evidence; default to observe."
