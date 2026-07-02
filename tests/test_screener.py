"""Tests for custom screener filters."""

import unittest

from analyzer.screener import (
    PRESET_SCREENS,
    ScreenerCriteria,
    ScreenerRow,
    apply_criteria,
    criteria_summary,
    merge_criteria,
)


def _row(**kwargs) -> ScreenerRow:
    base = dict(
        ticker="TEST.NS",
        nse_symbol="TEST",
        name="Test Ltd",
        price=100.0,
        sector="Technology",
        combined_score=25.0,
        combined_rec="BUY",
        technical_score=30.0,
        fundamental_score=18.0,
        short_action="BUY",
        short_score=28.0,
        long_action="ACCUMULATE",
        long_score=32.0,
        rsi=45.0,
        above_sma20=True,
        above_sma50=True,
        above_sma200=True,
        volume_ratio=1.2,
        pe=18.0,
        roe=0.15,
        debt_equity=0.5,
        revenue_growth=0.12,
        delivery_pct=42.0,
        delivery_quality="moderate",
        earnings_days_until=20,
    )
    base.update(kwargs)
    return ScreenerRow(**base)


class TestScreener(unittest.TestCase):
    def test_preset_screens_exist(self):
        self.assertIn("Swing momentum", PRESET_SCREENS)
        self.assertIn("Quality compounders", PRESET_SCREENS)

    def test_combined_score_filter(self):
        rows = [_row(combined_score=10), _row(combined_score=30)]
        crit = ScreenerCriteria(min_combined_score=20.0)
        out = apply_criteria(rows, crit)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].combined_score, 30.0)

    def test_rsi_oversold_filter(self):
        rows = [_row(rsi=28), _row(rsi=55)]
        crit = ScreenerCriteria(max_rsi=35.0)
        out = apply_criteria(rows, crit)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].rsi, 28.0)

    def test_exclude_speculative_delivery(self):
        rows = [_row(delivery_quality="speculative"), _row(delivery_quality="strong")]
        crit = ScreenerCriteria(exclude_speculative_delivery=True)
        out = apply_criteria(rows, crit)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].delivery_quality, "strong")

    def test_earnings_exclusion(self):
        rows = [_row(earnings_days_until=2), _row(earnings_days_until=10)]
        crit = ScreenerCriteria(exclude_earnings_within_days=5)
        out = apply_criteria(rows, crit)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].earnings_days_until, 10)

    def test_swing_momentum_preset(self):
        rows = [
            _row(short_score=30, volume_ratio=1.3, delivery_pct=30, delivery_quality="moderate"),
            _row(short_score=15, volume_ratio=1.3, delivery_pct=30),
            _row(short_score=30, volume_ratio=0.8, delivery_pct=30),
        ]
        out = apply_criteria(rows, PRESET_SCREENS["Swing momentum"])
        self.assertEqual(len(out), 1)

    def test_merge_criteria(self):
        base = PRESET_SCREENS["Strong buys"]
        merged = merge_criteria(base, ScreenerCriteria(min_short_score=25.0))
        self.assertEqual(merged.min_combined_score, base.min_combined_score)
        self.assertEqual(merged.min_short_score, 25.0)

    def test_criteria_summary_nonempty(self):
        text = criteria_summary(PRESET_SCREENS["Value hunters"])
        self.assertIn("P/E", text)


if __name__ == "__main__":
    unittest.main()
