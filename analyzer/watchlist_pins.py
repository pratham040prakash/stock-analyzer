"""Auto top-N watchlist names for the next MIS session."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.market_session import market_session_status

IST = ZoneInfo("Asia/Kolkata")
TOP_TOMORROW_PICKS = 5
MAX_PINNED = TOP_TOMORROW_PICKS  # legacy manual pin; MIS workflow uses sync_auto_top_picks
PINS_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "pinned_watchlist.json"


def infer_trade_side(entry: float, stop_loss: float, *, explicit: str | None = None) -> str:
    """LONG | SHORT from explicit side or stop vs entry geometry."""
    if explicit:
        side = explicit.upper()
        if side in ("LONG", "SHORT"):
            return side
    return "SHORT" if stop_loss > entry else "LONG"


@dataclass
class PinnedPlan:
    symbol: str
    entry: float
    stop_loss: float
    target: float
    prep_date: str
    pinned_at: str = ""
    sector: str = ""
    side: str = "LONG"


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
        entry = float(p["entry"])
        stop = float(p["stop_loss"])
        picks.append(
            PinnedPlan(
                symbol=p["symbol"],
                entry=entry,
                stop_loss=stop,
                target=float(p["target"]),
                prep_date=raw.get("prep_date", ""),
                pinned_at=p.get("pinned_at", ""),
                sector=p.get("sector", ""),
                side=infer_trade_side(entry, stop, explicit=p.get("side")),
            )
        )
    return picks


def pinned_symbols() -> set[str]:
    return {p.symbol.upper() for p in load_pinned_plans()}


def pinned_sector_map() -> dict[str, str]:
    """Symbol → sector from tonight's pinned top picks."""
    return {
        p.symbol.upper(): (p.sector or "").strip()
        for p in load_pinned_plans()
        if (p.sector or "").strip()
    }


def sector_for_symbol(symbol: str) -> str:
    sym = symbol.upper().replace(".NS", "")
    return pinned_sector_map().get(sym, "")


def is_pinned(symbol: str) -> bool:
    return symbol.upper().replace(".NS", "") in pinned_symbols()


def pin_pick(
    symbol: str,
    *,
    entry: float,
    stop_loss: float,
    target: float,
    side: str | None = None,
    max_pins: int = MAX_PINNED,
) -> tuple[bool, str]:
    """Pin a symbol manually (legacy). MIS workflow uses sync_auto_top_picks instead."""
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
        "side": infer_trade_side(entry, stop_loss, explicit=side),
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
    side: str | None = None,
    max_pins: int = MAX_PINNED,
) -> tuple[bool, str]:
    """Toggle pin; returns (now_pinned, message)."""
    if is_pinned(symbol):
        unpin_pick(symbol)
        return False, f"Unpinned **{symbol}**."
    ok, msg = pin_pick(
        symbol,
        entry=entry,
        stop_loss=stop_loss,
        target=target,
        side=side,
        max_pins=max_pins,
    )
    return ok, msg


def clear_pins() -> None:
    _save_raw({"prep_date": current_prep_date(), "picks": []})


def sync_auto_top_picks(
    picks: list,
    *,
    limit: int = TOP_TOMORROW_PICKS,
) -> list[PinnedPlan]:
    """
    Auto-select top N watchlist picks for tomorrow (no manual pin).
    Writes to pinned_watchlist.json for Telegram, scoring, and reminders.
    """
    from analyzer.watchlist_history import session_target_date

    limit = max(1, limit)
    top = picks[:limit]
    prep = current_prep_date()
    trade_for = session_target_date()
    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    rows = []
    for p in top:
        sym = (
            getattr(p, "nse_symbol", None) or getattr(p, "symbol", "")
        ).upper().replace(".NS", "")
        entry = float(getattr(p, "entry"))
        stop = float(getattr(p, "stop_loss"))
        rows.append({
            "symbol": sym,
            "entry": entry,
            "stop_loss": stop,
            "target": float(getattr(p, "target")),
            "side": infer_trade_side(
                entry,
                stop,
                explicit=getattr(p, "side", None),
            ),
            "pinned_at": now,
            "sector": (getattr(p, "sector", "") or "").strip(),
        })
    prev_raw = _load_raw()
    prev_syms = tuple(p.get("symbol") for p in prev_raw.get("picks", []))
    new_syms = tuple(r["symbol"] for r in rows)
    if prev_syms != new_syms:
        from analyzer.trade_selection import clear_selection

        clear_selection(trade_for)
    _save_raw({
        "prep_date": prep,
        "trade_date": trade_for,
        "auto": True,
        "picks": rows,
    })
    return load_pinned_plans()
