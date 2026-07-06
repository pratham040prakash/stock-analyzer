"""Nifty / Bank Nifty weekly expiry CE/PE watchlist for MIS options."""

from __future__ import annotations

from dataclasses import dataclass, field

from analyzer.affordable_invest import (
    DEFAULT_MAX_OPTION_LOT_COST_INR,
    INDEX_AFFORDABLE_TARGETS,
)
from analyzer.market_pulse_scan import INDEX_FNO_SYMBOLS, scan_index_options
from analyzer.options_watchlist_learning import get_options_premium_strategy
from analyzer.trade_ladder import OptionsLadder, build_options_ladder


@dataclass
class OptionsExpiryPick:
    rank: int
    fno_symbol: str
    name: str
    expiry: str
    spot: float
    signal: str
    option_type: str  # CE | PE
    strike: float
    premium: float | None
    lot_size: int
    lot_cost: float | None
    stop_premium: float | None
    target_premium: float | None
    iv: float | None
    recommended: bool
    reason: str
    target2_premium: float | None = None
    target3_premium: float | None = None
    stop_after_t1: float | None = None
    stop_after_t2: float | None = None
    stop_after_t3: float | None = None
    ce_reference: str = ""
    pe_reference: str = ""
    error: str | None = None


@dataclass
class OptionsExpiryWatchlist:
    picks: list[OptionsExpiryPick] = field(default_factory=list)
    routine_note: str = ""
    nse_available: bool = True
    errors: list[str] = field(default_factory=list)


def _premium_plan(premium: float | None) -> tuple[float | None, float | None, OptionsLadder | None]:
    """Intraday premium stop/target ladder from learned strategy multipliers."""
    if premium is None or premium <= 0:
        return None, None, None
    strat = get_options_premium_strategy()
    stop_mult = float(strat["stop_mult"])
    target_mult = float(strat["target_mult"])
    ladder = build_options_ladder(
        premium,
        stop_mult=stop_mult,
        target_mults=(target_mult, max(target_mult + 0.5, 2.0), max(target_mult + 1.0, 2.5)),
    )
    return ladder.initial_stop, ladder.target, ladder


def _recommended_side(options_action: str, primary_option_type: str | None = None) -> str | None:
    """Which side (CE/PE) aligns with the index signal."""
    if options_action in ("NO TRADE", "WAIT"):
        return None
    action = options_action.upper()
    if "CE" in action and "PE" not in action:
        return "CE"
    if "PE" in action and "CE" not in action:
        return "PE"
    if primary_option_type in ("CE", "PE"):
        return primary_option_type
    if "CE" in action:
        return "CE"
    if "PE" in action:
        return "PE"
    return None


def _index_pulse_map(report) -> dict[str, object]:
    return {p.symbol: p for p in getattr(report, "indices", [])}


def _cached_index_options(report, fno_symbol: str):
    for io in getattr(report, "index_options", []) or []:
        if io.fno_symbol == fno_symbol and io.chain:
            return io
    return None


def _leg_to_pick(
    leg,
    *,
    fno_symbol: str,
    name: str,
    chain,
    lot_size: int,
    signal: str,
    option_type: str,
    recommended: bool,
    reason: str,
    ce_ref: str,
    pe_ref: str,
    error: str | None = None,
) -> OptionsExpiryPick:
    from analyzer.nse_options import option_lot_buy_cost

    stop_p, target_p, ladder = _premium_plan(leg.ltp)
    lot_cost = option_lot_buy_cost(leg.ltp, lot_size)
    return OptionsExpiryPick(
        rank=0,
        fno_symbol=fno_symbol,
        name=name,
        expiry=chain.expiry,
        spot=chain.spot,
        signal=signal,
        option_type=option_type,
        strike=leg.strike,
        premium=leg.ltp,
        lot_size=lot_size,
        lot_cost=lot_cost,
        stop_premium=stop_p,
        target_premium=target_p,
        target2_premium=ladder.target2 if ladder else None,
        target3_premium=ladder.target3 if ladder else None,
        stop_after_t1=ladder.stops_after[0] if ladder else None,
        stop_after_t2=ladder.stops_after[1] if ladder else None,
        stop_after_t3=ladder.stops_after[2] if ladder else None,
        iv=leg.iv,
        recommended=recommended,
        reason=reason,
        ce_reference=ce_ref,
        pe_reference=pe_ref,
        error=error,
    )


def _scan_one_index(
    fno_symbol: str,
    name: str,
    yahoo: str,
    report,
    *,
    max_lot_cost: float,
    period: str,
) -> tuple[list[OptionsExpiryPick], object, str | None]:
    from analyzer.nse_options import (
        fetch_option_chain,
        format_leg_with_lot_cost,
        get_fno_lot_size,
        pick_affordable_strikes,
    )

    pulse = _index_pulse_map(report).get(yahoo)
    cached = _cached_index_options(report, fno_symbol)
    io = cached or scan_index_options(fno_symbol, name, yahoo, period, pulse)

    if not io.chain:
        try:
            chain = fetch_option_chain(fno_symbol)
        except Exception as exc:
            return [], io, str(exc)
    else:
        chain = io.chain

    lot_size = get_fno_lot_size(fno_symbol)
    ce_leg, pe_leg = pick_affordable_strikes(
        chain, max_lot_cost=max_lot_cost, lot_size=lot_size,
    )
    ce_ref = format_leg_with_lot_cost(ce_leg, chain.spot, lot_size) if ce_leg else "—"
    pe_ref = format_leg_with_lot_cost(pe_leg, chain.spot, lot_size) if pe_leg else "—"

    primary_type = io.picks[0].leg.option_type if io.picks else None
    rec_side = _recommended_side(io.options_action, primary_type)

    picks: list[OptionsExpiryPick] = []
    if ce_leg:
        rec = rec_side == "CE"
        reason = (
            f"Signal **{io.options_action}** — affordable liquid CE under lot budget"
            if rec
            else "Affordable **CE** reference (trade ★ side if signal aligns)"
        )
        picks.append(
            _leg_to_pick(
                ce_leg,
                fno_symbol=fno_symbol,
                name=name,
                chain=chain,
                lot_size=lot_size,
                signal=io.options_action,
                option_type="CE",
                recommended=rec,
                reason=reason,
                ce_ref=ce_ref,
                pe_ref=pe_ref,
                error=io.error,
            )
        )
    if pe_leg:
        rec = rec_side == "PE"
        reason = (
            f"Signal **{io.options_action}** — affordable liquid PE under lot budget"
            if rec
            else "Affordable **PE** reference (trade ★ side if signal aligns)"
        )
        picks.append(
            _leg_to_pick(
                pe_leg,
                fno_symbol=fno_symbol,
                name=name,
                chain=chain,
                lot_size=lot_size,
                signal=io.options_action,
                option_type="PE",
                recommended=rec,
                reason=reason,
                ce_ref=ce_ref,
                pe_ref=pe_ref,
                error=io.error,
            )
        )

    if not picks:
        return [], io, io.error or "No liquid CE/PE under lot budget"

    return picks, io, None


def build_options_expiry_watchlist(
    report=None,
    *,
    max_lot_cost: float = DEFAULT_MAX_OPTION_LOT_COST_INR,
    period: str = "1y",
    market: str = "india",
) -> OptionsExpiryWatchlist:
    """Build Nifty + Bank Nifty expiry CE/PE picks with strike and premium levels."""
    from analyzer.kite_status import kite_options_available
    from analyzer.nse_session import is_nse_available, nse_status_message

    kite_ok = kite_options_available()
    nse_ok = is_nse_available()
    if not kite_ok and not nse_ok:
        return OptionsExpiryWatchlist(
            picks=[],
            routine_note=(
                "Options need **Zerodha Kite** login (sidebar → Login with Zerodha) "
                "or NSE access. Kite is the recommended source on cloud deployments."
            ),
            nse_available=False,
            errors=[nse_status_message() or "Connect Zerodha Kite for NFO quotes"],
        )

    picks: list[OptionsExpiryPick] = []
    errors: list[str] = []

    targets = INDEX_AFFORDABLE_TARGETS
    if report is None:
        targets = [(f, n, y) for f, n, y in INDEX_FNO_SYMBOLS]

    for fno, name, yahoo in targets:
        try:
            index_picks, _, err = _scan_one_index(
                fno, name, yahoo, report,
                max_lot_cost=max_lot_cost, period=period,
            )
            if index_picks:
                picks.extend(index_picks)
            elif err:
                errors.append(f"{fno}: {err}")
        except Exception as exc:
            errors.append(f"{fno}: {exc}")

    for i, p in enumerate(picks, start=1):
        p.rank = i

    note = (
        f"**Weekly expiry** CE/PE for **Nifty** & **Bank Nifty** — "
        f"1-lot budget ≤ **₹{max_lot_cost:,.0f}**. "
        "One row per **CE** and **PE**; ★ = signal-aligned side. "
        "Premium stop/target are on **option price** (T1/T2/T3 ladder: 40/30/30%). "
        "Square off before **3:20 PM IST**."
    )
    if errors and not picks:
        note += " " + " · ".join(errors[:2])

    return OptionsExpiryWatchlist(
        picks=picks,
        routine_note=note,
        nse_available=nse_ok or kite_ok,
        errors=errors,
    )
