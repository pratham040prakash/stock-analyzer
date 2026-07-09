"""Tests for 9:46 morning options re-scan."""

import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch
from zoneinfo import ZoneInfo

from analyzer.morning_options_rescan import (
    format_morning_options_rescan_telegram,
    run_morning_options_rescan,
    run_morning_options_rescan_job,
)

IST = ZoneInfo("Asia/Kolkata")


class TestMorningOptionsRescan(unittest.TestCase):
    @patch("analyzer.morning_options_rescan.save_options_watchlist_snapshot")
    @patch("analyzer.morning_options_rescan.mark_prep_step")
    @patch("analyzer.morning_options_rescan.build_options_expiry_watchlist")
    def test_run_rescan_saves_snapshot(self, mock_build, mock_mark, mock_save):
        picks = [
            SimpleNamespace(recommended=True, fno_symbol="BANKNIFTY"),
            SimpleNamespace(recommended=False, fno_symbol="NIFTY"),
        ]
        mock_build.return_value = SimpleNamespace(picks=picks, errors=[])
        with patch("analyzer.morning_options_rescan.market_session_status", return_value={"date": "2026-07-09"}):
            result = run_morning_options_rescan(send_telegram=False)
        self.assertEqual(result.pick_count, 2)
        self.assertEqual(result.recommended_count, 1)
        mock_save.assert_called_once()
        mock_mark.assert_called_once_with("options")

    def test_format_telegram_includes_rescan_header(self):
        wl = SimpleNamespace(
            picks=[SimpleNamespace(recommended=True, fno_symbol="BANKNIFTY", option_type="PE", strike=55000)],
        )
        with patch(
            "analyzer.morning_options_rescan.format_options_watchlist_telegram",
            return_value="★ BANKNIFTY PE",
        ):
            with patch(
                "analyzer.morning_options_rescan.session_target_date",
                return_value="2026-07-09",
            ):
                msg = format_morning_options_rescan_telegram(wl)
        self.assertIn("re-scan", msg.lower())
        self.assertIn("BANKNIFTY PE", msg)

    @patch("analyzer.morning_options_rescan.run_morning_options_rescan")
    @patch("analyzer.morning_options_rescan.market_session_status", return_value={"is_open": True})
    @patch("analyzer.morning_options_rescan.skip_scheduled_job_reason", return_value="")
    def test_job_runs_in_window(self, _skip, _session, mock_run):
        mock_run.return_value = SimpleNamespace(
            pick_count=4,
            recommended_count=2,
            telegram_sent=False,
            telegram_error="",
            errors=[],
        )
        now = datetime(2026, 7, 9, 9, 47, tzinfo=IST)
        with patch("analyzer.morning_options_rescan.datetime") as mock_dt:
            mock_dt.now.return_value = now
            count, msg = run_morning_options_rescan_job()
        self.assertEqual(count, 4)
        self.assertIn("Re-scanned", msg)
        mock_run.assert_called_once()

    @patch("analyzer.morning_options_rescan.market_session_status", return_value={"is_open": True})
    @patch("analyzer.morning_options_rescan.skip_scheduled_job_reason", return_value="")
    def test_job_skips_outside_window(self, _skip, _session):
        now = datetime(2026, 7, 9, 11, 0, tzinfo=IST)
        with patch("analyzer.morning_options_rescan.datetime") as mock_dt:
            mock_dt.now.return_value = now
            count, msg = run_morning_options_rescan_job()
        self.assertEqual(count, 0)
        self.assertIn("Outside", msg)


if __name__ == "__main__":
    unittest.main()
