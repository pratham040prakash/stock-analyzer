"""Tests for suggestions export, telegram formats, and cloud mode."""

import os
import unittest
from unittest.mock import patch

from analyzer.watchlist_pins import PinnedPlan


class TestSuggestionsTelegram(unittest.TestCase):
    def test_nightly_format_compact(self):
        from analyzer.suggestions_telegram import format_nightly_suggestions_telegram

        msg = format_nightly_suggestions_telegram(
            [
                PinnedPlan(
                    symbol="RELIANCE",
                    entry=2500.0,
                    stop_loss=2480.0,
                    target=2550.0,
                    prep_date="2026-07-05",
                )
            ],
            market_bias="BULLISH",
        )
        self.assertIn("RELIANCE", msg)
        self.assertIn("2,500", msg)
        self.assertIn("Star your top 2", msg)

    def test_eod_hit_summary(self):
        from analyzer.suggestions_telegram import format_eod_hit_summary_telegram
        from analyzer.watchlist_history import SessionWatchlistRow

        rows = [
            SessionWatchlistRow(
                rank=1,
                symbol="TCS",
                entry=100.0,
                stop_loss=98.0,
                target=105.0,
                session_high=106.0,
                session_low=99.0,
                session_close=104.0,
                outcome="target_hit",
                note="",
                scored=True,
            )
        ]
        msg = format_eod_hit_summary_telegram(
            "2026-07-06",
            equity_rows=rows,
            include_weekly=False,
        )
        self.assertIn("Did targets hit", msg)
        self.assertIn("TCS", msg)
        self.assertIn("✅", msg)


class TestSuggestionsExport(unittest.TestCase):
    def test_csv_header(self):
        from analyzer.suggestions_export import build_suggestions_csv

        with patch(
            "analyzer.suggestions_export.build_recent_suggested_picks",
            return_value=[],
        ):
            csv = build_suggestions_csv(days=7)
        self.assertIn("trade_date", csv)
        self.assertIn("hit_target", csv)


class TestAppMode(unittest.TestCase):
    def test_simple_cloud_override(self):
        from analyzer.app_mode import is_simple_cloud_mode

        with patch.dict(os.environ, {"SIMPLE_CLOUD_MODE": "1"}):
            self.assertTrue(is_simple_cloud_mode())
        with patch.dict(os.environ, {"SIMPLE_CLOUD_MODE": "0"}):
            self.assertFalse(is_simple_cloud_mode())


if __name__ == "__main__":
    unittest.main()
