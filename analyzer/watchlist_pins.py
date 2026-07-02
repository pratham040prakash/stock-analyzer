"""Pin 2–3 watchlist names for the next MIS session."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.market_session import market_session_status

IST = ZoneInfo("Asia/Kolkata")
MAX_PINNED = 3
PINS_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "pinned_watchlist.json"


@dataclass
class PinnedPlan:
    symbol: str
    entry: float
    stop_loss: float
    target: float
    prep_date: str
    pinned_at: str = ""


def _ensure_dir() -> None:
    PINS_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_raw() -> dict:
    _ensure_dir()
    if not PINS_PATH.exists():
        return {"prep_date": "", "picks": []}
    try:
        return json.loads(PINS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"prep_date": "", "picks": []}


def _save_raw(data: dict) -> None:
    _ensure_dir()
    PINS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def current_prep_date() -> str:
    return market_session_status().get("date", datetime.now(IST).strftime("%Y-%m-%d"))


def load_pinned_plans() -> list[PinnedPlan]:
    raw = _load_raw()
    picks = []
    for p in raw.get("picks", []):
        picks.append(
            PinnedPlan(
                symbol=p["symbol"],
                entry=float(p["entry"]),
                stop_loss=float(p["stop_loss"]),
                target=float(p["target"]),
                prep_date=raw.get("prep_date", ""),
                pinned_at=p.get("pinned_at", ""),
            )
        )
    return picks


def pinned_symbols() -> set[str]:
    return {p.symbol.upper() for p in load_pinned_plans()}


def is_pinned(symbol: str) -> bool:
    return symbol.upper().replace(".NS", "") in pinned_symbols()


def pin_pick(
    symbol: str,
    *,
    entry: float,
    stop_loss: float,
    target: float,
    max_pins: int = MAX_PINNED,
) -> tuple[bool, str]:
    """Pin a symbol. Returns (success, message)."""
    sym = symbol.upper().replace(".NS", "")
    raw = _load_raw()
    prep = current_prep_date()
    if raw.get("prep_date") != prep:
        raw = {"prep_date": prep, "picks": []}

    picks = [p for p in raw.get("picks", []) if p["symbol"] != sym]
    if len(picks) >= max_pins:
        return False, f"Max **{max_pins}** picks — unpin one first."

    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    picks.append({
        "symbol": sym,
        "entry": entry,
        "stop_loss": stop_loss,
        "target": target,
        "pinned_at": now,
    })
    raw["picks"] = picks
    raw["prep_date"] = prep
    _save_raw(raw)
    return True, f"Pinned **{sym}** ({len(picks)}/{max_pins})."


def unpin_pick(symbol: str) -> None:
    sym = symbol.upper().replace(".NS", "")
    raw = _load_raw()
    raw["picks"] = [p for p in raw.get("picks", []) if p["symbol"] != sym]
    _save_raw(raw)


def toggle_pin(
    symbol: str,
    *,
    entry: float,
    stop_loss: float,
    target: float,
    max_pins: int = MAX_PINNED,
) -> tuple[bool, str]:
    """Toggle pin; returns (now_pinned, message)."""
    if is_pinned(symbol):
        unpin_pick(symbol)
        return False, f"Unpinned **{symbol}**."
    ok, msg = pin_pick(
        symbol, entry=entry, stop_loss=stop_loss, target=target, max_pins=max_pins
    )
    return ok, msg


def clear_pins() -> None:
    _save_raw({"prep_date": current_prep_date(), "picks": []})
