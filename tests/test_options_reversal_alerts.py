"""Tests for index OR reversal alerts on options."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from analyzer.options_reversal_alerts import (
    assess_option_index_thesis,
    check_options_reversal_alerts,
    format_options_reversal_telegram,
    leg_key,
)

IST = ZoneInfo("Asia/Kolkata")


class TestOptionsReversalAlerts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = Path(self.tmp.name) / "rev.json"
        self.p_state = patch("analyzer.options_reversal_alerts.STATE_PATH", self.state)
        self.p_state.start()
        self.p_date = patch(
            "analyzer.options_reversal_alerts.session_target_date",
            return_value="2026-07-09",
        )
        self.p_date.start()

    def tearDown(self):
        self.p_date.stop()
        self.p_state.stop()
        self.tmp.cleanup()

    def test_pe_invalidated_above_or_high(self):
        now = datetime(2026, 7, 9, 10, 30, tzinfo=IST)
        s = assess_option_index_thesis(
            "PE",
            fno_symbol="BANKNIFTY",
            strike=55000,
            spot=55120,
            or_high=55050,
            or_low=54800,
            now=now,
        )
        self.assertEqual(s.phase, "invalidated")
        self.assertIn("OR high", s.detail)

    def test_ce_invalidated_below_or_low(self):
        now = datetime(2026, 7, 9, 10, 30, tzinfo=IST)
        s = assess_option_index_thesis(
            "CE",
            fno_symbol="NIFTY",
            strike=25000,
            spot=24850,
            or_high=25100,
            or_low=24900,
            now=now,
        )
        self.assertEqual(s.phase, "invalidated")

    def test_observe_before_945(self):
        now = datetime(2026, 7, 9, 9, 30, tzinfo=IST)
        s = assess_option_index_thesis(
            "PE",
            fno_symbol="BANKNIFTY",
            strike=55000,
            spot=55200,
            or_high=55050,
            or_low=54800,
            now=now,
        )
        self.assertEqual(s.phase, "observe")

    def test_telegram_once_per_day(self):
        pick = {
            "fno_symbol": "BANKNIFTY",
            "option_type": "PE",
            "strike": 55000,
        }
        now = datetime(2026, 7, 9, 10, 30, tzinfo=IST)
        with patch("analyzer.options_reversal_alerts.load_selected_option", return_value=pick):
            with patch(
                "analyzer.options_reversal_alerts.assess_pick_index_reversal",
            ) as mock_assess:
                from analyzer.options_reversal_alerts import IndexReversalStatus

                mock_assess.return_value = IndexReversalStatus(
                    "BANKNIFTY", "PE", 55000, "Bank Nifty", 55120, 55050, 54800,
                    "invalidated", "PE thesis broken", "🔴", "reclaimed OR high", "CE",
                    "Exit PE",
                )
                msgs = check_options_reversal_alerts(trade_date="2026-07-09", now=now)
                self.assertEqual(len(msgs), 1)
                self.assertIn("BANKNIFTY", msgs[0])
                again = check_options_reversal_alerts(trade_date="2026-07-09", now=now)
                self.assertEqual(again, [])

    def test_format_message(self):
        from analyzer.options_reversal_alerts import IndexReversalStatus

        msg = format_options_reversal_telegram(
            IndexReversalStatus(
                "BANKNIFTY", "PE", 55000, "Bank Nifty", 55120, 55050, 54800,
                "invalidated", "PE thesis broken", "🔴", "detail", "CE", "Exit PE",
            )
        )
        self.assertIn("Index reversal", msg)
        self.assertIn(leg_key("BANKNIFTY", "PE", 55000).split(":")[0], msg)


if __name__ == "__main__":
    unittest.main()
