"""Unified strategy synthesis — all signal pillars → one trade verdict."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

ACTION_SCORE = {
    "STRONG BUY": 2.0,
    "BUY": 1.0,
    "WATCH": 0.25,
    "NEUTRAL": 0.0,
    "WAIT": 0.0,
    "WEAK": -0.5,
    "AVOID": -1.0,
    "SELL": -1.0,
    "STRONG SELL": -2.0,
    "NO TRADE": -0.5,
    "TRADE_OK": 1.5,
    "CAUTION": 0.25,
    "NO_TRADE": -1.5,
}

OPTIONS_PILLAR_WEIGHTS: dict[str, float] = {
    "timing": 0.14,
    "or_gate": 0.16,
    "mtf": 0.14,
    "regime": 0.10,
    "flow": 0.12,
    "reversal": 0.10,
    "iv": 0.08,
    "macro": 0.08,
    "global": 0.08,
}

EQUITY_PILLAR_WEIGHTS: dict[str, float] = {
    "timing": 0.10,
    "mtf": 0.14,
    "intraday": 0.14,
    "short_term": 0.12,
    "regime": 0.10,
    "sector": 0.08,
    "macro": 0.08,
    "global": 0.06,
    "checklist": 0.10,
    "plan": 0.08,
}


@dataclass
class StrategyVote:
    pillar: str
    category: str
    vote: float  # -2 .. +2
    weight: float
    detail: str
    emoji: str = "⚪"


@dataclass
class StrategySynthesis:
    target: str
    asset_class: str  # equity | options
    side: str  # LONG | SHORT | CE | PE
    net_score: float = 0.0
    confidence_pct: int = 0
    verdict: str = "WAIT"
    headline: str = ""
    summary: str = ""
    pillars: list[StrategyVote] = field(default_factory=list)
    positives: list[str] = field(default_factory=list)
    negatives: list[str] = field(default_factory=list)
    trade_allowed: bool = False
    evidence_packet: object | None = None  # EvidencePacket when built
    recommendation_from_evidence: object | None = None  # RecommendationFromEvidence
    decision_artifact: object | None = None  # DecisionArtifact — canonical verdict


def _norm_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(weights.values()) or 1.0
    return {k: v / total for k, v in weights.items()}


def _score_from_action(action: str) -> float:
    return ACTION_SCORE.get(action.upper().strip(), 0.0)


def _weighted_net(votes: list[StrategyVote]) -> float:
    if not votes:
        return 0.0
    total_w = sum(v.weight for v in votes) or 1.0
    return round(sum(v.vote * v.weight for v in votes) / total_w, 3)


def _confidence_pct(net: float, votes: list[StrategyVote]) -> int:
    agree = sum(1 for v in votes if v.vote > 0.2)
    conflict = sum(1 for v in votes if v.vote < -0.2)
    base = 50 + int(net * 22)
    base += min(agree * 4, 20)
    base -= min(conflict * 6, 30)
    return max(0, min(100, base))


def _add(votes: list[StrategyVote], pillar: str, category: str, vote: float, detail: str, *, emoji: str = "⚪") -> None:
    weights = OPTIONS_PILLAR_WEIGHTS if category in OPTIONS_PILLAR_WEIGHTS else EQUITY_PILLAR_WEIGHTS
    w = weights.get(pillar, 0.08)
    votes.append(StrategyVote(pillar=pillar, category=category, vote=max(-2.0, min(2.0, vote)), weight=w, detail=detail, emoji=emoji))


def _context_votes(now: datetime | None = None, *, market: str = "india"):
    from analyzer.context_engine import build_context_snapshot

    ctx = build_context_snapshot(market=market, now=now)
    return ctx


def synthesize_options(
    fno_symbol: str,
    option_type: str,
    strike: float,
    *,
    market: str = "india",
    now: datetime | None = None,
    budget: float = 0.0,
) -> StrategySynthesis:
    """Combine OR gate, MTF, flow, regime, macro, reversal, timing → options verdict."""
    from analyzer.gift_nifty import fetch_gift_nifty_cue
    from analyzer.multi_timeframe import index_mtf, mtf_supports_option
    from analyzer.options_entry_gate import assess_option_entry_gate
    from analyzer.options_flow_snapshot import fetch_index_flow, flow_supports_option
    from analyzer.options_reversal_alerts import INDEX_YAHOO, assess_option_index_thesis
    from analyzer.opening_range_confirm import fetch_symbol_opening_range
    from analyzer.providers import get_live_ltp
    from analyzer.sideways_options_advisor import advise_from_chain

    now = now or datetime.now(IST)
    ctx = _context_votes(now, market=market)
    opt = option_type.upper()
    fno = fno_symbol.upper()
    target = f"{fno} {opt} {strike:g}"
    votes: list[StrategyVote] = []
    hard_block = False

    # --- Timing ---
    allow_entries = bool(ctx.metadata.get("allow_new_entries", False))
    prefer_exit = bool(ctx.metadata.get("prefer_exit", False))
    timing_headline = ctx.trading_restrictions[0] if ctx.trading_restrictions else ctx.market_phase
    if not allow_entries:
        _add(votes, "timing", "timing", -1.5, timing_headline, emoji="🟡")
        if "9:45" in timing_headline or "Opening" in timing_headline:
            hard_block = True
    elif prefer_exit:
        _add(votes, "timing", "timing", -1.0, timing_headline, emoji="🟠")
    else:
        _add(votes, "timing", "timing", 1.0, timing_headline, emoji="🟢")

    yahoo = INDEX_YAHOO.get(fno, "^NSEI")
    spot, _ = get_live_ltp(yahoo, market=market)
    or_rng = fetch_symbol_opening_range(yahoo, market=market)
    or_hi = or_lo = None
    if or_rng:
        or_hi, or_lo = or_rng

    # --- OR gate ---
    gate = assess_option_entry_gate(
        opt, fno_symbol=fno, strike=strike, spot=spot, or_high=or_hi, or_low=or_lo, now=now,
    )
    g_vote = 1.5 if gate.allowed else (-1.5 if gate.phase == "do_not_enter" else -0.5)
    _add(votes, "or_gate", "or_gate", g_vote, gate.headline, emoji=gate.emoji)
    if not gate.allowed and "9:45" in gate.headline:
        hard_block = True

    # --- Multi-timeframe ---
    mtf = index_mtf(fno, market=market)
    mtf_ok, mtf_detail = mtf_supports_option(opt, mtf)
    m_vote = 1.5 if mtf_ok else (-1.0 if mtf.alignment_pct < 50 else 0.0)
    _add(votes, "mtf", "mtf", m_vote, mtf_detail or mtf.summary.replace("**", ""), emoji="📊")

    # --- Regime ---
    regime_name = ctx.market_regime
    regime_adx = dict(ctx.metadata.get("regime_detail", {}) or {}).get("adx")
    if regime_name == "Range-bound":
        _add(votes, "regime", "regime", -0.8, f"Range-bound ADX {regime_adx or '—'} — chop risk", emoji="🟡")
    elif opt == "CE" and regime_name == "Trending Bullish":
        _add(votes, "regime", "regime", 1.2, f"Trending bullish ADX {regime_adx or '—'}", emoji="🟢")
    elif opt == "PE" and regime_name == "Trending Bearish":
        _add(votes, "regime", "regime", 1.2, f"Trending bearish ADX {regime_adx or '—'}", emoji="🟢")
    else:
        _add(votes, "regime", "regime", 0.0, regime_name, emoji="⚪")

    # --- Flow (PCR / OI / IV) ---
    flow = fetch_index_flow(fno)
    flow_ok, flow_detail = flow_supports_option(opt, flow)
    f_vote = 1.0 if flow_ok else -0.8
    if flow.iv_band == "expensive":
        f_vote = min(f_vote, -0.5)
    _add(votes, "flow", "flow", f_vote, flow_detail or flow.summary, emoji="📈")

    # --- Reversal thesis ---
    rev = assess_option_index_thesis(
        opt,
        fno_symbol=fno,
        strike=strike,
        spot=spot,
        or_high=or_hi or 0.0,
        or_low=or_lo or 0.0,
        now=now,
    )
    r_vote = 1.0 if rev.phase == "ok" else (-1.5 if rev.phase == "invalidated" else 0.0)
    _add(votes, "reversal", "reversal", r_vote, rev.detail[:80], emoji=rev.emoji)

    # --- IV ---
    if flow.iv_rank is not None:
        if flow.iv_band == "cheap":
            _add(votes, "iv", "iv", 0.8, f"IV rank {flow.iv_rank:.0f} — cheaper options", emoji="🟢")
        elif flow.iv_band == "expensive":
            _add(votes, "iv", "iv", -1.2, f"IV rank {flow.iv_rank:.0f} — expensive premium", emoji="🔴")
        else:
            _add(votes, "iv", "iv", 0.0, f"IV rank {flow.iv_rank:.0f} mid", emoji="⚪")

    # --- Macro / global ---
    try:
        vix_note = str(ctx.macro_state.get("vix_regime", "") or "")
        if vix_note:
            v_vote = -0.5 if "high" in vix_note.lower() else 0.3
            _add(votes, "macro", "macro", v_vote, f"VIX context: {vix_note}", emoji="🌡")
    except Exception:
        pass

    try:
        g_bias = str(ctx.global_market_state.get("bias", "NEUTRAL"))
        g_action = str(ctx.global_market_state.get("india_action", ""))
        if g_bias == "Bullish" and opt == "CE":
            _add(votes, "global", "global", 0.8, g_action[:70], emoji="🌍")
        elif g_bias == "Bearish" and opt == "PE":
            _add(votes, "global", "global", 0.8, g_action[:70], emoji="🌍")
        else:
            _add(votes, "global", "global", 0.0, g_action[:70], emoji="🌍")
    except Exception:
        pass

    gift = fetch_gift_nifty_cue()
    if gift and gift.change_1d_pct is not None:
        chg = gift.change_1d_pct
        if opt == "CE" and chg > 0.3:
            _add(votes, "global", "global", min(0.5, chg / 2), f"Gap cue +{chg:.2f}%", emoji="📈")
        elif opt == "PE" and chg < -0.3:
            _add(votes, "global", "global", min(0.5, abs(chg) / 2), f"Gap cue {chg:.2f}%", emoji="📉")

    # --- Sideways block ---
    try:
        from analyzer.nse_options import fetch_option_chain

        chain = fetch_option_chain(fno)
        side_adv = advise_from_chain(fno_symbol=fno, chain=chain)
        if side_adv.blocks_directional:
            _add(votes, "regime", "regime", -1.0, f"Sideways: {side_adv.headline[:60]}", emoji="↔️")
    except Exception:
        pass

    net = _weighted_net(votes)
    conf = _confidence_pct(net, votes)
    positives = [f"{v.emoji} {v.pillar}: {v.detail}" for v in votes if v.vote > 0.3]
    negatives = [f"{v.emoji} {v.pillar}: {v.detail}" for v in votes if v.vote < -0.3]

    return _finalize_synthesis(StrategySynthesis(
        target=target,
        asset_class="options",
        side=opt,
        net_score=net,
        confidence_pct=conf,
        verdict="WAIT",
        headline="Routing evidence through Decision Engine",
        summary=f"{len(positives)} green · {len(negatives)} red · net {net:+.2f}",
        pillars=votes,
        positives=positives,
        negatives=negatives,
        trade_allowed=False,
    ))


def _finalize_synthesis(syn: StrategySynthesis) -> StrategySynthesis:
    from analyzer.decision_engine.migration import attach_decision_to_synthesis
    from analyzer.evidence_engine.migration import attach_synthesis_evidence

    attach_synthesis_evidence(syn)
    attach_decision_to_synthesis(syn)
    return syn


def synthesize_equity(
    symbol: str,
    *,
    entry: float | None = None,
    stop_loss: float | None = None,
    target: float | None = None,
    market: str = "india",
    now: datetime | None = None,
) -> StrategySynthesis:
    """Combine MTF, horizons, regime, macro, checklist, plan → equity verdict."""
    from analyzer.chart_horizon import analyze_short_term_chart
    from analyzer.data import fetch_stock_data
    from analyzer.gift_nifty import fetch_gift_nifty_cue
    from analyzer.intraday_data import fetch_intraday
    from analyzer.intraday_trade_plan import build_intraday_trade_plan
    from analyzer.multi_timeframe import analyze_multi_timeframe
    from analyzer.candle_narrative import analyze_live_chart
    from analyzer.watchlist_pins import load_pinned_plans, sector_for_symbol
    from analyzer.watchlist_sector import sector_concentration_warning

    now = now or datetime.now(IST)
    ctx = _context_votes(now, market=market)
    sym = symbol.upper().replace(".NS", "")
    votes: list[StrategyVote] = []
    hard_block = False

    allow_entries = bool(ctx.metadata.get("allow_new_entries", False))
    timing_headline = ctx.trading_restrictions[0] if ctx.trading_restrictions else ctx.market_phase
    if not allow_entries:
        _add(votes, "timing", "timing", -1.5, timing_headline, emoji="🟡")
        if "9:45" in timing_headline or "Opening" in timing_headline:
            hard_block = True
    else:
        _add(votes, "timing", "timing", 1.0, timing_headline, emoji="🟢")

    nse = f"{sym}.NS" if not sym.endswith(".NS") else sym
    try:
        mtf = analyze_multi_timeframe(nse, market=market, label=sym)
        m_vote = _score_from_action(mtf.consensus_action)
        _add(votes, "mtf", "mtf", m_vote, mtf.summary.replace("**", ""), emoji="📊")
    except Exception as exc:
        _add(votes, "mtf", "mtf", 0.0, f"MTF unavailable: {exc}"[:50])

    try:
        df, _ = fetch_intraday(nse, "5m", market)
        if df is not None and len(df) >= 5:
            v = analyze_live_chart(df, nse, "5m")
            _add(votes, "intraday", "intraday", _score_from_action(v.action), v.summary[:80], emoji="📉")
    except Exception:
        pass

    try:
        daily, _ = fetch_stock_data(sym, period="6mo", market=market)
        if daily is not None and len(daily) >= 30:
            short = analyze_short_term_chart(daily)
            _add(votes, "short_term", "short_term", _score_from_action(short.action), short.summary[:80], emoji="📅")
    except Exception:
        pass

    regime_name = ctx.market_regime
    regime_detail = dict(ctx.metadata.get("regime_detail", {}) or {})
    allow_agg = bool(regime_detail.get("allow_aggressive_intraday", True))
    if allow_agg:
        _add(votes, "regime", "regime", 1.0, f"{regime_name} ADX {regime_detail.get('adx', '—')}", emoji="🟢")
    else:
        _add(votes, "regime", "regime", -0.6, f"{regime_name} — size down", emoji="🟡")

    pins = {p.symbol.upper(): p for p in load_pinned_plans()}
    plan = pins.get(sym)
    pins_list = list(pins.values())
    e = entry or (plan.entry if plan else None)
    sl = stop_loss or (plan.stop_loss if plan else None)
    tg = target or (plan.target if plan else None)
    if e and sl and tg:
        tp = build_intraday_trade_plan("BUY", e, sl, tg)
        p_vote = 1.2 if tp.can_enter else -1.0
        _add(votes, "plan", "plan", p_vote, tp.summary.replace("**", "")[:80], emoji="✅" if tp.can_enter else "⛔")
        if not tp.can_enter:
            hard_block = True

    sec_warn = sector_concentration_warning(pins_list) if len(pins_list) >= 2 else None
    sec_name = sector_for_symbol(sym)
    if sec_warn:
        _add(votes, "sector", "sector", -0.3, sec_warn[:70], emoji="⚠️")
    elif sec_name:
        _add(votes, "sector", "sector", 0.4, f"Sector: {sec_name}", emoji="🏭")

    try:
        g_action = str(ctx.global_market_state.get("india_action", ""))
        g_bias = str(ctx.global_market_state.get("bias", "NEUTRAL"))
        _add(votes, "global", "global", _score_from_action(g_bias.split()[0] if g_bias else "NEUTRAL") * 0.5, g_action[:70], emoji="🌍")
    except Exception:
        pass

    gift = fetch_gift_nifty_cue()
    if gift and gift.change_1d_pct and gift.change_1d_pct > 0.2:
        _add(votes, "macro", "macro", 0.5, f"Gap cue +{gift.change_1d_pct:.2f}%", emoji="📈")

    net = _weighted_net(votes)
    conf = _confidence_pct(net, votes)
    positives = [f"{v.emoji} {v.pillar}: {v.detail}" for v in votes if v.vote > 0.3]
    negatives = [f"{v.emoji} {v.pillar}: {v.detail}" for v in votes if v.vote < -0.3]

    return _finalize_synthesis(StrategySynthesis(
        target=sym,
        asset_class="equity",
        side="LONG",
        net_score=net,
        confidence_pct=conf,
        verdict="WAIT",
        headline="Routing evidence through Decision Engine",
        summary=f"{len(positives)} green · {len(negatives)} red · net {net:+.2f}",
        pillars=votes,
        positives=positives,
        negatives=negatives,
        trade_allowed=False,
    ))


def format_synthesis_terminal(syn: StrategySynthesis, *, max_pillars: int = 8) -> list[str]:
    """Compact lines for terminal board."""
    lines = [
        f"  🧠 SYNTHESIS {syn.target} │ {syn.verdict} │ confidence {syn.confidence_pct}/100 │ {syn.headline}",
    ]
    for v in syn.pillars[:max_pillars]:
        bar = "+" if v.vote > 0.2 else ("-" if v.vote < -0.2 else "~")
        lines.append(f"    {v.emoji} [{bar}] {v.pillar}: {v.detail[:72]}")
    return lines
