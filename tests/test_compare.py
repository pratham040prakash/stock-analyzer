"""Tests for stock comparison."""

import unittest

from analyzer.compare import CompareRow, compare_stocks, pick_winner


class TestCompare(unittest.TestCase):
    def test_pick_winner_skips_errors(self):
        rows = [
            CompareRow(
                ticker="BAD.NS", name="Bad", price=0, combined_rec="ERROR", combined_score=0,
                technical_score=0, fundamental_score=0, short_action="—", short_score=0,
                long_action="—", long_score=0, rsi=None, pe=None, roe=None,
                rs_verdict="—", alpha_3m=None, delivery_pct=None, sector="", error="fail",
            ),
            CompareRow(
                ticker="GOOD.NS", name="Good", price=100, combined_rec="BUY", combined_score=40,
                technical_score=35, fundamental_score=30, short_action="BUY", short_score=30,
                long_action="ACCUMULATE", long_score=35, rsi=55, pe=20, roe=0.18,
                rs_verdict="Outperforming", alpha_3m=5.0, delivery_pct=45, sector="IT",
            ),
        ]
        winner = pick_winner(rows)
        self.assertIsNotNone(winner)
        assert winner is not None
        self.assertEqual(winner.ticker, "GOOD.NS")

    def test_compare_stocks_empty(self):
        self.assertEqual(compare_stocks([]), [])

    def test_compare_stocks_dedupes_and_caps(self):
        from unittest import mock

        def fake_compare_one(ticker, period, market, bench_df, bench_info):
            score = 10 if "TCS" in ticker else 5
            return CompareRow(
                ticker=ticker, name=ticker, price=100, combined_rec="BUY", combined_score=score,
                technical_score=score, fundamental_score=score, short_action="BUY", short_score=score,
                long_action="HOLD", long_score=score, rsi=50, pe=20, roe=0.15,
                rs_verdict="—", alpha_3m=None, delivery_pct=None, sector="",
            )

        with mock.patch("analyzer.compare._compare_one", side_effect=fake_compare_one):
            rows = compare_stocks(
                ["TCS.NS", "TCS.NS", "INFY.NS", "RELIANCE.NS", "HDFC.NS"],
                period="1y",
                market="india",
            )
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0].ticker, "TCS.NS")


if __name__ == "__main__":
    unittest.main()
