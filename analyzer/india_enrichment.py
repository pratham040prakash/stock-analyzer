"""India fundamentals enrichment — NSE shareholding, Screener.in ratios, extended metrics."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import requests

from analyzer.cache_utils import cached_compute
from analyzer.nse_session import is_nse_available, nse_fetch_json

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


@dataclass
class ShareholdingSnapshot:
    promoter_pct: float | None = None
    fii_pct: float | None = None
    dii_pct: float | None = None
    public_pct: float | None = None
    source: str = ""


@dataclass
class EnrichedFundamentals:
    symbol: str
    roce: float | None = None
    current_ratio: float | None = None
    interest_coverage: float | None = None
    cash_conversion_pct: float | None = None
    shareholding: ShareholdingSnapshot | None = None
    screener_roce: float | None = None
    screener_pe: float | None = None
    sources: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)


def _nse_symbol(symbol: str) -> str:
    return re.sub(r"\.(NS|BO)$", "", symbol.upper().strip())


def _from_yahoo_extended(info: dict) -> EnrichedFundamentals:
    sym = info.get("symbol", "")
    out = EnrichedFundamentals(symbol=sym)
    out.roce = info.get("returnOnCapitalEmployed") or info.get("roce")
    out.current_ratio = info.get("currentRatio")
    ebit = info.get("ebitda") or info.get("operatingIncome")
    interest = info.get("interestExpense")
    if ebit is not None and interest and abs(interest) > 1:
        out.interest_coverage = abs(ebit / interest)
        out.sources.append("Yahoo Finance")
    ni = info.get("netIncomeToCommon") or info.get("netIncome")
    fcf = info.get("freeCashflow") or info.get("free_cashflow")
    if ni and fcf and abs(ni) > 1:
        out.cash_conversion_pct = (fcf / ni) * 100
    inst = info.get("heldPercentInstitutions")
    insider = info.get("heldPercentInsiders")
    if inst is not None or insider is not None:
        out.shareholding = ShareholdingSnapshot(
            promoter_pct=insider * 100 if insider is not None else None,
            fii_pct=inst * 100 if inst is not None else None,
            source="Yahoo (institutional ≈ FII proxy)",
        )
    return out


def _fetch_nse_shareholding(nse_symbol: str) -> ShareholdingSnapshot | None:
    if not is_nse_available():
        return None
    data = nse_fetch_json(f"corporate-share-holdings?symbol={nse_symbol}")
    if not data or not isinstance(data, dict):
        return None
    # NSE returns categories in shareholding pattern
    categories = data.get("data", data.get("categories", []))
    if isinstance(categories, dict):
        categories = categories.get("data", [])
    promo = fii = dii = public = None
    for row in categories if isinstance(categories, list) else []:
        if not isinstance(row, dict):
            continue
        cat = (row.get("category") or row.get("displayName") or "").lower()
        pct = row.get("percentage") or row.get("shareholding")
        if pct is None:
            continue
        try:
            val = float(pct)
        except (TypeError, ValueError):
            continue
        if "promoter" in cat:
            promo = val
        elif "foreign" in cat or "fii" in cat:
            fii = val
        elif "domestic institutional" in cat or "dii" in cat or "mutual fund" in cat:
            dii = (dii or 0) + val
        elif "public" in cat or "retail" in cat:
            public = val
    if promo is None and fii is None:
        return None
    return ShareholdingSnapshot(
        promoter_pct=promo,
        fii_pct=fii,
        dii_pct=dii,
        public_pct=public,
        source="NSE shareholding pattern",
    )


def _fetch_screener_ratios(nse_symbol: str) -> dict[str, float]:
    """Best-effort Screener.in ratio scrape — may fail if blocked."""
    url = f"https://www.screener.in/company/{nse_symbol}/consolidated/"
    try:
        resp = requests.get(url, headers={"User-Agent": _USER_AGENT}, timeout=12)
        if resp.status_code != 200:
            return {}
        text = resp.text
        out: dict[str, float] = {}
        for label, key in (("ROCE", "roce"), ("Stock P/E", "pe"), ("Return on equity", "roe")):
            m = re.search(rf">{re.escape(label)}\s*</span>\s*<span[^>]*>([0-9.,]+)\s*%?", text)
            if m:
                try:
                    out[key] = float(m.group(1).replace(",", ""))
                except ValueError:
                    pass
        return out
    except Exception:
        return {}


def enrich_india_fundamentals(symbol: str, info: dict) -> EnrichedFundamentals:
    """Merge Yahoo + NSE + Screener.in fundamentals."""
    nse_sym = _nse_symbol(symbol)
    cache_key = f"india_fund_{nse_sym}"
    return cached_compute(cache_key, 43200, lambda: _build_enriched(nse_sym, symbol, info))


def _build_enriched(nse_sym: str, symbol: str, info: dict) -> EnrichedFundamentals:
    out = _from_yahoo_extended(info)
    if not out.sources:
        out.gaps.append("Extended Yahoo fundamentals partial or missing.")

    sh = _fetch_nse_shareholding(nse_sym)
    if sh:
        out.shareholding = sh
        out.sources.append("NSE shareholding")
    else:
        out.gaps.append("NSE shareholding pattern unavailable.")

    scr = _fetch_screener_ratios(nse_sym)
    if scr.get("roce") is not None:
        out.screener_roce = scr["roce"]
        if out.roce is None:
            out.roce = scr["roce"] / 100 if scr["roce"] > 1 else scr["roce"]
        out.sources.append("Screener.in")
    if scr.get("pe") is not None:
        out.screener_pe = scr["pe"]
    if not scr:
        out.gaps.append("Screener.in ratios unavailable (blocked or symbol not found).")

    return out


def format_enriched_markdown(enriched: EnrichedFundamentals) -> str:
    lines = ["**Extended fundamentals (FACT where sourced):**"]
    if enriched.roce is not None:
        v = enriched.roce * 100 if enriched.roce <= 1 else enriched.roce
        lines.append(f"- **ROCE:** {v:.1f}%")
    if enriched.current_ratio is not None:
        lines.append(f"- **Current ratio:** {enriched.current_ratio:.2f}")
    if enriched.interest_coverage is not None:
        lines.append(f"- **Interest coverage:** {enriched.interest_coverage:.1f}x")
    if enriched.cash_conversion_pct is not None:
        lines.append(f"- **Cash conversion (FCF/NI):** {enriched.cash_conversion_pct:.0f}%")
    sh = enriched.shareholding
    if sh:
        parts = []
        if sh.promoter_pct is not None:
            parts.append(f"Promoter {sh.promoter_pct:.1f}%")
        if sh.fii_pct is not None:
            parts.append(f"FII {sh.fii_pct:.1f}%")
        if sh.dii_pct is not None:
            parts.append(f"DII {sh.dii_pct:.1f}%")
        if parts:
            lines.append(f"- **Shareholding:** {', '.join(parts)} _({sh.source})_")
    if enriched.sources:
        lines.append(f"\n_Sources: {', '.join(dict.fromkeys(enriched.sources))}_")
    return "\n".join(lines)
