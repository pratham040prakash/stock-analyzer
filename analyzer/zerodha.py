"""Zerodha Kite symbol conversion, CSV import, and optional Kite Connect API."""

from __future__ import annotations

import csv
import io
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from analyzer.india import BSE_SCRIP_TO_NSE, _NSE_SERIES_RE

# Zerodha Kite format: NSE:RELIANCE-EQ, BSE:500325, NSE:SBIN
_KITE_PREFIX_RE = re.compile(r"^(NSE|BSE)[:\s]+", re.IGNORECASE)


@dataclass
class ZerodhaHolding:
    """One row from Zerodha holdings (CSV or Kite API)."""
    kite_symbol: str          # e.g. NSE:RELIANCE-EQ
    tradingsymbol: str        # e.g. RELIANCE
    exchange: str             # NSE | BSE
    quantity: float
    average_price: float | None = None
    last_price: float | None = None
    pnl: float | None = None
    yahoo_symbol: str = ""    # resolved e.g. RELIANCE.NS


@dataclass
class ZerodhaImportResult:
    holdings: list[ZerodhaHolding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    source: str = ""


def kite_to_yahoo(kite_symbol: str) -> str:
    """
    Convert Zerodha Kite symbol to Yahoo Finance symbol.

    Examples:
        NSE:RELIANCE-EQ  -> RELIANCE.NS
        NSE:SBIN         -> SBIN.NS
        BSE:500325       -> RELIANCE.NS (mapped) or 500325.BO
        RELIANCE         -> RELIANCE.NS (assume NSE)
    """
    raw = kite_symbol.strip().upper()
    exchange = "NSE"
    symbol = raw

    if _KITE_PREFIX_RE.match(raw):
        parts = re.split(r"[:\s]+", raw, maxsplit=1)
        exchange = parts[0].upper()
        symbol = parts[1] if len(parts) > 1 else ""

    symbol = _NSE_SERIES_RE.sub("", symbol)

    if exchange == "BSE" and re.match(r"^\d{6}$", symbol):
        nse = BSE_SCRIP_TO_NSE.get(symbol)
        if nse:
            return f"{nse}.NS"
        return f"{symbol}.BO"

    if exchange == "BSE":
        return f"{symbol}.BO"
    return f"{symbol}.NS"


def yahoo_to_kite(yahoo_symbol: str) -> str:
    """Convert Yahoo symbol to Zerodha-style display (NSE:SYMBOL-EQ)."""
    s = yahoo_symbol.strip().upper()
    if s.endswith(".NS"):
        return f"NSE:{s[:-3]}-EQ"
    if s.endswith(".BO"):
        base = s[:-3]
        if base.isdigit():
            return f"BSE:{base}"
        return f"BSE:{base}"
    return f"NSE:{s}-EQ"


def parse_kite_symbol_list(text: str) -> list[str]:
    """
    Parse pasted Zerodha symbols (comma/newline separated).
    Accepts: NSE:RELIANCE-EQ, SBIN, RELIANCE, etc.
    """
    items = text.replace("\n", ",").split(",")
    yahoo: list[str] = []
    seen: set[str] = set()
    for item in items:
        item = item.strip()
        if not item:
            continue
        y = kite_to_yahoo(item)
        if y not in seen:
            seen.add(y)
            yahoo.append(y)
    return yahoo


def _parse_float(val: str | None) -> float | None:
    if val is None or str(val).strip() in ("", "-", "NA"):
        return None
    try:
        return float(str(val).replace(",", "").strip())
    except ValueError:
        return None


def _row_get(row: dict, *keys: str) -> str:
    """Case-insensitive column lookup."""
    lower_map = {k.lower().strip(): v for k, v in row.items()}
    for key in keys:
        if key.lower() in lower_map:
            val = lower_map[key.lower()]
            return str(val).strip() if val is not None else ""
    return ""


def parse_holdings_csv(content: str) -> ZerodhaImportResult:
    """
    Parse Zerodha holdings CSV export.

    Supports Kite / Console exports with columns like:
    Symbol, Tradingsymbol, Exchange, Quantity, Average Price, LTP, P&L
    """
    result = ZerodhaImportResult(source="csv")
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        result.errors.append("CSV has no header row")
        return result

    for i, row in enumerate(reader, start=2):
        symbol_col = _row_get(row, "Symbol", "Instrument", "Trading Symbol", "tradingsymbol")
        exchange = _row_get(row, "Exchange", "exchange") or "NSE"
        tradingsymbol = _row_get(row, "Tradingsymbol", "tradingsymbol", "Trading Symbol")
        if not tradingsymbol and symbol_col:
            if ":" in symbol_col:
                parts = symbol_col.split(":", 1)
                exchange = parts[0].upper()
                tradingsymbol = _NSE_SERIES_RE.sub("", parts[1])
            else:
                tradingsymbol = symbol_col

        if not tradingsymbol:
            continue

        qty = _parse_float(_row_get(row, "Quantity", "Qty", "quantity", "Open Quantity"))
        if qty is None or qty <= 0:
            continue

        kite_sym = f"{exchange}:{tradingsymbol}"
        if not tradingsymbol.endswith("-EQ") and exchange == "NSE" and not tradingsymbol.isdigit():
            kite_sym = f"{exchange}:{tradingsymbol}-EQ"

        holding = ZerodhaHolding(
            kite_symbol=kite_sym,
            tradingsymbol=tradingsymbol.replace("-EQ", ""),
            exchange=exchange.upper(),
            quantity=qty,
            average_price=_parse_float(_row_get(row, "Average Price", "Avg Price", "average_price", "Buy Value")),
            last_price=_parse_float(_row_get(row, "LTP", "Last Price", "Close Price", "last_price")),
            pnl=_parse_float(_row_get(row, "P&L", "PnL", "pnl", "Unrealized P&L")),
            yahoo_symbol=kite_to_yahoo(kite_sym),
        )
        result.holdings.append(holding)

    if not result.holdings:
        result.errors.append(
            "No holdings found. Ensure CSV has Symbol/Tradingsymbol and Quantity columns."
        )
    return result


def _env_path() -> Path:
    return Path(__file__).resolve().parent.parent / ".env"


def _normalize_credential(value: str) -> str:
    """Strip whitespace and optional quotes from .env / form values."""
    return value.strip().strip('"').strip("'").strip()


def load_env_credentials() -> dict[str, str]:
    """Load Zerodha API credentials from environment, `.env`, or active Streamlit session."""
    try:
        from dotenv import load_dotenv

        load_dotenv(_env_path(), override=True)
    except ImportError:
        pass

    access_token = _normalize_credential(os.getenv("ZERODHA_ACCESS_TOKEN", ""))
    if not access_token:
        access_token = _access_token_from_streamlit_session()

    return {
        "api_key": _normalize_credential(os.getenv("ZERODHA_API_KEY", "")),
        "api_secret": _normalize_credential(os.getenv("ZERODHA_API_SECRET", "")),
        "access_token": access_token,
    }


def _access_token_from_streamlit_session() -> str:
    """Use in-memory token after OAuth (Streamlit Cloud cannot rely on `.env` writes)."""
    try:
        import streamlit as st

        return _normalize_credential(st.session_state.get("kite_access_token", ""))
    except Exception:
        return ""


def hydrate_kite_access_token() -> None:
    """Push session OAuth token into os.environ for this process."""
    token = _access_token_from_streamlit_session()
    if token:
        os.environ["ZERODHA_ACCESS_TOKEN"] = token


def save_access_token_to_env(access_token: str) -> None:
    """Persist access token to `.env` and activate it for the current process."""
    access_token = _normalize_credential(access_token)
    _save_env_value("ZERODHA_ACCESS_TOKEN", access_token)
    os.environ["ZERODHA_ACCESS_TOKEN"] = access_token


def save_zerodha_api_credentials_to_env(
    *,
    api_key: str | None = None,
    api_secret: str | None = None,
) -> None:
    """Persist API key/secret to .env (one-time Kite Connect app setup)."""
    from analyzer.env_loader import reload_app_env

    if api_key is not None:
        _save_env_value("ZERODHA_API_KEY", _normalize_credential(api_key))
    if api_secret is not None:
        _save_env_value("ZERODHA_API_SECRET", _normalize_credential(api_secret))
    reload_app_env()


def _save_env_value(key: str, value: str) -> None:
    env_path = _env_path()
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.environ[key] = value


def get_kite_login_url(api_key: str) -> str:
    return f"https://kite.zerodha.com/connect/login?api_key={api_key}&v=3"


def kite_app_base_url() -> str:
    """
    Public URL where Zerodha redirects after login.
    Must match the Redirect URL in your Kite Connect app (developers.kite.trade).
    """
    env_url = _normalize_credential(os.getenv("KITE_REDIRECT_URL", ""))
    if env_url:
        return env_url.rstrip("/")
    try:
        import streamlit as st

        url = getattr(st.context, "url", None) or ""
        if url.startswith("http"):
            return url.split("?")[0].rstrip("/")
    except Exception:
        pass
    return "http://127.0.0.1:8501"


def kite_runs_on_cloud() -> bool:
    """True when the app is not served from localhost (e.g. Streamlit Cloud)."""
    base = kite_app_base_url().lower()
    return not base.startswith("http://127.0.0.1") and not base.startswith("http://localhost")


def exchange_request_token(api_key: str, api_secret: str, request_token: str) -> str:
    """Exchange one-time request_token for access_token. User must save to .env."""
    try:
        from kiteconnect import KiteConnect
    except ImportError as exc:
        raise ImportError("Install kiteconnect: pip install kiteconnect") from exc

    api_key = _normalize_credential(api_key)
    api_secret = _normalize_credential(api_secret)
    request_token = _normalize_credential(request_token)
    if not api_key or not api_secret or not request_token:
        raise ValueError("API key, secret, and request token are all required.")

    kite = KiteConnect(api_key=api_key)
    data = kite.generate_session(request_token, api_secret=api_secret)
    return data["access_token"]


def _holding_from_kite_holdings_row(row: dict) -> ZerodhaHolding | None:
    qty = float(row.get("quantity", 0) or 0) + float(row.get("t1_quantity", 0) or 0)
    if qty <= 0:
        return None
    exchange = str(row.get("exchange") or "NSE").upper()
    tradingsymbol = str(row.get("tradingsymbol") or "").strip()
    if not tradingsymbol:
        return None
    kite_sym = f"{exchange}:{tradingsymbol}"
    return ZerodhaHolding(
        kite_symbol=kite_sym,
        tradingsymbol=tradingsymbol,
        exchange=exchange,
        quantity=qty,
        average_price=float(row.get("average_price") or 0) or None,
        last_price=float(row.get("last_price") or 0) or None,
        pnl=float(row.get("pnl") or 0) or None,
        yahoo_symbol=kite_to_yahoo(kite_sym),
    )


def _holding_from_cnc_position(row: dict) -> ZerodhaHolding | None:
    """Same-day CNC buys often appear in positions before T+1 holdings update."""
    product = str(row.get("product") or "").upper()
    if product != "CNC":
        return None
    qty = float(row.get("quantity") or 0)
    if qty <= 0:
        return None
    exchange = str(row.get("exchange") or "NSE").upper()
    tradingsymbol = str(row.get("tradingsymbol") or "").strip()
    if not tradingsymbol:
        return None
    kite_sym = f"{exchange}:{tradingsymbol}"
    avg = float(row.get("average_price") or row.get("buy_price") or 0) or None
    ltp = float(row.get("last_price") or 0) or None
    pnl = row.get("pnl")
    return ZerodhaHolding(
        kite_symbol=kite_sym,
        tradingsymbol=tradingsymbol,
        exchange=exchange,
        quantity=qty,
        average_price=avg,
        last_price=ltp,
        pnl=float(pnl) if pnl is not None else None,
        yahoo_symbol=kite_to_yahoo(kite_sym),
    )


def _merge_cnc_positions(kite, result: ZerodhaImportResult) -> int:
    """Add delivery (CNC) positions missing from holdings — e.g. bought today."""
    existing = {h.kite_symbol.upper() for h in result.holdings}
    added = 0
    try:
        positions = kite.positions()
    except Exception:
        return 0
    for row in positions.get("net") or []:
        holding = _holding_from_cnc_position(row)
        if not holding or holding.kite_symbol.upper() in existing:
            continue
        result.holdings.append(holding)
        existing.add(holding.kite_symbol.upper())
        added += 1
    return added


def fetch_holdings_from_kite(
    api_key: str | None = None,
    access_token: str | None = None,
) -> ZerodhaImportResult:
    """Fetch delivery equity from Kite holdings + same-day CNC positions."""
    result = ZerodhaImportResult(source="kite_api")
    creds = load_env_credentials()
    api_key = api_key or creds["api_key"]
    access_token = access_token or creds["access_token"]

    if not api_key or not access_token:
        result.errors.append(
            "Missing ZERODHA_API_KEY or ZERODHA_ACCESS_TOKEN in .env. "
            "See .env.example for setup steps."
        )
        return result

    try:
        from kiteconnect import KiteConnect
    except ImportError:
        result.errors.append("Install kiteconnect: pip install kiteconnect python-dotenv")
        return result

    try:
        kite = KiteConnect(api_key=api_key)
        kite.set_access_token(access_token)
        raw_holdings = kite.holdings()
    except Exception as exc:
        result.errors.append(f"Kite API error: {exc}")
        return result

    for row in raw_holdings:
        holding = _holding_from_kite_holdings_row(row)
        if holding:
            result.holdings.append(holding)

    same_day = _merge_cnc_positions(kite, result)

    if not result.holdings:
        result.errors.append(
            "No delivery holdings or CNC positions found in Kite. "
            "Intraday (MIS) positions are not counted as holdings."
        )
    elif same_day and not raw_holdings:
        result.notes.append(
            f"Included {same_day} same-day CNC position(s) from Kite positions "
            "(not yet in holdings after T+1 settlement)."
        )
    return result


def get_kite_client():
    """Return authenticated KiteConnect client or None."""
    hydrate_kite_access_token()
    creds = load_env_credentials()
    if not creds["api_key"] or not creds["access_token"]:
        return None
    try:
        from kiteconnect import KiteConnect
    except ImportError:
        return None
    try:
        kite = KiteConnect(api_key=creds["api_key"])
        kite.set_access_token(creds["access_token"])
        return kite
    except Exception:
        return None


def fetch_kite_profile() -> dict | None:
    """Logged-in Zerodha user profile (name, email, broker). None if not connected."""
    kite = get_kite_client()
    if kite is None:
        return None
    try:
        return kite.profile()
    except Exception:
        return None


def _position_to_kite_symbol(position: dict) -> str | None:
    ts = str(position.get("tradingsymbol") or "").strip()
    if not ts:
        return None
    exchange = str(position.get("exchange") or "NSE").upper()
    return f"{exchange}:{ts}"


def fetch_kite_activity_symbols() -> tuple[list[str], list[str]]:
    """
    Symbols the user is actively trading — open positions + recent orders.
    Kite Connect has no marketwatch API; this is the closest automated proxy.
    """
    kite = get_kite_client()
    if kite is None:
        return [], ["Kite not logged in"]

    symbols: list[str] = []
    errors: list[str] = []
    seen: set[str] = set()

    def _add(sym: str | None) -> None:
        if not sym:
            return
        key = sym.upper().strip()
        if key not in seen:
            seen.add(key)
            symbols.append(key)

    try:
        positions = kite.positions()
        for bucket in ("net", "day"):
            for row in positions.get(bucket) or []:
                qty = float(row.get("quantity") or 0)
                if qty != 0:
                    _add(_position_to_kite_symbol(row))
    except Exception as exc:
        errors.append(f"positions: {exc}")

    try:
        for order in kite.orders() or []:
            _add(_position_to_kite_symbol(order))
    except Exception as exc:
        errors.append(f"orders: {exc}")

    return symbols, errors


def fetch_kite_ltp(kite_symbols: list[str]) -> dict[str, float]:
    """Live LTP from Kite for NSE:SYMBOL-EQ keys. Returns {symbol: ltp}."""
    kite = get_kite_client()
    if not kite or not kite_symbols:
        return {}
    try:
        quotes = kite.quote(kite_symbols)
        out: dict[str, float] = {}
        for sym, q in quotes.items():
            ltp = q.get("last_price")
            if ltp:
                out[sym] = float(ltp)
        return out
    except Exception:
        return {}


def fetch_kite_margins() -> dict | None:
    """Equity margins from Kite — for position sizing."""
    kite = get_kite_client()
    if not kite:
        return None
    try:
        return kite.margins(segment="equity")
    except Exception:
        return None


def zerodha_setup_help() -> str:
    return """
### Connect your Zerodha account (Kite Connect API)

1. **Create a Kite Connect app** (one-time)
   - Go to [developers.kite.trade](https://developers.kite.trade/)
   - Sign in with your Zerodha credentials
   - Create app → note **API Key** and **API Secret**
   - Set redirect URL to your app URL (local: `http://127.0.0.1:8501`; cloud: your `*.streamlit.app` URL)

2. **Install Zerodha dependencies**
   ```bash
   pip install kiteconnect python-dotenv
   ```

3. **Create `.env`** in the project folder (copy from `.env.example`):
   ```
   ZERODHA_API_KEY=your_api_key
   ZERODHA_API_SECRET=your_api_secret
   ZERODHA_ACCESS_TOKEN=your_daily_token
   ```

4. **Get access token** (valid until ~6 AM IST next day)
   - Use the **Generate Login URL** button below
   - Log in with Zerodha → copy `request_token` from redirect URL
   - Paste it here to generate today's `access_token`
   - Add the token to `.env` as `ZERODHA_ACCESS_TOKEN`

**Without API:** Upload a holdings CSV from [Kite web](https://kite.zerodha.com) → Holdings → Download,
or paste symbols like `NSE:RELIANCE-EQ, NSE:TCS-EQ`.

> Kite Connect may require a subscription (₹500/month) for API access — check Zerodha's current pricing.
> CSV import is free and needs no API.
"""
