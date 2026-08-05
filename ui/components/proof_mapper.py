"""Map dashboard data → StructureProof (presentation only)."""
# APEX-012-LIFECYCLE: ACTIVE

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from analyzer.context_engine.models import ContextSnapshot
from analyzer.decision_engine.models import DecisionArtifact
from analyzer.intraday_prefs import IntradayPrefs
from analyzer.investment_os import InvestmentOS
from analyzer.markets import normalize_ticker
from analyzer.mis_trade_advisory import MisTradeAdvisory
from analyzer.providers.router import get_live_ltp
from analyzer.watchlist_pins import PinnedPlan
from ui.components.canvas_utils import VerdictCanvasState, _strip_md, _trim_words
from ui.components.morning_brief_ui import (
    load_brief_from_cache,
    market_is_rest_from_brief,
    mentor_line_from_brief,
    verdict_state_from_brief,
)
from ui.components.plan_canvas import _pick_plan_pin as plan_pick_pin
from ui.components.plan_canvas import build_trade_plan_view
from ui.components.proof_models import (
    CandleBar,
    PathAnnotation,
    PriceMarkers,
    StructureProof,
    ZoneAnnotation,
)

IST = ZoneInfo("Asia/Kolkata")

_BANNED_LABEL_RE = re.compile(
    r"\b(support|resistance|ema|rsi|macd|fibonacci|volume|trendline|bollinger)\b",
    re.I,
)

_ORIGIN_BACK: dict[str, str] = {
    "today": "Back to Today",
    "trades": "Back to Trades",
    "ask": "Back to Ask",
    "trust": "Back to Trust",
}


def _human_label(kind: str, *, symbol: str = "") -> str:
    labels = {
        "danger": "Do not buy here — price is extended",
        "supply": "Sellers consistently appeared here",
        "demand": "Previous buyers defended here",
        "reward": "This is where buyers regain control",
        "risk": "Risk corridor — protect capital below entry",
        "uncertainty": "Mixed signals — no clear control",
        "invalidation": "If price closes below here, the idea is wrong",
        "fossil_seen": "I saw: extended — called Wait",
        "fossil_outcome": "What happened: price rallied against the call",
        "fossil_learn": "What changed: tighter breakout confirmation",
        "loss_context": "Protect capital — recent sessions have been rough",
    }
    text = labels.get(kind, "Structure matters here.")
    if symbol and kind == "danger":
        return f"Do not buy here — {symbol} is extended"
    return text


def _assert_human_label(text: str) -> str:
    if _BANNED_LABEL_RE.search(text):
        return "Structure matters at this level."
    return text


def _fmt_inr(value: float) -> str:
    return f"₹{value:,.0f}"


def _price_pad(prices: list[float], *, pct: float = 0.04) -> tuple[float, float]:
    clean = [p for p in prices if p and p > 0]
    if not clean:
        return 0.0, 1.0
    lo, hi = min(clean), max(clean)
    span = max(hi - lo, hi * 0.02, 1.0)
    return lo - span * pct, hi + span * pct


def _resistance_above(entry: float, target: float, current: float) -> float:
    return max(entry, target, current) * 1.008


def _demand_below(stop: float, entry: float) -> float:
    return min(stop, entry) * 0.992


def _fetch_candles(symbol: str, market: str, *, interval: str = "15m", limit: int = 48) -> tuple[CandleBar, ...]:
    try:
        from analyzer.intraday_data import fetch_intraday

        ticker = normalize_ticker(symbol, market)
        df, _meta = fetch_intraday(ticker, interval=interval, market=market)
        if df is None or df.empty:
            return ()
        tail = df.tail(limit)
        bars: list[CandleBar] = []
        for idx, row in tail.iterrows():
            ts = idx.strftime("%Y-%m-%d %H:%M") if hasattr(idx, "strftime") else str(idx)
            bars.append(
                CandleBar(
                    time=ts,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                )
            )
        return tuple(bars)
    except Exception:
        return ()


def _current_price(symbol: str, market: str, candles: tuple[CandleBar, ...]) -> float | None:
    ticker = normalize_ticker(symbol, market)
    ltp, _src = get_live_ltp(ticker, market=market)
    if ltp is not None:
        return float(ltp)
    if candles:
        return float(candles[-1].close)
    return None


def _trade_zones(
    *,
    entry: float,
    stop: float,
    target: float,
    current: float,
) -> tuple[ZoneAnnotation, ...]:
    resist = _resistance_above(entry, target, current)
    zones = [
        ZoneAnnotation(
            "supply",
            resist * 1.004,
            resist * 0.996,
            _assert_human_label(_human_label("supply")),
        ),
        ZoneAnnotation(
            "reward",
            target,
            entry,
            _assert_human_label(_human_label("reward")),
        ),
        ZoneAnnotation(
            "risk",
            entry,
            stop,
            _assert_human_label(_human_label("risk")),
        ),
        ZoneAnnotation(
            "invalidation",
            stop,
            stop * 0.996,
            _assert_human_label(_human_label("invalidation")),
        ),
    ]
    return tuple(zones)


def _wait_zones(
    *,
    entry: float,
    stop: float,
    current: float,
    symbol: str,
) -> tuple[ZoneAnnotation, ...]:
    danger_top = max(current, entry) * 1.01
    danger_bottom = entry * 0.998
    demand_top = stop * 1.006 if stop > 0 else entry * 0.97
    demand_bottom = stop * 0.994 if stop > 0 else entry * 0.95
    return (
        ZoneAnnotation(
            "danger",
            danger_top,
            danger_bottom,
            _assert_human_label(_human_label("danger", symbol=symbol)),
        ),
        ZoneAnnotation(
            "demand",
            demand_top,
            demand_bottom,
            _assert_human_label(_human_label("demand")),
        ),
    )


def _pause_zones(*, entry: float, stop: float) -> tuple[ZoneAnnotation, ...]:
    mid = (entry + stop) / 2 if entry and stop else entry or stop or 100.0
    band = max(abs(entry - stop) * 0.6, mid * 0.01, 2.0)
    return (
        ZoneAnnotation(
            "uncertainty",
            mid + band,
            mid - band,
            _assert_human_label(_human_label("uncertainty")),
        ),
        ZoneAnnotation(
            "risk",
            mid - band,
            (stop or mid * 0.97),
            _assert_human_label(_human_label("loss_context")),
        ),
    )


def _trade_paths(entry: float, target: float, stop: float) -> tuple[PathAnnotation, ...]:
    return (
        PathAnnotation(
            "expected",
            (
                (stop, 0.1),
                (entry, 0.35),
                ((entry + target) / 2, 0.65),
                (target, 0.9),
            ),
        ),
    )


def _resolve_symbol_pin(
    os_report: InvestmentOS,
    pins: list[PinnedPlan],
    mis: MisTradeAdvisory | None = None,
) -> tuple[str, PinnedPlan | None]:
    pin = plan_pick_pin(os_report, pins)
    if pin:
        sym = pin.symbol.upper().replace(".NS", "").replace(".BO", "")
        return sym, pin
    star = (os_report.starred_symbol or "").upper().replace(".NS", "").replace(".BO", "")
    if star:
        return star, None
    if mis and mis.best_pick:
        sym = mis.best_pick.upper().replace(".NS", "").replace(".BO", "")
        if sym:
            return sym, None
    if pins:
        sym = pins[0].symbol.upper().replace(".NS", "").replace(".BO", "")
        return sym, pins[0]
    return "", None


def build_structure_proof(
    *,
    market: str,
    cached: dict[str, Any],
    proof_mode: str,
    origin: str,
    symbol: str | None = None,
    fossil_date: str | None = None,
    ask_query: str | None = None,
    ask_answer_word: str | None = None,
    miss_note: str | None = None,
) -> StructureProof:
    """Synthesize one StructureProof for the active proof mode."""
    from ui.broker.state import BrokerSnapshot, load_broker_snapshot

    from analyzer.use_cases.morning_brief import domain_from_cache_bundle
    from ui.components.canvas_utils import _snapshot_from_cache

    broker = BrokerSnapshot.from_dict(cached.get("broker")) if cached.get("broker") else load_broker_snapshot()
    brief = load_brief_from_cache(cached, broker=broker)
    state = verdict_state_from_brief(brief)
    domain = domain_from_cache_bundle(cached, broker=broker)

    snapshot = cached["snapshot"]
    if not isinstance(snapshot, ContextSnapshot):
        snapshot = _snapshot_from_cache(snapshot)
    mis: MisTradeAdvisory = cached["mis"]
    os_report: InvestmentOS = cached["os_report"]
    pins: list[PinnedPlan] = cached["pins"]
    prefs: IntradayPrefs = cached["prefs"]
    decision = domain.decision
    sym, pin = _resolve_symbol_pin(os_report, pins, mis)
    if symbol:
        sym = symbol.upper().replace(".NS", "").replace(".BO", "")

    if not sym:
        sym = "NIFTY"
        mentor = _trim_words(
            "No starred setup yet — here's how I read index structure when Today is still forming.",
            max_words=24,
        )
        action = "Star a name on Suggestions to get symbol-specific proof next."
        echo = "Index structure proof while your watchlist is empty."
        candles = _fetch_candles(sym, market)
        current = _current_price(sym, market, candles)
        entry = current or 100.0
        stop = entry * 0.985
        zones = _wait_zones(entry=entry, stop=stop, current=entry, symbol=sym)
        price_min, price_max = _price_pad([entry, stop, current or entry])
        return StructureProof(
            symbol=sym,
            verdict_state="wait",
            proof_mode=proof_mode,
            echo_line=echo,
            mentor_line=mentor,
            action_line=action,
            zones=zones,
            markers=PriceMarkers(current=current),
            price_min=price_min,
            price_max=price_max,
            candles=candles,
            primary_label=_ORIGIN_BACK.get(origin, "Back to Today"),
            origin=origin,
            blur_candles=True,
        )

    candles = _fetch_candles(sym, market)
    current = _current_price(sym, market, candles)

    entry = float(pin.entry) if pin else (current or 100.0)
    stop = float(pin.stop_loss) if pin else (entry * 0.985 if entry else 0.0)
    target = float(pin.target) if pin else (entry * 1.03 if entry else 0.0)

    verdict = state.key
    if proof_mode == "ask":
        verdict = "wait" if (ask_answer_word or "").lower() in ("wait", "pass", "tight") else "trade"
    elif proof_mode == "fossil":
        verdict = "wait"
    elif proof_mode == "trade" or (verdict == "trade" and proof_mode != "wait"):
        verdict = "trade"
    elif market_is_rest_from_brief(brief):
        verdict = "rest"

    prices = [p for p in (entry, stop, target, current or 0.0) if p and p > 0]
    price_min, price_max = _price_pad(prices)

    mentor = _trim_words(mentor_line_from_brief(brief), max_words=24)

    if proof_mode == "trade" and pin:
        plan = build_trade_plan_view(
            state=VerdictCanvasState("trade", "Trade", "See the plan", "plan"),
            pin=pin,
            decision=decision,
            mis=mis,
            snapshot=snapshot,
            prefs=prefs,
        )
        if plan and plan.has_plan:
            mentor = _trim_words(
                f"Buyers regained control above {_fmt_inr(pin.entry)} after "
                f"sellers failed repeatedly at the same level.",
                max_words=24,
            )
            action = f"Enter only above {_fmt_inr(pin.entry)} — below that, the proof invalidates."
            echo = "You decided to act — here's why."
        else:
            action = "Wait for the plan to clear before acting."
            echo = "Structure proof for today's idea."
    elif verdict == "wait" or proof_mode == "ask":
        mentor = _trim_words(
            f"{sym} is extended into seller territory — I'd wait for price to return "
            f"to where buyers last defended.",
            max_words=24,
        )
        action = "Patience is the proof — wait for price to return to defended ground."
        echo = f"You asked: {ask_query}" if ask_query else "Today says wait — here's why."
    elif verdict == "pause":
        mentor = _trim_words(
            "Mixed signals — neither buyers nor sellers have clear control. New risk isn't justified.",
            max_words=24,
        )
        action = "Standing down today is the disciplined choice — protect capital."
        echo = "Today says pause — structure is too weak."
    elif verdict == "rest":
        mentor = "Nothing deserves attention right now — rest is part of the plan."
        action = "Check back when Today builds the next stance."
        echo = "Markets are closed."
    else:
        action = "Follow the plan — structure supports today's stance."
        echo = "Here's why the AI made this call."

    zones: tuple[ZoneAnnotation, ...] = ()
    paths: tuple[PathAnnotation, ...] = ()
    blur = True
    opacity = 1.0
    fossil_badge = None
    learning_note = None

    if verdict == "trade" and pin:
        zones = _trade_zones(entry=entry, stop=stop, target=target, current=current or entry)
        paths = _trade_paths(entry, target, stop)
        blur = True
    elif verdict == "wait" or proof_mode in ("ask", "fossil"):
        zones = _wait_zones(entry=entry, stop=stop, current=current or entry, symbol=sym)
        blur = True
        if proof_mode == "fossil":
            badge_day = ""
            if fossil_date:
                try:
                    badge_day = datetime.strptime(fossil_date[:10], "%Y-%m-%d").strftime("%A")
                except ValueError:
                    badge_day = fossil_date
            fossil_badge = f"{badge_day} · frozen snapshot" if badge_day else "Frozen snapshot"
            echo = f"What I saw when I called Wait on {sym}."
            learn = _strip_md(miss_note or "") or "tightened my breakout confirmation rule"
            mentor = _trim_words(
                f"I read this as extended structure — {sym} rallied anyway. "
                f"I've since {learn.rstrip('.')}.",
                max_words=28,
            )
            action = "Misses update tomorrow's rules — that's how trust compounds."
            learning_note = learn
            zones = (
                ZoneAnnotation("fossil_seen", entry * 1.02, entry * 0.99, _human_label("fossil_seen")),
                ZoneAnnotation(
                    "fossil_outcome",
                    (current or entry) * 1.03,
                    entry,
                    _human_label("fossil_outcome"),
                ),
                ZoneAnnotation("fossil_learn", stop * 0.99, stop * 0.96, _human_label("fossil_learn")),
            )
            paths = (PathAnnotation("outcome", ((entry, 0.7), ((current or entry * 1.01), 0.95))),)
    elif verdict == "pause":
        zones = _pause_zones(entry=entry, stop=stop)
        blur = False
    elif verdict == "rest":
        opacity = 0.12
        blur = False
        zones = ()

    if prices:
        price_min, price_max = _price_pad(
            [price_min, price_max] + [z.price_top for z in zones] + [z.price_bottom for z in zones]
        )

    markers = PriceMarkers(
        entry=entry if verdict == "trade" and pin else None,
        stop=stop if pin else None,
        target=target if verdict == "trade" and pin else None,
        current=current,
    )

    return StructureProof(
        symbol=sym,
        verdict_state=verdict,
        proof_mode=proof_mode if proof_mode != "trade" else ("trade" if verdict == "trade" else proof_mode),
        echo_line=echo,
        mentor_line=mentor,
        action_line=action,
        zones=zones,
        paths=paths,
        markers=markers,
        price_min=price_min,
        price_max=price_max,
        timeframe="15m",
        fossil_date=fossil_date,
        fossil_badge=fossil_badge,
        learning_note=learning_note,
        candles=candles,
        primary_label=_ORIGIN_BACK.get(origin, "Back to Today"),
        origin=origin,
        blur_candles=blur,
        chart_opacity=opacity,
    )
