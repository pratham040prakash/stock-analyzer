"""Options analytics — IV rank, PCR trend, OI buildup vs prior snapshots."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.nse_options import NSEOptionChain, NSEOptionLeg

IST = ZoneInfo("Asia/Kolkata")
HISTORY_DIR = Path(__file__).resolve().parent.parent / "data" / "cache" / "options_history"
MAX_IV_SAMPLES = 60


@dataclass
class OptionsAnalytics:
    atm_iv: float | None
    iv_rank: float | None
    iv_rank_note: str
    pcr_oi: float | None
    pcr_change: float | None
    ce_oi_change_total: int
    pe_oi_change_total: int
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


def analyze_and_record_chain(chain: NSEOptionChain) -> OptionsAnalytics:
    """Compare chain to prior snapshot; append ATM IV to rolling history."""
    path = _history_path(chain.symbol, chain.expiry)
    hist = _load_history(path)
    iv_samples: list[float] = [float(x) for x in hist.get("iv_samples", [])]
    last = hist.get("last") or {}

    atm_iv = _atm_iv(chain)
    iv_rank, iv_note = (None, "IV unavailable")
    if atm_iv is not None:
        iv_rank, iv_note = _iv_rank(atm_iv, iv_samples)
        iv_samples.append(atm_iv)
        iv_samples = iv_samples[-MAX_IV_SAMPLES:]

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
        atm_iv=round(atm_iv, 2) if atm_iv else None,
        iv_rank=iv_rank,
        iv_rank_note=iv_note,
        pcr_oi=chain.pcr_oi,
        pcr_change=pcr_change,
        ce_oi_change_total=ce_oi_chg,
        pe_oi_change_total=pe_oi_chg,
        oi_buildup=buildup,
        snapshot_time=now,
    )


def analytics_markdown(a: OptionsAnalytics) -> str:
    lines = []
    if a.atm_iv is not None:
        rank_s = f"**{a.iv_rank:.0f}**" if a.iv_rank is not None else "—"
        lines.append(f"ATM IV **{a.atm_iv:.1f}%** · IV rank {rank_s} — {a.iv_rank_note}")
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
