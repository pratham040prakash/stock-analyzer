"""MIS trade / no-trade synthesis — regime, time, gate, OTM, loss streak."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.affordable_invest import DEFAULT_MAX_OPTION_LOT_COST_INR
from analyzer.intraday_beginner_tips import OPENING_OBSERVE_UNTIL
from analyzer.options_entry_gate import assess_option_entry_gate
from analyzer.options_expiry_watchlist import build_options_expiry_watchlist
from analyzer.options_reversal_alerts import INDEX_YAHOO
from analyzer.options_trade_selection import load_selected_option
from analyzer.opening_range_confirm import fetch_symbol_opening_range
from analyzer.providers import get_live_ltp
from analyzer.trade_journal import load_journal_entries

IST = ZoneInfo("Asia/Kolkata")

# New naked MIS option entries — avoid late fade / square-off rush
LATE_ENTRY_HOUR = 14  # 2:00 PM IST
CAUTION_ENTRY_HOUR = 11
CAUTION_ENTRY_MINUTE = 30
HARD_STOP_NEW_ENTRY = (15, 10)  # 3:10 PM IST


@dataclass
class MisTradeAdvisory:
    verdict: str  # legacy: TRADE_OK | CAUTION | NO_TRADE | OBSERVE — mapped from Decision Engine
    emoji: str
    headline: str
    summary: str
    score: int  # 0–100 evidence input
    flags: list[str] = field(default_factory=list)
    positives: list[str] = field(default_factory=list)
    best_pick: str = ""
    gate_allowed: bool = False
    loss_streak_days: int = 0
    regime: str = ""
    time_note: str = ""
    mtf_alignment: int = 0
    mtf_summary: str = ""
    flow_summary: str = ""
    confidence_pct: int = 0
    synthesis_verdict: str = ""
    synthesis_confidence: int = 0
    synthesis_summary: str = ""
    synthesis_pillars: list[str] = field(default_factory=list)
    evidence_packet: object | None = None
    decision_artifact: object | None = None


def recent_loss_streak_days(*, lookback: int = 14) -> int:
    """Consecutive recent session-days with net negative P&L in trade journal."""
    by_date: dict[str, float] = {}
    for entry in load_journal_entries(limit=lookback):
        if entry.pnl_inr is None:
            continue
        by_date[entry.trade_date] = by_date.get(entry.trade_date, 0.0) + float(entry.pnl_inr)

    streak = 0
    for day in sorted(by_date.keys(), reverse=True):
        if by_date[day] < 0:
            streak += 1
        else:
            break
    return streak


def _time_flags(now: datetime, session: dict) -> tuple[list[str], list[str], str]:
    flags: list[str] = []
    positives: list[str] = []
    note = ""

    if not session.get("is_open"):
        flags.append("Market **closed** — no new MIS entries.")
        return flags, positives, note

    observe_until = now.replace(
        hour=OPENING_OBSERVE_UNTIL[0],
        minute=OPENING_OBSERVE_UNTIL[1],
        second=0,
        microsecond=0,
    )
    if now < observe_until:
        flags.append(
            f"**Before 9:45** — observe opening range only; no CE/PE entries yet."
        )
        note = "Opens after 9:45 when OR is set."
        return flags, positives, note

    hard_stop = now.replace(
        hour=HARD_STOP_NEW_ENTRY[0],
        minute=HARD_STOP_NEW_ENTRY[1],
        second=0,
        microsecond=0,
    )
    if now >= hard_stop:
        flags.append(
            "**After 3:10 PM** — too late for new MIS options; square off only."
        )
        note = "Square off all MIS by 3:20 PM IST."
        return flags, positives, note

    late_cutoff = now.replace(hour=LATE_ENTRY_HOUR, minute=0, second=0, microsecond=0)
    if now >= late_cutoff:
        flags.append(
            "**After 2:00 PM** — premium fade risk high; avoid new naked CE/PE."
        )
        note = "Late session — chop and theta hurt buyers."
    elif now.hour > CAUTION_ENTRY_HOUR or (
        now.hour == CAUTION_ENTRY_HOUR and now.minute >= CAUTION_ENTRY_MINUTE
    ):
        flags.append(
            "**After 11:30 AM** — prefer 1 lot only; moves have less time to work."
        )
        note = "Mid-session — size down."
    else:
        positives.append("Morning window — best time for OR-breakout MIS.")

    return flags, positives, note


def _best_actionable_pick(
    *,
    market: str,
    now: datetime,
) -> tuple[str, bool, str, float | None]:
    """Return label, gate_allowed, gate_headline, otm_pct for starred or top ★ pick."""
    starred = load_selected_option()
    picks = []
    if starred:
        picks.append(
            (
                starred["fno_symbol"],
                starred["option_type"],
                float(starred["strike"]),
                True,
            )
        )
    else:
        wl = build_options_expiry_watchlist(
            max_lot_cost=DEFAULT_MAX_OPTION_LOT_COST_INR,
            market=market,
        )
        for p in wl.picks:
            if p.recommended:
                picks.append((p.fno_symbol, p.option_type, p.strike, False))
        if not picks and wl.picks:
            p = wl.picks[0]
            picks.append((p.fno_symbol, p.option_type, p.strike, False))

    for fno, opt, strike, is_star in picks[:4]:
        yahoo = INDEX_YAHOO.get(fno.upper())
        if not yahoo:
            continue
        spot, _ = get_live_ltp(yahoo, market=market)
        rng = fetch_symbol_opening_range(yahoo, market=market)
        or_hi, or_lo = rng or (None, None)
        gate = assess_option_entry_gate(
            opt,
            fno_symbol=fno,
            strike=strike,
            spot=spot,
            or_high=or_hi,
            or_low=or_lo,
            now=now,
        )
        star = "⭐ " if is_star else ""
        label = f"{star}{fno} {opt} {strike:g}"
        if gate.allowed:
            return label, True, gate.headline, gate.otm_pct
        if gate.phase == "do_not_enter" and "OTM" in gate.headline.upper():
            return label, False, gate.headline, gate.otm_pct
        return label, False, gate.headline, gate.otm_pct

    return "", False, "No options pick loaded", None


def _parse_pick_label(label: str) -> tuple[str, str, float] | None:
    parts = label.replace("⭐", "").strip().split()
    if len(parts) >= 3:
        try:
            return parts[0].upper(), parts[1].upper(), float(parts[2])
        except ValueError:
            return None
    return None


def build_mis_trade_advisory(*, market: str = "india", now: datetime | None = None) -> MisTradeAdvisory:
    """One combined TRADE / CAUTION / NO TRADE read for index options MIS."""
    now = now or datetime.now(IST)
    from analyzer.context_engine import build_context_snapshot

    ctx = build_context_snapshot(market=market, now=now)
    session = dict(ctx.market_session)
    regime_detail = dict(ctx.metadata.get("regime_detail", {}) or {})
    regime_name = ctx.market_regime
    regime_adx = regime_detail.get("adx")
    flags: list[str] = []
    positives: list[str] = []

    time_flags, time_pos, time_note = _time_flags(now, session)
    flags.extend(time_flags)
    positives.extend(time_pos)

    loss_streak = recent_loss_streak_days()
    if loss_streak >= 2:
        flags.append(
            f"**{loss_streak} loss days** in journal — sit out until tomorrow's prep."
        )
    elif loss_streak == 1:
        flags.append(
            "**1 loss day** logged — max **1 lot** if gate is green; no revenge sizing."
        )

    if regime_name == "Range-bound":
        adx_s = f"{regime_adx:.0f}" if regime_adx is not None else "—"
        flags.append(
            f"**Range-bound** (ADX {adx_s}) — naked CE/PE bleed in chop; "
            "prefer 1 lot or credit spreads."
        )
    elif regime_name == "Trending Bullish":
        adx_s = f"{regime_adx:.0f}" if regime_adx is not None else "—"
        positives.append(f"Trending bullish (ADX {adx_s}) — CE setups favoured.")
    elif regime_name == "Trending Bearish":
        adx_s = f"{regime_adx:.0f}" if regime_adx is not None else "—"
        positives.append(f"Trending bearish (ADX {adx_s}) — PE setups favoured.")

    pick_label, gate_ok, gate_headline, otm = _best_actionable_pick(market=market, now=now)
    if pick_label:
        if gate_ok:
            positives.append(f"**{pick_label}** — gate 🟢 ({gate_headline}).")
        else:
            flags.append(f"**{pick_label}** — gate blocked: {gate_headline}.")
        if otm is not None and otm >= 2.0:
            flags.append(
                f"**{pick_label}** is **{otm:.1f}% OTM** — lottery strike; pick nearer ATM."
            )
    else:
        flags.append("No starred / ★ option — run **Prep all** or star one leg.")

    if loss_streak == 0 and not load_journal_entries(limit=1):
        flags.append(
            "_Tip: log losses in **Track Record → journal** to enable loss-streak alerts._"
        )

    score = 70
    score += min(len(positives) * 8, 24)
    score -= min(len(flags) * 12, 72)
    if gate_ok:
        score += 10
    if loss_streak >= 2:
        score = min(score, 25)
    if any("9:45" in f for f in flags):
        score = min(score, 15)
    if any("3:10" in f for f in flags):
        score = min(score, 10)
    if any("2:00 PM" in f for f in flags):
        score = min(score, 35)

    # Multi-timeframe + options flow confidence
    mtf_align = 0
    mtf_summary = ""
    flow_summary = ""
    fno_for_mtf = "NIFTY"
    opt_for_mtf = "CE"
    if pick_label:
        parts = pick_label.replace("⭐", "").strip().split()
        if len(parts) >= 3:
            fno_for_mtf = parts[0].upper()
            opt_for_mtf = parts[1].upper()
    try:
        from analyzer.multi_timeframe import index_mtf, mtf_supports_option
        from analyzer.options_flow_snapshot import fetch_index_flow, flow_supports_option

        mtf = index_mtf(fno_for_mtf, market=market)
        mtf_align = mtf.alignment_pct
        mtf_summary = mtf.summary
        mtf_ok, mtf_detail = mtf_supports_option(opt_for_mtf, mtf)
        if mtf_ok:
            score += 12
        elif mtf.alignment_pct < 50:
            score -= 15
            flags.append(f"MTF conflict — {mtf.consensus_action} ({mtf.alignment_pct}%)")

        flow = fetch_index_flow(fno_for_mtf)
        flow_summary = flow.summary
        flow_ok, flow_detail = flow_supports_option(opt_for_mtf, flow)
        if flow_ok:
            score += 8
        elif flow.iv_band == "expensive":
            score -= 10
            flags.append(f"IV expensive — naked CE/PE risky")
        elif not flow_ok and flow.error is None:
            score -= 5
    except Exception:
        pass

    # Unified multi-strategy synthesis (OR, MTF, flow, regime, macro, IV, reversal…)
    synthesis_verdict = ""
    synthesis_confidence = 0
    synthesis_summary = ""
    synthesis_pillars: list[str] = []
    parsed = _parse_pick_label(pick_label) if pick_label else None
    if parsed:
        fno_syn, opt_syn, strike_syn = parsed
        try:
            from analyzer.strategy_synthesis import synthesize_options

            syn = synthesize_options(
                fno_syn, opt_syn, strike_syn, market=market, now=now,
            )
            synthesis_verdict = syn.verdict
            synthesis_confidence = syn.confidence_pct
            synthesis_summary = syn.summary
            synthesis_pillars = [
                f"{v.emoji} {v.pillar}: {v.detail}" for v in syn.pillars[:10]
            ]
            score = int(round(score * 0.4 + syn.confidence_pct * 0.6))
            if syn.verdict == "NO_TRADE":
                score = min(score, 30)
            elif syn.verdict == "STRONG_BUY" and syn.trade_allowed:
                score = max(score, 72)
            elif syn.verdict == "BUY" and syn.trade_allowed:
                score = max(score, 62)
            for p in syn.positives[:3]:
                if p not in positives:
                    positives.append(p)
            for n in syn.negatives[:3]:
                if n not in flags:
                    flags.append(n)
            if not syn.trade_allowed and syn.verdict in ("NO_TRADE", "WAIT"):
                hard_block_syn = True
            else:
                hard_block_syn = False
        except Exception:
            hard_block_syn = False
    else:
        hard_block_syn = False

    score = max(0, min(100, score))
    confidence_pct = score

    hard_no = (
        hard_block_syn
        or any("9:45" in f for f in flags)
        or any("3:10" in f for f in flags)
        or loss_streak >= 2
        or (not gate_ok and any("2:00 PM" in f for f in flags))
    )

    # Build advisory shell — verdict issued only by Decision Engine
    advisory = MisTradeAdvisory(
        verdict="OBSERVE",
        emoji="⚪",
        headline="Evaluating…",
        summary="Routing evidence through Decision Engine.",
        score=score,
        flags=flags,
        positives=positives,
        best_pick=pick_label,
        gate_allowed=gate_ok,
        loss_streak_days=loss_streak,
        regime=regime_name,
        time_note=time_note,
        mtf_alignment=mtf_align,
        mtf_summary=mtf_summary,
        flow_summary=flow_summary,
        confidence_pct=confidence_pct,
        synthesis_verdict=synthesis_verdict,
        synthesis_confidence=synthesis_confidence,
        synthesis_summary=synthesis_summary,
        synthesis_pillars=synthesis_pillars,
    )

    try:
        from analyzer.decision_engine.migration import attach_decision_to_mis_advisory
        from analyzer.intraday_prefs import load_intraday_prefs

        attach_decision_to_mis_advisory(
            advisory,
            prefs=load_intraday_prefs(),
            session_open=bool(session.get("is_open")),
            pick_label=pick_label,
            context_snapshot=ctx,
        )
    except Exception:
        advisory.decision_artifact = None
        advisory.verdict = "OBSERVE"
        advisory.emoji = "⚪"
        advisory.headline = "Observe — decision unavailable"
        advisory.summary = "Decision Engine could not evaluate evidence; default to observe."

    return advisory
