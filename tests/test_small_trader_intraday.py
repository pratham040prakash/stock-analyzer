"""Tests for small-trader portfolio intraday scan."""

import unittest
from unittest import mock

from analyzer.small_trader_intraday import (
    MAX_SMALL_TRADER_STOCKS,
    SmallTraderHoldingRow,
    _owner_note,
    _pnl_pct,
    scan_small_trader_portfolio,
    small_trader_intraday_tips,
)
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult


class TestSmallTraderIntraday(unittest.TestCase):
    def _holding(self, sym: str, qty: float = 10, avg: float = 100.0) -> ZerodhaHolding:
        return ZerodhaHolding(
            kite_symbol=f"NSE:{sym}-EQ",
            tradingsymbol=sym,
            exchange="NSE",
            quantity=qty,
            average_price=avg,
            yahoo_symbol=f"{sym}.NS",
        )

    def test_pnl_pct(self):
        h = self._holding("TCS", avg=100.0)
        self.assertAlmostEqual(_pnl_pct(h, 110.0), 10.0)
        self.assertIsNone(_pnl_pct(h, None))

    def test_owner_note_loss_on_buy(self):
        h = self._holding("INFY", avg=100.0)
        note = _owner_note(h, "BUY", -12.0)
        self.assertIn("risky", note.lower())

    def test_scan_returns_none_over_limit(self):
        holdings = [self._holding(f"S{i}") for i in range(MAX_SMALL_TRADER_STOCKS + 1)]
        imp = ZerodhaImportResult(holdings=holdings, source="manual")
        self.assertIsNone(scan_small_trader_portfolio(imp))

    def test_scan_small_portfolio(self):
        imp = ZerodhaImportResult(
            holdings=[self._holding("RELIANCE"), self._holding("TCS")],
            source="manual",
        )
        row = SmallTraderHoldingRow(
            nse_symbol="RELIANCE",
            name="RELIANCE",
            quantity=10,
            avg_price=100.0,
            pnl_pct=5.0,
            price=105.0,
            vwap=104.0,
            above_vwap=True,
            action="BUY",
            confidence="medium",
            score=3.0,
            entry=104.0,
            stop_loss=102.0,
            target=108.0,
            hypothesis="test",
            owner_note="hold",
        )
        with mock.patch(
            "analyzer.small_trader_intraday._scan_holding",
            return_value=row,
        ):
            report = scan_small_trader_portfolio(imp, interval="5m")
        self.assertIsNotNone(report)
        assert report is not None
        self.assertEqual(report.holdings_count, 2)
        self.assertEqual(report.buy_count, 2)
        self.assertIn("RELIANCE", report.focus_symbols)

    def test_tips_include_focus(self):
        from analyzer.small_trader_intraday import SmallTraderIntradayReport

        report = SmallTraderIntradayReport(
            holdings_count=2,
            interval="5m",
            updated_at="10:00 IST",
            focus_symbols=["TCS"],
            buy_count=1,
            sell_count=0,
            wait_count=1,
            session_open=True,
        )
        tips = small_trader_intraday_tips(report)
        self.assertIn("TCS", tips)
        self.assertIn("1–2 setups", tips)


if __name__ == "__main__":
    unittest.main()
