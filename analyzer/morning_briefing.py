"""Morning briefing — session, global, macro, pulse, optional holdings."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.daily_advisor import DailyBriefing, build_daily_briefing
from analyzer.global_impact import build_india_impact_report
from analyzer.india_macro import build_india_macro_snapshot
from analyzer.intraday_data import market_session_status
from analyzer.market_pulse_scan import run_market_pulse_scan
from analyzer.market_regime import detect_nifty_regime
from analyzer.zerodha import (
    ZerodhaImportResult,
    fetch_holdings_from_kite,
    load_env_credentials,
    parse_holdings_csv,
)

IST = ZoneInfo("Asia/Kolkata")


@dataclass
class MorningBriefing:
    generated_at: str
    session_status: str
    next_session: str
    global_bias: str
    spillover_score: float
    predicted_move_pct: float
    vix_regime: str
    fii_dii_summary: str
    regime: str
    market_verdict: str
    intraday_picks: list[str] = field(default_factory=list)
    swing_picks: list[str] = field(default_factory=list)
    long_picks: list[str] = field(default_factory=list)
    holdings_briefing: DailyBriefing | None = None
    errors: list[str] = field(default_factory=list)


def _load_holdings(holdings_csv: str | None) -> ZerodhaImportResult | None:
    csv_path = holdings_csv or ""
    if not csv_path:
        import os
        csv_path = os.getenv("HOLDINGS_CSV", "")

    if csv_path and Path(csv_path).is_file():
        try:
            content = Path(csv_path).read_text(encoding="utf-8")
            imp = parse_holdings_csv(content)
            if imp.holdings:
                return imp
        except Exception:
            pass

    creds = load_env_credentials()
    if creds.get("api_key") and creds.get("access_token"):
        try:
            imp = fetch_holdings_from_kite(creds["api_key"], creds["access_token"])
            if imp.holdings:
                return imp
        except Exception:
            pass
    return None


def build_morning_briefing(
    period: str = "6mo",
    holdings_csv: str | None = None,
    use_pulse_cache: bool = True,
    include_holdings: bool = True,
) -> MorningBriefing:
    now = datetime.now(IST)
    errors: list[str] = []
    session = market_session_status()

    global_bias, spillover, move = "NEUTRAL", 0.0, 0.0
    try:
        g = build_india_impact_report()
        global_bias = g.predicted_nifty_bias
        spillover = g.spillover_score
        move = g.predicted_move_pct
    except Exception as exc:
        errors.append(f"Global: {exc}")

    vix_regime, fii = "—", "—"
    try:
        macro = build_india_macro_snapshot()
        vix_regime = macro.vix_regime
        if macro.fii_dii:
            fii = macro.fii_dii.summary.replace("**", "")
        if macro.premarket_note:
            fii = f"{fii} · {macro.premarket_note}" if fii != "—" else macro.premarket_note
    except Exception as exc:
        errors.append(f"Macro: {exc}")

    regime_s = "—"
    try:
        regime = detect_nifty_regime(period)
        regime_s = f"{regime.regime} (ADX {regime.adx:.0f})"
    except Exception as exc:
        errors.append(f"Regime: {exc}")

    pulse = None
    try:
        pulse = run_market_pulse_scan(period, "india", use_cache=use_pulse_cache)
    except Exception as exc:
        errors.append(f"Pulse: {exc}")

    market_verdict = pulse.market_verdict if pulse else "—"
    intra = [f"{p.nse_symbol} {p.action}" for p in (pulse.intraday_picks[:4] if pulse else [])]
    swing = [f"{p.nse_symbol} {p.action}" for p in (pulse.short_term_picks[:4] if pulse else [])]
    long_ = [f"{p.nse_symbol} {p.action}" for p in (pulse.long_term_picks[:4] if pulse else [])]

    holdings_brief: DailyBriefing | None = None
    if include_holdings:
        imp = _load_holdings(holdings_csv)
        if imp and imp.holdings:
            try:
                holdings_brief = build_daily_briefing(imp, period=period, include_market_picks=False)
            except Exception as exc:
                errors.append(f"Holdings: {exc}")
        elif include_holdings:
            errors.append("No holdings (set HOLDINGS_CSV or Kite token in .env)")

    return MorningBriefing(
        generated_at=now.strftime("%Y-%m-%d %H:%M IST"),
        session_status=session["status"],
        next_session=session.get("next_session", ""),
        global_bias=global_bias,
        spillover_score=spillover,
        predicted_move_pct=move,
        vix_regime=vix_regime,
        fii_dii_summary=fii,
        regime=regime_s,
        market_verdict=market_verdict.replace("**", ""),
        intraday_picks=intra,
        swing_picks=swing,
        long_picks=long_,
        holdings_briefing=holdings_brief,
        errors=errors,
    )


def format_morning_markdown(b: MorningBriefing) -> str:
    lines = [
        f"## Morning briefing — {b.generated_at}",
        f"**Session:** {b.session_status} · {b.next_session}",
        f"**Global → Nifty:** {b.global_bias} (spillover {b.spillover_score:+.0f}, move {b.predicted_move_pct:+.2f}%)",
        f"**VIX:** {b.vix_regime}",
        f"**Flows:** {b.fii_dii_summary}",
        f"**Regime:** {b.regime}",
        f"**Market:** {b.market_verdict}",
    ]
    if b.swing_picks:
        lines.append(f"**Swing:** {', '.join(b.swing_picks)}")
    if b.long_picks:
        lines.append(f"**Long-term:** {', '.join(b.long_picks)}")
    if b.intraday_picks and "OPEN" in b.session_status.upper():
        lines.append(f"**Intraday:** {', '.join(b.intraday_picks)}")
    if b.holdings_briefing:
        lines.append("")
        lines.append("### Your holdings")
        lines.append(b.holdings_briefing.summary.replace("**", ""))
        for a in b.holdings_briefing.priority_actions[:5]:
            lines.append(f"- {a.replace('**', '')}")
    if b.errors:
        lines.append("")
        lines.append("_Warnings: " + "; ".join(b.errors[:4]) + "_")
    lines.append("")
    lines.append("_Not financial advice._")
    return "\n\n".join(lines)
