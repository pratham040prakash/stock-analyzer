"""Pick one options leg (Nifty / Bank Nifty CE or PE) for alerts & EOD."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from analyzer.watchlist_history import session_target_date

IST = ZoneInfo("Asia/Kolkata")
SELECT_PATH = Path(__file__).resolve().parent.parent / "data" / "intraday" / "selected_option.json"


def _ensure_dir() -> None:
    SELECT_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_raw() -> dict:
    _ensure_dir()
    if not SELECT_PATH.exists():
        return {"trade_date": "", "pick": None, "auto": False}
    try:
        return json.loads(SELECT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"trade_date": "", "pick": None, "auto": False}


def _save_raw(data: dict) -> None:
    _ensure_dir()
    existing = _load_raw()
    history = dict(existing.get("history", {}))
    trade_date = data.get("trade_date")
    pick = data.get("pick")
    if trade_date and pick:
        history[trade_date] = {
            "pick": pick,
            "auto": bool(data.get("auto", False)),
        }
    data["history"] = history
    data["updated_at"] = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    SELECT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def option_pick_key(fno_symbol: str, option_type: str, strike: float) -> tuple[str, str, float]:
    return (fno_symbol.upper().strip(), option_type.upper().strip(), float(strike))


def _pick_dict(fno_symbol: str, option_type: str, strike: float) -> dict[str, Any]:
    return {
        "fno_symbol": fno_symbol.upper().strip(),
        "option_type": option_type.upper().strip(),
        "strike": float(strike),
    }


def load_selected_option(trade_date: str | None = None) -> dict[str, Any] | None:
    trade_date = trade_date or session_target_date()
    raw = _load_raw()
    if raw.get("trade_date") == trade_date:
        pick = raw.get("pick")
        return dict(pick) if pick else None
    hist = raw.get("history", {}).get(trade_date, {})
    pick = hist.get("pick")
    return dict(pick) if pick else None


def is_option_selected(
    fno_symbol: str,
    option_type: str,
    strike: float,
    trade_date: str | None = None,
) -> bool:
    pick = load_selected_option(trade_date)
    if not pick:
        return False
    return option_pick_key(fno_symbol, option_type, strike) == option_pick_key(
        pick["fno_symbol"], pick["option_type"], pick["strike"],
    )


def snap_matches_pick(snap: Any, pick: dict[str, Any] | None = None, trade_date: str | None = None) -> bool:
    pick = pick or load_selected_option(trade_date)
    if not pick:
        return False
    return option_pick_key(
        getattr(snap, "fno_symbol", ""),
        getattr(snap, "option_type", ""),
        float(getattr(snap, "strike", 0)),
    ) == option_pick_key(pick["fno_symbol"], pick["option_type"], pick["strike"])


def toggle_option_selected(
    fno_symbol: str,
    option_type: str,
    strike: float,
    *,
    trade_date: str | None = None,
) -> tuple[bool, str]:
    """Toggle one options leg. Returns (now_selected, message)."""
    trade_date = trade_date or session_target_date()
    key = option_pick_key(fno_symbol, option_type, strike)
    label = f"{fno_symbol} {option_type} {strike:g}"
    raw = _load_raw()
    if raw.get("trade_date") != trade_date:
        raw = {"trade_date": trade_date, "pick": None, "auto": False}

    current = raw.get("pick")
    if current and option_pick_key(current["fno_symbol"], current["option_type"], current["strike"]) == key:
        raw["pick"] = None
        raw["auto"] = False
        _save_raw(raw)
        return False, f"Removed **{label}** from today's option pick."

    raw["trade_date"] = trade_date
    raw["pick"] = _pick_dict(fno_symbol, option_type, strike)
    raw["auto"] = False
    _save_raw(raw)
    return True, f"Selected **{label}** for alerts & EOD."


def clear_option_selection(trade_date: str | None = None) -> None:
    trade_date = trade_date or session_target_date()
    _save_raw({"trade_date": trade_date, "pick": None, "auto": False})


def option_selection_status_line(trade_date: str | None = None) -> str:
    pick = load_selected_option(trade_date)
    if not pick:
        return "Star **1** option leg below (optional)."
    label = f"{pick['fno_symbol']} {pick['option_type']} {pick['strike']:g}"
    auto = is_auto_option_selected(trade_date)
    suffix = " (auto ★)" if auto else ""
    return f"Option leg: **{label}**{suffix} — alerts & EOD focus on this only."


def is_auto_option_selected(trade_date: str | None = None) -> bool:
    trade_date = trade_date or session_target_date()
    raw = _load_raw()
    if raw.get("trade_date") == trade_date:
        return bool(raw.get("auto"))
    hist = raw.get("history", {}).get(trade_date, {})
    return bool(hist.get("auto"))


def auto_select_recommended_option(
    *,
    trade_date: str | None = None,
) -> tuple[bool, str]:
    """Default to lowest-rank ★ recommended leg from saved options snapshot."""
    from analyzer.options_watchlist_history import fetch_options_snapshots_for_date

    trade_date = trade_date or session_target_date()
    if load_selected_option(trade_date):
        return False, "Option leg already set — skip auto-pick."

    snaps = fetch_options_snapshots_for_date(trade_date)
    recs = [s for s in snaps if s.recommended]
    if not recs:
        return False, "No ★ option in snapshot — run **Prep all** or nightly options prep."

    recs.sort(key=lambda s: (s.rank, s.fno_symbol))
    best = recs[0]
    label = f"{best.fno_symbol} {best.option_type} {best.strike:g}"
    raw = {
        "trade_date": trade_date,
        "pick": _pick_dict(best.fno_symbol, best.option_type, best.strike),
        "auto": True,
    }
    _save_raw(raw)
    return True, f"Auto-picked option **{label}** (★ recommended)."
