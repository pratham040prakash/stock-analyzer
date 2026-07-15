"""Context Engine — canonical market environment snapshot (composition only)."""

from analyzer.context_engine.cache import (
    LIVE_TTL_SEC,
    GLOBAL_TTL_SEC,
    cache_age_sec,
    cached_build,
    clear_cache,
    get_cached,
    put_cached,
)
from analyzer.context_engine.composer import compose_context_snapshot
from analyzer.context_engine.migration import (
    evidence_items_from_snapshot,
    global_impact_from_snapshot,
    macro_from_snapshot,
    market_context_from_snapshot,
    regime_from_snapshot,
)
from analyzer.context_engine.models import (
    SCHEMA_VERSION,
    VALID_RISK_MODES,
    ContextSnapshot,
)
from analyzer.context_engine.normalizer import (
    normalize_regime,
    normalize_risk_mode,
    normalize_volatility,
)

__all__ = [
    "GLOBAL_TTL_SEC",
    "LIVE_TTL_SEC",
    "SCHEMA_VERSION",
    "VALID_RISK_MODES",
    "ContextSnapshot",
    "build_context_snapshot",
    "cache_age_sec",
    "clear_cache",
    "compose_context_snapshot",
    "evidence_items_from_snapshot",
    "get_cached",
    "global_impact_from_snapshot",
    "macro_from_snapshot",
    "market_context_from_snapshot",
    "put_cached",
    "regime_from_snapshot",
]


def build_context_snapshot(
    *,
    market: str = "india",
    now=None,
    include_global: bool = True,
    use_cache: bool = True,
    period: str = "6mo",
) -> ContextSnapshot:
    """Single entry point — parallel compose, normalize, cache."""
    return cached_build(
        market,
        include_global,
        lambda: compose_context_snapshot(
            market=market,
            now=now,
            include_global=include_global,
            period=period,
        ),
        use_cache=use_cache,
    )
