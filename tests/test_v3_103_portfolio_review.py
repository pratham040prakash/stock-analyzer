"""V3-103 — Portfolio Review contracts and render integration."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from analyzer.intraday_prefs import IntradayPrefs
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult
from ui.broker.state import BrokerSnapshot
from ui.components.portfolio_review_experience import (
    render_allocation_policy_review_section,
    render_healthy_reassurance_block,
    render_portfolio_explanation_block,
    render_portfolio_review_experience,
    render_review_broker_truth_footer,
    render_review_context_header,
    render_review_progress_strip,
    render_theme_review_queue,
)
from ui.components.portfolio_review_ui import (
    portfolio_review_from_inputs,
    theme_understand_contract,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _holding(symbol: str, qty: int, avg: float, ltp: float, pnl: float) -> ZerodhaHolding:
    return ZerodhaHolding(
        kite_symbol=f"NSE:{symbol}-EQ",
        tradingsymbol=symbol,
        exchange="NSE",
        quantity=qty,
        average_price=avg,
        last_price=ltp,
        pnl=pnl,
        yahoo_symbol=f"{symbol}.NS",
    )


class TestPortfolioReviewContracts(unittest.TestCase):
    def test_healthy_portfolio_reassurance_not_theme_queue(self):
        broker = BrokerSnapshot(
            state="connected",
            holdings_count=5,
            portfolio_value_inr=50000.0,
            available_cash_inr=5000.0,
        )
        portfolio = ZerodhaImportResult(
            holdings=[_holding(sym, 10, 1000, 1000, 100) for sym in ("RELIANCE", "TCS", "INFY", "HDFCBANK", "ITC")],
            source="kite",
        )
        contract = portfolio_review_from_inputs(
            broker=broker,
            portfolio=portfolio,
            prefs=IntradayPrefs(capital=50000, allocation_pct=32),
        )
        self.assertEqual(len(contract.themes), 0)
        self.assertFalse(contract.show_progress)
        self.assertTrue(any(item.passed for item in contract.reassurance_items))
        self.assertIn("healthy", contract.explanation.headline.lower())

    def test_single_position_risk_theme(self):
        broker = BrokerSnapshot(state="connected", holdings_count=1, portfolio_value_inr=100000)
        portfolio = ZerodhaImportResult(
            holdings=[_holding("RELIANCE", 10, 1000, 10000, 0)],
            source="manual",
        )
        contract = portfolio_review_from_inputs(
            broker=broker,
            portfolio=portfolio,
            prefs=IntradayPrefs(),
        )
        self.assertGreaterEqual(len(contract.themes), 1)
        theme = contract.themes[0]
        self.assertEqual(theme.theme_title, "Single Position Risk")
        self.assertIn("RELIANCE", theme.explanation)
        self.assertTrue(theme.affected_holdings)
        self.assertEqual(theme.affected_holdings[0].symbol, "RELIANCE")

    def test_theme_first_not_symbol_headline(self):
        broker = BrokerSnapshot(state="connected", holdings_count=2, portfolio_value_inr=100000)
        portfolio = ZerodhaImportResult(
            holdings=[
                _holding("RELIANCE", 10, 1000, 10000, 0),
                _holding("TCS", 10, 1000, 5000, 0),
            ],
            source="manual",
        )
        contract = portfolio_review_from_inputs(
            broker=broker,
            portfolio=portfolio,
            prefs=IntradayPrefs(),
        )
        for theme in contract.themes:
            self.assertIn(
                theme.theme_title,
                (
                    "Sector Concentration",
                    "Single Position Risk",
                    "Policy Drift",
                    "Cash Allocation",
                ),
            )
            self.assertNotEqual(theme.theme_title, theme.affected_holdings[0].symbol if theme.affected_holdings else "")

    def test_theme_item_has_required_blocks(self):
        contract = portfolio_review_from_inputs(
            broker=BrokerSnapshot(state="connected", holdings_count=1, portfolio_value_inr=100000),
            portfolio=ZerodhaImportResult(
                holdings=[_holding("RELIANCE", 10, 1000, 10000, 0)],
                source="manual",
            ),
            prefs=IntradayPrefs(),
        )
        theme = contract.themes[0]
        self.assertTrue(theme.explanation)
        self.assertTrue(theme.investigation_guidance)
        understand = theme_understand_contract(theme)
        titles = [section.title for section in understand.sections]
        self.assertIn("Why this theme was flagged", titles)
        self.assertIn("Affected holdings", titles)
        self.assertIn("Investigation guidance", titles)


class TestPortfolioReviewRender(unittest.TestCase):
    def test_render_markers(self):
        contract = portfolio_review_from_inputs(
            broker=BrokerSnapshot(state="connected", holdings_count=1, portfolio_value_inr=100000),
            portfolio=ZerodhaImportResult(
                holdings=[_holding("RELIANCE", 10, 1000, 10000, 0)],
                source="manual",
            ),
            prefs=IntradayPrefs(),
        )
        chunks: list[str] = []

        mock_st = MagicMock()
        mock_st.markdown.side_effect = lambda html, **kwargs: chunks.append(html)
        mock_st.columns.side_effect = lambda spec: [MagicMock() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.button.return_value = False
        mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
        mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.session_state = {}

        with patch("ui.components.portfolio_review_experience.st", mock_st):
            render_review_context_header(contract=contract)
            render_portfolio_explanation_block(contract=contract)
            render_review_progress_strip(contract=contract)
            render_theme_review_queue(contract=contract)
            render_healthy_reassurance_block(contract=contract)
            render_allocation_policy_review_section(contract=contract)
            render_review_broker_truth_footer(contract=contract)

        joined = "".join(chunks)
        self.assertIn("apex-review-explanation", joined)
        self.assertIn("apex-review-theme-queue", joined)
        self.assertIn("apex-review-allocation", joined)
        self.assertIn("Zerodha Console", joined)

    def test_experience_composes_main_landmark(self):
        contract = portfolio_review_from_inputs(
            broker=BrokerSnapshot(state="connected", holdings_count=5, portfolio_value_inr=50000),
            portfolio=ZerodhaImportResult(
                holdings=[_holding("TCS", 10, 1000, 1000, 0) for _ in range(5)],
                source="kite",
            ),
            prefs=IntradayPrefs(),
        )
        chunks: list[str] = []
        mock_st = MagicMock()
        mock_st.markdown.side_effect = lambda html, **kwargs: chunks.append(html)
        mock_st.columns.side_effect = lambda spec: [MagicMock() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.button.return_value = False
        mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
        mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.session_state = {}

        with patch("ui.components.portfolio_review_experience.st", mock_st):
            render_portfolio_review_experience(contract=contract)

        joined = "".join(chunks)
        self.assertIn("apex-portfolio-review", joined)

    def test_module_files_exist(self):
        for rel in (
            "ui/components/portfolio_review_experience.py",
            "ui/components/portfolio_review_ui.py",
        ):
            self.assertTrue((REPO_ROOT / rel).is_file())


if __name__ == "__main__":
    unittest.main()
