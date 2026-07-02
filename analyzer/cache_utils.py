"""File + in-memory cache with TTL for expensive fetches."""

from __future__ import annotations

import json
import pickle
import time
from pathlib import Path
from typing import Any, Callable, TypeVar

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
CACHE_VERSION = "v2"

_MEM: dict[str, tuple[float, Any, int]] = {}
T = TypeVar("T")


def _cache_path(key: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{CACHE_VERSION}_{safe}.pkl"


def load_cached(key: str, ttl_seconds: int = 900) -> Any | None:
    data, fresh = load_cached_with_stale(key, ttl_seconds)
    return data if fresh else None


def save_cached(key: str, data: Any) -> None:
    path = _cache_path(key)
    try:
        with path.open("wb") as f:
            pickle.dump({"ts": time.time(), "data": data, "ver": CACHE_VERSION}, f)
    except (pickle.PicklingError, TypeError, AttributeError):
        # Streamlit hot-reload can change class identities — skip unsafe pickle cache
        return


def load_cached_with_stale(key: str, ttl_seconds: int = 900) -> tuple[Any | None, bool]:
    """Return (data, is_fresh). Serves expired cache for instant UI while revalidating."""
    path = _cache_path(key)
    if not path.exists():
        return None, False
    try:
        with path.open("rb") as f:
            payload = pickle.load(f)
        if payload.get("ver") != CACHE_VERSION:
            return None, False
        data = payload.get("data")
        fresh = time.time() - payload.get("ts", 0) <= ttl_seconds
        return data, fresh
    except Exception:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        return None, False


def cached_compute(key: str, ttl_seconds: int, factory: Callable[[], T]) -> T:
    """In-memory TTL cache (shared across tabs in one process)."""
    now = time.time()
    if key in _MEM:
        ts, data, ttl = _MEM[key]
        if now - ts < ttl:
            return data
    data = factory()
    _MEM[key] = (now, data, ttl_seconds)
    return data


def invalidate_memory_cache(prefix: str = "") -> None:
    if not prefix:
        _MEM.clear()
        return
    for k in list(_MEM):
        if k.startswith(prefix):
            del _MEM[k]


def save_json_cache(key: str, data: dict) -> None:
    path = CACHE_DIR / f"{CACHE_VERSION}_{key}.json"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"ts": time.time(), "data": data}, default=str), encoding="utf-8")
