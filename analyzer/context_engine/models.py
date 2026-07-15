"""Context Engine — immutable market context snapshot models."""

from __future__ import annotations

import json
import hashlib
import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

SCHEMA_VERSION = "1.0"

VALID_REGIMES = frozenset({
    "Trending Bullish",
    "Trending Bearish",
    "Range-bound",
    "Neutral trend",
    "Unknown",
})
VALID_PHASES = frozenset({
    "pre_market",
    "opening",
    "mid_session",
    "wind_down",
    "closed",
    "weekend",
    "holiday",
    "pre_open",
    "core",
    "after_hours",
    "open",
})
VALID_RISK_MODES = frozenset({"RISK-ON", "NEUTRAL", "RISK-OFF", "CLOSED"})
VALID_VOLATILITY = frozenset({"low", "normal", "elevated", "high_fear", "unknown"})
VALID_BREADTH = frozenset({"broad", "mixed", "narrow", "unknown"})
VALID_LIQUIDITY = frozenset({"normal", "thin", "unknown"})


def _freeze_mapping(data: dict[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(data or {}))


def _canonical_payload(
    *,
    timestamp: str,
    market_regime: str,
    market_phase: str,
    market_breadth: str,
    volatility_state: str,
    liquidity_state: str,
    market_session: Mapping[str, Any],
    sector_strength: Mapping[str, Any],
    industry_strength: Mapping[str, Any],
    macro_state: Mapping[str, Any],
    global_market_state: Mapping[str, Any],
    risk_mode: str,
    trading_restrictions: tuple[str, ...],
    confidence: float,
    schema_version: str,
    metadata: Mapping[str, Any],
) -> str:
    body = {
        "timestamp": timestamp,
        "market_regime": market_regime,
        "market_phase": market_phase,
        "market_breadth": market_breadth,
        "volatility_state": volatility_state,
        "liquidity_state": liquidity_state,
        "market_session": dict(market_session),
        "sector_strength": dict(sector_strength),
        "industry_strength": dict(industry_strength),
        "macro_state": dict(macro_state),
        "global_market_state": dict(global_market_state),
        "risk_mode": risk_mode,
        "trading_restrictions": list(trading_restrictions),
        "confidence": confidence,
        "schema_version": schema_version,
        "metadata": dict(metadata),
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class ContextSnapshot:
    """Single canonical market context object — immutable."""

    timestamp: str
    market_regime: str
    market_phase: str
    market_breadth: str
    volatility_state: str
    liquidity_state: str
    market_session: Mapping[str, Any]
    sector_strength: Mapping[str, Any]
    industry_strength: Mapping[str, Any]
    macro_state: Mapping[str, Any]
    global_market_state: Mapping[str, Any]
    risk_mode: str
    trading_restrictions: tuple[str, ...]
    confidence: float
    schema_version: str = SCHEMA_VERSION
    snapshot_id: str = field(default="")
    context_hash: str = field(default="")
    metadata: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))

    @staticmethod
    def create(
        *,
        timestamp: str,
        market_regime: str,
        market_phase: str,
        market_breadth: str,
        volatility_state: str,
        liquidity_state: str,
        market_session: dict[str, Any],
        sector_strength: dict[str, Any],
        industry_strength: dict[str, Any],
        macro_state: dict[str, Any],
        global_market_state: dict[str, Any],
        risk_mode: str,
        trading_restrictions: list[str] | tuple[str, ...],
        confidence: float,
        schema_version: str = SCHEMA_VERSION,
        metadata: dict[str, Any] | None = None,
    ) -> ContextSnapshot:
        """Build snapshot with computed snapshot_id and context_hash."""
        restrictions = tuple(trading_restrictions)
        meta = _freeze_mapping(metadata)
        session_f = _freeze_mapping(market_session)
        sector_f = _freeze_mapping(sector_strength)
        industry_f = _freeze_mapping(industry_strength)
        macro_f = _freeze_mapping(macro_state)
        global_f = _freeze_mapping(global_market_state)

        canonical = _canonical_payload(
            timestamp=timestamp,
            market_regime=market_regime,
            market_phase=market_phase,
            market_breadth=market_breadth,
            volatility_state=volatility_state,
            liquidity_state=liquidity_state,
            market_session=session_f,
            sector_strength=sector_f,
            industry_strength=industry_f,
            macro_state=macro_f,
            global_market_state=global_f,
            risk_mode=risk_mode,
            trading_restrictions=restrictions,
            confidence=confidence,
            schema_version=schema_version,
            metadata=meta,
        )
        context_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        snapshot_id = f"ctx_{context_hash[:16]}_{uuid.uuid4().hex[:8]}"

        return ContextSnapshot(
            timestamp=timestamp,
            market_regime=market_regime,
            market_phase=market_phase,
            market_breadth=market_breadth,
            volatility_state=volatility_state,
            liquidity_state=liquidity_state,
            market_session=session_f,
            sector_strength=sector_f,
            industry_strength=industry_f,
            macro_state=macro_f,
            global_market_state=global_f,
            risk_mode=risk_mode,
            trading_restrictions=restrictions,
            confidence=confidence,
            schema_version=schema_version,
            snapshot_id=snapshot_id,
            context_hash=context_hash,
            metadata=meta,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "context_hash": self.context_hash,
            "schema_version": self.schema_version,
            "timestamp": self.timestamp,
            "market_regime": self.market_regime,
            "market_phase": self.market_phase,
            "market_breadth": self.market_breadth,
            "volatility_state": self.volatility_state,
            "liquidity_state": self.liquidity_state,
            "market_session": dict(self.market_session),
            "sector_strength": dict(self.sector_strength),
            "industry_strength": dict(self.industry_strength),
            "macro_state": dict(self.macro_state),
            "global_market_state": dict(self.global_market_state),
            "risk_mode": self.risk_mode,
            "trading_restrictions": list(self.trading_restrictions),
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }
