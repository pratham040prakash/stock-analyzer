"""Tests for prep status and nightly prep."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from analyzer.prep_status import mark_prep_step, prep_status_for, prep_complete_count
from analyzer.watchlist_telegram import format_combined_prep_telegram
from analyzer.watchlist_pins import PinnedPlan
from analyzer.options_expiry_watchlist import OptionsExpiryPick


class TestPrepStatus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "prep.json"
        self.p = patch("analyzer.prep_status.STATUS_PATH", self.path)
        self.p.start()

    def tearDown(self):
        self.p.stop()
        self.tmp.cleanup()

    @patch("analyzer.prep_status.session_target_date", return_value="2026-07-04")
    def test_mark_steps(self, _d):
        mark_prep_step("equity")
        mark_prep_step("options")
        status = prep_status_for("2026-07-04")
        self.assertTrue(status["equity"])
        self.assertTrue(status["options"])
        self.assertEqual(prep_complete_count(status), 2)


class TestCombinedTelegram(unittest.TestCase):
    def test_format(self):
        eq = [PinnedPlan("TCS", 4000, 3950, 4100, "2026-07-03")]
        opt = OptionsExpiryPick(
            rank=1,
            fno_symbol="NIFTY",
            name="Nifty",
            expiry="10-Jul-2026",
            spot=25000,
            signal="BUY CE",
            option_type="CE",
            strike=25050,
            premium=100,
            lot_size=75,
            lot_cost=7500,
            stop_premium=65,
            target_premium=150,
            iv=12,
            recommended=True,
            reason="",
        )
        msg = format_combined_prep_telegram(eq, [opt], market_bias="BULLISH")
        self.assertIn("TCS", msg)
        self.assertIn("NIFTY", msg)
        self.assertIn("BULLISH", msg)


class TestNightlyPrep(unittest.TestCase):
    @patch("analyzer.nightly_prep.mark_prep_step")
    @patch("analyzer.nightly_prep.build_options_expiry_watchlist")
    @patch("analyzer.nightly_prep.run_quick_watchlist_scan")
    def test_run_prep(self, mock_scan, mock_opt, _mark):
        from analyzer.intraday_watchlist import IntradayWatchlistReport
        from analyzer.nightly_prep import run_nightly_prep

        report = MagicMock(stock_map={"TCS": object()})
        mock_scan.return_value = report
        mock_opt.return_value = MagicMock(picks=[], errors=[], nse_available=True)

        with patch("analyzer.nightly_prep.build_intraday_watchlist") as mock_wl:
            mock_wl.return_value = IntradayWatchlistReport(
                market_bias="NEUTRAL",
                sector_leader="—",
                sector_laggard="—",
                routine_note="",
                picks=[],
            )
            result, pulse = run_nightly_prep("india", send_telegram=False)
        self.assertEqual(result.equity_count, 0)
        self.assertIs(pulse, report)


if __name__ == "__main__":
    unittest.main()
