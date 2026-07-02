"""Tests for penny stock scanner."""

import unittest

from analyzer.penny_stocks import (
    PennyStockPick,
    _penny_score,
    _risk_flags,
    penny_universe_yahoo,
    scan_penny_stocks,
)
from analyzer.screener import ScreenerRow


def _row(**kwargs) -> ScreenerRow:
    base = dict(
        ticker="TEST.NS",
        nse_symbol="TEST",
        name="Test Ltd",
        price=12.0,
        sector="Industrial",
        combined_score=18.0,
        combined_rec="BUY",
        technical_score=20.0,
        fundamental_score=5.0,
        short_action="BUY",
        short_score=22.0,
        long_action="HOLD",
        long_score=8.0,
        rsi=52.0,
        volume_ratio=1.4,
        delivery_pct=35.0,
        delivery_quality="moderate",
    )
    base.update(kwargs)
    return ScreenerRow(**base)


class TestPennyStocks(unittest.TestCase):
    def test_universe_has_ns_suffix(self):
        syms = penny_universe_yahoo()
        self.assertGreater(len(syms), 30)
        self.assertTrue(all(s.endswith(".NS") for s in syms))

    def test_penny_score_prefers_momentum(self):
        weak = _penny_score(_row(short_score=5, short_action="HOLD", volume_ratio=0.9))
        strong = _penny_score(_row(short_score=28, short_action="STRONG BUY", volume_ratio=1.8))
        self.assertGreater(strong, weak)

    def test_risk_flags_ultra_low(self):
        flags = _risk_flags(_row(price=4.5))
        self.assertTrue(any("Ultra-low" in f for f in flags))

    def test_scan_non_india_empty(self):
        report = scan_penny_stocks(market="us", max_price_inr=20)
        self.assertEqual(report.scanned, 0)
        self.assertIn("India", report.disclaimer)

    def test_row_to_pick_rank(self):
        from analyzer.penny_stocks import _row_to_pick

        pick = _row_to_pick(_row(), 1)
        self.assertEqual(pick.rank, 1)
        self.assertEqual(pick.nse_symbol, "TEST")
        self.assertGreater(pick.penny_score, 0)


if __name__ == "__main__":
    unittest.main()
