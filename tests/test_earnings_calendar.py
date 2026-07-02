"""Tests for earnings calendar."""

import unittest
from datetime import date, timedelta

from analyzer.earnings_calendar import (
    CorporateEvent,
    _enrich,
    _risk_band,
    should_skip_pick,
    trading_guidance,
    upcoming_within_days,
)


class TestEarningsCalendar(unittest.TestCase):
    def test_risk_band_critical(self):
        self.assertEqual(_risk_band(0, "Earnings"), "critical")
        self.assertEqual(_risk_band(2, "Earnings"), "critical")

    def test_enrich_days_until(self):
        tomorrow = (date.today() + timedelta(days=2)).isoformat()
        ev = _enrich(CorporateEvent(
            symbol="TCS.NS",
            nse_symbol="TCS",
            name="TCS",
            event_type="Earnings",
            date=tomorrow,
            detail="test",
        ))
        self.assertEqual(ev.days_until, 2)
        self.assertEqual(ev.risk_band, "critical")
        self.assertIn("Results in 2d", ev.guidance)

    def test_skip_intraday_near_earnings(self):
        ev = CorporateEvent(
            symbol="X.NS",
            nse_symbol="X",
            name="X",
            event_type="Earnings",
            date="2099-01-01",
            detail="",
            days_until=2,
            risk_band="critical",
        )
        self.assertTrue(should_skip_pick(ev, "intraday", skip_earnings_week=True))
        self.assertFalse(should_skip_pick(ev, "long", skip_earnings_week=True))

    def test_upcoming_filter(self):
        events = [
            CorporateEvent("A.NS", "A", "A", "Earnings", "2099-01-01", "", days_until=5, risk_band="elevated"),
            CorporateEvent("B.NS", "B", "B", "Earnings", "2099-01-01", "", days_until=20, risk_band="clear"),
        ]
        soon = upcoming_within_days(events, days=14)
        self.assertEqual(len(soon), 1)

    def test_trading_guidance_options(self):
        msg = trading_guidance(2, horizon="options")
        self.assertIn("IV", msg)


if __name__ == "__main__":
    unittest.main()
