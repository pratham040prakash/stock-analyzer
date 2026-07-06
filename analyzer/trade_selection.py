"""Pick up to 2 equity names from tonight's top-5 for tomorrow's MIS session."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.watchlist_history import session_target_date
from analyzer.watchlist_pins import PinnedPlan, load_pinned_plans, sector_for_symbol

IST = ZoneInfo("Asia/Kolkata")
SELECT_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "selected_trades.json"
DEFAULT_MAX_SELECTED = 2
MAX_SAME_SECTOR = 1  # force 2 picks from different sectors


def _ensure_dir() -> None:
    SELECT_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_raw() -> dict:
    _ensure_dir()
    if not SELECT_PATH.exists():
        return {"trade_date": "", "symbols": [], "auto": False}
    try:
        return json.loads(SELECT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"trade_date": "", "symbols": [], "auto": False}


def _save_raw(data: dict) -> None:
    _ensure_dir()
    existing = _load_raw()
    history = dict(existing.get("history", {}))
    trade_date = data.get("trade_date")
    symbols = data.get("symbols") or []
    if trade_date and symbols:
        history[trade_date] = {
            "symbols": [_normalize(s) for s in symbols],
            "auto": bool(data.get("auto", False)),
        }
    data["history"] = history
    data["updated_at"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    SELECT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _normalize(sym: str) -> str:
    return sym.upper().replace(".NS", "")


def load_selected_symbols(trade_date: str | None = None) -> list[str]:
    trade_date = trade_date or session_target_date()
    raw = _load_raw()
    if raw.get("trade_date") == trade_date:
        return [_normalize(s) for s in raw.get("symbols", [])]
    hist = raw.get("history", {}).get(trade_date, {})
    return [_normalize(s) for s in hist.get("symbols", [])]


def is_auto_selected(trade_date: str | None = None) -> bool:
    trade_date = trade_date or session_target_date()
    raw = _load_raw()
    if raw.get("trade_date") == trade_date:
        return bool(raw.get("auto"))
    hist = raw.get("history", {}).get(trade_date, {})
    return bool(hist.get("auto"))


def is_selection_complete(
    trade_date: str | None = None,
    *,
    max_selected: int = DEFAULT_MAX_SELECTED,
) -> bool:
    return len(load_selected_symbols(trade_date)) >= max_selected


def is_selected(symbol: str, trade_date: str | None = None) -> bool:
    return _normalize(symbol) in load_selected_symbols(trade_date)


def _sector_count(symbols: list[str], sector: str) -> int:
    if not sector:
        return 0
    return sum(1 for s in symbols if sector_for_symbol(s) == sector)


def set_selected_symbols(
    symbols: list[str],
    *,
    trade_date: str | None = None,
    max_selected: int = DEFAULT_MAX_SELECTED,
    auto: bool = False,
) -> tuple[bool, str]:
    trade_date = trade_date or session_target_date()
    syms = [_normalize(s) for s in symbols][:max_selected]
    _save_raw({"trade_date": trade_date, "symbols": syms, "auto": auto})
    if not syms:
        return True, "Cleared trade selection."
    suffix = " _(auto top 2)_" if auto else ""
    return True, f"Selected **{', '.join(syms)}** ({len(syms)}/{max_selected}).{suffix}"


def toggle_selected(
    symbol: str,
    *,
    trade_date: str | None = None,
    max_selected: int = DEFAULT_MAX_SELECTED,
    sector: str = "",
    max_same_sector: int = MAX_SAME_SECTOR,
) -> tuple[bool, str]:
    """Toggle symbol in selection. Returns (now_selected, message)."""
    trade_date = trade_date or session_target_date()
    sym = _normalize(symbol)
    raw = _load_raw()
    if raw.get("trade_date") != trade_date:
        raw = {"trade_date": trade_date, "symbols": [], "auto": False}

    symbols = [_normalize(s) for s in raw.get("symbols", [])]
    if sym in symbols:
        symbols.remove(sym)
        raw["symbols"] = symbols
        raw["auto"] = False
        _save_raw(raw)
        return False, f"Removed **{sym}** from today's 2 picks."

    if len(symbols) >= max_selected:
        return False, f"Max **{max_selected}** trades — remove one first."

    sec = (sector or sector_for_symbol(sym)).strip()
    if sec and _sector_count(symbols, sec) >= max_same_sector:
        return (
            False,
            f"Already **{max_same_sector}** from **{sec}** — diversify your 2 picks.",
        )

    symbols.append(sym)
    raw["trade_date"] = trade_date
    raw["symbols"] = symbols
    raw["auto"] = False
    _save_raw(raw)
    return True, f"Selected **{sym}** ({len(symbols)}/{max_selected})."


def clear_selection(trade_date: str | None = None) -> None:
    trade_date = trade_date or session_target_date()
    _save_raw({"trade_date": trade_date, "symbols": [], "auto": False})


def reset_selection_for_new_prep(trade_date: str | None = None) -> None:
    """Clear picks when a new prep session is saved."""
    trade_date = trade_date or session_target_date()
    raw = _load_raw()
    if raw.get("trade_date") != trade_date:
        _save_raw({"trade_date": trade_date, "symbols": [], "auto": False})


def auto_select_top_by_rank(
    *,
    trade_date: str | None = None,
    max_selected: int = DEFAULT_MAX_SELECTED,
    max_same_sector: int = MAX_SAME_SECTOR,
) -> tuple[bool, str]:
    """Default to top ranked picks with different sectors when possible."""
    trade_date = trade_date or session_target_date()
    if load_selected_symbols(trade_date):
        return False, "Selection already set — skip auto-pick."

    pins = load_pinned_plans()
    if not pins:
        return False, "No pinned picks to auto-select."

    syms = _pick_diverse_from_pins(pins, max_selected=max_selected, max_same_sector=max_same_sector)
    if len(syms) < max_selected:
        return False, "Not enough sector-diverse picks in top 5 — star manually."

    _save_raw({"trade_date": trade_date, "symbols": syms, "auto": True})
    return True, f"Auto-picked **{', '.join(syms)}** (top ranks, different sectors)."


def _pick_diverse_from_pins(
    pins: list[PinnedPlan],
    *,
    max_selected: int,
    max_same_sector: int,
) -> list[str]:
    picked: list[str] = []
    picked_sector: dict[str, str] = {}
    for p in pins:
        sym = _normalize(p.symbol)
        sec = (getattr(p, "sector", "") or sector_for_symbol(sym)).strip()
        if sec:
            same = sum(1 for s in picked if picked_sector.get(s) == sec)
            if same >= max_same_sector:
                continue
        picked.append(sym)
        if sec:
            picked_sector[sym] = sec
        if len(picked) >= max_selected:
            break
    return picked


def effective_trade_plans(trade_date: str | None = None) -> list[PinnedPlan]:
    """Pinned plans filtered to user-selected names (if any)."""
    trade_date = trade_date or session_target_date()
    pins = load_pinned_plans()
    selected = load_selected_symbols(trade_date)
    if not selected:
        return pins[:DEFAULT_MAX_SELECTED] if pins else pins
    sel_set = set(selected)
    filtered = [p for p in pins if _normalize(p.symbol) in sel_set]
    return filtered or pins[:DEFAULT_MAX_SELECTED]


def selection_status_line(trade_date: str | None = None, max_selected: int = DEFAULT_MAX_SELECTED) -> str:
    selected = load_selected_symbols(trade_date)
    if not selected:
        return f"Pick **{max_selected}** names below for tomorrow's session."
    auto = is_auto_selected(trade_date)
    suffix = " _(auto)_" if auto else ""
    return f"Trading **{', '.join(selected)}** ({len(selected)}/{max_selected}){suffix}."
