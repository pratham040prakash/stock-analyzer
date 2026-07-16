"""Tests for OAuth callback handling and startup re-entry."""

import unittest
from unittest.mock import MagicMock, patch

from ui.components.broker_startup import run_broker_startup
from ui.components.kite_auth import (
    has_kite_oauth_callback,
    handle_kite_redirect,
    process_oauth_callback_early,
)


class TestOAuthCallbackDetection(unittest.TestCase):
    @patch("ui.components.kite_auth.st")
    def test_has_callback_when_token_present(self, mock_st):
        mock_st.query_params.get.return_value = "abc123token"
        self.assertTrue(has_kite_oauth_callback())

    @patch("ui.components.kite_auth.st")
    def test_no_callback_when_token_missing(self, mock_st):
        mock_st.query_params.get.return_value = ""
        self.assertFalse(has_kite_oauth_callback())


class TestBrokerStartupOAuthReentry(unittest.TestCase):
    @patch("ui.components.broker_startup._show_broker_toast")
    @patch("ui.components.broker_startup.has_kite_oauth_callback", return_value=True)
    @patch("ui.components.broker_startup.handle_kite_redirect", return_value=True)
    @patch("ui.components.broker_startup.broker_bootstrap")
    @patch("ui.components.broker_startup.start_kite_ticker_on_app_start")
    @patch("ui.components.broker_startup.hydrate_kite_access_token")
    @patch("ui.components.broker_startup.st")
    def test_processes_callback_when_startup_already_done(
        self,
        mock_st,
        _hydrate,
        _ticker,
        mock_bootstrap,
        mock_handle,
        _has_cb,
        _toast,
    ):
        mock_st.session_state = {"_broker_startup_done": True}
        mock_st.empty.return_value = MagicMock()

        run_broker_startup()

        mock_handle.assert_called_once_with(quiet=True)
        mock_bootstrap.assert_called_once()
        self.assertTrue(mock_st.session_state["_broker_startup_done"])

    @patch("ui.components.broker_startup._show_broker_toast")
    @patch("ui.components.broker_startup.has_kite_oauth_callback", return_value=False)
    @patch("ui.components.broker_startup.handle_kite_redirect")
    @patch("ui.components.broker_startup.st")
    def test_skips_when_startup_done_and_no_callback(self, mock_st, mock_handle, _has_cb, _toast):
        mock_st.session_state = {"_broker_startup_done": True}

        run_broker_startup()

        mock_handle.assert_not_called()


class TestProcessOAuthCallbackEarly(unittest.TestCase):
    @patch("ui.components.kite_auth.st")
    @patch("ui.components.kite_auth.handle_kite_redirect", return_value=True)
    @patch("ui.components.kite_auth._clear_oauth_query_params")
    def test_schedules_rerun_when_token_present(self, _clear, _handle, mock_st):
        mock_st.query_params = {"request_token": "abc123456789"}
        mock_st.session_state = {}

        with patch("ui.components.kite_auth._query_param", return_value="abc123456789"):
            process_oauth_callback_early()

        mock_st.rerun.assert_called_once()
        self.assertEqual(mock_st.session_state["_oauth_rerun_count"], 1)

    @patch("ui.components.kite_auth.st")
    def test_no_rerun_without_token(self, mock_st):
        mock_st.session_state = {}
        with patch("ui.components.kite_auth._query_param", return_value=""):
            process_oauth_callback_early()
        mock_st.rerun.assert_not_called()


class TestHandleKiteRedirect(unittest.TestCase):
    @patch("ui.components.kite_auth.st")
    def test_skips_already_exchanged_token(self, mock_st):
        mock_st.query_params.get.return_value = "tok12345678"
        mock_st.session_state = {"kite_token_exchanged": "tok12345678"}

        with patch("ui.components.kite_auth.exchange_request_token") as mock_exchange:
            result = handle_kite_redirect(quiet=True)

        self.assertFalse(result)
        mock_exchange.assert_not_called()


if __name__ == "__main__":
    unittest.main()
