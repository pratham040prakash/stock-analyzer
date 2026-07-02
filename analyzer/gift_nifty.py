"""Gift Nifty / pre-open gap cue for India macro."""

from __future__ import annotations

from datetime import datetime

import yfinance as yf

from analyzer.india_macro import MacroQuote
from analyzer.kite_stream import get_ltp_by_kite_symbol
from analyzer.market_session import IST
from analyzer.providers.kite import is_kite_configured
from analyzer.zerodha import get_kite_client


def _nifty_gap_from_yahoo() -> MacroQuote | None:
    hist = yf.Ticker("^NSEI").history(period="5d", interval="1d", auto_adjust=True)
    if len(hist) < 2:
        return None
    prev_close = float(hist["Close"].iloc[-2])
    last = float(hist["Close"].iloc[-1])
    gap_pct = (last - prev_close) / prev_close * 100
    return MacroQuote(
        symbol="^NSEI",
        name="Nifty 50 gap cue",
        price=last,
        change_1d_pct=round(gap_pct, 2),
        note="Yahoo spot vs prior close — proxy before 9:15 IST",
    )


def _nifty_futures_from_kite() -> MacroQuote | None:
    if not is_kite_configured():
        return None
    kite = get_kite_client()
    if kite is None:
        return None
    try:
        fut_rows = [
            r for r in kite.instruments("NFO")
            if r.get("name") == "NIFTY" and r.get("instrument_type") == "FUT"
        ]
        if not fut_rows:
            return None
        fut_rows.sort(key=lambda r: r.get("expiry", datetime.min.date()))
        nearest = fut_rows[0]
        token = int(nearest["instrument_token"])
        sym = nearest["tradingsymbol"]
        quotes = kite.quote([f"NFO:{sym}"])
        q = quotes.get(f"NFO:{sym}", {})
        ltp = float(q.get("last_price") or 0)
        if ltp <= 0:
            return None
        ohlc = q.get("ohlc", {})
        prev = float(ohlc.get("close") or ltp)
        chg = (ltp - prev) / prev * 100 if prev else None
        return MacroQuote(
            symbol=f"NFO:{sym}",
            name="Nifty Futures (nearest)",
            price=ltp,
            change_1d_pct=round(chg, 2) if chg is not None else None,
            note="Kite live Nifty fut — best pre-open gap cue when market data active",
        )
    except Exception:
        pass

    ltp = get_ltp_by_kite_symbol("NSE:NIFTY 50")
    if ltp:
        return MacroQuote(
            symbol="NSE:NIFTY 50",
            name="Nifty 50 (Kite LTP)",
            price=ltp,
            change_1d_pct=None,
            note="Kite index LTP — use with global overnight cues",
        )
    return None


def fetch_gift_nifty_cue() -> MacroQuote | None:
    """
    Pre-open Nifty cue: Kite nearest futures → Kite spot → Yahoo gap proxy.
    True Gift Nifty (NSE IX) requires licensed feed; this is the best free stack.
    """
    now = datetime.now(IST)
    fut = _nifty_futures_from_kite()
    if fut:
        if now.weekday() < 5 and 6 <= now.hour < 9:
            fut.name = "Gift Nifty proxy (Nifty Fut)"
        return fut
    return _nifty_gap_from_yahoo()
