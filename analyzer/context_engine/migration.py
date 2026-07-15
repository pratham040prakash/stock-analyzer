"""Context → downstream engine adapters (no Decision/Evidence Engine modifications)."""

from __future__ import annotations

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import MarketContext


def market_context_from_snapshot(snapshot: ContextSnapshot) -> MarketContext:
    """Map ContextSnapshot → DecisionEngine.MarketContext."""
    session = snapshot.market_session
    global_state = snapshot.global_market_state
    allow_agg = snapshot.market_regime in ("Trending Bullish", "Neutral trend")
    if snapshot.risk_mode in ("RISK-OFF", "CLOSED"):
        allow_agg = False
    timing_headline = ""
    if snapshot.trading_restrictions:
        timing_headline = snapshot.trading_restrictions[0]
    return MarketContext(
        regime=snapshot.market_regime,
        market_bias=str(global_state.get("bias", "")),
        session_open=bool(session.get("is_open")),
        allow_new_entries=bool(snapshot.metadata.get("allow_new_entries", False)),
        allow_aggressive=allow_agg,
        timing_headline=timing_headline,
    )


def evidence_items_from_snapshot(snapshot: ContextSnapshot) -> list:
    """Evidence-only context items for packet builders."""
    from analyzer.evidence_engine.builder import EvidenceBuilder
    from analyzer.evidence_engine.models import EvidenceCategory, EvidenceConfidence, EvidenceSource

    b = EvidenceBuilder()
    items = [
        b.fact(
            category=EvidenceCategory.MARKET,
            label="Context risk mode",
            value=snapshot.risk_mode,
            explanation=f"Market context {snapshot.risk_mode} ({snapshot.market_phase})",
            source=EvidenceSource.INTERNAL_MODEL,
            confidence=EvidenceConfidence.HIGH,
            metadata={"signal": _risk_to_signal(snapshot.risk_mode), "vote": _risk_to_vote(snapshot.risk_mode)},
        ),
        b.fact(
            category=EvidenceCategory.MARKET,
            label="Market regime",
            value=snapshot.market_regime,
            explanation=f"ADX regime: {snapshot.market_regime}",
            source=EvidenceSource.INTERNAL_MODEL,
            metadata={"signal": _regime_to_signal(snapshot.market_regime)},
        ),
        b.estimate(
            category=EvidenceCategory.MARKET,
            label="Volatility state",
            value=snapshot.volatility_state,
            explanation=f"VIX context: {snapshot.volatility_state}",
            source=EvidenceSource.INTERNAL_MODEL,
            metadata={"vote": -0.5 if snapshot.volatility_state in ("elevated", "high_fear") else 0.2},
        ),
    ]
    spill = snapshot.global_market_state.get("spillover_score")
    if spill is not None:
        items.append(
            b.estimate(
                category=EvidenceCategory.MACRO,
                label="Global spillover",
                value=spill,
                explanation=str(snapshot.global_market_state.get("india_action", "")),
                source=EvidenceSource.MACRO_FEED,
                metadata={"vote": max(-1.5, min(1.5, float(spill) / 40.0))},
            )
        )
    for restriction in snapshot.trading_restrictions[:4]:
        items.append(
            b.opinion(
                category=EvidenceCategory.RISK,
                label="Trading restriction",
                value=restriction[:120],
                explanation=restriction,
                metadata={"signal": "bearish", "vote": -0.4},
            )
        )
    return items


def _risk_to_signal(risk_mode: str) -> str:
    if risk_mode == "RISK-ON":
        return "bullish"
    if risk_mode in ("RISK-OFF", "CLOSED"):
        return "bearish"
    return "neutral"


def _risk_to_vote(risk_mode: str) -> float:
    if risk_mode == "RISK-ON":
        return 0.8
    if risk_mode == "RISK-OFF":
        return -0.9
    if risk_mode == "CLOSED":
        return -1.2
    return 0.0


def _regime_to_signal(regime: str) -> str:
    if regime == "Trending Bullish":
        return "bullish"
    if regime in ("Trending Bearish", "Range-bound"):
        return "bearish"
    return "neutral"


def regime_from_snapshot(snapshot: ContextSnapshot):
    """Reconstruct MarketRegime view from snapshot (no re-fetch)."""
    from analyzer.market_regime import MarketRegime

    detail = dict(snapshot.metadata.get("regime_detail", {}) or {})
    if snapshot.market_regime == "Unknown" and not detail:
        return None
    return MarketRegime(
        symbol="^NSEI",
        adx=detail.get("adx"),
        plus_di=detail.get("plus_di"),
        minus_di=detail.get("minus_di"),
        regime=snapshot.market_regime,
        allow_aggressive_intraday=bool(detail.get("allow_aggressive_intraday", True)),
        allow_aggressive_swing=bool(detail.get("allow_aggressive_swing", True)),
        message=str(detail.get("message", "")),
        banner=str(detail.get("banner", "")),
    )


def macro_from_snapshot(snapshot: ContextSnapshot):
    """Reconstruct IndiaMacroSnapshot view from snapshot (no re-fetch)."""
    from analyzer.india_macro import FiiDiiFlow, IndiaMacroSnapshot, MacroQuote

    macro = dict(snapshot.macro_state)
    if macro.get("status") == "GAP":
        return None
    vix_price = macro.get("vix_price")
    india_vix = None
    if vix_price is not None:
        india_vix = MacroQuote(
            symbol="^INDIAVIX",
            name="India VIX",
            price=float(vix_price),
            change_1d_pct=None,
        )
    sectors = []
    for row in macro.get("sectors", [])[:12]:
        if isinstance(row, dict) and row.get("name"):
            sectors.append(
                MacroQuote(
                    symbol=str(row.get("symbol", "")),
                    name=str(row["name"]),
                    price=0.0,
                    change_1d_pct=row.get("change_1d_pct"),
                )
            )
    fii_summary = str(macro.get("fii_dii_summary", "") or "")
    fii = FiiDiiFlow(
        date="",
        fii_net_cr=None,
        dii_net_cr=None,
        fii_derivative_cr=None,
        summary=fii_summary,
    ) if fii_summary else None
    sector = dict(snapshot.sector_strength)
    return IndiaMacroSnapshot(
        fetched_at=str(macro.get("fetched_at", snapshot.timestamp)),
        india_vix=india_vix,
        gift_nifty_proxy=None,
        sectors=sectors,
        fii_dii=fii,
        vix_regime=str(macro.get("vix_regime", snapshot.volatility_state)),
        sector_leader=str(sector.get("leader", "")),
        sector_laggard=str(sector.get("laggard", "")),
        premarket_note=str(macro.get("premarket_note", "")),
        errors=list(macro.get("errors", []) or []),
    )


def global_impact_from_snapshot(snapshot: ContextSnapshot):
    """Reconstruct IndiaImpactReport summary from snapshot (no re-fetch)."""
    from analyzer.global_impact import IndiaImpactReport
    from analyzer.global_markets import GlobalMarketSnapshot

    state = dict(snapshot.global_market_state)
    if state.get("status") == "GAP":
        return None
    spill = state.get("spillover_score")
    return IndiaImpactReport(
        fetched_at=str(state.get("fetched_at", snapshot.timestamp)),
        global_snapshot=GlobalMarketSnapshot(fetched_at=snapshot.timestamp),
        spillover_score=float(spill) if spill is not None else 0.0,
        predicted_nifty_bias=str(state.get("bias", "NEUTRAL")),
        predicted_move_pct=float(state.get("predicted_move_pct") or 0.0),
        confidence=str(state.get("confidence", "")),
        india_action=str(state.get("india_action", "")),
        ce_pe_hint="",
        drivers=list(state.get("drivers", []) or []),
        risks=list(state.get("risks", []) or []),
        narrative="",
    )
