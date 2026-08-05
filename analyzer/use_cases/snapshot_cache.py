"""ContextSnapshot serialization for caches — pickle-safe plain dicts."""

from __future__ import annotations

from typing import Any

from analyzer.context_engine.models import ContextSnapshot


def snapshot_to_cache(snapshot: ContextSnapshot) -> dict[str, Any]:
    return snapshot.as_dict()


def snapshot_from_cache(data: dict[str, Any]) -> ContextSnapshot:
    return ContextSnapshot(
        timestamp=str(data["timestamp"]),
        market_regime=str(data["market_regime"]),
        market_phase=str(data["market_phase"]),
        market_breadth=str(data["market_breadth"]),
        volatility_state=str(data["volatility_state"]),
        liquidity_state=str(data["liquidity_state"]),
        market_session=dict(data.get("market_session") or {}),
        sector_strength=dict(data.get("sector_strength") or {}),
        industry_strength=dict(data.get("industry_strength") or {}),
        macro_state=dict(data.get("macro_state") or {}),
        global_market_state=dict(data.get("global_market_state") or {}),
        risk_mode=str(data["risk_mode"]),
        trading_restrictions=tuple(data.get("trading_restrictions") or ()),
        confidence=float(data.get("confidence") or 0.0),
        schema_version=str(data.get("schema_version") or "1.0"),
        snapshot_id=str(data.get("snapshot_id") or ""),
        context_hash=str(data.get("context_hash") or ""),
        metadata=dict(data.get("metadata") or {}),
    )
