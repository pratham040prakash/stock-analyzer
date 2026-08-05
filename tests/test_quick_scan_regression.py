"""Regression tests for Quick Scan / market pulse scan wiring."""

from __future__ import annotations

import unittest
from types import MappingProxyType
from unittest.mock import MagicMock, patch

from analyzer.context_engine.models import ContextSnapshot
from analyzer.intraday_pulse_source import run_quick_watchlist_scan
from analyzer.market_pulse import IndexPulse, india_market_pulse
import analyzer.market_pulse_scan as market_pulse_scan_module


def _empty_context() -> ContextSnapshot:
    return ContextSnapshot(
        timestamp="2026-08-05T09:00:00+05:30",
        market_regime="Neutral",
        market_phase="regular",
        market_breadth="mixed",
        volatility_state="normal",
        liquidity_state="normal",
        market_session=MappingProxyType({"phase": "regular", "is_open": True, "date": "2026-08-05"}),
        sector_strength=MappingProxyType({}),
        industry_strength=MappingProxyType({}),
        macro_state=MappingProxyType({}),
        global_market_state=MappingProxyType({}),
        risk_mode="NEUTRAL",
        trading_restrictions=(),
        confidence=0.85,
        snapshot_id="ctx-qs",
        context_hash="hash-qs",
    )


class TestQuickScanRegression(unittest.TestCase):
    """P0: Quick Scan must resolve india_market_pulse (regression from commit 6dfe7fa)."""

    def test_market_pulse_scan_module_exports_india_market_pulse(self):
        self.assertIs(market_pulse_scan_module.india_market_pulse, india_market_pulse)
        self.assertIs(market_pulse_scan_module.IndexPulse, IndexPulse)

    @patch("analyzer.pulse_cache.save_pulse_cache")
    @patch("analyzer.pulse_cache.load_pulse_cache_with_stale", return_value=(None, False))
    @patch("analyzer.market_pulse_scan.fetch_delivery_batch", return_value={})
    @patch("analyzer.market_pulse_scan.fetch_nifty50_earnings", return_value=[])
    @patch("analyzer.market_pulse_scan._scan_all_stocks", return_value=[])
    @patch("analyzer.market_pulse_scan.india_market_pulse")
    @patch("analyzer.market_pulse_scan.fetch_stock_data", return_value=(None, None))
    @patch("analyzer.context_engine.build_context_snapshot")
    def test_quick_scan_executes_without_name_error(
        self,
        mock_ctx,
        _fetch,
        mock_indices,
        _scan,
        _earnings,
        _delivery,
        _load_cache,
        _save_cache,
    ):
        mock_ctx.return_value = _empty_context()
        mock_indices.return_value = [
            IndexPulse(
                symbol="^NSEI",
                name="Nifty 50",
                price=24000.0,
                change_1m_pct=1.2,
                recommendation="BUY",
                score=25.0,
                regime="Bullish",
            )
        ]

        report = run_quick_watchlist_scan("india", "1y", use_cache=False)

        self.assertIsNotNone(report)
        mock_indices.assert_called_once()
        self.assertEqual(len(report.indices), 1)


if __name__ == "__main__":
    unittest.main()
