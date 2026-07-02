"""Kite live quotes — REST cache + WebSocket for holdings and Nifty 50."""

from __future__ import annotations

import threading
import time
from typing import Any

from analyzer.cache_utils import cached_compute
from analyzer.india import NIFTY_50
from analyzer.market_session import market_session_status
from analyzer.zerodha import fetch_kite_ltp, get_kite_client, load_env_credentials

_LTP_CACHE: dict[str, tuple[float, float]] = {}
_TOKEN_TO_KEY: dict[int, str] = {}
_CACHE_LOCK = threading.Lock()
_WS: Any = None
_WS_THREAD: threading.Thread | None = None
_WS_TOKENS: set[int] = set()
_INSTRUMENT_MAP: dict[str, int] | None = None
_NIFTY_INDEX_TOKEN = 256265


def _cache_key(symbol: str) -> str:
    return symbol.upper().strip()


def get_kite_ltp_cached(symbols: list[str], max_age_sec: float = 5.0) -> dict[str, float]:
    """LTP by NSE:SYMBOL-EQ keys using cache then REST."""
    if not symbols:
        return {}

    now = time.time()
    out: dict[str, float] = {}
    stale: list[str] = []

    with _CACHE_LOCK:
        for sym in symbols:
            key = _cache_key(sym)
            if key in _LTP_CACHE:
                price, ts = _LTP_CACHE[key]
                if now - ts <= max_age_sec:
                    out[key] = price
                    continue
            stale.append(sym)

    if stale:
        try:
            fresh = fetch_kite_ltp(stale)
            with _CACHE_LOCK:
                for k, v in fresh.items():
                    ck = _cache_key(k)
                    _LTP_CACHE[ck] = (v, now)
                    out[ck] = v
        except Exception:
            pass

    return out


def get_ltp_by_kite_symbol(kite_symbol: str, max_age_sec: float = 3.0) -> float | None:
    m = get_kite_ltp_cached([kite_symbol], max_age_sec=max_age_sec)
    return m.get(_cache_key(kite_symbol))


def _build_instrument_map() -> dict[str, int]:
    """Map NSE:RELIANCE-EQ and RELIANCE -> instrument_token."""
    kite = get_kite_client()
    if kite is None:
        return {}

    def _fetch() -> dict[str, int]:
        out: dict[str, int] = {}
        try:
            for row in kite.instruments("NSE"):
                tok = int(row["instrument_token"])
                ts = row.get("tradingsymbol", "")
                if not ts:
                    continue
                out[ts.upper()] = tok
                out[f"NSE:{ts}-EQ".upper()] = tok
            out["NIFTY"] = _NIFTY_INDEX_TOKEN
            out["NSE:NIFTY 50"] = _NIFTY_INDEX_TOKEN
        except Exception:
            pass
        return out

    return cached_compute("kite_instruments_nse", 86400, _fetch)


def nifty50_kite_symbols() -> list[str]:
    """NSE equity symbols for Nifty 50 constituents."""
    return [f"NSE:{symbol}-EQ" for symbol in NIFTY_50]


def _ensure_instrument_map() -> dict[str, int]:
    global _INSTRUMENT_MAP
    if _INSTRUMENT_MAP is None:
        _INSTRUMENT_MAP = _build_instrument_map()
    return _INSTRUMENT_MAP


def _bind_token_keys(kite_symbols: list[str]) -> None:
    """Map instrument tokens → cache keys for WebSocket tick routing."""
    inst = _ensure_instrument_map()
    with _CACHE_LOCK:
        for sym in kite_symbols:
            key = _cache_key(sym)
            tok = inst.get(key)
            if not tok and "-EQ" not in key:
                tok = inst.get(f"{key}-EQ") or inst.get(f"NSE:{key}-EQ")
            if tok:
                _TOKEN_TO_KEY[int(tok)] = key


def resolve_instrument_tokens(kite_symbols: list[str]) -> list[int]:
    inst = _ensure_instrument_map()
    tokens: list[int] = []
    for sym in kite_symbols:
        key = _cache_key(sym)
        tok = inst.get(key)
        if not tok and "-EQ" not in key:
            tok = inst.get(f"{key}-EQ") or inst.get(f"NSE:{key}-EQ")
        if tok:
            tokens.append(tok)
    if not tokens:
        tokens.append(_NIFTY_INDEX_TOKEN)
    return list(dict.fromkeys(tokens))


def _on_ticks(_ws: Any, ticks: list[dict]) -> None:
    now = time.time()
    with _CACHE_LOCK:
        for t in ticks:
            ltp = t.get("last_price")
            if ltp is None:
                continue
            token = t.get("instrument_token")
            key = _TOKEN_TO_KEY.get(int(token)) if token else None
            if not key:
                ts = t.get("tradingsymbol")
                if ts:
                    key = f"NSE:{ts}-EQ".upper()
            if key:
                _LTP_CACHE[_cache_key(key)] = (float(ltp), now)


def start_kite_ticker_background(instrument_tokens: list[int] | None = None) -> bool:
    """Start WebSocket LTP feed (default: Nifty index token)."""
    return _start_ticker(instrument_tokens or [_NIFTY_INDEX_TOKEN])


def start_kite_ticker_for_nifty50() -> bool:
    """Subscribe WebSocket to all Nifty 50 equities + Nifty index."""
    symbols = nifty50_kite_symbols()
    tokens = resolve_instrument_tokens(symbols)
    tokens = list(dict.fromkeys(tokens + [_NIFTY_INDEX_TOKEN]))
    _bind_token_keys(symbols + ["NSE:NIFTY 50", "NIFTY"])
    return _start_ticker(tokens)


def start_kite_ticker_on_app_start() -> bool:
    """
    App bootstrap: Nifty 50 WebSocket when NSE is open, index-only otherwise.
    Safe to call on every Streamlit rerun — adds tokens if session just opened.
    """
    creds = load_env_credentials()
    if not creds.get("api_key") or not creds.get("access_token"):
        return False
    session = market_session_status()
    if session.get("is_open"):
        return start_kite_ticker_for_nifty50()
    return start_kite_ticker_background()


def ws_subscription_status() -> dict:
    """Diagnostics for UI — how many tokens are live on the WebSocket."""
    session = market_session_status()
    return {
        "market_open": bool(session.get("is_open")),
        "subscribed_tokens": len(_WS_TOKENS),
        "nifty50_mode": bool(session.get("is_open") and len(_WS_TOKENS) > 1),
        "ws_active": _WS_THREAD is not None and _WS_THREAD.is_alive(),
    }


def start_kite_ticker_for_holdings(kite_symbols: list[str]) -> bool:
    """Subscribe WebSocket to portfolio symbols + Nifty."""
    tokens = resolve_instrument_tokens(kite_symbols)
    tokens = list(dict.fromkeys(tokens + [_NIFTY_INDEX_TOKEN]))
    _bind_token_keys(kite_symbols)
    return _start_ticker(tokens)


def _start_ticker(tokens: list[int]) -> bool:
    global _WS, _WS_THREAD, _WS_TOKENS

    creds = load_env_credentials()
    api_key = creds.get("api_key") or ""
    access_token = creds.get("access_token") or ""
    if not api_key or not access_token:
        return False

    new_tokens = set(tokens) - _WS_TOKENS
    if _WS is not None and not new_tokens:
        return True

    try:
        from kiteconnect import KiteTicker
    except ImportError:
        return False

    all_tokens = list(_WS_TOKENS | set(tokens))

    def _run() -> None:
        global _WS
        kws = KiteTicker(api_key, access_token)
        kws.on_ticks = _on_ticks

        def on_connect(ws, response):
            ws.subscribe(all_tokens)
            ws.set_mode(ws.MODE_LTP, all_tokens)

        kws.on_connect = on_connect
        _WS = kws
        kws.connect(threaded=True)

    try:
        if _WS_THREAD is None or not _WS_THREAD.is_alive():
            _WS_THREAD = threading.Thread(target=_run, daemon=True, name="kite-ticker")
            _WS_THREAD.start()
        else:
            try:
                _WS.subscribe(list(new_tokens))
                _WS.set_mode(_WS.MODE_LTP, list(new_tokens))
            except Exception:
                pass
        _WS_TOKENS.update(tokens)
        return True
    except Exception:
        return False
