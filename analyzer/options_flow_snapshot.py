"""Live options flow — PCR, OI change, IV rank for index confidence."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from analyzer.nse_options import fetch_option_chain

_FLOW_CACHE: dict[str, tuple[float, "OptionsFlowSnapshot"]] = {}
FLOW_CACHE_TTL_SEC = 25.0


@dataclass
class OptionsFlowSnapshot:
    fno_symbol: str
    expiry: str = ""
    spot: float | None = None
    pcr_oi: float | None = None
    pcr_change: float | None = None
    ce_oi_change: int = 0
    pe_oi_change: int = 0
    atm_iv: float | None = None
    iv_rank: float | None = None
    iv_band: str = ""
    buyer_signal: str = "neutral"  # bullish | bearish | neutral
    oi_buildup: list[dict] = field(default_factory=list)
    summary: str = ""
    lines: list[str] = field(default_factory=list)
    error: str | None = None


def _pcr_bias(pcr: float | None, change: float | None) -> str:
    if pcr is None:
        return "neutral"
    if pcr > 1.1 or (change is not None and change > 0.05):
        return "bullish"  # more puts = supportive floor / bullish positioning context
    if pcr < 0.85 or (change is not None and change < -0.05):
        return "bearish"
    return "neutral"


def fetch_index_flow(
    fno_symbol: str,
    *,
    use_cache: bool = True,
    record_history: bool = True,
) -> OptionsFlowSnapshot:
    """PCR / OI / IV from NSE chain with short TTL cache."""
    key = fno_symbol.upper()
    if use_cache:
        cached = _FLOW_CACHE.get(key)
        if cached and time.time() - cached[0] < FLOW_CACHE_TTL_SEC:
            return cached[1]

    snap = OptionsFlowSnapshot(fno_symbol=key)
    try:
        chain = fetch_option_chain(key)
    except Exception as exc:
        snap.error = str(exc)[:100]
        snap.summary = "Flow data unavailable"
        return snap

    if record_history:
        from analyzer.options_analytics import analyze_and_record_chain

        analytics = analyze_and_record_chain(chain)
        snap.atm_iv = analytics.atm_iv
        snap.iv_rank = analytics.iv_rank
        snap.iv_band = analytics.iv_band
        snap.buyer_signal = analytics.signal
        snap.pcr_change = analytics.pcr_change
        snap.ce_oi_change = analytics.ce_oi_change_total
        snap.pe_oi_change = analytics.pe_oi_change_total
        snap.oi_buildup = list(analytics.oi_buildup[:3])
    else:
        snap.pcr_oi = chain.pcr_oi
        snap.atm_iv = None

    snap.expiry = chain.expiry or ""
    snap.spot = chain.spot
    snap.pcr_oi = chain.pcr_oi

    pcr_s = f"{snap.pcr_oi:.2f}" if snap.pcr_oi is not None else "—"
    pcr_d = ""
    if snap.pcr_change is not None:
        pcr_d = f" ({snap.pcr_change:+.2f})"
    iv_s = f"IV rank {snap.iv_rank:.0f}" if snap.iv_rank is not None else "IV building"
    oi_s = f"CE OI {snap.ce_oi_change:+,} · PE OI {snap.pe_oi_change:+,}"
    bias = _pcr_bias(snap.pcr_oi, snap.pcr_change)

    snap.lines = [
        f"PCR(OI) {pcr_s}{pcr_d} · {iv_s} · {oi_s}",
    ]
    if snap.oi_buildup:
        top = snap.oi_buildup[0]
        snap.lines.append(
            f"OI buildup: {top.get('label', '—')} "
            f"(+{top.get('oi_change', 0):,})"
        )

    snap.summary = (
        f"Flow {bias} · PCR {pcr_s}{pcr_d} · {snap.iv_band or 'IV —'}"
    )
    _FLOW_CACHE[key] = (time.time(), snap)
    return snap


def flow_supports_option(option_type: str, flow: OptionsFlowSnapshot) -> tuple[bool, str]:
    """Rough CE/PE vs PCR+IV context."""
    if flow.error:
        return False, "Flow data missing"
    opt = option_type.upper()
    bias = _pcr_bias(flow.pcr_oi, flow.pcr_change)
    if flow.iv_band == "expensive":
        return False, "IV expensive — option buying risky"
    if opt == "CE":
        ok = bias in ("bullish", "neutral") and flow.buyer_signal != "bearish"
        return ok, f"CE vs flow: {bias} PCR, IV {flow.iv_band}"
    if opt == "PE":
        ok = bias in ("bearish", "neutral") and flow.buyer_signal != "bullish"
        return ok, f"PE vs flow: {bias} PCR, IV {flow.iv_band}"
    return False, "—"
