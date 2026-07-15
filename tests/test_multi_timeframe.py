"""Tests for multi-timeframe alignment."""

import unittest
from unittest.mock import patch

from analyzer.candle_narrative import LiveChartVerdict
from analyzer.intraday_signals import IntradayAnalysis
from analyzer.multi_timeframe import (
    ACTION_SCORE,
    MultiTimeframeReport,
    TimeframeSnapshot,
    _action_from_net,
    _alignment_pct,
    analyze_multi_timeframe,
    mtf_supports_option,
)


class TestMultiTimeframe(unittest.TestCase):
    def test_action_from_net(self):
        self.assertEqual(_action_from_net(2.0), "STRONG BUY")
        self.assertEqual(_action_from_net(0.8), "BUY")
        self.assertEqual(_action_from_net(0.0), "WAIT")
        self.assertEqual(_action_from_net(-0.8), "SELL")

    def test_alignment_pct(self):
        frames = [
            TimeframeSnapshot("1m", "BUY", "medium", 1, None, "BULLISH", "Green", ""),
            TimeframeSnapshot("5m", "BUY", "medium", 1, None, "BULLISH", "Green", ""),
            TimeframeSnapshot("15m", "WAIT", "low", 0, None, "NEUTRAL", "Doji", ""),
        ]
        self.assertEqual(_alignment_pct(frames), 67)

    def test_mtf_supports_ce(self):
        report = MultiTimeframeReport(
            symbol="^NSEI",
            label="Nifty",
            consensus_action="BUY",
            alignment_pct=67,
        )
        ok, _ = mtf_supports_option("CE", report)
        self.assertTrue(ok)

    @patch("analyzer.multi_timeframe.analyze_timeframe")
    def test_analyze_multi_timeframe_vote(self, mock_tf):
        mock_tf.side_effect = [
            TimeframeSnapshot("1m", "BUY", "high", 1.5, 100.0, "BULLISH", "Hammer", ""),
            TimeframeSnapshot("5m", "BUY", "medium", 1.0, 100.0, "BULLISH", "Green", ""),
            TimeframeSnapshot("15m", "WAIT", "low", 0.0, 100.0, "NEUTRAL", "Doji", ""),
        ]
        report = analyze_multi_timeframe("^NSEI", use_cache=False)
        self.assertIn(report.consensus_action, ("BUY", "STRONG BUY", "WAIT", "SELL", "STRONG SELL"))
        self.assertGreaterEqual(report.alignment_pct, 50)
        self.assertEqual(len(report.frames), 3)


if __name__ == "__main__":
    unittest.main()
