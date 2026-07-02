"""Options analytics — IV rank / percentile, PCR trend, OI buildup vs prior snapshots."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.earnings_calendar import CorporateEvent
from analyzer.nse_options import NSEOptionChain, NSEOptionLeg

IST = ZoneInfo("Asia/Kolkata")
HISTORY_DIR = Path(__file__).resolve().parent.parent / "data" / "cache" / "options_history"
MAX_IV_SAMPLES = 60
MIN_SAMPLES_FOR_RANK = 3


@dataclass
class OptionsAnalytics:
    symbol: str = ""
    expiry: str = ""
    atm_iv: float | None = None
    iv_rank: float | None = None
    iv_percentile: float | None = None
    iv_band: str = "unknown"  # cheap | mid | expensive | building | unknown
    iv_rank_note: str = ""
    guidance: str = ""
    signal: str = "neutral"  # bullish | bearish | neutral (for option buyers)
    flags: list[str] = field(default_factory=list)
    sample_count: int = 0
    india_vix: float | None = None
    india_vix_regime: str = ""
    pcr_oi: float | None = None
    pcr_change: float | None = None
    ce_oi_change_total: int = 0
    pe_oi_change_total: int = 0
    oi_buildup: list[dict] = field(default_factory=list)
    snapshot_time: str = ""


def _history_path(symbol: str, expiry: str) -> Path:
    safe = f"{symbol}_{expiry}".replace("/", "-").replace(" ", "_")
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    return HISTORY_DIR / f"{safe}.json"


def _atm_iv(chain: NSEOptionChain) -> float | None:
    if not chain.strikes or not chain.spot:
        return None
    atm = min(chain.strikes, key=lambda s: abs(s - chain.spot))
    for leg in chain.legs:
        if leg.strike == atm and leg.option_type == "CE" and leg.iv:
            return leg.iv
    for leg in chain.ce_legs + chain.pe_legs:
        if abs(leg.strike - atm) < 0.01 and leg.iv:
            return leg.iv
    return None


def _load_history(path: Path) -> dict:
    if not path.exists():
        return {"iv_samples": [], "last": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"iv_samples": [], "last": {}}


def _save_history(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def classify_iv_band(rank: float | None, sample_count: int) -> str:
    if sample_count < MIN_SAMPLES_FOR_RANK or rank is None:
        return "building"
    if rank >= 70:
        return "expensive"
    if rank <= 30:
        return "cheap"
    return "mid"


def _iv_rank(current_iv: float, samples: list[float]) -> tuple[float | None, str]:
    if not samples:
        return None, "Building IV history — rank available after more snapshots"
    low, high = min(samples), max(samples)
    if high - low < 0.5:
        return 50.0, "IV range tight — rank ~mid"
    rank = (current_iv - low) / (high - low) * 100
    rank = max(0.0, min(100.0, rank))
    if rank >= 70:
        note = "IV elevated — favour selling premium / cautious buying"
    elif rank <= 30:
        note = "IV low — cheaper options, breakout risk"
    else:
        note = "IV mid-range"
    return round(rank, 1), note


def _iv_percentile(current_iv: float, samples: list[float]) -> float | None:
    if not samples:
        return None
    below = sum(1 for s in samples if s < current_iv)
    return round(below / len(samples) * 100, 1)


def _buyer_signal(band: str) -> str:
    if band == "expensive":
        return "bearish"
    if band == "cheap":
        return "bullish"
    return "neutral"


def guidance_for_horizon(analytics: OptionsAnalytics, horizon: str = "all") -> str:
    """Trading guidance keyed to intraday / swing / long / options."""
    band = analytics.iv_band
    rank = analytics.iv_rank
    rank_s = f"{rank:.0f}" if rank is not None else "—"

    if band == "building":
        base = "IV rank building — revisit after a few sessions of data."
        if analytics.india_vix_regime:
            return f"{base} India VIX context: {analytics.india_vix_regime}"
        return base

    if horizon in ("intraday", "short", "options"):
        if band == "expensive":
            return (
                f"IV rank **{rank_s}** (expensive) — avoid naked CE/PE buys; "
                "prefer defined-risk spreads or wait for IV crush after events."
            )
        if band == "cheap":
            return (
                f"IV rank **{rank_s}** (cheap) — options cheaper; "
                "breakout trades can work but size small until direction confirms."
            )
        return f"IV rank **{rank_s}** — mid-range; stick to plan, avoid overpaying for OTM lottery tickets."

    if band == "expensive":
        return f"IV rank **{rank_s}** — elevated premium; long-term holders can wait for calmer IV."
    if band == "cheap":
        return f"IV rank **{rank_s}** — favourable for protective PE hedges on long equity."
    return f"IV rank **{rank_s}** — neutral for long-term equity; options timing is secondary."


def should_warn_options_entry(
    analytics: OptionsAnalytics | None,
    *,
    horizon: str = "options",
    earnings_event: CorporateEvent | None = None,
) -> bool:
    """True when option buying is especially risky (high IV and/or earnings)."""
    if not analytics or analytics.iv_band == "building":
        if earnings_event and earnings_event.days_until is not None:
            return earnings_event.days_until <= 3 and horizon in ("intraday", "short", "options")
        return False
    if horizon not in ("intraday", "short", "options", "all"):
        return False
    if analytics.iv_band == "expensive":
        return True
    if (
        earnings_event
        and earnings_event.days_until is not None
        and earnings_event.days_until <= 7
        and analytics.iv_rank is not None
        and analytics.iv_rank >= 55
    ):
        return True
    return False


def options_note_for_pick(
    analytics: OptionsAnalytics | None,
    horizon: str = "short",
) -> str:
    if not analytics or analytics.iv_rank is None:
        return ""
    if analytics.iv_band == "expensive" and horizon in ("intraday", "short"):
        return f"IV rank {analytics.iv_rank:.0f} — expensive premium; size down or use spreads."
    if analytics.iv_band == "cheap" and horizon == "long":
        return f"IV rank {analytics.iv_rank:.0f} — cheap hedges available via protective PE."
    return ""


def _india_vix_context() -> tuple[float | None, str]:
    try:
        from analyzer.india_macro import build_india_macro_snapshot

        macro = build_india_macro_snapshot()
        if macro.india_vix:
            return macro.india_vix.price, macro.vix_regime
    except Exception:
        pass
    return None, ""


def analyze_and_record_chain(chain: NSEOptionChain) -> OptionsAnalytics:
    """Compare chain to prior snapshot; append ATM IV to rolling history."""
    path = _history_path(chain.symbol, chain.expiry)
    hist = _load_history(path)
    iv_samples: list[float] = [float(x) for x in hist.get("iv_samples", [])]
    last = hist.get("last") or {}

    atm_iv = _atm_iv(chain)
    iv_rank, iv_note = (None, "IV unavailable")
    iv_percentile = None
    flags: list[str] = []

    if atm_iv is not None:
        iv_rank, iv_note = _iv_rank(atm_iv, iv_samples)
        iv_percentile = _iv_percentile(atm_iv, iv_samples)
        iv_samples.append(atm_iv)
        iv_samples = iv_samples[-MAX_IV_SAMPLES:]

    sample_count = len(iv_samples)
    band = classify_iv_band(iv_rank, sample_count)
    india_vix, vix_regime = (None, "")
    if sample_count < MIN_SAMPLES_FOR_RANK:
        india_vix, vix_regime = _india_vix_context()
        if vix_regime:
            flags.append(f"India VIX {india_vix:.1f}" if india_vix else "India VIX")
            flags.append(vix_regime)

    guidance = guidance_for_horizon(
        OptionsAnalytics(iv_band=band, iv_rank=iv_rank, india_vix_regime=vix_regime),
        horizon="options",
    )

    pcr_change = None
    if chain.pcr_oi is not None and last.get("pcr_oi") is not None:
        pcr_change = round(chain.pcr_oi - float(last["pcr_oi"]), 3)

    ce_oi_chg = sum(l.oi_change for l in chain.ce_legs)
    pe_oi_chg = sum(l.oi_change for l in chain.pe_legs)

    buildup: list[dict] = []
    for leg in sorted(chain.legs, key=lambda l: -abs(l.oi_change))[:6]:
        if abs(leg.oi_change) < 100:
            continue
        buildup.append({
            "type": leg.option_type,
            "strike": leg.strike,
            "oi_change": leg.oi_change,
            "oi": leg.open_interest,
            "iv": leg.iv,
        })

    now = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    hist["iv_samples"] = iv_samples
    hist["last"] = {
        "ts": now,
        "pcr_oi": chain.pcr_oi,
        "total_ce_oi": chain.total_ce_oi,
        "total_pe_oi": chain.total_pe_oi,
        "atm_iv": atm_iv,
        "spot": chain.spot,
    }
    _save_history(path, hist)

    return OptionsAnalytics(
        symbol=chain.symbol,
        expiry=chain.expiry,
        atm_iv=round(atm_iv, 2) if atm_iv else None,
        iv_rank=iv_rank,
        iv_percentile=iv_percentile,
        iv_band=band,
        iv_rank_note=iv_note,
        guidance=guidance,
        signal=_buyer_signal(band),
        flags=flags,
        sample_count=sample_count,
        india_vix=india_vix,
        india_vix_regime=vix_regime,
        pcr_oi=chain.pcr_oi,
        pcr_change=pcr_change,
        ce_oi_change_total=ce_oi_chg,
        pe_oi_change_total=pe_oi_chg,
        oi_buildup=buildup,
        snapshot_time=now,
    )


def build_options_analytics(nse_symbol: str) -> OptionsAnalytics | None:
    """Best-effort IV rank for an F&O symbol (equity or index)."""
    sym = nse_symbol.upper().replace(".NS", "").replace(".BO", "")
    if not sym or sym.startswith("^"):
        return None
    try:
        from analyzer.nse_options import fetch_option_chain

        chain = fetch_option_chain(sym)
        if chain:
            return analyze_and_record_chain(chain)
    except Exception:
        pass
    return None


def analytics_to_dict(a: OptionsAnalytics) -> dict:
    return {
        "symbol": a.symbol,
        "expiry": a.expiry,
        "atm_iv": a.atm_iv,
        "iv_rank": a.iv_rank,
        "iv_percentile": a.iv_percentile,
        "iv_band": a.iv_band,
        "iv_rank_note": a.iv_rank_note,
        "guidance": a.guidance,
        "signal": a.signal,
        "flags": list(a.flags),
        "sample_count": a.sample_count,
        "india_vix": a.india_vix,
        "india_vix_regime": a.india_vix_regime,
        "pcr_oi": a.pcr_oi,
        "pcr_change": a.pcr_change,
        "ce_oi_change_total": a.ce_oi_change_total,
        "pe_oi_change_total": a.pe_oi_change_total,
        "oi_buildup": list(a.oi_buildup),
        "snapshot_time": a.snapshot_time,
    }


def analytics_from_dict(d: dict) -> OptionsAnalytics:
    return OptionsAnalytics(
        symbol=d.get("symbol", ""),
        expiry=d.get("expiry", ""),
        atm_iv=d.get("atm_iv"),
        iv_rank=d.get("iv_rank"),
        iv_percentile=d.get("iv_percentile"),
        iv_band=d.get("iv_band", "unknown"),
        iv_rank_note=d.get("iv_rank_note", ""),
        guidance=d.get("guidance", ""),
        signal=d.get("signal", "neutral"),
        flags=list(d.get("flags", [])),
        sample_count=int(d.get("sample_count", 0)),
        india_vix=d.get("india_vix"),
        india_vix_regime=d.get("india_vix_regime", ""),
        pcr_oi=d.get("pcr_oi"),
        pcr_change=d.get("pcr_change"),
        ce_oi_change_total=int(d.get("ce_oi_change_total", 0)),
        pe_oi_change_total=int(d.get("pe_oi_change_total", 0)),
        oi_buildup=list(d.get("oi_buildup", [])),
        snapshot_time=d.get("snapshot_time", ""),
    )


def analytics_markdown(a: OptionsAnalytics) -> str:
    lines = []
    if a.atm_iv is not None:
        rank_s = f"**{a.iv_rank:.0f}**" if a.iv_rank is not None else "—"
        pct_s = f" · pct **{a.iv_percentile:.0f}**" if a.iv_percentile is not None else ""
        lines.append(
            f"ATM IV **{a.atm_iv:.1f}%** · IV rank {rank_s}{pct_s} ({a.iv_band}) — {a.iv_rank_note}"
        )
    if a.india_vix_regime and a.iv_band == "building":
        lines.append(f"India VIX **{a.india_vix:.1f}** — {a.india_vix_regime}")
    if a.guidance:
        lines.append(a.guidance)
    if a.pcr_change is not None:
        direction = "↑" if a.pcr_change > 0 else "↓"
        lines.append(f"PCR change vs last snapshot: {direction}{abs(a.pcr_change):.2f}")
    lines.append(
        f"Session OI Δ — CE **{a.ce_oi_change_total:+,}** · PE **{a.pe_oi_change_total:+,}**"
    )
    if a.oi_buildup:
        top = ", ".join(
            f"{b['type']} {b['strike']:g} ({b['oi_change']:+,})" for b in a.oi_buildup[:4]
        )
        lines.append(f"OI buildup: {top}")
    return "\n\n".join(lines) if lines else ""
