"""Tests for OAuth callback handling and startup re-entry."""

import unittest
from unittest.mock import MagicMock, patch

from ui.components.broker_startup import run_broker_startup
from ui.components.kite_auth import (
    get_request_token,
    has_kite_oauth_callback,
    handle_kite_redirect,
    process_oauth_callback_if_present,
)


class TestOAuthCallbackDetection(unittest.TestCase):
    @patch("ui.components.kite_auth._query_param", return_value="abc123token")
    @patch("ui.components.kite_auth._query_param_from_context_url", return_value="")
    def test_has_callback_from_query_params(self, *_mocks):
        self.assertTrue(has_kite_oauth_callback())
        self.assertEqual(get_request_token(), "abc123token")

    @patch("ui.components.kite_auth._query_param", return_value="")
    @patch(
        "ui.components.kite_auth._query_param_from_context_url",
        return_value="fallbacktoken123",
    )
    def test_has_callback_from_context_url(self, *_mocks):
        self.assertTrue(has_kite_oauth_callback())
        self.assertEqual(get_request_token(), "fallbacktoken123")

    @patch("ui.components.kite_auth._query_param", return_value="")
    @patch("ui.components.kite_auth._query_param_from_context_url", return_value="")
    def test_no_callback_when_token_missing(self, *_mocks):
        self.assertFalse(has_kite_oauth_callback())


class TestBrokerStartupOAuthOrder(unittest.TestCase):
    @patch("ui.components.broker_startup.st")
    @patch("ui.components.broker_startup.get_request_token", return_value="tok12345678")
    @patch("ui.components.broker_startup.handle_kite_redirect", return_value=True)
    @patch("ui.components.broker_startup._clear_oauth_query_params")
    @patch("ui.components.broker_startup.broker_bootstrap")
    @patch("ui.components.broker_startup.hydrate_kite_access_token")
    @patch("ui.components.broker_startup.load_env_credentials")
    def test_oauth_before_bootstrap(
        self,
        mock_creds,
        mock_hydrate,
        mock_bootstrap,
        _clear,
        mock_handle,
        _token,
        mock_st,
    ):
        mock_creds.return_value = {"api_key": "k", "api_secret": "s", "access_token": ""}
        mock_st.session_state = {}
        mock_st.empty.return_value = MagicMock()

        call_order: list[str] = []

        def _handle(*_a, **_k):
            call_order.append("handle_kite_redirect")
            return True

        def _bootstrap(*_a, **_k):
            call_order.append("broker_bootstrap")

        mock_handle.side_effect = _handle
        mock_bootstrap.side_effect = _bootstrap

        with patch("ui.components.broker_startup.get_request_token", side_effect=["tok12345678", ""]):
            run_broker_startup()

        self.assertEqual(call_order, ["handle_kite_redirect", "broker_bootstrap"])
        mock_st.rerun.assert_called_once()

    @patch("ui.components.broker_startup._show_broker_toast")
    @patch("ui.components.broker_startup.get_request_token", return_value="")
    @patch("ui.components.broker_startup.handle_kite_redirect")
    @patch("ui.components.broker_startup.st")
    def test_skips_when_startup_done_and_no_callback(self, mock_st, mock_handle, _token, _toast):
        mock_st.session_state = {"_broker_startup_done": True}
        mock_st.empty.return_value = MagicMock()

        run_broker_startup()

        mock_handle.assert_not_called()


class TestHandleKiteRedirect(unittest.TestCase):
    @patch("ui.components.kite_auth.get_request_token", return_value="tok12345678")
    @patch("ui.components.kite_auth.st")
    def test_skips_already_exchanged_token(self, mock_st, _token):
        mock_st.session_state = {"kite_token_exchanged": "tok12345678"}

        with patch("ui.components.kite_auth.exchange_request_token") as mock_exchange:
            result = handle_kite_redirect(quiet=True)

        self.assertFalse(result)
        mock_exchange.assert_not_called()


class TestEarlyOAuthGate(unittest.TestCase):
    @patch("ui.components.kite_auth.st")
    @patch("ui.broker.bootstrap.broker_bootstrap")
    @patch("analyzer.zerodha.hydrate_kite_access_token")
    @patch("ui.components.kite_auth.handle_kite_redirect", return_value=True)
    @patch("ui.components.kite_auth.get_request_token", return_value="tok12345678")
    def test_process_oauth_reruns_before_nav(
        self,
        _token,
        mock_handle,
        _hydrate,
        mock_bootstrap,
        mock_st,
    ):
        mock_st.session_state = {}

        process_oauth_callback_if_present()

        mock_handle.assert_called_once_with(quiet=True)
        mock_bootstrap.assert_called_once_with(force_sync=True)
        mock_st.rerun.assert_called_once()
        self.assertEqual(mock_st.session_state["nav_tab"], "My Portfolio")


if __name__ == "__main__":
    unittest.main()
