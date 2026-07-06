"""Session-aware market guidance — especially when NSE is closed."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.global_impact import IndiaImpactReport, build_india_impact_report
from analyzer.india_macro import IndiaMacroSnapshot, build_india_macro_snapshot
from analyzer.market_session import market_session_status
from analyzer.market_pulse import IndexPulse, india_market_pulse, overall_market_verdict
from analyzer.market_regime import MarketRegime, detect_nifty_regime

IST = ZoneInfo("Asia/Kolkata")


@dataclass
class PulseLiveSnapshot:
    updated_at: str
    session: dict
    indices: list[IndexPulse]
    market_verdict: str
    macro: IndiaMacroSnapshot | None
    regime: MarketRegime | None
    global_impact: IndiaImpactReport | None
    advisory_markdown: str
    focus_horizons: list[str]


def _focus_horizons(session: dict) -> list[str]:
    if session.get("is_open"):
        return ["intraday", "short", "long"]
    if session.get("phase") == "pre_market":
        return ["short", "long", "global"]
    return ["short", "long", "global"]


def build_session_advisory(
    session: dict,
    indices: list[IndexPulse],
    macro: IndiaMacroSnapshot | None,
    regime: MarketRegime | None,
    global_report: IndiaImpactReport | None,
    pulse_report=None,
) -> str:
    """Actionable guidance for the current session (open or closed)."""
    lines: list[str] = []
    phase = session.get("phase", "closed")

    if session.get("is_open"):
        lines.append(
            f"**NSE is OPEN** ({session.get('time_ist', '')}). "
            "Intraday MIS is active — square off before **3:20 PM IST**."
        )
        if global_report:
            lines.append(
                f"Global bias today: **{global_report.predicted_nifty_bias}** "
                f"({global_report.predicted_move_pct:+.2f}% spillover) — "
                f"{global_report.india_action}"
            )
        return "\n\n".join(lines)

    lines.append(
        f"**Market closed** — {session.get('status', 'Closed')}. "
        f"{session.get('next_session', '')}. "
        "Suggestions use **last close**, **global markets**, and **daily charts**."
    )

    if phase == "pre_market":
        lines.append(
            "**Pre-market plan:** Check global heatmap & Gift Nifty proxy below. "
            "Set price alerts; avoid market orders until 9:15 AM IST opening range forms."
        )
    elif phase == "weekend":
        lines.append(
            "**Weekend review:** Use swing & long-term picks to plan Monday. "
            "US/Europe moves over the weekend may gap Nifty at open."
        )
    else:
        lines.append(
            "**After hours:** US session can shift overnight bias. "
            "Watch **Global Markets** tab — focus on **delivery/swing**, not MIS."
        )

    if global_report:
        lines.append(
            f"**Bias for next Indian session:** {global_report.predicted_nifty_bias} "
            f"(spillover {global_report.spillover_score:+.0f}, "
            f"implied move {global_report.predicted_move_pct:+.2f}%). "
            f"{global_report.india_action}"
        )
        if global_report.drivers:
            lines.append("**Global drivers:** " + "; ".join(global_report.drivers[:3]))

    if macro:
        if macro.india_vix:
            lines.append(f"**India VIX:** {macro.india_vix.price:.1f} — {macro.vix_regime}")
        if macro.fii_dii:
            lines.append(f"**Flows:** {macro.fii_dii.summary}")
        if macro.premarket_note:
            lines.append(macro.premarket_note)
        if macro.sector_leader and macro.sector_laggard:
            lines.append(
                f"**Sector rotation:** {macro.sector_leader} leading · "
                f"{macro.sector_laggard} lagging"
            )

    if regime:
        lines.append(f"**Nifty regime:** {regime.regime} — {regime.message}")

    if indices:
        verdict = overall_market_verdict(indices)
        lines.append(f"**Index TA (daily):** {verdict.replace('**', '')}")

    if pulse_report:
        short_syms = [p.nse_symbol for p in getattr(pulse_report, "short_term_picks", [])[:4]]
        long_syms = [p.nse_symbol for p in getattr(pulse_report, "long_term_picks", [])[:4]]
        if short_syms:
            lines.append(f"**Swing watchlist (from scan):** {', '.join(short_syms)}")
        if long_syms:
            lines.append(f"**Long-term accumulates:** {', '.join(long_syms)}")
        if phase != "open" and not short_syms and not long_syms:
            lines.append(
                "Run **Refresh full market pulse** for swing/long ideas from the Nifty 50 scan."
            )

    lines.append(
        "_Intraday 5m charts refresh when data updates; during closed hours they show the "
        "**last session**._"
    )
    return "\n\n".join(lines)


def fetch_pulse_live_update(
    period: str = "6mo",
    pulse_report=None,
    include_global: bool = True,
) -> PulseLiveSnapshot:
    """Lightweight refresh for 30s auto-update (indices, macro, regime, global)."""
    session = market_session_status()
    indices: list[IndexPulse] = []
    macro: IndiaMacroSnapshot | None = None
    regime: MarketRegime | None = None
    global_r: IndiaImpactReport | None = None

    try:
        indices = india_market_pulse(period)
    except Exception:
        pass
    try:
        macro = build_india_macro_snapshot()
    except Exception:
        pass
    try:
        regime = detect_nifty_regime(period)
    except Exception:
        pass
    if include_global:
        try:
            global_r = build_india_impact_report()
        except Exception:
            pass

    verdict = overall_market_verdict(indices) if indices else (
        getattr(pulse_report, "market_verdict", None) or "Unable to assess market"
    )
    advisory = build_session_advisory(session, indices, macro, regime, global_r, pulse_report)

    return PulseLiveSnapshot(
        updated_at=datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
        session=session,
        indices=indices,
        market_verdict=verdict,
        macro=macro,
        regime=regime,
        global_impact=global_r,
        advisory_markdown=advisory,
        focus_horizons=_focus_horizons(session),
    )
