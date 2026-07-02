"""Persist portfolio holdings to disk — broker-agnostic, no Kite required."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult, kite_to_yahoo

IST = ZoneInfo("Asia/Kolkata")
STORE_DIR = Path(__file__).resolve().parent.parent / "data" / "portfolio"
DEFAULT_PROFILE = "default"


def _safe_profile(profile: str | None) -> str:
    raw = (profile or DEFAULT_PROFILE).strip().lower()
    safe = re.sub(r"[^a-z0-9_-]", "", raw.replace(" ", "_"))[:32]
    return safe or DEFAULT_PROFILE


def store_path(profile: str | None = None) -> Path:
    return STORE_DIR / f"{_safe_profile(profile)}.json"


def _ensure_dir() -> None:
    STORE_DIR.mkdir(parents=True, exist_ok=True)


def holding_to_dict(h: ZerodhaHolding) -> dict:
    return {
        "kite_symbol": h.kite_symbol,
        "tradingsymbol": h.tradingsymbol,
        "exchange": h.exchange,
        "quantity": h.quantity,
        "average_price": h.average_price,
        "last_price": h.last_price,
        "pnl": h.pnl,
        "yahoo_symbol": h.yahoo_symbol or kite_to_yahoo(h.kite_symbol),
    }


def holding_from_dict(d: dict) -> ZerodhaHolding:
    yahoo = d.get("yahoo_symbol") or kite_to_yahoo(d.get("kite_symbol", ""))
    return ZerodhaHolding(
        kite_symbol=d.get("kite_symbol", ""),
        tradingsymbol=d.get("tradingsymbol", ""),
        exchange=d.get("exchange", "NSE"),
        quantity=float(d.get("quantity", 0)),
        average_price=d.get("average_price"),
        last_price=d.get("last_price"),
        pnl=d.get("pnl"),
        yahoo_symbol=yahoo,
    )


def import_to_dict(imp: ZerodhaImportResult) -> dict:
    return {
        "source": imp.source,
        "holdings": [holding_to_dict(h) for h in imp.holdings],
        "errors": list(imp.errors),
    }


def import_from_dict(d: dict) -> ZerodhaImportResult:
    return ZerodhaImportResult(
        holdings=[holding_from_dict(h) for h in d.get("holdings", [])],
        errors=list(d.get("errors", [])),
        source=d.get("source", "saved"),
    )


def make_manual_holding(symbol: str, quantity: float, average_price: float | None) -> ZerodhaHolding | None:
    sym = symbol.strip().upper()
    if not sym or quantity <= 0:
        return None
    if sym.endswith(".NS"):
        base = sym.replace(".NS", "")
        kite_sym = f"NSE:{base}-EQ"
        yahoo = sym
        exchange = "NSE"
    elif sym.endswith(".BO"):
        base = sym.replace(".BO", "")
        kite_sym = f"BSE:{base}"
        yahoo = sym
        exchange = "BSE"
    else:
        base = sym.replace("-EQ", "")
        kite_sym = f"NSE:{base}-EQ"
        yahoo = f"{base}.NS"
        exchange = "NSE"
    avg = average_price if average_price and average_price > 0 else None
    return ZerodhaHolding(
        kite_symbol=kite_sym,
        tradingsymbol=base,
        exchange=exchange,
        quantity=quantity,
        average_price=avg,
        yahoo_symbol=yahoo,
    )


def enrich_holding_pnl(h: ZerodhaHolding, last_price: float | None) -> ZerodhaHolding:
    """Compute P&L from avg price and live LTP when missing."""
    ltp = last_price or h.last_price
    pnl = h.pnl
    if pnl is None and ltp is not None and h.average_price is not None and h.quantity:
        pnl = (ltp - h.average_price) * h.quantity
    return ZerodhaHolding(
        kite_symbol=h.kite_symbol,
        tradingsymbol=h.tradingsymbol,
        exchange=h.exchange,
        quantity=h.quantity,
        average_price=h.average_price,
        last_price=ltp,
        pnl=pnl,
        yahoo_symbol=h.yahoo_symbol,
    )


def portfolio_profile_key() -> str:
    """Session profile id — keeps holdings separate on shared Streamlit Cloud."""
    try:
        import streamlit as st

        return _safe_profile(st.session_state.get("portfolio_profile"))
    except Exception:
        return DEFAULT_PROFILE


def save_portfolio(imp: ZerodhaImportResult, profile: str | None = None) -> None:
    _ensure_dir()
    path = store_path(profile)
    payload = {
        "version": 1,
        "profile": _safe_profile(profile),
        "updated_at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
        "portfolio": import_to_dict(imp),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_saved_portfolio(profile: str | None = None) -> ZerodhaImportResult | None:
    path = store_path(profile)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        imp = import_from_dict(data.get("portfolio", {}))
        if imp.holdings:
            imp.source = imp.source or "saved"
            return imp
    except Exception:
        pass
    return None


def portfolio_summary(imp: ZerodhaImportResult) -> str:
    return f"{len(imp.holdings)} holdings · source: {imp.source}"


def clear_saved_portfolio(profile: str | None = None) -> None:
    path = store_path(profile)
    if path.exists():
        path.unlink()
