"""NSE historical option premium OHLC (fallback when Kite NFO unavailable)."""

from __future__ import annotations

from datetime import date, datetime
from urllib.parse import urlencode


def fetch_nse_option_day_ohlc(
    trade_date: str,
    *,
    fno_symbol: str,
    strike: float,
    expiry: str,
    option_type: str,
) -> tuple[float, float, float] | None:
    """
    Session high/low/close for an index option from NSE historicalOR API.
    Returns None if NSE has no row for that contract/day.
    """
    from analyzer.nse_session import is_nse_available, nse_fetch_json

    if not is_nse_available():
        return None

    try:
        exp = datetime.strptime(expiry.strip(), "%d-%b-%Y").date()
        td = date.fromisoformat(trade_date)
    except ValueError:
        return None

    strike_s = str(int(strike)) if float(strike).is_integer() else f"{strike:g}"
    d = td.strftime("%d-%m-%Y")
    params = {
        "symbol": fno_symbol,
        "instrumentType": "OPTIDX",
        "from": d,
        "to": d,
        "year": str(td.year),
        "expiryDate": exp.strftime("%d-%m-%Y"),
        "optionType": option_type,
        "strikePrice": strike_s,
    }
    query = urlencode(params)

    for path in (f"historicalOR/foCPV?{query}", f"historical-or-options?{query}"):
        payload = nse_fetch_json(path, timeout=25)
        rows = _extract_rows(payload)
        if rows:
            return _rows_to_ohlc(rows)
    return None


def _extract_rows(payload) -> list[dict]:
    if not payload:
        return []
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        for key in ("data", "foCPV", "records"):
            block = payload.get(key)
            if isinstance(block, list):
                return [r for r in block if isinstance(r, dict)]
    return []


def _rows_to_ohlc(rows: list[dict]) -> tuple[float, float, float] | None:
    highs: list[float] = []
    lows: list[float] = []
    closes: list[float] = []

    for row in rows:
        high = _pick_float(row, "CH_TRADE_HIGH_PRICE", "FH_TRADE_HIGH_PRICE", "high")
        low = _pick_float(row, "CH_TRADE_LOW_PRICE", "FH_TRADE_LOW_PRICE", "low")
        close = _pick_float(
            row,
            "CH_CLOSING_PRICE",
            "FH_CLOSING_PRICE",
            "CH_LAST_TRADED_PRICE",
            "close",
        )
        if high is not None:
            highs.append(high)
        if low is not None:
            lows.append(low)
        if close is not None:
            closes.append(close)

    if not highs or not lows:
        return None
    return max(highs), min(lows), closes[-1] if closes else max(highs)


def _pick_float(row: dict, *keys: str) -> float | None:
    for key in keys:
        val = row.get(key)
        if val is None or val == "" or val == "-":
            continue
        try:
            return float(str(val).replace(",", ""))
        except (TypeError, ValueError):
            continue
    return None
