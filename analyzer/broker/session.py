"""BrokerSessionService — single session authority for broker OAuth and lifecycle.

Architecture (ETS-002.1 / APEX-005 §31)
---------------------------------------

**Current:** UI components (``kite_auth``, ``broker_startup``, ``broker_setup_wizard``)
call ``analyzer.zerodha`` and ``ui.broker.bootstrap`` directly, with duplicate OAuth
paths and plaintext ``.env`` credential storage.

**Target:** Experience layer depends only on ``BrokerSessionService``. The service
coordinates (in later commits):

- OAuth callback handling and login URL generation
- ``BrokerCredentialStore`` (secure app credentials + access tokens)
- ``ZerodhaBrokerAdapter`` (multi-broker-ready execution boundary)
- ``broker_bootstrap`` (portfolio sync and ``BrokerSnapshot``)

Dependency direction::

    ui/*  →  BrokerSessionService  →  credentials / adapter / bootstrap  →  zerodha.py

``BrokerTruthService`` (``analyzer/broker_truth``) remains separate — it imports
executed trades; it does not own connection lifecycle.

This module is introduced in ETS-002.1 Commit A-1 as a skeleton. Commit A-2
delegates early OAuth orchestration to ``ui.components.kite_auth`` without
changing behaviour. Commit A-4 adds ``initialize()`` as the single startup
orchestration entry for the Experience layer. Commit A-5 finalizes the
lifecycle: one OAuth owner, one session owner, expired-token clearing.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ui.broker.state import BrokerSnapshot

logger = logging.getLogger(__name__)


class BrokerSessionService:
    """Single session authority for broker OAuth, credentials, and connection state.

    UI and ``app.py`` will eventually call this service instead of ``zerodha.py``
    or scattered broker UI helpers. Implementation is deferred to ETS-002.1
    commits A-2 onward.
    """

    def __init__(self) -> None:
        """Initialize the session service.

        Optional dependencies (credential store, broker adapter, bootstrap) will
        be injected or constructed here in later commits.
        """

    def process_oauth_callback_if_present(self) -> None:
        """Process a Kite OAuth redirect if ``request_token`` is present.

        Delegates to ``ui.components.kite_auth.process_oauth_callback_if_present``.
        Intended to run immediately after ``st.set_page_config()`` in ``app.py``,
        before navigation init or credential gates. On callback: exchange token,
        persist session, bootstrap, strip URL params, and ``st.rerun()``.

        Returns:
            None. When a callback is present the delegate may call ``st.rerun()``
            and never return to the caller.
        """
        from ui.components.kite_auth import (
            process_oauth_callback_if_present as _process_oauth_callback,
        )

        _process_oauth_callback()

    def initialize(self, *, early_oauth: bool = False) -> BrokerSnapshot | None:
        """Single public startup entry for broker session and portfolio sync.

        **Early OAuth** (``early_oauth=True``): run immediately after
        ``st.set_page_config()`` — before nav init or credential wizard.
        Delegates to ``process_oauth_callback_if_present()``; may ``st.rerun()``.

        **Main startup** (default): run after ``ensure_broker_configured()``.
        Orchestrates restore → validate → broker startup → returns snapshot.

        Returns:
            ``BrokerSnapshot`` after main startup; ``None`` for early OAuth gate.
        """
        from ui.broker.oauth_log import fn_trace, startup_trace
        from ui.broker.state import load_broker_snapshot

        if early_oauth:
            fn_trace("BrokerSessionService.initialize", "ENTER", "early_oauth=True")
            startup_trace(2, "BrokerSessionService.initialize.early_oauth")
            self.process_oauth_callback_if_present()
            return None

        fn_trace("BrokerSessionService.initialize", "ENTER", "early_oauth=False")
        startup_trace(3, "BrokerSessionService.initialize")

        if self._oauth_callback_pending():
            from ui.broker.oauth_log import oauth_log

            oauth_log(
                "Late OAuth callback",
                "routing to BrokerSessionService — startup OAuth path removed",
            )
            self.process_oauth_callback_if_present()
            return load_broker_snapshot()

        self.restore_session()
        self.validate_session()
        self._run_broker_startup()
        return load_broker_snapshot()

    def _oauth_callback_pending(self) -> bool:
        """True when a callback URL exists but the early gate did not run."""
        try:
            import streamlit as st
            from ui.components.kite_auth import get_request_token

            return bool(get_request_token()) and not st.session_state.get(
                "_oauth_early_processed"
            )
        except Exception:
            return False

    def _run_broker_startup(self) -> None:
        """Delegate portfolio sync and session UI startup to existing pipeline."""
        from ui.components.broker_startup import run_broker_startup

        run_broker_startup()

    def restore_session(self) -> bool:
        """Load persisted access token and hydrate in-process session state.

        Delegates to ``hydrate_kite_access_token`` and ``load_env_credentials``.
        Full credential-store restore is deferred to ETS-002.1 Phase B.

        Returns:
            True if an access token is available after hydration; False otherwise.
        """
        from analyzer.zerodha import hydrate_kite_access_token, load_env_credentials

        hydrate_kite_access_token()
        creds = load_env_credentials()
        return bool(creds.get("access_token"))

    def validate_session(self) -> bool:
        """Probe broker session and clear stale expired tokens before bootstrap.

        Uses ``kite_connection_status`` probe. On ``expired``, clears the access
        token so bootstrap presents a disconnected state instead of repeated
        sync failures (ETS RC-3).

        Returns:
            True if session is usable (``ok`` or ``limited``); False otherwise.
        """
        from analyzer.kite_status import kite_connection_status
        from analyzer.zerodha import load_env_credentials

        creds = load_env_credentials()
        if not creds.get("access_token") or not creds.get("api_key"):
            return False

        status = kite_connection_status(probe=True)
        level = status.get("level", "")

        if level == "expired":
            self.clear_session()
            return False

        return level in ("ok", "limited")

    def clear_session(self) -> None:
        """Remove access token from store and in-process session without disconnect UI.

        Used when validation fails or token expiry is detected. Does not remove
        app API key/secret (one-time Zerodha Connect registration).
        """
        from analyzer.kite_status import clear_kite_probe_cache
        from analyzer.zerodha import save_access_token_to_env
        from ui.broker.oauth_log import fn_trace

        fn_trace("BrokerSessionService.clear_session", "ENTER")
        save_access_token_to_env("")
        clear_kite_probe_cache()
        try:
            import streamlit as st

            st.session_state.pop("kite_access_token", None)
            st.session_state.pop("kite_token_exchanged", None)
        except Exception:
            pass
        fn_trace("BrokerSessionService.clear_session", "EXIT")

    def disconnect(self) -> None:
        """Explicit user disconnect — clear tokens and reset ``BrokerSnapshot``.

        Distinct from ``clear_session``: user-initiated full disconnect from settings.

        Raises:
            NotImplementedError: Commit A-1 skeleton — wired in Phase C.
        """
        raise NotImplementedError(
            "ETS-002.1 Phase C: disconnect not yet implemented"
        )

    def get_health(self) -> dict[str, Any]:
        """Return connection health for sync indicators (e.g. Today header).

        Expected keys after implementation: ``state``, ``connected``,
        ``last_sync_at``, ``message``, ``needs_sign_in``.

        Returns:
            Health snapshot dict for UI rendering.

        Raises:
            NotImplementedError: Commit A-1 skeleton — wired in Phase C.
        """
        raise NotImplementedError(
            "ETS-002.1 Phase C: health probe not yet implemented"
        )

    def ensure_app_credentials(self) -> bool:
        """Ensure Zerodha API key and secret are available (one-time app registration).

        If missing, the unified broker connection wizard should render step 1.
        Replaces direct ``ensure_broker_configured()`` calls from ``app.py``.

        Returns:
            True if app credentials exist; False if wizard was shown / blocked.

        Raises:
            NotImplementedError: Commit A-1 skeleton — wired in Phase B.
        """
        raise NotImplementedError(
            "ETS-002.1 Phase B: app credential gate not yet implemented"
        )

    def get_login_url(self) -> str:
        """Build the Kite OAuth login URL for the configured API key.

        Delegates to ``get_kite_login_url`` in ``zerodha.py`` once credentials
        are loaded from the credential store.

        Returns:
            Kite v3 login URL string.

        Raises:
            NotImplementedError: Commit A-1 skeleton — wired in A-2+.
        """
        raise NotImplementedError(
            "ETS-002.1 A-2: login URL not yet implemented"
        )
