"""India-specific macro: VIX, sector indices, FII/DII, pre-market cues."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

import yfinance as yf

from analyzer.nse_session import nse_fetch_json, record_nse_error

IST = ZoneInfo("Asia/Kolkata")

# Yahoo symbols for India macro
INDIA_VIX_SYMBOL = "^INDIAVIX"

SECTOR_INDICES: list[tuple[str, str]] = [
    ("^NSEBANK", "Nifty Bank"),
    ("^CNXIT", "Nifty IT"),
    ("^CNXAUTO", "Nifty Auto"),
    ("^CNXPHARMA", "Nifty Pharma"),
    ("^CNXFMCG", "Nifty FMCG"),
    ("^CNXMETAL", "Nifty Metal"),
    ("^CNXREALTY", "Nifty Realty"),
    ("^CNXENERGY", "Nifty Energy"),
]


@dataclass
class MacroQuote:
    symbol: str
    name: str
    price: float
    change_1d_pct: float | None
    note: str = ""


@dataclass
class FiiDiiFlow:
    date: str
    fii_net_cr: float | None
    dii_net_cr: float | None
    fii_derivative_cr: float | None
    summary: str


@dataclass
class IndiaMacroSnapshot:
    fetched_at: str
    india_vix: MacroQuote | None
    gift_nifty_proxy: MacroQuote | None
    sectors: list[MacroQuote] = field(default_factory=list)
    fii_dii: FiiDiiFlow | None = None
    vix_regime: str = ""
    sector_leader: str = ""
    sector_laggard: str = ""
    premarket_note: str = ""
    errors: list[str] = field(default_factory=list)


def _quote_from_yahoo(symbol: str, name: str) -> MacroQuote | None:
    try:
        hist = yf.Ticker(symbol).history(period="5d", interval="1d", auto_adjust=True)
        if hist.empty:
            return None
        price = float(hist["Close"].iloc[-1])
        chg = None
        if len(hist) >= 2:
            chg = round((price / float(hist["Close"].iloc[-2]) - 1) * 100, 2)
        return MacroQuote(symbol=symbol, name=name, price=price, change_1d_pct=chg)
    except Exception:
        return None


def _vix_regime(vix: float | None) -> str:
    if vix is None:
        return "Unknown"
    if vix >= 20:
        return "High fear — options expensive, reduce leverage"
    if vix >= 15:
        return "Elevated — cautious with aggressive CE buying"
    if vix <= 12:
        return "Low fear — complacency risk; cheap hedges via PE"
    return "Normal"


def fetch_fii_dii() -> FiiDiiFlow | None:
    """FII/DII cash market flows from NSE (₹ crore)."""
    data = nse_fetch_json("fiidiiTradeReact", timeout=20)
    if not data:
        return None
    try:
        row = data[0] if isinstance(data, list) else data
        fii = _parse_flow(row.get("fii") or row.get("FII"))
        dii = _parse_flow(row.get("dii") or row.get("DII"))
        fii_deriv = _parse_flow(row.get("fiiDerivatives") or row.get("fii_derivative"))

        parts = []
        if fii is not None:
            parts.append(f"FII cash **{'bought' if fii > 0 else 'sold'} ₹{abs(fii):,.0f} Cr**")
        if dii is not None:
            parts.append(f"DII **{'bought' if dii > 0 else 'sold'} ₹{abs(dii):,.0f} Cr**")
        summary = " · ".join(parts) if parts else "FII/DII data unavailable"

        return FiiDiiFlow(
            date=str(row.get("date") or datetime.now(IST).strftime("%d-%b-%Y")),
            fii_net_cr=fii,
            dii_net_cr=dii,
            fii_derivative_cr=fii_deriv,
            summary=summary,
        )
    except Exception as exc:
        record_nse_error(f"FII/DII parse: {exc}")
        return None


def _parse_flow(val) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(str(val).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _build_india_macro_snapshot() -> IndiaMacroSnapshot:
    from analyzer.gift_nifty import fetch_gift_nifty_cue

    now = datetime.now(IST)
    errors: list[str] = []

    vix = _quote_from_yahoo(INDIA_VIX_SYMBOL, "India VIX")
    if not vix:
        errors.append("India VIX unavailable")

    gift = fetch_gift_nifty_cue()
    if not gift:
        errors.append("Gift Nifty / pre-open cue unavailable")

    sectors: list[MacroQuote] = []
    for sym, name in SECTOR_INDICES:
        q = _quote_from_yahoo(sym, name)
        if q:
            sectors.append(q)
        else:
            errors.append(f"{name} unavailable")

    fii = fetch_fii_dii()
    if not fii:
        errors.append("FII/DII flow unavailable")

    leader = laggard = ""
    if sectors:
        sorted_s = sorted(sectors, key=lambda x: x.change_1d_pct or -999, reverse=True)
        if sorted_s[0].change_1d_pct is not None:
            leader = f"{sorted_s[0].name} ({sorted_s[0].change_1d_pct:+.2f}%)"
        if sorted_s[-1].change_1d_pct is not None:
            laggard = f"{sorted_s[-1].name} ({sorted_s[-1].change_1d_pct:+.2f}%)"

    premarket = ""
    h = now.hour + now.minute / 60
    if now.weekday() < 5 and 8.0 <= h < 9.25:
        premarket = "Pre-open window — watch Gift Nifty / global cues for gap direction"
    elif vix and vix.change_1d_pct and vix.change_1d_pct > 5:
        premarket = "VIX spiking — expect wider intraday swings"

    return IndiaMacroSnapshot(
        fetched_at=now.strftime("%Y-%m-%d %H:%M IST"),
        india_vix=vix,
        gift_nifty_proxy=gift,
        sectors=sectors,
        fii_dii=fii,
        vix_regime=_vix_regime(vix.price if vix else None),
        sector_leader=leader,
        sector_laggard=laggard,
        premarket_note=premarket,
        errors=errors,
    )


def build_india_macro_snapshot() -> IndiaMacroSnapshot:
    from analyzer.cache_utils import cached_compute

    return cached_compute("india_macro_v1", 60, _build_india_macro_snapshot)
