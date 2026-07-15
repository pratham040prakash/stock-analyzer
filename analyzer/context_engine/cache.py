"""Unified Context Engine cache — single TTL policy, thread-safe."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, TypeVar

from analyzer.context_engine.models import ContextSnapshot

T = TypeVar("T")

LIVE_TTL_SEC = 60.0
GLOBAL_TTL_SEC = 86_400.0

_lock = threading.RLock()
_cache: dict[str, tuple[float, ContextSnapshot]] = {}


@dataclass(frozen=True)
class CacheStats:
    hits: int = 0
    misses: int = 0
    size: int = 0


_stats = CacheStats()


def _cache_key(market: str, include_global: bool) -> str:
    return f"{market}:global={int(include_global)}"


def get_cached(market: str, include_global: bool) -> ContextSnapshot | None:
    key = _cache_key(market, include_global)
    with _lock:
        row = _cache.get(key)
        if not row:
            return None
        ts, snap = row
        ttl = GLOBAL_TTL_SEC if not snap.market_session.get("is_open") else LIVE_TTL_SEC
        if time.time() - ts > ttl:
            _cache.pop(key, None)
            return None
        return snap


def put_cached(market: str, include_global: bool, snapshot: ContextSnapshot) -> None:
    key = _cache_key(market, include_global)
    with _lock:
        _cache[key] = (time.time(), snapshot)


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def cache_age_sec(market: str, include_global: bool) -> float | None:
    key = _cache_key(market, include_global)
    with _lock:
        row = _cache.get(key)
        if not row:
            return None
        return round(time.time() - row[0], 1)


def cached_build(
    market: str,
    include_global: bool,
    builder: Callable[[], ContextSnapshot],
    *,
    use_cache: bool = True,
) -> ContextSnapshot:
    if use_cache:
        hit = get_cached(market, include_global)
        if hit is not None:
            return hit
    snap = builder()
    if use_cache:
        put_cached(market, include_global, snap)
    return snap
