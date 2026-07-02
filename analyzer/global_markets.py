"""World market indices — fetch quotes and 5-minute bars via Yahoo Finance."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

IST = ZoneInfo("Asia/Kolkata")

# symbol, display name, region, weight for spillover model
WORLD_INDICES: list[tuple[str, str, str, float]] = [
    # US — largest FII influence on India
    ("^GSPC", "S&P 500", "US", 0.28),
    ("^IXIC", "Nasdaq", "US", 0.12),
    ("^DJI", "Dow Jones", "US", 0.08),
    # Europe
    ("^FTSE", "FTSE 100", "Europe", 0.06),
    ("^GDAXI", "DAX", "Europe", 0.06),
    ("^FCHI", "CAC 40", "Europe", 0.04),
    # Asia-Pacific
    ("^N225", "Nikkei 225", "Asia", 0.08),
    ("^HSI", "Hang Seng", "Asia", 0.10),
    ("^KS11", "Kospi", "Asia", 0.05),
    ("^STI", "Singapore STI", "Asia", 0.03),
    # India
    ("^NSEI", "Nifty 50", "India", 0.0),
    ("^NSEBANK", "Bank Nifty", "India", 0.0),
    # Macro proxies
    ("CL=F", "Crude Oil WTI", "Commodity", 0.08),
    ("GC=F", "Gold", "Commodity", 0.04),
    ("INR=X", "USD/INR", "FX", 0.08),
]

INDIA_SYMBOLS = {"^NSEI", "^NSEBANK", "^BSESN"}
EXTERNAL_SYMBOLS = [t for t, _, _, _ in WORLD_INDICES if t not in INDIA_SYMBOLS]


@dataclass
class MarketQuote:
    symbol: str
    name: str
    region: str
    weight: float
    price: float
    change_1d_pct: float | None
    change_5m_pct: float | None
    session_status: str
    last_update: str


@dataclass
class GlobalMarketSnapshot:
    fetched_at: str
    quotes: list[MarketQuote] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _session_label(symbol: str) -> str:
    """Rough session status in IST."""
    now = datetime.now(IST)
    h = now.hour + now.minute / 60
    if symbol in INDIA_SYMBOLS:
        if now.weekday() >= 5:
            return "Closed"
        if 9.25 <= h <= 15.5:
            return "Open"
        return "Closed"
    if symbol in ("^GSPC", "^IXIC", "^DJI"):
        # US ~19:30–02:00 IST
        if now.weekday() < 5 and (h >= 19.5 or h <= 2.0):
            return "Open"
        return "Closed"
    if symbol in ("^N225", "^HSI", "^KS11", "^STI"):
        if now.weekday() < 5 and 5.5 <= h <= 15.5:
            return "Open"
        return "Closed"
    if symbol in ("^FTSE", "^GDAXI", "^FCHI"):
        if now.weekday() < 5 and 12.0 <= h <= 21.0:
            return "Open"
        return "Closed"
    return "—"


def _pct_change(current: float, prior: float) -> float | None:
    if prior is None or prior == 0:
        return None
    return round((current / prior - 1) * 100, 3)


def fetch_quote(symbol: str, name: str, region: str, weight: float) -> MarketQuote:
    tk = yf.Ticker(symbol)
    price = change_1d = change_5m = None

    # Daily change
    hist_d = tk.history(period="5d", interval="1d", auto_adjust=True)
    if not hist_d.empty:
        price = float(hist_d["Close"].iloc[-1])
        if len(hist_d) >= 2:
            change_1d = _pct_change(price, float(hist_d["Close"].iloc[-2]))

    # 5-minute change (last bar vs prior)
    try:
        hist_5m = tk.history(period="5d", interval="5m", auto_adjust=True)
        if len(hist_5m) >= 2:
            c = float(hist_5m["Close"].iloc[-1])
            p = float(hist_5m["Close"].iloc[-2])
            price = price or c
            change_5m = _pct_change(c, p)
    except Exception:
        pass

    if price is None:
        raise ValueError(f"No price data for {symbol}")

    return MarketQuote(
        symbol=symbol,
        name=name,
        region=region,
        weight=weight,
        price=price,
        change_1d_pct=change_1d,
        change_5m_pct=change_5m,
        session_status=_session_label(symbol),
        last_update=datetime.now(IST).strftime("%H:%M IST"),
    )


def fetch_global_snapshot() -> GlobalMarketSnapshot:
    """Pull latest quotes for all world markets."""
    quotes: list[MarketQuote] = []
    errors: list[str] = []
    for sym, name, region, weight in WORLD_INDICES:
        try:
            quotes.append(fetch_quote(sym, name, region, weight))
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    return GlobalMarketSnapshot(
        fetched_at=datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
        quotes=quotes,
        errors=errors,
    )


def fetch_daily_history(symbol: str, period: str = "6mo") -> pd.DataFrame:
    df = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=True)
    if df.empty:
        return df
    return df[["Close"]].copy()


def fetch_intraday_5m(symbol: str, period: str = "5d") -> pd.DataFrame:
    df = yf.Ticker(symbol).history(period=period, interval="5m", auto_adjust=True)
    if df.empty:
        return df
    out = df[["Close"]].copy()
    if out.index.tz is None:
        out.index = out.index.tz_localize("UTC")
    out.index = out.index.tz_convert(IST)
    return out


def build_global_heatmap_df(quotes: list[MarketQuote]) -> pd.DataFrame:
    rows = []
    for q in quotes:
        rows.append({
            "Market": q.name,
            "Region": q.region,
            "Price": q.price,
            "1D %": q.change_1d_pct,
            "5m %": q.change_5m_pct,
            "Session": q.session_status,
        })
    return pd.DataFrame(rows)
