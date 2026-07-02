"""Tests for JSON pulse cache (Streamlit reload-safe)."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analyzer.chart_horizon import HorizonAnalysis
from analyzer.india_macro import IndiaMacroSnapshot, MacroQuote
from analyzer.market_pulse import IndexPulse
from analyzer.market_pulse_scan import ChartStockPick, MarketPulseReport, StockPulseEntry
from analyzer.market_regime import MarketRegime
from analyzer.pulse_cache import (
    deserialize_pulse_report,
    load_pulse_cache_with_stale,
    save_pulse_cache,
    serialize_pulse_report,
)


def _sample_report() -> MarketPulseReport:
    return MarketPulseReport(
        indices=[
            IndexPulse("^NSEI", "Nifty 50", 24000.0, 1.2, "BUY", 25.0, "Bullish"),
        ],
        market_verdict="Bullish bias",
        index_options=[],
        top_stocks=[
            StockPulseEntry(
                symbol="RELIANCE.NS",
                nse_symbol="RELIANCE",
                name="Reliance",
                price=2500.0,
                combined_rec="BUY",
                combined_score=30.0,
                short_term=HorizonAnalysis(
                    horizon="short",
                    action="BUY",
                    score=25.0,
                    timeframe="2-8 weeks",
                    entry_hint="breakout",
                    stop_hint="2450",
                    target_hint="2600",
                    chart_signals=["RSI ok"],
                    summary="swing",
                ),
            ),
        ],
        intraday_picks=[
            ChartStockPick(
                symbol="RELIANCE.NS",
                nse_symbol="RELIANCE",
                name="Reliance",
                price=2500.0,
                action="BUY",
                score=40.0,
                horizon="intraday",
                timeframe="5m",
                entry_hint="e",
                stop_hint="s",
                target_hint="t",
            ),
        ],
        regime=MarketRegime(
            symbol="^NSEI",
            adx=28.0,
            plus_di=30.0,
            minus_di=18.0,
            regime="Trending Bullish",
            allow_aggressive_intraday=True,
            allow_aggressive_swing=True,
            message="trend",
            banner="banner",
        ),
        macro=IndiaMacroSnapshot(
            fetched_at="2026-07-02",
            india_vix=MacroQuote("^INDIAVIX", "VIX", 14.0, -1.0),
            gift_nifty_proxy=None,
            vix_regime="Low",
        ),
    )


class TestPulseCache(unittest.TestCase):
    def test_roundtrip(self) -> None:
        original = _sample_report()
        data = serialize_pulse_report(original)
        restored = deserialize_pulse_report(data)
        self.assertEqual(restored.market_verdict, original.market_verdict)
        self.assertEqual(len(restored.indices), 1)
        self.assertEqual(restored.top_stocks[0].nse_symbol, "RELIANCE")
        self.assertEqual(restored.macro.vix_regime, "Low")
        self.assertIsNone(restored.top_stocks[0].short_chart_df)

    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch("analyzer.pulse_cache.CACHE_DIR", Path(tmp)):
                report = _sample_report()
                save_pulse_cache("pulse_1y_india", report)
                loaded, fresh = load_pulse_cache_with_stale("pulse_1y_india", 900)
                self.assertIsNotNone(loaded)
                assert loaded is not None
                self.assertTrue(fresh)
                self.assertEqual(loaded.intraday_picks[0].nse_symbol, "RELIANCE")


if __name__ == "__main__":
    unittest.main()
