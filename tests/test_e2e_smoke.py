"""E2E smoke: persist snapshot → score → CSV row."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.intraday_watchlist import (
    IntradayWatchlistPick,
    IntradayWatchlistReport,
    PivotLevels,
    ProChecklist,
)
from analyzer.watchlist_eod import WatchlistOutcome


class TestE2ESmoke(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "journal.db"
        self.jp = patch("analyzer.suggestion_journal.journal_db_path", return_value=self.db)
        self.je = patch("analyzer.watchlist_eod.journal_db_path", return_value=self.db)
        self.jh = patch("analyzer.watchlist_history.journal_db_path", return_value=self.db)
        self.jp.start()
        self.je.start()
        self.jh.start()
        from analyzer.watchlist_history import init_watchlist_history

        init_watchlist_history()

    def tearDown(self):
        self.jh.stop()
        self.je.stop()
        self.jp.stop()
        self.tmp.cleanup()

    def _sample_pick(self) -> IntradayWatchlistPick:
        return IntradayWatchlistPick(
            rank=1,
            nse_symbol="RELIANCE",
            name="Reliance",
            price=2500.0,
            sector="Energy",
            prep_score=72.0,
            market_bias="BULLISH",
            checklist=ProChecklist(True, True, True, True, True, 5),
            entry=2500.0,
            stop_loss=2480.0,
            target=2550.0,
            pivot=PivotLevels(2500, 2520, 2540, 2480, 2460),
            support=2480.0,
            resistance=2550.0,
            atr_pct=2.1,
            rsi=58.0,
            macd_bullish=True,
            volume_ratio=1.5,
            sector_tailwind=True,
            breakout_note="",
            news_note="",
            can_enter=True,
            plan_summary="",
        )

    @patch("analyzer.watchlist_history.market_session_status", return_value={"date": "2026-07-10"})
    @patch("analyzer.watchlist_history.session_target_date", return_value="2026-07-11")
    def test_snapshot_score_export(self, _td, _ms):
        from analyzer.suggestions_export import build_suggestions_csv
        from analyzer.watchlist_history import save_watchlist_snapshot, score_daily_watchlist

        wl = IntradayWatchlistReport(market_bias="BULLISH", sector_leader="", sector_laggard="", routine_note="", picks=[self._sample_pick()])
        n = save_watchlist_snapshot(wl.picks, market_bias="BULLISH", prep_date="2026-07-10")
        self.assertEqual(n, 1)

        with patch("analyzer.watchlist_history.can_score_trade_date", return_value=True):
            with patch("analyzer.watchlist_history._session_ohlc", return_value=(2560.0, 2490.0, 2540.0)):
                outcomes = score_daily_watchlist(trade_date="2026-07-11", market="india")
        self.assertTrue(outcomes)
        self.assertEqual(outcomes[0].outcome, "target_hit")

        csv = build_suggestions_csv(days=7, market="india")
        self.assertIn("RELIANCE", csv)
        self.assertIn("target_hit", csv)


if __name__ == "__main__":
    unittest.main()
