"""Morning briefing — session, global, macro, pulse, optional holdings."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from analyzer.context_engine import build_context_snapshot
from analyzer.context_engine.migration import macro_from_snapshot
from analyzer.daily_advisor import DailyBriefing, build_daily_briefing
from analyzer.market_pulse_scan import run_market_pulse_scan
from analyzer.portfolio_store import load_saved_portfolio
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
    context_snapshot_id: str = ""


def _kite_sdk_available() -> bool:
    try:
        import kiteconnect  # noqa: F401

        return True
    except ImportError:
        return False


def _load_holdings(holdings_csv: str | None) -> tuple[ZerodhaImportResult | None, str]:
    """Return holdings import and a user-facing hint when nothing could be loaded."""
    csv_path = holdings_csv or ""
    if not csv_path:
        import os

        csv_path = os.getenv("HOLDINGS_CSV", "")

    if csv_path and Path(csv_path).is_file():
        try:
            content = Path(csv_path).read_text(encoding="utf-8")
            imp = parse_holdings_csv(content)
            if imp.holdings:
                return imp, ""
            if imp.errors:
                return None, imp.errors[0]
        except Exception as exc:
            return None, f"Holdings CSV: {exc}"

    creds = load_env_credentials()
    if creds.get("api_key") and creds.get("access_token"):
        if not _kite_sdk_available():
            return None, (
                "Kite SDK missing — run with project venv: "
                f"{Path(__file__).resolve().parent.parent / '.venv/bin/python3'} "
                "scripts/morning_briefing.py (or pip install kiteconnect)"
            )
        try:
            imp = fetch_holdings_from_kite(creds["api_key"], creds["access_token"])
            if imp.holdings:
                return imp, ""
            if imp.errors:
                err = imp.errors[0]
                low = err.lower()
                if "access_token" in low or "incorrect" in low or "token" in low:
                    return None, (
                        "Kite token expired or invalid — open the app → sidebar "
                        "**Zerodha Kite** → **Login with Zerodha**"
                    )
                return None, err
        except Exception as exc:
            return None, f"Kite API: {exc}"
    elif creds.get("api_key"):
        return None, (
            "Kite login required — open the app → sidebar **Zerodha Kite** → "
            "**Login with Zerodha** (token valid until ~6 AM IST)"
        )

    try:
        imp = load_saved_portfolio()
        if imp and imp.holdings:
            return imp, ""
    except Exception as exc:
        return None, f"Saved portfolio: {exc}"

    return None, (
        "No holdings — set HOLDINGS_CSV in .env, connect Kite in the app, "
        "or save a portfolio under **My Portfolio**"
    )


def build_morning_briefing(
    period: str = "6mo",
    holdings_csv: str | None = None,
    use_pulse_cache: bool = True,
    include_holdings: bool = True,
) -> MorningBriefing:
    now = datetime.now(IST)
    ctx = build_context_snapshot(period=period, use_cache=True)
    errors: list[str] = list(dict.fromkeys(ctx.metadata.get("errors", [])))
    session = dict(ctx.market_session)
    global_state = dict(ctx.global_market_state)
    macro_view = macro_from_snapshot(ctx)

    global_bias = str(global_state.get("bias", "NEUTRAL"))
    spillover = float(global_state.get("spillover_score") or 0.0)
    move = float(global_state.get("predicted_move_pct") or 0.0)

    vix_regime = macro_view.vix_regime if macro_view else str(ctx.macro_state.get("vix_regime", "—"))
    fii = "—"
    if macro_view and macro_view.fii_dii:
        fii = macro_view.fii_dii.summary.replace("**", "")
        if macro_view.premarket_note:
            fii = f"{fii} · {macro_view.premarket_note}" if fii != "—" else macro_view.premarket_note

    regime_detail = dict(ctx.metadata.get("regime_detail", {}) or {})
    adx = regime_detail.get("adx")
    regime_s = ctx.market_regime
    if adx is not None:
        regime_s = f"{ctx.market_regime} (ADX {float(adx):.0f})"

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
        imp, holdings_hint = _load_holdings(holdings_csv)
        if imp and imp.holdings:
            try:
                holdings_brief = build_daily_briefing(imp, period=period, include_market_picks=False)
            except Exception as exc:
                errors.append(f"Holdings: {exc}")
        elif holdings_hint:
            errors.append(holdings_hint)

    return MorningBriefing(
        generated_at=now.strftime("%Y-%m-%d %H:%M IST"),
        session_status=session.get("status", "Unknown"),
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
        context_snapshot_id=ctx.snapshot_id,
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
