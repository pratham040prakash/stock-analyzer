"""User watchlist — mirror Kite marketwatch via paste (no Kite watchlist API)."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.zerodha import kite_to_yahoo, parse_kite_symbol_list, yahoo_to_kite

IST = ZoneInfo("Asia/Kolkata")
STORE_DIR = Path(__file__).resolve().parent.parent / "data" / "portfolio"
DEFAULT_PROFILE = "default"


def _safe_profile(profile: str | None) -> str:
    raw = (profile or DEFAULT_PROFILE).strip().lower()
    safe = re.sub(r"[^a-z0-9_-]", "", raw.replace(" ", "_"))[:32]
    return safe or DEFAULT_PROFILE


def watchlist_path(profile: str | None = None) -> Path:
    return STORE_DIR / f"{_safe_profile(profile)}_watchlist.json"


def _ensure_dir() -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)


def parse_watchlist_text(text: str) -> list[str]:
    """Normalize pasted Kite symbols to NSE:SYMBOL-EQ keys."""
    yahoo_syms = parse_kite_symbol_list(text)
    out: list[str] = []
    seen: set[str] = set()
    for y in yahoo_syms:
        kite = yahoo_to_kite(y).upper()
        if kite not in seen:
            seen.add(kite)
            out.append(kite)
    return out


def save_kite_watchlist(symbols: list[str], profile: str | None = None) -> None:
    _ensure_dir()
    clean = list(dict.fromkeys(s.strip().upper() for s in symbols if s.strip()))
    payload = {
        "version": 1,
        "profile": _safe_profile(profile),
        "updated_at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
        "symbols": clean,
    }
    watchlist_path(profile).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_kite_watchlist(profile: str | None = None) -> list[str]:
    path = watchlist_path(profile)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return [str(s).upper() for s in data.get("symbols", []) if str(s).strip()]
    except Exception:
        return []


def watchlist_yahoo_symbols(profile: str | None = None) -> list[str]:
    return [kite_to_yahoo(s) for s in load_kite_watchlist(profile)]
