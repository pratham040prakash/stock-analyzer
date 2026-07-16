"""Tests for personal desktop broker bootstrap."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from analyzer.zerodha import ZerodhaHolding, ZerodhaImportResult
from ui.broker.bootstrap import (
    _is_network_error,
    _map_connection_level,
    _open_positions_count,
    _portfolio_metrics_from_import,
    broker_bootstrap,
    is_broker_configured,
)
from ui.broker.state import BrokerSnapshot, load_broker_snapshot, save_broker_snapshot


class TestBrokerState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "session_state.json"
        self.dir = Path(self.tmp.name)
        self.p = patch("ui.broker.state.BROKER_DIR", self.dir)
        self.p.start()
        self.p2 = patch("ui.broker.state.SNAPSHOT_PATH", self.path)
        self.p2.start()

    def tearDown(self):
        self.p2.stop()
        self.p.stop()
        self.tmp.cleanup()

    def test_save_and_load_snapshot(self):
        snap = BrokerSnapshot(
            state="connected",
            user_name="Test User",
            holdings_count=3,
            portfolio_value_inr=100000,
        )
        save_broker_snapshot(snap)
        loaded = load_broker_snapshot()
        self.assertEqual(loaded.state, "connected")
        self.assertEqual(loaded.user_name, "Test User")
        self.assertEqual(loaded.holdings_count, 3)

    def test_connected_helpers(self):
        snap = BrokerSnapshot(state="connected")
        self.assertTrue(snap.connected())
        self.assertFalse(snap.needs_sign_in())
        limited = BrokerSnapshot(state="limited")
        self.assertTrue(limited.connected())


class TestBrokerBootstrapHelpers(unittest.TestCase):
    def test_network_error_detection(self):
        self.assertTrue(_is_network_error("Connection timed out"))
        self.assertFalse(_is_network_error("Invalid token"))

    def test_map_connection_level(self):
        self.assertEqual(_map_connection_level("ok"), "connected")
        self.assertEqual(_map_connection_level("limited"), "limited")
        self.assertEqual(_map_connection_level("expired"), "expired")

    def test_portfolio_metrics(self):
        imp = ZerodhaImportResult(
            holdings=[
                ZerodhaHolding(
                    kite_symbol="NSE:TCS-EQ",
                    tradingsymbol="TCS",
                    exchange="NSE",
                    quantity=2,
                    average_price=3500,
                    last_price=3600,
                    pnl=200,
                    yahoo_symbol="TCS.NS",
                )
            ],
            source="kite",
        )
        value, pnl = _portfolio_metrics_from_import(imp)
        self.assertEqual(value, 7200.0)
        self.assertEqual(pnl, 200.0)

    @patch("ui.broker.bootstrap.get_kite_client")
    def test_open_positions_count(self, mock_client):
        kite = MagicMock()
        kite.positions.return_value = {
            "net": [{"quantity": 10}, {"quantity": 0}],
            "day": [{"quantity": -5}],
        }
        mock_client.return_value = kite
        self.assertEqual(_open_positions_count(), 2)

    @patch("ui.broker.bootstrap.load_env_credentials")
    def test_is_broker_configured(self, mock_creds):
        mock_creds.return_value = {"api_key": "k", "api_secret": "s", "access_token": ""}
        self.assertTrue(is_broker_configured())
        mock_creds.return_value = {"api_key": "", "api_secret": "", "access_token": ""}
        self.assertFalse(is_broker_configured())


class TestBrokerBootstrap(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.path = self.dir / "session_state.json"
        self.p_dir = patch("ui.broker.state.BROKER_DIR", self.dir)
        self.p_path = patch("ui.broker.state.SNAPSHOT_PATH", self.path)
        self.p_dir.start()
        self.p_path.start()

    def tearDown(self):
        self.p_path.stop()
        self.p_dir.stop()
        self.tmp.cleanup()

    @patch("ui.broker.bootstrap.is_broker_configured", return_value=False)
    def test_not_configured(self, _cfg):
        snap = broker_bootstrap(force_sync=True)
        self.assertEqual(snap.state, "not_configured")

    @patch("ui.broker.bootstrap.sync_holdings_from_kite")
    @patch("ui.broker.bootstrap.fetch_kite_margins")
    @patch("ui.broker.bootstrap._open_positions_count", return_value=1)
    @patch("ui.broker.bootstrap.fetch_kite_profile")
    @patch("ui.broker.bootstrap.kite_connection_status")
    @patch("ui.broker.bootstrap.is_broker_configured", return_value=True)
    @patch("ui.broker.bootstrap.load_env_credentials")
    def test_connected_sync(
        self,
        mock_creds,
        _cfg,
        mock_status,
        mock_profile,
        _pos,
        mock_margins,
        mock_sync,
    ):
        mock_creds.return_value = {"api_key": "k", "api_secret": "s", "access_token": "t"}
        mock_status.return_value = {"level": "ok", "market_data": "ok"}
        mock_profile.return_value = {"user_id": "AB12", "user_name": "Pratham"}
        mock_sync.return_value = (
            ZerodhaImportResult(
                holdings=[
                    ZerodhaHolding(
                        kite_symbol="NSE:TCS-EQ",
                        tradingsymbol="TCS",
                        exchange="NSE",
                        quantity=1,
                        last_price=100.0,
                        pnl=5.0,
                        yahoo_symbol="TCS.NS",
                    )
                ],
                source="kite",
            ),
            "",
        )
        mock_margins.return_value = {"equity": {"available": {"cash": 25000}}}

        snap = broker_bootstrap(force_sync=True)
        self.assertEqual(snap.state, "connected")
        self.assertEqual(snap.holdings_count, 1)
        self.assertEqual(snap.available_cash_inr, 25000.0)
        self.assertEqual(snap.positions_count, 1)

    @patch("ui.broker.bootstrap.kite_connection_status")
    @patch("ui.broker.bootstrap.is_broker_configured", return_value=True)
    @patch("ui.broker.bootstrap.load_env_credentials")
    def test_expired_session(self, mock_creds, _cfg, mock_status):
        mock_creds.return_value = {"api_key": "k", "api_secret": "s", "access_token": "t"}
        mock_status.return_value = {
            "level": "expired",
            "market_data": "expired",
            "detail": "Reconnect to Zerodha.",
        }
        snap = broker_bootstrap(force_sync=True)
        self.assertEqual(snap.state, "expired")


if __name__ == "__main__":
    unittest.main()
