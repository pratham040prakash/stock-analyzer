"""One-click nightly MIS prep — equity scan, options CE/PE, combined Telegram."""

from __future__ import annotations

from dataclasses import dataclass, field

from analyzer.affordable_invest import DEFAULT_MAX_OPTION_LOT_COST_INR
from analyzer.intraday_pulse_source import DEFAULT_INTRADAY_PULSE_PERIOD, run_quick_watchlist_scan
from analyzer.intraday_watchlist import build_intraday_watchlist
from analyzer.market_session import market_session_status
from analyzer.options_expiry_watchlist import build_options_expiry_watchlist
from analyzer.options_watchlist_history import save_options_watchlist_snapshot
from analyzer.prep_status import mark_prep_step
from analyzer.watchlist_persist import persist_watchlist_state
from analyzer.watchlist_pins import TOP_TOMORROW_PICKS
from analyzer.suggestions_telegram import format_nightly_suggestions_telegram


@dataclass
class NightlyPrepResult:
    equity_count: int = 0
    options_count: int = 0
    market_bias: str = ""
    prep_date: str = ""
    telegram_sent: bool = False
    telegram_error: str = ""
    errors: list[str] = field(default_factory=list)


def run_nightly_prep(
    market: str = "india",
    *,
    period: str = DEFAULT_INTRADAY_PULSE_PERIOD,
    max_lot_cost: float = DEFAULT_MAX_OPTION_LOT_COST_INR,
    send_telegram: bool = True,
    use_cache: bool = False,
) -> NightlyPrepResult:
    """Quick scan → top 5 equity → Nifty/Bank Nifty CE/PE → optional Telegram."""
    result = NightlyPrepResult()
    prep_date = market_session_status().get("date", "")
    result.prep_date = prep_date

    try:
        report = run_quick_watchlist_scan(market, period, use_cache=use_cache)
    except Exception as exc:
        result.errors.append(f"Equity scan: {exc}")
        report = None

    pulse_report = report
    if pulse_report and getattr(pulse_report, "stock_map", None):
        wl = build_intraday_watchlist(pulse_report, limit=TOP_TOMORROW_PICKS)
        result.market_bias = wl.market_bias
        result.equity_count = len(wl.picks)
        if wl.picks:
            persist_watchlist_state(
                wl,
                prep_date=prep_date,
                force=True,
            )

    opt_picks = []
    try:
        opt_wl = build_options_expiry_watchlist(
            pulse_report if pulse_report and getattr(pulse_report, "stock_map", None) else None,
            max_lot_cost=max_lot_cost,
            period=period,
            market=market,
        )
        opt_picks = opt_wl.picks
        result.options_count = len(opt_picks)
        if opt_picks:
            save_options_watchlist_snapshot(opt_picks, prep_date=prep_date)
            mark_prep_step("options")
        for err in opt_wl.errors:
            result.errors.append(err)
        if not opt_wl.nse_available:
            result.errors.append("NSE unavailable for options chain")
    except Exception as exc:
        result.errors.append(f"Options: {exc}")

    if send_telegram and (result.equity_count or result.options_count):
        from analyzer.telegram_notify import send_telegram_broadcast, telegram_configured
        from analyzer.watchlist_pins import load_pinned_plans

        if not telegram_configured():
            result.telegram_error = "Telegram not configured"
        else:
            msg = format_nightly_suggestions_telegram(
                load_pinned_plans(),
                market_bias=result.market_bias,
                prep_date=prep_date,
            )
            ok, err = send_telegram_broadcast(msg, alert_type="morning")
            result.telegram_sent = ok
            result.telegram_error = err if not ok else ""
            if ok:
                mark_prep_step("telegram")

    return result, pulse_report
