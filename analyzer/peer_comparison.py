"""Sector peer comparison — median P/E, ROE from Nifty peers."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median

import yfinance as yf

from analyzer.cache_utils import cached_compute
from analyzer.india import NIFTY_50


@dataclass
class PeerStat:
    symbol: str
    name: str
    pe: float | None
    roe: float | None


@dataclass
class PeerComparison:
    sector: str
    peers: list[PeerStat] = field(default_factory=list)
    median_pe: float | None = None
    median_roe: float | None = None
    target_symbol: str = ""
    target_pe: float | None = None
    target_roe: float | None = None
    pe_vs_median: str = ""
    roe_vs_median: str = ""


def _sector_peers(sector: str, exclude: str) -> list[str]:
    """Pick up to 8 Nifty 50 names in same sector via quick Yahoo sector match."""
    if not sector or sector == "N/A":
        return [s for s in NIFTY_50 if s != exclude][:6]
    peers: list[str] = []
    for sym in NIFTY_50:
        if sym == exclude:
            continue
        try:
            info = yf.Ticker(f"{sym}.NS").info
            if (info.get("sector") or "") == sector:
                peers.append(sym)
        except Exception:
            continue
        if len(peers) >= 8:
            break
    return peers or [s for s in NIFTY_50 if s != exclude][:5]


def build_peer_comparison(
    symbol: str,
    sector: str,
    *,
    target_pe: float | None = None,
    target_roe: float | None = None,
) -> PeerComparison:
    base = symbol.replace(".NS", "").replace(".BO", "").upper()
    key = f"peers_{base}_{sector}"
    return cached_compute(
        key,
        86400,
        lambda: _compute_peers(base, sector, target_pe, target_roe),
    )


def _compute_peers(
    base: str,
    sector: str,
    target_pe: float | None,
    target_roe: float | None,
) -> PeerComparison:
    peer_syms = _sector_peers(sector, base)
    stats: list[PeerStat] = []
    pes: list[float] = []
    roes: list[float] = []
    for sym in peer_syms:
        try:
            info = yf.Ticker(f"{sym}.NS").info
            pe = info.get("trailingPE")
            roe = info.get("returnOnEquity")
            if pe and pe > 0:
                pes.append(pe)
            if roe is not None:
                roes.append(roe * 100 if roe <= 1 else roe)
            stats.append(
                PeerStat(
                    sym,
                    (info.get("shortName") or sym)[:30],
                    pe,
                    roe * 100 if roe and roe <= 1 else roe,
                )
            )
        except Exception:
            continue

    med_pe = median(pes) if pes else None
    med_roe = median(roes) if roes else None
    pe_note = ""
    roe_note = ""
    if target_pe and med_pe:
        pe_note = f"{'Below' if target_pe < med_pe else 'Above'} sector median P/E ({med_pe:.1f})"
    if target_roe and med_roe:
        roe_note = f"{'Above' if target_roe > med_roe else 'Below'} sector median ROE ({med_roe:.1f}%)"

    return PeerComparison(
        sector=sector,
        peers=stats,
        median_pe=round(med_pe, 1) if med_pe else None,
        median_roe=round(med_roe, 1) if med_roe else None,
        target_symbol=base,
        target_pe=target_pe,
        target_roe=target_roe * 100 if target_roe and target_roe <= 1 else target_roe,
        pe_vs_median=pe_note,
        roe_vs_median=roe_note,
    )


def format_peer_markdown(pc: PeerComparison) -> str:
    lines = [f"**Sector peers ({pc.sector}):** median P/E **{pc.median_pe or 'N/A'}**, median ROE **{pc.median_roe or 'N/A'}%**"]
    if pc.pe_vs_median:
        lines.append(f"- P/E vs peers: {pc.pe_vs_median}")
    if pc.roe_vs_median:
        lines.append(f"- ROE vs peers: {pc.roe_vs_median}")
    if pc.peers:
        lines.append("\n| Peer | P/E | ROE |")
        lines.append("|------|-----|-----|")
        for p in pc.peers[:6]:
            lines.append(f"| {p.symbol} | {p.pe or '—'} | {p.roe or '—'} |")
    return "\n".join(lines)
