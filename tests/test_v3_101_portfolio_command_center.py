"""V3-101 — Portfolio Command Center contracts and render integration."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from analyzer.intraday_prefs import IntradayPrefs
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult
from ui.broker.state import BrokerSnapshot
from ui.components.portfolio_command_center import (
    render_allocation_snapshot_card,
    render_attention_list_card,
    render_broker_truth_footer,
    render_holdings_preview_card,
    render_portfolio_action_row,
    render_portfolio_command_center,
    render_portfolio_depth_popover,
    render_portfolio_health_hero,
    render_portfolio_status_strip,
    render_standouts_card,
)
from ui.components.portfolio_overview_ui import portfolio_overview_from_inputs

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


def _balanced_portfolio() -> ZerodhaImportResult:
    symbols = ("RELIANCE", "TCS", "INFY", "HDFCBANK", "ITC")
    return ZerodhaImportResult(
        holdings=[_holding(sym, 10, 1000, 1000, 100) for sym in symbols],
        source="kite",
    )


class TestPortfolioOverviewContracts(unittest.TestCase):
    def test_healthy_connected_portfolio(self):
        broker = BrokerSnapshot(
            state="connected",
            holdings_count=5,
            portfolio_value_inr=50000.0,
            available_cash_inr=5000.0,
            today_unrealized_pnl_inr=800.0,
            last_sync_at="2m ago",
        )
        portfolio = _balanced_portfolio()
        contract = portfolio_overview_from_inputs(
            broker=broker,
            portfolio=portfolio,
            prefs=IntradayPrefs(capital=50000, allocation_pct=32),
        )
        self.assertEqual(contract.hero.badge_key, "healthy")
        self.assertEqual(contract.action.primary_action, "holdings")
        self.assertEqual(contract.status.holdings_count_label, "5")
        self.assertIn("Zerodha Console", contract.broker_footer)
        self.assertLessEqual(len(contract.attention.items), 3)

    def test_connect_when_disconnected_and_empty(self):
        contract = portfolio_overview_from_inputs(
            broker=BrokerSnapshot(state="disconnected"),
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        self.assertEqual(contract.hero.badge_key, "connect")
        self.assertEqual(contract.action.primary_action, "connect")

    def test_attention_on_concentration(self):
        broker = BrokerSnapshot(state="connected", holdings_count=1, portfolio_value_inr=100000)
        portfolio = ZerodhaImportResult(
            holdings=[_holding("RELIANCE", 10, 1000, 10000, 0)],
            source="manual",
        )
        contract = portfolio_overview_from_inputs(
            broker=broker,
            portfolio=portfolio,
            prefs=IntradayPrefs(),
        )
        self.assertEqual(contract.hero.badge_key, "attention")
        self.assertEqual(contract.action.primary_action, "review")
        self.assertGreaterEqual(len(contract.attention.items), 1)

    def test_stale_sync_primary_action(self):
        broker = BrokerSnapshot(
            state="limited",
            holdings_count=5,
            portfolio_value_inr=50000,
            last_sync_at="18h ago",
        )
        contract = portfolio_overview_from_inputs(
            broker=broker,
            portfolio=_balanced_portfolio(),
            prefs=IntradayPrefs(),
        )
        self.assertEqual(contract.action.primary_action, "sync")


class TestPortfolioCommandCenterRender(unittest.TestCase):
    def test_render_functions_emit_expected_markers(self):
        broker = BrokerSnapshot(
            state="connected",
            holdings_count=2,
            portfolio_value_inr=200000.0,
            available_cash_inr=50000.0,
        )
        portfolio = ZerodhaImportResult(
            holdings=[
                _holding("RELIANCE", 10, 2400, 2500, 1000),
                _holding("TCS", 10, 2400, 2500, 500),
                _holding("INFY", 10, 1500, 1550, 200),
                _holding("HDFCBANK", 10, 1600, 1650, 300),
            ],
            source="kite",
        )
        contract = portfolio_overview_from_inputs(
            broker=broker,
            portfolio=portfolio,
            prefs=IntradayPrefs(),
        )
        chunks: list[str] = []

        def capture(html: str, **kwargs) -> None:
            chunks.append(html)

        mock_st = MagicMock()
        mock_st.markdown.side_effect = capture
        mock_st.columns.return_value = [MagicMock(), MagicMock()]
        mock_st.button.return_value = False
        mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
        mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)

        with patch("ui.components.portfolio_command_center.st", mock_st):
            render_portfolio_health_hero(contract=contract)
            render_portfolio_status_strip(contract=contract)
            render_allocation_snapshot_card(contract=contract)
            render_standouts_card(contract=contract)
            render_attention_list_card(contract=contract)
            render_holdings_preview_card(contract=contract)
            render_broker_truth_footer(contract=contract)

        joined = "".join(chunks)
        self.assertIn("apex-portfolio-hero", joined)
        self.assertIn("apex-status-strip", joined)
        self.assertIn("apex-portfolio-allocation", joined)
        self.assertIn("apex-portfolio-standouts", joined)
        self.assertIn("apex-portfolio-attention", joined)
        self.assertIn("apex-portfolio-preview", joined)
        self.assertIn("Zerodha Console", joined)

    def test_command_center_composes_all_sections(self):
        contract = portfolio_overview_from_inputs(
            broker=BrokerSnapshot(state="connected", holdings_count=1, portfolio_value_inr=50000),
            portfolio=ZerodhaImportResult(
                holdings=[_holding("TCS", 1, 3600, 3700, 100)],
                source="manual",
            ),
            prefs=IntradayPrefs(),
        )
        chunks: list[str] = []

        mock_st = MagicMock()
        mock_st.markdown.side_effect = lambda html, **kwargs: chunks.append(html)
        mock_st.columns.side_effect = [
            [MagicMock(), MagicMock()],
            [MagicMock(), MagicMock()],
        ]
        mock_st.button.return_value = False
        mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
        mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)

        with patch("ui.components.portfolio_command_center.st", mock_st):
            with patch(
                "ui.components.portfolio_command_center.render_portfolio_action_row"
            ) as action_row:
                render_portfolio_command_center(contract=contract)
                action_row.assert_called_once()

        joined = "".join(chunks)
        self.assertIn("apex-portfolio-command-center", joined)
        self.assertIn("apex-portfolio-below-fold", joined)

    def test_module_files_exist(self):
        for rel in (
            "ui/components/portfolio_overview_ui.py",
            "ui/components/portfolio_command_center.py",
            "ui/components/understand_popover.py",
            "analyzer/use_cases/portfolio_overview_assembly.py",
            "analyzer/use_cases/portfolio_overview_models.py",
        ):
            self.assertTrue((REPO_ROOT / rel).is_file())

    def test_understand_popover_shared_renderer(self):
        contract = portfolio_overview_from_inputs(
            broker=BrokerSnapshot(state="connected", holdings_count=5, portfolio_value_inr=50000),
            portfolio=_balanced_portfolio(),
            prefs=IntradayPrefs(),
        )
        with patch("ui.components.portfolio_command_center.render_understand_popover") as popover:
            render_portfolio_depth_popover(contract=contract)
            popover.assert_called_once()


if __name__ == "__main__":
    unittest.main()
