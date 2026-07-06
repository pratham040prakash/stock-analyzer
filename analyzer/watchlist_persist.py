"""Persist watchlist pins + DB snapshot only when picks actually change."""

from __future__ import annotations

from analyzer.intraday_watchlist import IntradayWatchlistReport
from analyzer.prep_status import mark_prep_step
from analyzer.watchlist_history import save_watchlist_snapshot
from analyzer.watchlist_pins import TOP_TOMORROW_PICKS, sync_auto_top_picks

_SESSION_FP_KEY = "_wl_persist_fp"


def watchlist_state_fingerprint(wl: IntradayWatchlistReport) -> str:
    parts = [wl.market_bias or ""]
    for p in wl.picks:
        side = getattr(p, "side", "LONG")
        parts.append(
            f"{p.nse_symbol}:{side}:{p.entry}:{p.stop_loss}:{p.target}:{p.prep_score}"
        )
    return "|".join(parts)


def persist_watchlist_state(
    wl: IntradayWatchlistReport,
    *,
    prep_date: str,
    limit: int = TOP_TOMORROW_PICKS,
    force: bool = False,
    session_store: dict | None = None,
) -> bool:
    """
    Sync auto top picks and save DB snapshot when the watchlist changes.
    Returns True if persistence ran.
    """
    if not wl.picks:
        return False

    fp = watchlist_state_fingerprint(wl)
    if session_store is not None and not force:
        if session_store.get(_SESSION_FP_KEY) == fp:
            return False
        session_store[_SESSION_FP_KEY] = fp

    sync_auto_top_picks(wl.picks, limit=limit)
    save_watchlist_snapshot(
        wl.picks,
        market_bias=wl.market_bias,
        prep_date=prep_date,
    )
    mark_prep_step("equity")
    return True
