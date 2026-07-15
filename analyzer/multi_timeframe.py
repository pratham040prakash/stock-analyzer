"""Multi-timeframe (1m / 5m / 15m) alignment for MIS confidence."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from analyzer.candle_narrative import LiveChartVerdict, analyze_live_chart
from analyzer.intraday_data import fetch_intraday

MTF_INTERVALS = ("1m", "5m", "15m")

ACTION_SCORE = {
    "STRONG BUY": 2.0,
    "BUY": 1.0,
    "WAIT": 0.0,
    "SELL": -1.0,
    "STRONG SELL": -2.0,
}

BULLISH_ACTIONS = frozenset({"STRONG BUY", "BUY"})
BEARISH_ACTIONS = frozenset({"STRONG SELL", "SELL"})

_MTF_CACHE: dict[str, tuple[float, "MultiTimeframeReport"]] = {}
MTF_CACHE_TTL_SEC = 20.0


@dataclass
class TimeframeSnapshot:
    interval: str
    action: str
    confidence: str
    score: float
    vwap: float | None
    session_bias: str
    candle_type: str
    volume_note: str
    error: str | None = None


@dataclass
class MultiTimeframeReport:
    symbol: str
    label: str
    frames: list[TimeframeSnapshot] = field(default_factory=list)
    net_score: float = 0.0
    consensus_action: str = "WAIT"
    alignment_pct: int = 0
    confidence: str = "low"  # low | medium | high
    summary: str = ""
    lines: list[str] = field(default_factory=list)


def _action_from_net(net: float) -> str:
    if net >= 1.5:
        return "STRONG BUY"
    if net >= 0.6:
        return "BUY"
    if net <= -1.5:
        return "STRONG SELL"
    if net <= -0.6:
        return "SELL"
    return "WAIT"


def _alignment_pct(frames: list[TimeframeSnapshot]) -> int:
    if not frames:
        return 0
    bulls = sum(1 for f in frames if f.action in BULLISH_ACTIONS)
    bears = sum(1 for f in frames if f.action in BEARISH_ACTIONS)
    waits = len(frames) - bulls - bears
    majority = max(bulls, bears, waits)
    return int(round(majority / len(frames) * 100))


def _confidence_label(alignment_pct: int, frames: list[TimeframeSnapshot]) -> str:
    if alignment_pct >= 67 and all(f.error is None for f in frames):
        highs = sum(1 for f in frames if f.confidence == "high")
        if highs >= 2:
            return "high"
        return "medium"
    if alignment_pct >= 50:
        return "medium"
    return "low"


def _snapshot_from_verdict(interval: str, verdict: LiveChartVerdict) -> TimeframeSnapshot:
    intra = verdict.intraday
    cur = verdict.current_candle
    return TimeframeSnapshot(
        interval=interval,
        action=verdict.action,
        confidence=verdict.confidence,
        score=verdict.directional_score,
        vwap=intra.vwap if intra else None,
        session_bias=intra.session_bias if intra else "NEUTRAL",
        candle_type=cur.candle_type if cur else "—",
        volume_note=cur.volume_note if cur else "",
    )


def analyze_timeframe(
    symbol: str,
    interval: str,
    *,
    market: str = "india",
) -> TimeframeSnapshot:
    """Single-interval live chart read."""
    try:
        df, _meta = fetch_intraday(symbol, interval=interval, market=market)
        if df is None or len(df) < 5:
            return TimeframeSnapshot(
                interval=interval,
                action="WAIT",
                confidence="low",
                score=0.0,
                vwap=None,
                session_bias="NEUTRAL",
                candle_type="—",
                volume_note="",
                error=f"Not enough {interval} bars yet",
            )
        verdict = analyze_live_chart(df, symbol, interval)
        return _snapshot_from_verdict(interval, verdict)
    except Exception as exc:
        return TimeframeSnapshot(
            interval=interval,
            action="WAIT",
            confidence="low",
            score=0.0,
            vwap=None,
            session_bias="NEUTRAL",
            candle_type="—",
            volume_note="",
            error=str(exc)[:80],
        )


def analyze_multi_timeframe(
    symbol: str,
    *,
    market: str = "india",
    label: str = "",
    use_cache: bool = True,
) -> MultiTimeframeReport:
    """1m + 5m + 15m vote — higher alignment = higher confidence."""
    cache_key = f"{market}:{symbol}"
    if use_cache:
        cached = _MTF_CACHE.get(cache_key)
        if cached and time.time() - cached[0] < MTF_CACHE_TTL_SEC:
            return cached[1]

    frames = [analyze_timeframe(symbol, iv, market=market) for iv in MTF_INTERVALS]
    scored = [ACTION_SCORE.get(f.action, 0.0) for f in frames if not f.error]
    net = round(sum(scored) / max(len(scored), 1), 2) if scored else 0.0
    consensus = _action_from_net(net)
    align = _alignment_pct(frames)
    conf = _confidence_label(align, frames)

    lines: list[str] = []
    for f in frames:
        tag = f"{f.interval}: {f.action}"
        if f.error:
            tag += f" ({f.error})"
        else:
            extras = []
            if f.candle_type and f.candle_type != "—":
                extras.append(f.candle_type)
            if f.volume_note:
                extras.append(f.volume_note[:40])
            if extras:
                tag += f" · {' · '.join(extras)}"
        lines.append(tag)

    if align >= 67:
        summary = f"MTF **{align}%** aligned → **{consensus}** ({conf} confidence)"
    elif align >= 50:
        summary = f"MTF mixed **{align}%** → lean **{consensus}** ({conf})"
    else:
        summary = f"MTF **conflict** ({align}% align) → **WAIT**"

    report = MultiTimeframeReport(
        symbol=symbol,
        label=label or symbol,
        frames=frames,
        net_score=net,
        consensus_action=consensus,
        alignment_pct=align,
        confidence=conf,
        summary=summary,
        lines=lines,
    )
    from analyzer.decision_engine.verdict_bridge import attach_decision_to_mtf_report

    attach_decision_to_mtf_report(report)
    consensus = report.consensus_action
    if align >= 67:
        summary = f"MTF **{align}%** aligned → **{consensus}** ({conf} confidence)"
    elif align >= 50:
        summary = f"MTF mixed **{align}%** → lean **{consensus}** ({conf})"
    else:
        summary = f"MTF **conflict** ({align}% align) → **{consensus}**"
    report.summary = summary
    _MTF_CACHE[cache_key] = (time.time(), report)
    return report


def mtf_supports_option(option_type: str, report: MultiTimeframeReport) -> tuple[bool, str]:
    """CE wants bullish MTF; PE wants bearish."""
    opt = option_type.upper()
    if opt == "CE":
        ok = report.consensus_action in BULLISH_ACTIONS and report.alignment_pct >= 50
        detail = (
            f"CE supported ({report.alignment_pct}% bullish MTF)"
            if ok
            else f"CE weak — MTF {report.consensus_action} ({report.alignment_pct}% align)"
        )
        return ok, detail
    if opt == "PE":
        ok = report.consensus_action in BEARISH_ACTIONS and report.alignment_pct >= 50
        detail = (
            f"PE supported ({report.alignment_pct}% bearish MTF)"
            if ok
            else f"PE weak — MTF {report.consensus_action} ({report.alignment_pct}% align)"
        )
        return ok, detail
    return False, "Unknown option type"


def index_mtf(fno_symbol: str, *, market: str = "india") -> MultiTimeframeReport:
    """MTF for NIFTY / BANKNIFTY index."""
    from analyzer.options_reversal_alerts import INDEX_LABEL, INDEX_YAHOO

    key = fno_symbol.upper()
    yahoo = INDEX_YAHOO.get(key)
    if not yahoo:
        return MultiTimeframeReport(symbol=key, label=key, summary="Unknown index")
    label = INDEX_LABEL.get(key, key)
    return analyze_multi_timeframe(yahoo, market=market, label=label)
