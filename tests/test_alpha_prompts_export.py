"""Tests for Alpha AI prompts & export enhancements (items 13–20)."""

from __future__ import annotations

import unittest
import numpy as np
import pandas as pd

from analyzer.alpha_ai_export import report_to_markdown
from analyzer.alpha_ai_prompts import detect_report_mode, mode_framing
from analyzer.alpha_ai_report import AlphaAIReport, ScenarioCase, _confidence_pct
from analyzer.alpha_monte_carlo import monte_carlo_scenarios
from analyzer.alpha_red_flags import detect_red_flags


class TestAlphaPrompts(unittest.TestCase):
    def test_etf_mode(self):
        mode = detect_report_mode("NIFTYBEES.NS", {"quoteType": "ETF"}, 270, "india")
        self.assertEqual(mode, "etf")
        self.assertIn("ETF", mode_framing(mode)["business"])

    def test_penny_mode(self):
        mode = detect_report_mode("SUZLON.NS", {}, 45, "india")
        self.assertEqual(mode, "penny")


class TestMonteCarlo(unittest.TestCase):
    def test_scenarios_from_returns(self):
        idx = pd.date_range("2024-01-01", periods=200, freq="B")
        prices = 100 * np.exp(np.cumsum(np.random.default_rng(1).normal(0.0005, 0.01, 200)))
        df = pd.DataFrame({"Close": prices}, index=idx)
        scenarios = monte_carlo_scenarios(df, 100.0, "₹")
        self.assertEqual(len(scenarios), 3)
        self.assertIn("Monte Carlo", scenarios[0].description)


class TestRedFlags(unittest.TestCase):
    def test_high_debt_flag(self):
        flags = detect_red_flags({"debt_to_equity": 2.0}, tech_score=0, fund_score=0)
        self.assertTrue(any("leverage" in f.lower() or "debt" in f.lower() for f in flags))


class TestExport(unittest.TestCase):
    def test_markdown_contains_sections(self):
        r = AlphaAIReport(
            symbol="TCS.NS",
            name="TCS",
            sector="Tech",
            industry="IT",
            price=100,
            currency="₹",
            generated_at="now",
            report_mode="large_cap",
            section_sources={"fundamentals": ["Yahoo"]},
            scenarios=[ScenarioCase("Bull", "mc", 25, "₹110", "10%")],
        )
        md = report_to_markdown(r)
        self.assertIn("Executive Summary", md)
        self.assertIn("Data sources", md)


class TestInsufficientData(unittest.TestCase):
    def test_confidence_drops_with_gaps(self):
        self.assertLess(_confidence_pct(20, ["a"] * 10, "medium"), _confidence_pct(20, [], "medium"))


if __name__ == "__main__":
    unittest.main()
