"""Investment Operating System — seven modules, one question each."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from analyzer.intraday_prefs import IntradayPrefs, load_intraday_prefs
from analyzer.intraday_trade_plan import build_intraday_trade_plan
from analyzer.market_regime import MarketRegime
from analyzer.pulse_cache import load_pulse_cache_with_stale
from analyzer.trade_journal import load_journal_entries
from analyzer.trade_selection import load_selected_symbols
from analyzer.watchlist_learning import build_watchlist_learning_report
from analyzer.watchlist_pins import PinnedPlan, load_pinned_plans

IST = ZoneInfo("Asia/Kolkata")

MODULE_KEYS = (
    "market",
    "sector",
    "stock",
    "strategy",
    "risk",
    "execution",
    "review",
)

STATUS_OK = "ok"
STATUS_WAIT = "wait"
STATUS_WARN = "warn"
STATUS_INFO = "info"
STATUS_OFF = "off"

PULSE_CACHE_TTL = 86_400  # stale OK for overnight prep


@dataclass
class OSModule:
    key: str
    label: str
    question: str
    headline: str
    detail: str = ""
    status: str = STATUS_INFO
    confidence_pct: int | None = None


@dataclass
class InvestmentOS:
    modules: list[OSModule] = field(default_factory=list)
    verdict: str = "WAIT"
    starred_symbol: str = ""
    can_trade: bool = False
    next_step: str = ""
    goal_inr: int = 0
    max_loss_inr: int = 0
    session_status: str = ""
    built_at: str = ""
    deep: bool = False
    context_snapshot_id: str = ""

    def module(self, key: str) -> OSModule | None:
        for m in self.modules:
            if m.key == key:
                return m
        return None


def _risk_reward(entry: float, stop: float, target: float) -> float | None:
    risk = abs(entry - stop)
    reward = abs(target - entry)
    if risk <= 0:
        return None
    return round(reward / risk, 2)


def _rank_pins(pins: list[PinnedPlan]) -> list[tuple[PinnedPlan, float | None]]:
    scored: list[tuple[PinnedPlan, float | None]] = []
    for p in pins:
        rr = _risk_reward(p.entry, p.stop_loss, p.target)
        scored.append((p, rr))
    scored.sort(key=lambda x: (x[1] is not None, x[1] or 0), reverse=True)
    return scored


def _pick_starred(pins: list[PinnedPlan], ranked: list[tuple[PinnedPlan, float | None]]) -> PinnedPlan | None:
    selected = load_selected_symbols()
    if selected:
        sel = selected[0].upper().replace(".NS", "")
        for p in pins:
            if p.symbol.upper().replace(".NS", "") == sel:
                return p
    return ranked[0][0] if ranked else None


def _load_pulse(market: str, period: str):
    key = f"pulse_{period}_{market}"
    report, _fresh = load_pulse_cache_with_stale(key, PULSE_CACHE_TTL)
    return report


def _regime_favor_avoid(regime: MarketRegime | None) -> tuple[str, str]:
    if not regime:
        return "Use normal discretion", "Chasing without a plan"
    name = regime.regime
    if "Bullish" in name:
        return "ORB breakout · momentum longs", "Shorting into strength"
    if "Bearish" in name:
        return "Breakdown fades · selective shorts", "Buying dips without confirmation"
    if "Range" in name:
        return "VWAP fades · range edges", "Breakout chase in chop"
    return "Smaller size · wait for clarity", "Oversized bets"


def _infer_strategy(
    plan: PinnedPlan | None,
    *,
    market_bias: str,
    regime: MarketRegime | None,
    timing_blocked: bool,
    synthesis_verdict: str = "",
    synthesis_headline: str = "",
) -> tuple[str, str, str]:
    if timing_blocked:
        return (
            "Wait — opening range",
            "No new entries until the opening window clears.",
            STATUS_WAIT,
        )
    if synthesis_verdict and synthesis_headline:
        status = STATUS_OK if synthesis_verdict in ("STRONG_BUY", "BUY", "TRADE_OK") else STATUS_WAIT
        if synthesis_verdict in ("NO_TRADE", "AVOID"):
            status = STATUS_WARN
        return synthesis_headline[:80], f"Unified synthesis: {synthesis_verdict}", status

    if not plan:
        return "No setup", "Run tonight's scan and star one stock.", STATUS_OFF

    side = getattr(plan, "side", "LONG")
    bias = (market_bias or "NEUTRAL").upper()
    regime_name = regime.regime if regime else ""

    if side == "SHORT":
        if "Bearish" in regime_name or bias == "BEARISH":
            return "Trend breakdown short", "Aligned with bearish regime and short plan.", STATUS_OK
        return "Counter-trend short", "Short plan vs mixed regime — reduce size.", STATUS_WARN

    if "Range" in regime_name:
        return "VWAP / range reclaim", "Range-bound day — prefer mean reversion entries.", STATUS_INFO
    if "Bullish" in regime_name or bias == "BULLISH":
        return "ORB breakout / momentum", "Trend day — buy hold above opening range.", STATUS_OK
    return "Pullback to VWAP", "Neutral bias — wait for confirmation at entry.", STATUS_INFO


def _sector_rankings(
    pins: list[PinnedPlan],
    *,
    leader: str = "",
    laggard: str = "",
    macro_sectors: list | None = None,
) -> tuple[list[str], str]:
    lines: list[str] = []
    if macro_sectors:
        ranked = sorted(
            [s for s in macro_sectors if getattr(s, "change_1d_pct", None) is not None],
            key=lambda s: s.change_1d_pct,
            reverse=True,
        )
        for s in ranked[:3]:
            chg = s.change_1d_pct
            tag = " ▲ leading" if s.name == leader or leader in s.name else ""
            lines.append(f"{s.name} {chg:+.1f}%{tag}")
        if ranked:
            weak = ranked[-1]
            detail = f"Weakest: {weak.name} {weak.change_1d_pct:+.1f}%"
            if laggard:
                detail += f" · Laggard cue: {laggard}"
            return lines, detail

    sectors = [p.sector.strip() for p in pins if p.sector.strip()]
    if not sectors:
        return [], "Sector data unavailable — run scan after close."

    counts = Counter(sectors).most_common()
    for sec, n in counts[:3]:
        tail = " (watchlist tailwind)" if leader and leader.lower() in sec.lower() else ""
        lines.append(f"{sec} — {n} pick{'s' if n > 1 else ''}{tail}")
    detail = f"Leader cue: {leader}" if leader else "Ranked from tonight's watchlist sectors."
    return lines, detail


def _build_review(*, phase: str, session_date: str = "") -> OSModule:
    insights: list[str] = []
    entries = load_journal_entries(limit=5)
    if entries:
        last = entries[0]
        if last.pnl_inr is not None:
            sign = "+" if last.pnl_inr >= 0 else ""
            insights.append(f"Last session {last.symbol}: {sign}₹{last.pnl_inr:,.0f}")
        if last.mistake:
            insights.append(f"Mistake: {last.mistake[:120]}")
        if last.fix:
            insights.append(f"Fix: {last.fix[:120]}")

    learn = build_watchlist_learning_report(days=14)
    if learn.insights:
        insights.extend(i.replace("**", "") for i in learn.insights[:2])

    if phase in ("after_hours", "weekend", "holiday") and not any(
        e.trade_date == session_date for e in entries[:2]
    ):
        insights.insert(0, "Log today's Zerodha P&L before scanning — coach logs are not proof.")

    headline = insights[0] if insights else "No journal yet — log trades to unlock learning."
    detail = " · ".join(insights[1:3]) if len(insights) > 1 else "Review AI improves as you journal."
    status = STATUS_INFO if insights else STATUS_OFF
    return OSModule(
        key="review",
        label="Review AI",
        question="What did I learn from today's trades?",
        headline=headline,
        detail=detail,
        status=status,
    )


def build_investment_os(
    market: str = "india",
    *,
    period: str = "1y",
    prefs: IntradayPrefs | None = None,
    deep: bool = False,
    now: datetime | None = None,
) -> InvestmentOS:
    """Assemble all seven OS modules. Default is lightweight (cached data, no live synthesis)."""
    now = now or datetime.now(IST)
    prefs = prefs or load_intraday_prefs()

    from analyzer.context_engine import build_context_snapshot

    ctx = build_context_snapshot(market=market, now=now)
    session = dict(ctx.market_session)
    timing_blocked = not bool(ctx.metadata.get("allow_new_entries", False))
    pins = load_pinned_plans()
    ranked = _rank_pins(pins)
    star = _pick_starred(pins, ranked)
    pulse = _load_pulse(market, period)

    regime_detail = dict(ctx.metadata.get("regime_detail", {}) or {})
    regime: MarketRegime | None = None
    if regime_detail:
        regime = MarketRegime(
            symbol="^NSEI",
            adx=regime_detail.get("adx"),
            plus_di=regime_detail.get("plus_di"),
            minus_di=regime_detail.get("minus_di"),
            regime=ctx.market_regime,
            allow_aggressive_intraday=bool(regime_detail.get("allow_aggressive_intraday", True)),
            allow_aggressive_swing=bool(regime_detail.get("allow_aggressive_swing", True)),
            message=str(regime_detail.get("message", "")),
            banner=str(regime_detail.get("banner", "")),
        )
    elif pulse and pulse.regime:
        regime = pulse.regime

    market_bias = str(ctx.global_market_state.get("bias", "")) or (pulse.market_verdict if pulse else "")
    leader = str(ctx.sector_strength.get("leader", ""))
    laggard = str(ctx.sector_strength.get("laggard", ""))
    macro_sectors = None
    if pulse and pulse.macro and pulse.macro.sectors:
        macro_sectors = list(pulse.macro.sectors)

    goal_inr = round(prefs.capital * prefs.min_daily_profit_pct / 100)
    max_loss_inr = round(prefs.capital * prefs.max_risk_pct / 100)

    # --- Market AI ---
    favor, avoid = _regime_favor_avoid(regime)
    if regime:
        m_head = regime.regime
        m_detail = f"{regime.banner} · Favor: {favor} · Avoid: {avoid}"
        m_status = STATUS_OK if regime.allow_aggressive_intraday else STATUS_WARN
    elif pulse and pulse.market_verdict:
        m_head = pulse.market_verdict
        m_detail = f"Cached pulse · Favor: {favor} · Avoid: {avoid}"
        m_status = STATUS_INFO
    else:
        m_head = ctx.risk_mode
        m_detail = f"{ctx.market_regime} · {ctx.volatility_state} · Favor: {favor} · Avoid: {avoid}"
        m_status = STATUS_WAIT if ctx.risk_mode in ("RISK-OFF", "CLOSED") else STATUS_INFO

    market_mod = OSModule(
        key="market",
        label="Market AI",
        question="What's the current market regime?",
        headline=m_head,
        detail=m_detail,
        status=m_status,
    )

    # --- Sector AI ---
    sec_lines, sec_detail = _sector_rankings(
        pins, leader=leader, laggard=laggard, macro_sectors=macro_sectors
    )
    if sec_lines:
        sector_mod = OSModule(
            key="sector",
            label="Sector AI",
            question="Which sectors are strongest?",
            headline=" · ".join(sec_lines[:3]),
            detail=sec_detail,
            status=STATUS_OK,
        )
    else:
        sector_mod = OSModule(
            key="sector",
            label="Sector AI",
            question="Which sectors are strongest?",
            headline="No sector data yet",
            detail="Run tonight's scan to populate sector rankings.",
            status=STATUS_OFF,
        )

    # --- Stock AI ---
    synthesis_verdict = ""
    synthesis_headline = ""
    synthesis_conf = 0
    if star:
        rr = _risk_reward(star.entry, star.stop_loss, star.target)
        rr_txt = f"R:R {rr:.1f}×" if rr else "R:R n/a"
        sec_note = f" · {star.sector}" if star.sector else ""
        stock_mod = OSModule(
            key="stock",
            label="Stock AI",
            question="Which stocks have the best risk/reward?",
            headline=f"{star.symbol} — {rr_txt}{sec_note}",
            detail="Best ranked pick in tonight's list (⭐ = your selection).",
            status=STATUS_OK if rr and rr >= 1.5 else STATUS_WARN,
            confidence_pct=int(min(95, (rr or 0) * 40)) if rr else None,
        )
    elif ranked:
        p, rr = ranked[0]
        stock_mod = OSModule(
            key="stock",
            label="Stock AI",
            question="Which stocks have the best risk/reward?",
            headline=f"{p.symbol} — R:R {rr:.1f}×" if rr else p.symbol,
            detail="Star one stock below to confirm today's focus.",
            status=STATUS_INFO,
        )
    else:
        stock_mod = OSModule(
            key="stock",
            label="Stock AI",
            question="Which stocks have the best risk/reward?",
            headline="No picks saved",
            detail="Scan tonight's stocks after market close.",
            status=STATUS_OFF,
        )

    # --- Strategy AI (optional deep synthesis) ---
    if deep and star:
        try:
            from analyzer.strategy_synthesis import synthesize_equity

            syn = synthesize_equity(
                star.symbol,
                entry=star.entry,
                stop_loss=star.stop_loss,
                target=star.target,
                market=market,
                now=now,
            )
            synthesis_verdict = syn.verdict
            synthesis_headline = syn.headline
            synthesis_conf = syn.confidence_pct
        except Exception as exc:
            synthesis_headline = f"Synthesis unavailable: {exc}"[:80]

    strat_head, strat_detail, strat_status = _infer_strategy(
        star,
        market_bias=market_bias,
        regime=regime,
        timing_blocked=timing_blocked,
        synthesis_verdict=synthesis_verdict,
        synthesis_headline=synthesis_headline,
    )
    strategy_mod = OSModule(
        key="strategy",
        label="Strategy AI",
        question="Which strategy fits this stock today?",
        headline=strat_head,
        detail=strat_detail,
        status=strat_status,
        confidence_pct=synthesis_conf or None,
    )

    # --- Risk AI ---
    trade_plan = None
    if star:
        action = "SELL" if getattr(star, "side", "LONG") == "SHORT" else "BUY"
        trade_plan = build_intraday_trade_plan(
            action,
            star.entry,
            star.stop_loss,
            star.target,
            account_inr=prefs.capital,
            max_risk_pct=prefs.max_risk_pct,
        )
        if trade_plan.suggested_shares and trade_plan.max_loss_inr:
            r_head = f"{trade_plan.suggested_shares} shares · max loss ₹{trade_plan.max_loss_inr:,.0f}"
            r_detail = trade_plan.summary.replace("**", "")
            r_status = STATUS_OK if trade_plan.can_enter else STATUS_WARN
        else:
            r_head = "Size blocked"
            r_detail = trade_plan.skip_reason or trade_plan.summary.replace("**", "")
            r_status = STATUS_WARN
    else:
        r_head = f"Budget ₹{max_loss_inr:,} per trade ({prefs.max_risk_pct:.1f}%)"
        r_detail = "Star a stock to calculate exact quantity."
        r_status = STATUS_OFF

    risk_mod = OSModule(
        key="risk",
        label="Risk AI",
        question="How much should I buy?",
        headline=r_head,
        detail=r_detail,
        status=r_status,
    )

    # --- Execution AI ---
    if trade_plan and trade_plan.entry:
        e_head = (
            f"Entry ₹{trade_plan.entry:,.2f} · SL ₹{trade_plan.stop_loss:,.2f} · "
            f"T ₹{trade_plan.target:,.2f}"
        )
        partial = int(trade_plan.partial_exit_fraction * 100)
        e_detail = (
            f"Book {partial}% at target · trail stop to breakeven · "
            f"R:R {trade_plan.risk_reward_ratio or '—'}×"
        )
        e_status = STATUS_OK if trade_plan.can_enter else STATUS_WAIT
    elif star:
        e_head = (
            f"Entry ₹{star.entry:,.0f} · SL ₹{star.stop_loss:,.0f} · T ₹{star.target:,.0f}"
        )
        e_detail = "Set these on Kite before entry — stops are non-negotiable."
        e_status = STATUS_INFO
    else:
        e_head = "No execution plan"
        e_detail = "Complete scan + stock selection first."
        e_status = STATUS_OFF

    execution_mod = OSModule(
        key="execution",
        label="Execution AI",
        question="Where should I enter, place the stop, and take profits?",
        headline=e_head,
        detail=e_detail,
        status=e_status,
    )

    review_mod = _build_review(phase=session.get("phase", ""), session_date=session.get("date", ""))

    modules = [
        market_mod,
        sector_mod,
        stock_mod,
        strategy_mod,
        risk_mod,
        execution_mod,
        review_mod,
    ]

    session_open = bool(session.get("is_open"))
    plan_ok = trade_plan.can_enter if trade_plan else False
    synth_ok = synthesis_verdict not in ("NO_TRADE", "AVOID") if synthesis_verdict else True
    can_trade = bool(
        session_open
        and not timing_blocked
        and star
        and plan_ok
        and synth_ok
        and strategy_mod.status != STATUS_WARN
    )

    if not star:
        verdict = "PREP"
    elif not session_open:
        verdict = "CLOSED"
    else:
        verdict = "WAIT"

    next_step = _next_step(
        session,
        timing_blocked,
        star,
        verdict,
        timing_headline=ctx.trading_restrictions[0] if ctx.trading_restrictions else "",
    )

    os_result = InvestmentOS(
        modules=modules,
        verdict=verdict,
        starred_symbol=star.symbol if star else "",
        can_trade=can_trade,
        next_step=next_step,
        goal_inr=goal_inr,
        max_loss_inr=max_loss_inr,
        session_status=session.get("status", ""),
        built_at=now.strftime("%Y-%m-%d %H:%M IST"),
        deep=deep,
        context_snapshot_id=ctx.snapshot_id,
    )
    if star and session_open:
        from analyzer.decision_engine.verdict_bridge import attach_decision_to_investment_os

        attach_decision_to_investment_os(
            os_result,
            has_star=True,
            session_open=session_open,
            allow_entries=not timing_blocked,
            can_enter=bool(trade_plan and trade_plan.can_enter),
            synthesis_verdict=synthesis_verdict,
            plan_blocked=bool(trade_plan and not trade_plan.can_enter),
            prefs=prefs,
        )
        os_result.context_snapshot_id = ctx.snapshot_id
        verdict = os_result.verdict
        can_trade = os_result.can_trade
        os_result.next_step = _next_step(
            session,
            timing_blocked,
            star,
            verdict,
            timing_headline=ctx.trading_restrictions[0] if ctx.trading_restrictions else "",
        )

    return os_result


def _next_step(
    session: dict,
    timing_blocked: bool,
    star: PinnedPlan | None,
    verdict: str,
    *,
    timing_headline: str = "",
) -> str:
    phase = session.get("phase", "")
    if phase in ("weekend", "holiday"):
        return "Market closed — run scan tonight for the next session."
    if phase == "after_hours":
        return "Log P&L in Review AI, then scan for tomorrow."
    if not star:
        return "Run tonight's scan, then star one stock."
    if phase == "pre_market":
        return f"⭐ {star.symbol} selected — wait until entries are allowed."
    if verdict == "TRADE OK":
        return f"Execute ⭐ {star.symbol} on Kite — stop first, then entry."
    if timing_blocked:
        return timing_headline or "Entries blocked — wait for session timing gate."
    return "Conditions not met — read Risk and Strategy AI before trading."
