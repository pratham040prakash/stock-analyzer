"""Tests for watchlist persistence fingerprinting."""

import unittest

from analyzer.intraday_watchlist import IntradayWatchlistPick, IntradayWatchlistReport, ProChecklist
from analyzer.watchlist_persist import persist_watchlist_state, watchlist_state_fingerprint


def _pick(sym: str, entry: float = 100.0, side: str = "LONG") -> IntradayWatchlistPick:
    checklist = ProChecklist(
        volume_ok=True,
        atr_ok=True,
        rsi_macd_ok=True,
        levels_ok=True,
        news_ok=True,
        passed=5,
    )
    return IntradayWatchlistPick(
        rank=1,
        nse_symbol=sym,
        name=sym,
        price=entry,
        sector="IT",
        prep_score=80,
        market_bias="BULLISH",
        checklist=checklist,
        entry=entry,
        stop_loss=entry - 5,
        target=entry + 10,
        pivot=None,
        support=entry - 10,
        resistance=entry + 10,
        atr_pct=2.0,
        rsi=60,
        macd_bullish=True,
        volume_ratio=1.5,
        sector_tailwind=True,
        breakout_note="test",
        news_note="ok",
        can_enter=True,
        plan_summary="ok",
        side=side,
    )


class TestWatchlistPersist(unittest.TestCase):
    def test_fingerprint_changes_with_side(self):
        wl_long = IntradayWatchlistReport(
            market_bias="BULLISH",
            sector_leader="IT",
            sector_laggard="Metal",
            routine_note="",
            picks=[_pick("TCS", side="LONG")],
        )
        wl_short = IntradayWatchlistReport(
            market_bias="BEARISH",
            sector_leader="IT",
            sector_laggard="Metal",
            routine_note="",
            picks=[_pick("TCS", side="SHORT")],
        )
        self.assertNotEqual(
            watchlist_state_fingerprint(wl_long),
            watchlist_state_fingerprint(wl_short),
        )

    def test_persist_skips_when_unchanged(self):
        wl = IntradayWatchlistReport(
            market_bias="BULLISH",
            sector_leader="IT",
            sector_laggard="Metal",
            routine_note="",
            picks=[_pick("RELIANCE")],
        )
        store: dict = {}
        first = persist_watchlist_state(wl, prep_date="2026-07-06", session_store=store)
        second = persist_watchlist_state(wl, prep_date="2026-07-06", session_store=store)
        self.assertTrue(first)
        self.assertFalse(second)


if __name__ == "__main__":
    unittest.main()
