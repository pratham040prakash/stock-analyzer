"""V3-102 — Holdings Experience contracts and render integration."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from analyzer.intraday_prefs import IntradayPrefs
from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult
from ui.broker.state import BrokerSnapshot
from ui.components.holdings_experience import (
    _apply_filters_and_sort,
    render_holdings_broker_truth_footer,
    render_holdings_card_list,
    render_holdings_context_bar,
    render_holdings_experience,
    render_holdings_table_region,
    render_watchlist_collapsible,
)
from ui.components.holdings_experience_ui import (
    HoldingsExperienceContract,
    HoldingsRowContract,
    holdings_experience_from_inputs,
    holdings_row_understand_contract,
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


def _row(
    symbol: str,
    *,
    weight: float = 10.0,
    value: float = 10000.0,
    qty: float = 10.0,
    health_key: str = "ok",
) -> HoldingsRowContract:
    return HoldingsRowContract(
        symbol=symbol,
        name=symbol,
        quantity=qty,
        value_inr=value,
        weight_pct=weight,
        quantity_label=str(int(qty)),
        average_cost_label="₹1,000",
        ltp_label="₹1,100",
        value_label=f"₹{value:,.0f}",
        weight_label=f"{weight:.1f}%",
        health_key=health_key,
        health_label="OK" if health_key == "ok" else "Attention",
        pnl_label="+₹100",
        stale=False,
        attention_reason="",
        understand_headline=f"You hold {int(qty)} shares · {weight:.1f}% of portfolio",
    )


class TestHoldingsExperienceContracts(unittest.TestCase):
    def test_connected_portfolio_rows_sorted_by_weight(self):
        broker = BrokerSnapshot(
            state="connected",
            holdings_count=3,
            portfolio_value_inr=30000.0,
            last_sync_at="2m ago",
        )
        portfolio = ZerodhaImportResult(
            holdings=[
                _holding("INFY", 10, 1000, 1000, 0),
                _holding("RELIANCE", 10, 1000, 2000, 1000),
                _holding("TCS", 10, 1000, 1000, 0),
            ],
            source="kite",
        )
        contract = holdings_experience_from_inputs(
            broker=broker,
            portfolio=portfolio,
            prefs=IntradayPrefs(),
        )
        self.assertTrue(contract.context.has_holdings)
        self.assertEqual(len(contract.rows), 3)
        self.assertGreaterEqual(contract.rows[0].weight_pct, contract.rows[1].weight_pct)
        self.assertIn("quantities, cost basis", contract.broker_footer)

    def test_attention_health_matches_overview(self):
        broker = BrokerSnapshot(state="connected", holdings_count=1, portfolio_value_inr=100000)
        portfolio = ZerodhaImportResult(
            holdings=[_holding("RELIANCE", 10, 1000, 10000, 0)],
            source="manual",
        )
        contract = holdings_experience_from_inputs(
            broker=broker,
            portfolio=portfolio,
            prefs=IntradayPrefs(),
        )
        self.assertEqual(contract.rows[0].health_key, "attention")
        self.assertTrue(contract.rows[0].attention_reason)

    def test_watchlist_excludes_held_symbols(self):
        broker = BrokerSnapshot(state="connected", holdings_count=1, portfolio_value_inr=10000)
        portfolio = ZerodhaImportResult(
            holdings=[
                _holding("TCS", 5, 1000, 1100, 100),
                _holding("WIPRO", 0, 0, 500, 0),
            ],
            source="kite",
        )
        contract = holdings_experience_from_inputs(
            broker=broker,
            portfolio=portfolio,
            prefs=IntradayPrefs(),
        )
        self.assertEqual(len(contract.rows), 1)
        self.assertEqual(contract.rows[0].symbol, "TCS")
        self.assertEqual(len(contract.watchlist), 1)
        self.assertEqual(contract.watchlist[0].symbol, "WIPRO")

    def test_disconnected_empty_context(self):
        contract = holdings_experience_from_inputs(
            broker=BrokerSnapshot(state="disconnected"),
            portfolio=None,
            prefs=IntradayPrefs(),
        )
        self.assertFalse(contract.context.has_holdings)
        self.assertTrue(contract.context.show_connect_cta)


class TestHoldingsPresentationFilters(unittest.TestCase):
    def test_search_and_attention_filter(self):
        rows = (
            _row("RELIANCE", health_key="attention"),
            _row("TCS"),
            _row("INFY"),
        )
        filtered = _apply_filters_and_sort(
            rows,
            search="tcs",
            filter_key="all",
            sort_key="weight_desc",
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].symbol, "TCS")

        attention_only = _apply_filters_and_sort(
            rows,
            search="",
            filter_key="attention",
            sort_key="weight_desc",
        )
        self.assertEqual(len(attention_only), 1)
        self.assertEqual(attention_only[0].symbol, "RELIANCE")


class TestHoldingsExperienceRender(unittest.TestCase):
    def test_render_markers(self):
        contract = holdings_experience_from_inputs(
            broker=BrokerSnapshot(state="connected", holdings_count=2, portfolio_value_inr=20000),
            portfolio=ZerodhaImportResult(
                holdings=[
                    _holding("RELIANCE", 10, 1000, 1100, 100),
                    _holding("TCS", 5, 2000, 2100, 50),
                ],
                source="kite",
            ),
            prefs=IntradayPrefs(),
        )
        chunks: list[str] = []

        mock_st = MagicMock()
        mock_st.markdown.side_effect = lambda html, **kwargs: chunks.append(html)
        mock_st.columns.side_effect = lambda spec: [MagicMock() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.button.return_value = False
        mock_st.text_input.return_value = ""
        mock_st.radio.return_value = "all"
        mock_st.selectbox.return_value = "weight_desc"
        mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
        mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.expander.return_value.__enter__ = MagicMock(return_value=None)
        mock_st.expander.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.session_state = {}

        with patch("ui.components.holdings_experience.st", mock_st):
            render_holdings_context_bar(contract=contract)
            render_holdings_table_region(rows=contract.rows, empty_message="empty")
            render_holdings_card_list(rows=contract.rows, empty_message="empty")
            render_watchlist_collapsible(contract=contract)
            render_holdings_broker_truth_footer(contract=contract)

        joined = "".join(chunks)
        self.assertIn("apex-holdings-context", joined)
        self.assertIn("apex-holdings-table", joined)
        self.assertIn("apex-holdings-card-list", joined)
        self.assertIn("quantities, cost basis", joined)

    def test_experience_composes_main_landmark(self):
        contract = holdings_experience_from_inputs(
            broker=BrokerSnapshot(state="connected", holdings_count=1, portfolio_value_inr=5000),
            portfolio=ZerodhaImportResult(
                holdings=[_holding("TCS", 1, 3600, 3700, 100)],
                source="manual",
            ),
            prefs=IntradayPrefs(),
        )
        chunks: list[str] = []
        mock_st = MagicMock()
        mock_st.markdown.side_effect = lambda html, **kwargs: chunks.append(html)
        mock_st.columns.side_effect = lambda spec: [MagicMock() for _ in range(len(spec) if isinstance(spec, list) else spec)]
        mock_st.button.return_value = False
        mock_st.text_input.return_value = ""
        mock_st.radio.return_value = "all"
        mock_st.selectbox.return_value = "weight_desc"
        mock_st.popover.return_value.__enter__ = MagicMock(return_value=None)
        mock_st.popover.return_value.__exit__ = MagicMock(return_value=False)
        mock_st.session_state = {}

        with patch("ui.components.holdings_experience.st", mock_st):
            render_holdings_experience(contract=contract)

        joined = "".join(chunks)
        self.assertIn("apex-holdings-experience", joined)

    def test_row_understand_uses_shared_sections(self):
        row = _row("RELIANCE", weight=14.2, qty=120)
        contract = holdings_row_understand_contract(row)
        titles = [section.title for section in contract.sections]
        self.assertEqual(
            titles,
            [
                "Position",
                "Why this weight matters",
                "Cost basis vs current value",
                "Health indicator",
            ],
        )

    def test_module_files_exist(self):
        for rel in (
            "ui/components/holdings_experience.py",
            "ui/components/holdings_experience_ui.py",
        ):
            self.assertTrue((REPO_ROOT / rel).is_file())


if __name__ == "__main__":
    unittest.main()
