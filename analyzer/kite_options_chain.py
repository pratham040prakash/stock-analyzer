"""Option chain data from Zerodha Kite NFO — primary source when logged in."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from analyzer.nse_options import (
    NSEOptionChain,
    NSEOptionLeg,
    DEFAULT_INDEX_LOT_SIZES,
    normalize_fno_symbol,
)

IST = ZoneInfo("Asia/Kolkata")
_INSTRUMENTS_CACHE: tuple[float, list[dict]] | None = None
_INSTRUMENTS_TTL = 3600

_INDEX_KITE_SYMBOL = {
    "NIFTY": "NSE:NIFTY 50",
    "BANKNIFTY": "NSE:NIFTY BANK",
    "FINNIFTY": "NSE:NIFTY FIN SERVICE",
    "MIDCPNIFTY": "NSE:NIFTY MID SELECT",
}


def kite_options_available() -> bool:
    from analyzer.zerodha import get_kite_client

    return get_kite_client() is not None


def _kite_client():
    from analyzer.zerodha import get_kite_client

    return get_kite_client()


def _load_nfo_instruments() -> list[dict]:
    global _INSTRUMENTS_CACHE
    now = datetime.now(IST).timestamp()
    if _INSTRUMENTS_CACHE and now - _INSTRUMENTS_CACHE[0] < _INSTRUMENTS_TTL:
        return _INSTRUMENTS_CACHE[1]
    kite = _kite_client()
    if kite is None:
        return []
    try:
        rows = kite.instruments("NFO")
    except Exception:
        return []
    _INSTRUMENTS_CACHE = (now, rows)
    return rows


def _format_nse_expiry(exp: date) -> str:
    return exp.strftime("%d-%b-%Y")


def _parse_expiry(exp) -> date | None:
    if isinstance(exp, date):
        return exp
    if not exp:
        return None
    try:
        return datetime.strptime(str(exp).strip(), "%d-%b-%Y").date()
    except ValueError:
        try:
            return datetime.strptime(str(exp).strip(), "%Y-%m-%d").date()
        except ValueError:
            return None


def _quote_bid_ask(q: dict) -> tuple[float | None, float | None]:
    depth = q.get("depth") or {}
    buy = depth.get("buy") or []
    sell = depth.get("sell") or []
    bid = float(buy[0]["price"]) if buy and buy[0].get("price") else None
    ask = float(sell[0]["price"]) if sell and sell[0].get("price") else None
    return bid, ask


def _index_spot(nse_sym: str) -> float:
    kite = _kite_client()
    if kite is None:
        return 0.0
    sym = _INDEX_KITE_SYMBOL.get(nse_sym)
    if not sym:
        from analyzer.providers.kite import _INDEX_TOKEN

        token = _INDEX_TOKEN.get(nse_sym)
        if token is None:
            return 0.0
        sym = str(token)
    try:
        q = kite.quote([sym])
        row = q.get(sym) or q.get(str(sym)) or {}
        return float(row.get("last_price") or row.get("ohlc", {}).get("close") or 0)
    except Exception:
        return 0.0


def fetch_contract_info_from_kite(symbol: str) -> dict | None:
    """Expiries/strikes/lot size from Kite NFO instrument dump."""
    nse_sym, kind = normalize_fno_symbol(symbol)
    if kind != "index":
        return None
    rows = [r for r in _load_nfo_instruments() if r.get("name") == nse_sym]
    if not rows:
        return None
    expiries: list[str] = []
    strikes: list[float] = []
    lot_size = DEFAULT_INDEX_LOT_SIZES.get(nse_sym, 1)
    for r in rows:
        exp = _parse_expiry(r.get("expiry"))
        if exp:
            expiries.append(_format_nse_expiry(exp))
        strike = r.get("strike")
        if strike is not None:
            strikes.append(float(strike))
        if r.get("lot_size"):
            lot_size = int(r["lot_size"])
    expiries = sorted(set(expiries), key=lambda x: _parse_expiry(x) or date.max)
    if not expiries:
        return None
    return {
        "expiryDates": expiries,
        "strikes": sorted(set(strikes)),
        "lotSize": lot_size,
        "source": "Kite NFO",
    }


def fetch_option_chain_from_kite(
    symbol: str,
    expiry: str | None = None,
) -> NSEOptionChain | None:
    """Nearest (or chosen) expiry chain via Kite instruments + quote API."""
    nse_sym, kind = normalize_fno_symbol(symbol)
    if kind != "index":
        return None

    rows = [
        r for r in _load_nfo_instruments()
        if r.get("name") == nse_sym and r.get("instrument_type") in ("CE", "PE")
    ]
    if not rows:
        return None

    expiry_map: dict[str, list[dict]] = {}
    for r in rows:
        exp = _parse_expiry(r.get("expiry"))
        if not exp:
            continue
        key = _format_nse_expiry(exp)
        expiry_map.setdefault(key, []).append(r)

    expiries = sorted(expiry_map.keys(), key=lambda x: _parse_expiry(x) or date.max)
    if not expiries:
        return None

    use_expiry = expiry if expiry in expiries else expiries[0]
    leg_rows = expiry_map.get(use_expiry, [])
    if not leg_rows:
        return None

    kite = _kite_client()
    if kite is None:
        return None

    keys = [f"NFO:{r['tradingsymbol']}" for r in leg_rows]
    quotes: dict = {}
    try:
        for i in range(0, len(keys), 200):
            batch = keys[i : i + 200]
            quotes.update(kite.quote(batch))
    except Exception:
        return None

    legs: list[NSEOptionLeg] = []
    strikes: list[float] = []
    total_ce_oi = total_pe_oi = total_ce_vol = total_pe_vol = 0

    for r in leg_rows:
        sym = f"NFO:{r['tradingsymbol']}"
        q = quotes.get(sym) or {}
        strike = float(r.get("strike") or 0)
        opt = str(r.get("instrument_type") or "CE")
        strikes.append(strike)
        oi = int(q.get("oi") or 0)
        vol = int(q.get("volume") or 0)
        bid, ask = _quote_bid_ask(q)
        if opt == "CE":
            total_ce_oi += oi
            total_ce_vol += vol
        else:
            total_pe_oi += oi
            total_pe_vol += vol
        legs.append(
            NSEOptionLeg(
                option_type=opt,
                strike=strike,
                expiry=use_expiry,
                ltp=float(q.get("last_price") or 0) or None,
                bid=bid,
                ask=ask,
                open_interest=oi,
                oi_change=0,
                volume=vol,
                iv=None,
                identifier=str(r.get("tradingsymbol") or ""),
            )
        )

    spot = _index_spot(nse_sym)
    pcr = total_pe_oi / total_ce_oi if total_ce_oi else None
    return NSEOptionChain(
        symbol=nse_sym,
        instrument_type="index",
        spot=spot,
        expiry=use_expiry,
        expiry_dates=expiries,
        strikes=sorted(set(strikes)),
        legs=legs,
        total_ce_oi=total_ce_oi,
        total_pe_oi=total_pe_oi,
        total_ce_volume=total_ce_vol,
        total_pe_volume=total_pe_vol,
        pcr_oi=round(pcr, 2) if pcr else None,
        source="Kite NFO",
    )
