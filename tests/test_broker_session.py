"""Unit tests for BrokerSessionService (ETS-002.1 Commits A-1–A-4)."""

import unittest
from unittest.mock import patch

from analyzer.broker import BrokerSessionService
from analyzer.broker.session import BrokerSessionService as SessionClassDirect
from ui.broker.state import BrokerSnapshot


class TestBrokerSessionServiceSkeleton(unittest.TestCase):
    """Verify package import, class init, and method surface."""

    PLACEHOLDER_METHODS = (
        "disconnect",
        "get_health",
        "ensure_app_credentials",
        "get_login_url",
    )

    IMPLEMENTED_METHODS = (
        "process_oauth_callback_if_present",
        "initialize",
        "restore_session",
        "validate_session",
        "clear_session",
    )

    def test_package_exports_broker_session_service(self):
        self.assertIs(BrokerSessionService, SessionClassDirect)

    def test_class_initializes(self):
        service = BrokerSessionService()
        self.assertIsInstance(service, BrokerSessionService)

    def test_implemented_methods_exist(self):
        for name in self.IMPLEMENTED_METHODS:
            self.assertTrue(callable(getattr(BrokerSessionService, name)), name)

    def test_placeholder_methods_raise_not_implemented(self):
        service = BrokerSessionService()
        for name in self.PLACEHOLDER_METHODS:
            with self.subTest(method=name):
                with self.assertRaises(NotImplementedError):
                    getattr(service, name)()

    def test_process_oauth_delegates_to_kite_auth(self):
        service = BrokerSessionService()
        with patch(
            "ui.components.kite_auth.process_oauth_callback_if_present"
        ) as mock_process:
            service.process_oauth_callback_if_present()
        mock_process.assert_called_once_with()

    def test_process_oauth_does_not_reimplement_exchange(self):
        service = BrokerSessionService()
        with patch(
            "ui.components.kite_auth.process_oauth_callback_if_present"
        ) as mock_process:
            with patch("analyzer.zerodha.exchange_request_token") as mock_exchange:
                service.process_oauth_callback_if_present()
        mock_process.assert_called_once_with()
        mock_exchange.assert_not_called()

    def test_methods_have_docstrings(self):
        for name in self.PLACEHOLDER_METHODS + self.IMPLEMENTED_METHODS:
            method = getattr(BrokerSessionService, name)
            self.assertIsNotNone(method.__doc__)
            self.assertGreater(len(method.__doc__.strip()), 20)


class TestBrokerSessionInitialize(unittest.TestCase):
    """Startup orchestration via initialize()."""

    def test_initialize_early_oauth_delegates_only(self):
        service = BrokerSessionService()
        with patch.object(service, "process_oauth_callback_if_present") as mock_oauth:
            with patch.object(service, "_run_broker_startup") as mock_startup:
                result = service.initialize(early_oauth=True)
        mock_oauth.assert_called_once_with()
        mock_startup.assert_not_called()
        self.assertIsNone(result)

    def test_initialize_main_runs_pipeline_and_returns_snapshot(self):
        service = BrokerSessionService()
        snap = BrokerSnapshot(state="connected", holdings_count=2)
        with patch.object(service, "restore_session", return_value=True) as mock_restore:
            with patch.object(service, "validate_session", return_value=True) as mock_validate:
                with patch.object(service, "_run_broker_startup") as mock_startup:
                    with patch(
                        "ui.broker.state.load_broker_snapshot", return_value=snap
                    ):
                        result = service.initialize()
        mock_restore.assert_called_once_with()
        mock_validate.assert_called_once_with()
        mock_startup.assert_called_once_with()
        self.assertIs(result, snap)
        self.assertEqual(result.holdings_count, 2)

    def test_initialize_main_does_not_call_early_oauth(self):
        service = BrokerSessionService()
        with patch.object(service, "process_oauth_callback_if_present") as mock_oauth:
            with patch.object(service, "restore_session", return_value=False):
                with patch.object(service, "validate_session", return_value=False):
                    with patch.object(service, "_run_broker_startup"):
                        with patch(
                            "ui.broker.state.load_broker_snapshot",
                            return_value=BrokerSnapshot(),
                        ):
                            service.initialize()
        mock_oauth.assert_not_called()

    def test_run_broker_startup_delegates(self):
        service = BrokerSessionService()
        with patch("ui.components.broker_startup.run_broker_startup") as mock_run:
            service._run_broker_startup()
        mock_run.assert_called_once_with()

    @patch("analyzer.zerodha.hydrate_kite_access_token")
    @patch("analyzer.zerodha.load_env_credentials", return_value={"access_token": "tok"})
    def test_restore_session_delegates(self, _creds, mock_hydrate):
        service = BrokerSessionService()
        self.assertTrue(service.restore_session())
        mock_hydrate.assert_called_once_with()

    @patch(
        "analyzer.kite_status.kite_connection_status",
        return_value={"level": "ok"},
    )
    @patch(
        "analyzer.zerodha.load_env_credentials",
        return_value={"api_key": "k", "access_token": "tok"},
    )
    def test_validate_session_checks_token_presence(self, _creds, _status):
        self.assertTrue(BrokerSessionService().validate_session())

    @patch("analyzer.zerodha.load_env_credentials", return_value={"access_token": ""})
    def test_validate_session_false_without_token(self, _creds):
        self.assertFalse(BrokerSessionService().validate_session())

    @patch.object(BrokerSessionService, "clear_session")
    @patch(
        "analyzer.kite_status.kite_connection_status",
        return_value={"level": "expired"},
    )
    @patch(
        "analyzer.zerodha.load_env_credentials",
        return_value={"api_key": "k", "access_token": "tok"},
    )
    def test_validate_session_clears_expired(self, _creds, _status, mock_clear):
        self.assertFalse(BrokerSessionService().validate_session())
        mock_clear.assert_called_once()

    @patch(
        "analyzer.kite_status.kite_connection_status",
        return_value={"level": "ok"},
    )
    @patch(
        "analyzer.zerodha.load_env_credentials",
        return_value={"api_key": "k", "access_token": "tok"},
    )
    def test_validate_session_true_when_ok(self, _creds, _status):
        self.assertTrue(BrokerSessionService().validate_session())

    @patch("analyzer.zerodha.save_access_token_to_env")
    @patch("analyzer.kite_status.clear_kite_probe_cache")
    def test_clear_session_clears_token(self, mock_cache, mock_save):
        BrokerSessionService().clear_session()
        mock_save.assert_called_once_with("")
        mock_cache.assert_called_once()

    def test_late_oauth_routes_to_session_service(self):
        service = BrokerSessionService()
        with patch.object(service, "_oauth_callback_pending", return_value=True):
            with patch.object(service, "process_oauth_callback_if_present") as mock_oauth:
                with patch.object(service, "_run_broker_startup") as mock_startup:
                    with patch(
                        "ui.broker.state.load_broker_snapshot",
                        return_value=BrokerSnapshot(),
                    ):
                        service.initialize()
        mock_oauth.assert_called_once()
        mock_startup.assert_not_called()

    def test_single_oauth_owner_in_app_source(self):
        from pathlib import Path

        app_source = (Path(__file__).resolve().parents[1] / "app.py").read_text(
            encoding="utf-8"
        )
        self.assertEqual(app_source.count("initialize(early_oauth=True)"), 1)
        self.assertNotIn("process_oauth_callback_if_present()", app_source)


class TestAppStartupEntryPoint(unittest.TestCase):
    """Verify app.py uses BrokerSessionService as the sole startup boundary."""

    @staticmethod
    def _app_source() -> str:
        from pathlib import Path

        return (Path(__file__).resolve().parents[1] / "app.py").read_text(encoding="utf-8")

    def test_app_uses_initialize_early_oauth(self):
        source = self._app_source()
        self.assertIn("initialize(early_oauth=True)", source)

    def test_app_uses_initialize_main_startup(self):
        source = self._app_source()
        self.assertIn("broker_session.initialize()", source)

    def test_app_does_not_import_broker_startup(self):
        source = self._app_source()
        self.assertNotIn("from ui.components.broker_startup import", source)
        self.assertNotIn("run_broker_startup", source)

    def test_app_does_not_import_kite_auth_oauth_directly(self):
        source = self._app_source()
        self.assertNotIn(
            "from ui.components.kite_auth import process_oauth_callback_if_present",
            source,
        )


if __name__ == "__main__":
    unittest.main()
